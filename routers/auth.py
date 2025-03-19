from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import models
import auth as auth_utils

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """로그인 처리 및 토큰 발급"""
    user = auth_utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_class=RedirectResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """로그인 폼 처리"""
    user = auth_utils.authenticate_user(db, email, password)
    if not user:
        # 로그인 실패 시 오류 메시지와 함께 로그인 페이지로 리다이렉트
        # 실제 구현에서는 메시지 전달 로직 필요
        return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)
    
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/mypage", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    
    return response

@router.post("/register", response_class=RedirectResponse)
async def register(
    request: Request,
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """회원가입 폼 처리"""
    # 이메일 중복 확인
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        # 이미 등록된 이메일인 경우
        return RedirectResponse(url="/register?error=email_exists", status_code=status.HTTP_303_SEE_OTHER)
    
    # 새 사용자 생성
    hashed_password = auth_utils.get_password_hash(password)
    new_user = models.User(email=email, name=name, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 로그인 처리
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/mypage", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        samesite="lax"  # 이 부분 추가
    )
    
    return response

@router.get("/logout", response_class=RedirectResponse)
async def logout():
    """로그아웃 처리"""
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response