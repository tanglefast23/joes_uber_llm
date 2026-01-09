"""Route handlers for the application."""

from joes_uber_llm.routes.chat import router as chat_router
from joes_uber_llm.routes.pages import router as pages_router

__all__ = ["chat_router", "pages_router"]
