from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import models
import auth as auth_utils

router = APIRouter()

@router.post("/update")
async def update_user_info(
    request: Request,
    name: str = Form(None),
    openai_api: str = Form(None),
    gemini_api: str = Form(None),
    db: Session = Depends(get_db)
):
    """사용자 정보 업데이트"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # 업데이트할 필드 확인
    update_data = {}
    if name:
        update_data["name"] = name
    if openai_api:
        update_data["openai_api"] = openai_api
    if gemini_api:
        update_data["gemini_api"] = gemini_api
    
    if update_data:
        # 사용자 정보 업데이트
        db.query(models.User).filter(models.User.id == user.id).update(update_data)
        db.commit()
    
    return {"status": "success", "message": "User information updated successfully"}

@router.get("/api-keys")
async def get_api_keys(
    request: Request,
    db: Session = Depends(get_db)
):
    """사용자 API 키 정보 조회"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    return {
        "openai_api": user.openai_api,
        "gemini_api": user.gemini_api
    }