from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"

app = FastAPI(title="Local Embedding API")

model = SentenceTransformer(MODEL_NAME)

class EmbedRequest(BaseModel):
    text: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "model": MODEL_NAME}

@app.post("/embed")
def embed(payload: EmbedRequest):
    embedding = model.encode(payload.text, normalize_embeddings=True)
    return {
        "model": MODEL_NAME,
        "dimension": len(embedding),
        "embedding": embedding.tolist(),
    }