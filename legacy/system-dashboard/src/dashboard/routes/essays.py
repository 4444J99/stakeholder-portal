"""Essay feed."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dashboard.data.loader import load_essays

router = APIRouter(prefix="/essays", tags=["essays"])


@router.get("/", response_class=HTMLResponse)
async def essays_page(request: Request):
    essays = load_essays(request.app.state.path_config)

    return request.app.state.templates.TemplateResponse(
        request,
        name="essays.html",
        context={
            "page_title": "Essays",
            "essays": essays,
            "total": len(essays),
        },
    )
