from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from pathlib import Path

from models import models
from database import engine, get_db
from routers import auth, user, paper
import auth as auth_utils

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLM Paper Review for Arobot")

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 라우터 포함
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(paper.router, prefix="/paper", tags=["paper"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """홈페이지 렌더링"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지 렌더링"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """회원가입 페이지 렌더링"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/mypage", response_class=HTMLResponse)
async def mypage(request: Request, db: Session = Depends(get_db)):
    """마이페이지 렌더링"""
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    papers = db.query(models.Paper).filter(models.Paper.user_id == user.id).all()
    return templates.TemplateResponse("mypage.html", {
        "request": request, 
        "user": user,
        "papers": papers
    })

@app.get("/paper/review", response_class=HTMLResponse)
async def paper_review(request: Request, db: Session = Depends(get_db)):
    """논문 리뷰 페이지 렌더링"""
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("paper_review.html", {"request": request, "user": user})

@app.get("/paper/{paper_id}", response_class=HTMLResponse)
async def view_paper(request: Request, paper_id: int, db: Session = Depends(get_db)):
    """저장된 논문 보기"""
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    paper = db.query(models.Paper).filter(models.Paper.id == paper_id, models.Paper.user_id == user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return templates.TemplateResponse("paper_review.html", {
        "request": request, 
        "user": user,
        "paper": paper
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)