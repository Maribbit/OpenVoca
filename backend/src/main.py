import asyncio
import json
import csv
import io
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
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
    import_vocabulary,
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

# ---------------------------------------------------------------------------
# Update check
# ---------------------------------------------------------------------------

_GITHUB_REPO = "Maribbit/OpenVoca"

_update_info: dict = {
    "checked": False,
    "hasUpdate": False,
    "currentVersion": "",
    "latestVersion": "",
    "url": "",
}


def _version_gt(a: str, b: str) -> bool:
    """Return True if version string a is strictly greater than b."""
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except ValueError:
        return False


async def _check_for_updates() -> None:
    """Background startup task: query GitHub Releases for a newer version."""
    current = os.environ.get("OPENVOCA_VERSION", "").strip()
    _update_info["currentVersion"] = current
    if not current:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest",
                headers={"User-Agent": f"OpenVoca/{current}"},
            )
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v")
            url = data.get("html_url", "")
            _update_info["checked"] = True
            _update_info["latestVersion"] = latest
            _update_info["url"] = url
            _update_info["hasUpdate"] = _version_gt(latest, current)
    except Exception:  # noqa: BLE001
        pass  # network failure is expected in offline / air-gapped environments


@asynccontextmanager
async def lifespan(application: FastAPI):  # noqa: ARG001
    """Close the persistent LLM HTTP client on shutdown."""
    asyncio.create_task(_check_for_updates())
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
    original_targets: list[str] = Field(default_factory=list, alias="originalTargets")


class WordRecordOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lemma: str
    pos: str
    level: int
    cooldown: int
    first_seen: str = Field(alias="firstSeen")
    last_seen: str = Field(alias="lastSeen")
    last_context: str | None = Field(default=None, alias="lastContext")
    seen_count: int = Field(default=0, alias="seenCount")


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


@app.get("/api/update-check")
def get_update_check() -> dict:
    """Return the result of the background update check (non-blocking)."""
    return _update_info


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


@app.post("/api/reading-sentence/next/stream")
async def stream_next_reading_sentence(
    request: ReadingSentenceRequest,
) -> StreamingResponse:
    """Generate a sentence with SSE progress events.

    Events:
    - ``progress``: ``{"wordCount": N}`` — running word count
    - ``complete``: full ``ReadingSentenceResponse`` JSON
    - ``error``: ``{"detail": "..."}``
    """
    tick_cooldowns()
    final_prompt = build_sentence_generation_prompt(
        request.prompt, request.target_words
    )

    async def event_stream():  # noqa: ANN202
        accumulated = ""
        try:
            async for chunk in llm.generate_completion_stream(final_prompt):
                accumulated += chunk
                word_count = len(accumulated.split())
                yield f"event: progress\ndata: {json.dumps({'wordCount': word_count})}\n\n"
        except (httpx.HTTPError, ValueError) as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)[:300]})}\n\n"
            return

        sentence = " ".join(accumulated.split())
        if not sentence:
            yield f"event: error\ndata: {json.dumps({'detail': 'Empty response from model.'})}\n\n"
            return

        tokens = tokenize_sentence(sentence)
        result = ReadingSentenceResponse(
            sentence=sentence,
            words=request.target_words,
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
        yield f"event: complete\ndata: {result.model_dump_json(by_alias=True)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest) -> dict[str, str]:
    apply_feedback(
        target_words=[(e.lemma, e.pos) for e in request.target_words],
        marked_words=[(e.lemma, e.pos) for e in request.marked_words],
        sentence=request.sentence,
        original_targets=request.original_targets or None,
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
                level=r.level,
                cooldown=r.cooldown,
                first_seen=_utc_iso(r.first_seen),
                last_seen=_utc_iso(r.last_seen),
                last_context=r.last_context,
                seen_count=r.seen_count,
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

    level: int | None = None
    cooldown: int | None = None


@app.patch("/api/vocabulary/{lemma}/{pos}", response_model=WordRecordOut)
def patch_vocabulary_word(
    lemma: str, pos: str, body: WordRecordUpdate
) -> WordRecordOut:
    record = update_word_record(lemma, pos, level=body.level, cooldown=body.cooldown)
    if record is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return WordRecordOut(
        lemma=record.lemma,
        pos=record.pos,
        level=record.level,
        cooldown=record.cooldown,
        firstSeen=_utc_iso(record.first_seen),
        lastSeen=_utc_iso(record.last_seen),
        lastContext=record.last_context,
        seenCount=record.seen_count,
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
    writer.writerow(
        [
            "lemma",
            "pos",
            "level",
            "cooldown",
            "first_seen",
            "last_seen",
            "last_context",
            "seen_count",
        ]
    )
    for r in records:
        writer.writerow(
            [
                r.lemma,
                r.pos,
                r.level,
                r.cooldown,
                r.first_seen.isoformat() if r.first_seen else "",
                r.last_seen.isoformat() if r.last_seen else "",
                r.last_context or "",
                r.seen_count,
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=openvoca-vocabulary.csv"},
    )


class VocabularyImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@app.post("/api/vocabulary/import")
async def import_vocabulary_endpoint(
    file: UploadFile = File(...),
    mode: str = Form(default="skip"),
) -> VocabularyImportResponse:
    """Import vocabulary from a CSV file.

    mode: "skip" (default) keeps existing records; "overwrite" replaces them.
    """
    if mode not in ("skip", "overwrite"):
        raise HTTPException(
            status_code=422, detail="mode must be 'skip' or 'overwrite'"
        )

    _MAX_BYTES = 1 * 1024 * 1024  # 1 MB
    content = await file.read(_MAX_BYTES + 1)
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 1 MB)")

    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="File must be UTF-8 encoded")

    try:
        rows = list(csv.DictReader(io.StringIO(text_content)))
    except csv.Error as exc:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {exc}")

    result = import_vocabulary(rows, mode=mode)  # type: ignore[arg-type]
    return VocabularyImportResponse(
        imported=result.imported,
        skipped=result.skipped,
        errors=result.errors[:20],
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


# --- TTS (Text-to-Speech via Edge TTS) ---

_DEFAULT_VOICE = "en-US-EmmaMultilingualNeural"
_MAX_TTS_LENGTH = 2000


@app.get("/api/tts")
async def get_tts(
    text: str = Query(min_length=1, max_length=_MAX_TTS_LENGTH),
    voice: str = Query(default=_DEFAULT_VOICE, max_length=100),
) -> StreamingResponse:
    """Stream MP3 audio for the given text using Edge TTS."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice)

    async def audio_stream():  # noqa: ANN202
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception:  # noqa: BLE001
            # Edge TTS unavailable — yield nothing so the client gets
            # an empty / truncated response and can fall back to browser TTS.
            return

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "inline",
        },
    )


@app.get("/api/tts/voices")
async def get_tts_voices(
    locale: str = Query(default="en", max_length=20),
) -> list[dict[str, str]]:
    """Return available TTS voices filtered by locale prefix."""
    import edge_tts

    all_voices = await edge_tts.list_voices()
    return [
        {
            "name": v["ShortName"],
            "gender": v["Gender"],
            "locale": v["Locale"],
            "friendlyName": v["FriendlyName"],
        }
        for v in all_voices
        if v["Locale"].startswith(locale)
    ]


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
    async def spa_fallback(path: str) -> FileResponse:
        # Serve real files (e.g. favicon.svg) from dist root before SPA fallback
        candidate = _frontend_dist / path
        if candidate.is_file() and _frontend_dist in candidate.resolve().parents:
            return FileResponse(candidate)
        return FileResponse(_frontend_dist / "index.html")
