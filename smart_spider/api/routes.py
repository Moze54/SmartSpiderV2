from fastapi import APIRouter

api_router = APIRouter()   # 原来是 router

@api_router.get("/status")
def get_status():
    return {"status": "running", "version": "0.1.0"}