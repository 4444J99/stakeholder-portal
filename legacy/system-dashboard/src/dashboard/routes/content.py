"""Content pipeline page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dashboard.data.loader import load_content_data

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/", response_class=HTMLResponse)
async def content_page(request: Request):
    data = load_content_data(request.app.state.path_config)
    return request.app.state.templates.TemplateResponse(
        request,
        name="content.html",
        context={
            "page_title": "Content Pipeline",
            "posts": data["posts"],
            "cadence": data["cadence"],
            "total": len(data["posts"]),
        },
    )
