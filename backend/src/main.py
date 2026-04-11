import csv
import io
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from src.integrations.openai_compat import OpenAICompatibleClient
from src.integrations.provider import LLMProvider
from src.services.prompt_builder import (
    build_sentence_generation_prompt,
)
from src.services.tokenizer import tokenize_sentence
from src.services.word_store import (
    apply_feedback,
    clear_all_words,
    delete_word_record,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
    update_word_record,
)
from src.services.settings_store import (
    clear_all_settings,
    get_all_settings,
    get_namespace,
    init_settings_table,
    upsert_namespace,
    upsert_setting,
)
from src.services.dictionary import lookup as dict_lookup


@asynccontextmanager
async def lifespan(application: FastAPI):  # noqa: ARG001
    """Close the persistent LLM HTTP client on shutdown."""
    yield
    if isinstance(llm, OpenAICompatibleClient):
        await llm.aclose()


app = FastAPI(title="OpenVoca API", lifespan=lifespan)
init_settings_table()

DEFAULT_ENDPOINT = "http://localhost:11434"
DEFAULT_MODEL = ""


def _load_provider() -> OpenAICompatibleClient:
    """Build the LLM client from persisted settings (namespace 'provider')."""
    cfg = get_namespace("provider")
    return OpenAICompatibleClient(
        base_url=cfg.get("endpoint", DEFAULT_ENDPOINT),
        model=cfg.get("model", DEFAULT_MODEL),
        api_key=cfg.get("apiKey", ""),
    )


llm: LLMProvider = _load_provider()


class ReadingSentenceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: str = Field(min_length=1, max_length=5000)
    target_words: list[str] = Field(alias="targetWords")


class ReadingSentenceResponse(BaseModel):
    sentence: str
    words: list[str]
    tokens: list["ReadingSentenceToken"]


class ReadingSentenceToken(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    is_word: bool = Field(alias="isWord")
    is_target: bool = Field(default=False, alias="isTarget")
    pos: str | None = None
    lemma: str | None = None
    trailing_space: bool = Field(default=True, alias="trailingSpace")


class WordPosEntry(BaseModel):
    lemma: str
    pos: str


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_words: list[WordPosEntry] = Field(alias="targetWords")
    marked_words: list[WordPosEntry] = Field(alias="markedWords")
    sentence: str


class WordRecordOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lemma: str
    pos: str
    interval: int
    cooldown: int
    last_seen: str = Field(alias="lastSeen")
    last_context: str | None = Field(default=None, alias="lastContext")


class VocabularyResponse(BaseModel):
    words: list[WordRecordOut]
    total: int


def _utc_iso(dt: datetime) -> str:
    """Ensure a datetime is serialized with UTC offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


@app.get("/api/health")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "OpenVoca backend is running!"}


def _mask_api_key(key: str) -> str:
    """Return a masked version for safe display."""
    if len(key) <= 8:
        return "••••" if key else ""
    return key[:3] + "••••" + key[-4:]


class ProviderConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    endpoint: str = Field(default=DEFAULT_ENDPOINT, max_length=500)
    model: str = Field(default=DEFAULT_MODEL, max_length=200)
    api_key: str = Field(default="", alias="apiKey", max_length=500)


@app.get("/api/provider")
def get_provider() -> dict[str, str]:
    """Return the current LLM provider configuration (API key masked)."""
    if isinstance(llm, OpenAICompatibleClient):
        return {
            "endpoint": llm.base_url,
            "model": llm.model,
            "apiKey": _mask_api_key(llm.api_key),
        }
    return {"endpoint": DEFAULT_ENDPOINT, "model": DEFAULT_MODEL, "apiKey": ""}


@app.put("/api/provider")
async def set_provider(config: ProviderConfig) -> dict[str, str]:
    """Switch the LLM provider at runtime and persist to settings."""
    global llm
    if isinstance(llm, OpenAICompatibleClient):
        await llm.aclose()
    llm = OpenAICompatibleClient(
        base_url=config.endpoint,
        model=config.model,
        api_key=config.api_key,
    )
    # Persist for next startup
    settings: dict[str, str] = {
        "endpoint": config.endpoint,
        "model": config.model,
    }
    if config.api_key:
        settings["apiKey"] = config.api_key
    upsert_namespace("provider", settings)
    return {
        "endpoint": llm.base_url,
        "model": llm.model,
        "apiKey": _mask_api_key(llm.api_key),
    }


@app.post("/api/provider/test")
async def test_provider() -> dict[str, str | bool]:
    """Send a minimal request to verify the current LLM connection."""
    try:
        result = await llm.generate_completion("Say 'ok' and nothing else.")
        return {"ok": True, "message": result[:200]}
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "message": str(exc)[:300]}


async def _generate_reading_response(
    prompt: str, words: list[str]
) -> ReadingSentenceResponse:
    """Shared logic: finalize prompt, call LLM, tokenize, return response."""
    try:
        final_prompt = build_sentence_generation_prompt(prompt, words)
        sentence = await llm.generate_completion(final_prompt)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a sentence. Check your model configuration.",
        ) from exc

    tokens = tokenize_sentence(sentence)
    return ReadingSentenceResponse(
        sentence=sentence,
        words=words,
        tokens=[
            ReadingSentenceToken(
                text=t.text,
                is_word=t.is_word,
                is_target=t.is_target,
                pos=t.pos,
                lemma=t.lemma,
                trailing_space=t.trailing_space,
            )
            for t in tokens
        ],
    )


@app.get("/api/target-words")
def get_target_words(limit: int = 3) -> dict[str, list[str]]:
    """Pick target words that are currently available (cooldown == 0).

    Does NOT tick cooldowns — ticking happens in /api/reading-sentence/next
    to avoid burning through cooldowns on repeated page loads.
    """
    words = pick_target_words(limit=limit)
    return {"words": words}


@app.post("/api/reading-sentence/next", response_model=ReadingSentenceResponse)
async def get_next_reading_sentence(
    request: ReadingSentenceRequest,
) -> ReadingSentenceResponse:
    """Generate a sentence using the target words chosen by the user.

    Ticks cooldowns so that cooling words advance toward availability
    for the next generation cycle.
    """
    tick_cooldowns()
    return await _generate_reading_response(request.prompt, request.target_words)


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest) -> dict[str, str]:
    apply_feedback(
        target_words=[(e.lemma, e.pos) for e in request.target_words],
        marked_words=[(e.lemma, e.pos) for e in request.marked_words],
        sentence=request.sentence,
    )
    return {"status": "ok"}


@app.get("/api/vocabulary", response_model=VocabularyResponse)
def get_vocabulary(
    sort: str = Query(default="due", pattern="^(due|familiarity|recent)$"),
) -> VocabularyResponse:
    records = list_all_words(sort=sort)
    return VocabularyResponse(
        words=[
            WordRecordOut(
                lemma=r.lemma,
                pos=r.pos,
                interval=r.interval,
                cooldown=r.cooldown,
                last_seen=_utc_iso(r.last_seen),
                last_context=r.last_context,
            )
            for r in records
        ],
        total=len(records),
    )


@app.delete("/api/vocabulary")
def delete_vocabulary() -> dict[str, int]:
    count = clear_all_words()
    return {"deleted": count}


class WordRecordUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    interval: int | None = None
    cooldown: int | None = None


@app.patch("/api/vocabulary/{lemma}/{pos}", response_model=WordRecordOut)
def patch_vocabulary_word(
    lemma: str, pos: str, body: WordRecordUpdate
) -> WordRecordOut:
    record = update_word_record(
        lemma, pos, interval=body.interval, cooldown=body.cooldown
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return WordRecordOut(
        lemma=record.lemma,
        pos=record.pos,
        interval=record.interval,
        cooldown=record.cooldown,
        lastSeen=_utc_iso(record.last_seen),
        lastContext=record.last_context,
    )


@app.delete("/api/vocabulary/{lemma}/{pos}")
def delete_vocabulary_word(lemma: str, pos: str) -> dict[str, bool]:
    deleted = delete_word_record(lemma, pos)
    if not deleted:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"deleted": True}


@app.get("/api/vocabulary/export")
def export_vocabulary() -> StreamingResponse:
    """Export the vocabulary as a CSV file."""
    records = list_all_words()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["lemma", "pos", "interval", "cooldown"])
    for r in records:
        writer.writerow([r.lemma, r.pos, r.interval, r.cooldown])
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=openvoca-vocabulary.csv"},
    )


# --- Dictionary ---


@app.get("/api/dictionary/{word}")
def get_definition(word: str) -> dict:
    """Look up a word in the built-in dictionary."""
    entry = dict_lookup(word)
    if entry is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return {
        "word": entry.word,
        "phonetic": entry.phonetic,
        "definition": entry.definition,
        "translation": entry.translation,
        "pos": entry.pos,
        "tag": entry.tag,
        "exchange": entry.exchange,
    }


# --- Settings ---


class SettingValueBody(BaseModel):
    value: str = Field(min_length=1)


@app.get("/api/settings")
def get_settings_all() -> dict[str, dict[str, str]]:
    return get_all_settings()


@app.get("/api/settings/{namespace}")
def get_settings_namespace(namespace: str) -> dict[str, str]:
    return get_namespace(namespace)


@app.put("/api/settings/{namespace}/{key}")
def put_setting(namespace: str, key: str, body: SettingValueBody) -> dict[str, str]:
    upsert_setting(namespace, key, body.value)
    return {"status": "ok"}


@app.put("/api/settings/{namespace}")
def put_settings_namespace(namespace: str, settings: dict[str, str]) -> dict[str, str]:
    upsert_namespace(namespace, settings)
    return {"status": "ok"}


@app.delete("/api/settings")
def delete_all_settings() -> dict[str, int]:
    count = clear_all_settings()
    return {"deleted": count}


# --- Frontend SPA (must be last) ---

_frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _frontend_dist.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=_frontend_dist / "assets"),
        name="static-assets",
    )

    @app.get("/", include_in_schema=False)
    async def serve_root() -> FileResponse:
        return FileResponse(_frontend_dist / "index.html")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa_fallback(path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(_frontend_dist / "index.html")
