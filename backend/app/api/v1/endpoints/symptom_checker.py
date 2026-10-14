import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.config import settings

router = APIRouter(prefix="/ai", tags=["symptom checker"])


class SymptomInput(BaseModel):
    symptoms: str = Field(min_length=3, max_length=3000)


@router.post("/symptom-check")
async def symptom_check(payload: SymptomInput):
    if not settings.groq_api_key:
        raise HTTPException(503, "Symptom checker is unavailable until GROQ_API_KEY is configured")
    request_body = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": "Offer general health information only. Never diagnose or prescribe. Mention urgent red flags and advise professional care. State clearly that this is not a diagnosis."},
            {"role": "user", "content": payload.symptoms},
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {settings.groq_api_key}"}, json=request_body)
    if response.status_code >= 400:
        raise HTTPException(502, "Symptom guidance provider returned an error")
    result = response.json()["choices"][0]["message"]["content"]
    return {"guidance": result, "disclaimer": "This is general information, not a diagnosis or a substitute for professional medical care."}
