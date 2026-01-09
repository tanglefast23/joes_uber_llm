"""Page rendering routes."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from joes_uber_llm.config import DEFAULT_MODELS, PROVIDER_MODELS

router = APIRouter()
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main chat page.

    Args:
        request: FastAPI request object.

    Returns:
        Rendered HTML response.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "providers": list(PROVIDER_MODELS.keys()),
            "provider_models": PROVIDER_MODELS,
            "default_models": DEFAULT_MODELS,
        },
    )
