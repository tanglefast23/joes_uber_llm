"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from joes_uber_llm.config import settings
from joes_uber_llm.routes import chat_router, pages_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Args:
        app: FastAPI application instance.

    Yields:
        None during application runtime.
    """
    logger.info("Starting Joe's Uber LLM application")
    yield
    logger.info("Shutting down Joe's Uber LLM application")


app = FastAPI(
    title="Joe's Uber LLM",
    description="A web interface for chatting with multiple LLM providers",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pages_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "joes_uber_llm.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
