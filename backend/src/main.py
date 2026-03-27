import httpx
from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI, HTTPException

from src.integrations.ollama import OllamaClient
from src.integrations.provider import LLMProvider
from src.services.prompt_builder import build_sentence_generation_prompt
from src.services.tokenizer import tokenize_sentence
from src.services.word_store import (
    apply_feedback,
    clear_all_words,
    list_all_words,
    pick_target_words,
)

app = FastAPI(title="OpenVoca API")
llm: LLMProvider = OllamaClient()


class ReadingSentenceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_words: list[str] = Field(default_factory=list, alias="targetWords")
    prompt_template: str = Field(alias="promptTemplate", min_length=1)
    target_word_count: int = Field(default=3, alias="targetWordCount", ge=1, le=5)


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
    word: str
    pos: str


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_words: list[WordPosEntry] = Field(alias="targetWords")
    marked_words: list[WordPosEntry] = Field(alias="markedWords")
    sentence: str


class WordRecordOut(BaseModel):
    word: str
    pos: str
    familiarity: int


class VocabularyResponse(BaseModel):
    words: list[WordRecordOut]
    total: int


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "OpenVoca backend is running!"}


async def _generate_reading_response(
    words: list[str], prompt_template: str
) -> ReadingSentenceResponse:
    """Shared logic: build prompt, call LLM, tokenize, return response."""
    try:
        prompt = build_sentence_generation_prompt(words, prompt_template)
        sentence = await llm.generate_completion(prompt)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a sentence from the local Ollama model.",
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

    Falls back to frontend-provided words only for compatibility.
    """
    db_words = pick_target_words(limit=request.target_word_count)
    words = (
        db_words if db_words else [w.strip() for w in request.target_words if w.strip()]
    )
    return await _generate_reading_response(words, request.prompt_template)


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest) -> dict[str, str]:
    apply_feedback(
        target_words=[(e.word, e.pos) for e in request.target_words],
        marked_words=[(e.word, e.pos) for e in request.marked_words],
        sentence=request.sentence,
    )
    return {"status": "ok"}


@app.get("/api/vocabulary", response_model=VocabularyResponse)
def get_vocabulary() -> VocabularyResponse:
    records = list_all_words()
    return VocabularyResponse(
        words=[
            WordRecordOut(word=r.word, pos=r.pos, familiarity=r.familiarity)
            for r in records
        ],
        total=len(records),
    )


@app.delete("/api/vocabulary")
def delete_vocabulary() -> dict[str, int]:
    count = clear_all_words()
    return {"deleted": count}
