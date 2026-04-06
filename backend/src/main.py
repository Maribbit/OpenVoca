import httpx
from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI, HTTPException

from src.integrations.openai_compat import OpenAICompatibleClient
from src.integrations.provider import LLMProvider
from src.services.prompt_builder import (
    build_sentence_generation_prompt,
)
from src.services.tokenizer import tokenize_sentence
from src.services.word_store import (
    apply_feedback,
    clear_all_words,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
)
from src.services.settings_store import (
    clear_all_settings,
    get_all_settings,
    get_namespace,
    init_settings_table,
    upsert_namespace,
    upsert_setting,
)

app = FastAPI(title="OpenVoca API")
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

    prompt_template: str = Field(alias="promptTemplate", min_length=1)
    target_word_count: int = Field(default=3, alias="targetWordCount", ge=1, le=5)
    composer_instructions: str = Field(
        default="", alias="composerInstructions", max_length=2000
    )


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
    last_context: str | None = Field(default=None, alias="lastContext")


class VocabularyResponse(BaseModel):
    words: list[WordRecordOut]
    total: int


@app.get("/")
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
def set_provider(config: ProviderConfig) -> dict[str, str]:
    """Switch the LLM provider at runtime and persist to settings."""
    global llm
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
    words: list[str], prompt_template: str, composer_instructions: str = ""
) -> ReadingSentenceResponse:
    """Shared logic: build prompt, call LLM, tokenize, return response."""
    try:
        prompt = build_sentence_generation_prompt(
            words, prompt_template, composer_instructions
        )
        sentence = await llm.generate_completion(prompt)
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


@app.post("/api/reading-sentence/next", response_model=ReadingSentenceResponse)
async def get_next_reading_sentence(
    request: ReadingSentenceRequest,
) -> ReadingSentenceResponse:
    """Pick target words from the database and generate a sentence.

    Ticks cooldowns before picking so words become available on schedule.
    """
    tick_cooldowns()
    words = pick_target_words(limit=request.target_word_count)

    composer_instructions = request.composer_instructions

    return await _generate_reading_response(
        words, request.prompt_template, composer_instructions
    )


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest) -> dict[str, str]:
    apply_feedback(
        target_words=[(e.lemma, e.pos) for e in request.target_words],
        marked_words=[(e.lemma, e.pos) for e in request.marked_words],
        sentence=request.sentence,
    )
    return {"status": "ok"}


@app.get("/api/vocabulary", response_model=VocabularyResponse)
def get_vocabulary() -> VocabularyResponse:
    records = list_all_words()
    return VocabularyResponse(
        words=[
            WordRecordOut(
                lemma=r.lemma,
                pos=r.pos,
                interval=r.interval,
                cooldown=r.cooldown,
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
