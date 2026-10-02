import asyncio

from fastapi import APIRouter

from app.services.ai import get_ai, vision_health

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    text, vision = await asyncio.gather(get_ai().health(), vision_health())
    return {"status": "ok", "ai": text, "vision": vision}
