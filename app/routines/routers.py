from fastapi import APIRouter

router = APIRouter(prefix="/routines", tags=["routines"])


@router.get("/ping")
async def ping():
    return {"ok": True}
