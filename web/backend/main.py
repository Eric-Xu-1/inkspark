"""InkSpark Web API entry point."""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from routes.conversations import router as conv_router
from routes.stream import router as stream_router

app = FastAPI(title="InkSpark API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conv_router)
app.include_router(stream_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "5000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
