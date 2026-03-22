import httpx
from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI, HTTPException

from src.integrations.ollama import OllamaClient
from src.services.tokenizer import tokenize_sentence
from src.services.word_store import (
    apply_feedback,
    clear_all_words,
    list_all_words,
    pick_target_words,
)

app = FastAPI(title="OpenVoca API")
ollama_client = OllamaClient()


class ReadingSentenceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_words: list[str] = Field(alias="targetWords", min_length=1)
    prompt_template: str = Field(alias="promptTemplate", min_length=1)


class ReadingSentenceResponse(BaseModel):
    sentence: str
    words: list[str]
    tokens: list["ReadingSentenceToken"]


class ReadingSentenceToken(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    is_word: bool = Field(alias="isWord")


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_words: list[str] = Field(alias="targetWords")
    marked_words: list[str] = Field(alias="markedWords")
    sentence: str


class WordRecordOut(BaseModel):
    word: str
    familiarity: int


class VocabularyResponse(BaseModel):
    words: list[WordRecordOut]
    total: int


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "OpenVoca backend is running!"}


@app.post("/api/reading-sentence", response_model=ReadingSentenceResponse)
async def get_reading_sentence(
    request: ReadingSentenceRequest,
) -> ReadingSentenceResponse:
    try:
        words = [word.strip() for word in request.target_words if word.strip()]
        sentence = await ollama_client.generate_sentence(
            words,
            request.prompt_template,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a sentence from the local Ollama model.",
        ) from exc

    return ReadingSentenceResponse(
        sentence=sentence,
        words=words,
        tokens=[
            ReadingSentenceToken(text=token.text, isWord=token.is_word)
            for token in tokenize_sentence(sentence)
        ],
    )


@app.post("/api/reading-sentence/next", response_model=ReadingSentenceResponse)
async def get_next_reading_sentence(
    request: ReadingSentenceRequest,
) -> ReadingSentenceResponse:
    """Pick target words from the database and generate a sentence.

    Falls back to the frontend-provided target words when the database is empty.
    """
    db_words = pick_target_words(limit=3)
    words = (
        db_words if db_words else [w.strip() for w in request.target_words if w.strip()]
    )

    try:
        sentence = await ollama_client.generate_sentence(
            words,
            request.prompt_template,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a sentence from the local Ollama model.",
        ) from exc

    return ReadingSentenceResponse(
        sentence=sentence,
        words=words,
        tokens=[
            ReadingSentenceToken(text=token.text, isWord=token.is_word)
            for token in tokenize_sentence(sentence)
        ],
    )


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest) -> dict[str, str]:
    apply_feedback(
        target_words=request.target_words,
        marked_words=request.marked_words,
        sentence=request.sentence,
    )
    return {"status": "ok"}


@app.get("/api/vocabulary", response_model=VocabularyResponse)
def get_vocabulary() -> VocabularyResponse:
    records = list_all_words()
    return VocabularyResponse(
        words=[WordRecordOut(word=r.word, familiarity=r.familiarity) for r in records],
        total=len(records),
    )


@app.delete("/api/vocabulary")
def delete_vocabulary() -> dict[str, int]:
    count = clear_all_words()
    return {"deleted": count}
