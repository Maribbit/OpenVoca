import httpx
from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI, HTTPException

from src.integrations.ollama import OllamaClient

app = FastAPI(title="OpenVoca API")
ollama_client = OllamaClient()


class ReadingSentenceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_words: list[str] = Field(alias="targetWords", min_length=1)
    prompt_template: str = Field(alias="promptTemplate", min_length=1)


class ReadingSentenceResponse(BaseModel):
    sentence: str
    words: list[str]


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
    )
