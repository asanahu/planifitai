from fastapi import APIRouter

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/ping")
async def ping():
    return {"ok": True}
