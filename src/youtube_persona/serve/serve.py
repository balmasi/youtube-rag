#!/usr/bin/env python
from fastapi import FastAPI
from langserve import add_routes

from youtube_persona.serve.retrieval import chain

app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
)

add_routes(
    app,
    chain,
    path="/chat",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)