from fastapi import FastAPI, UploadFile, Form
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests

from .app.endpoints import sketch, user, clone

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(sketch.router)

app.include_router(sketch.router)
app.include_router(user.router)
app.include_router(clone.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
