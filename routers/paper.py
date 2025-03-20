import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import aiofiles
from datetime import datetime
from database import get_db
from models import models
import auth as auth_utils

router = APIRouter()

# PDF 파일 저장 경로
UPLOAD_DIR = "static/uploads/pdf"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_paper(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """논문 PDF 업로드"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # 파일 확장자 확인
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # 파일 저장 경로 생성
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # 파일 저장
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # 제목이 없으면 파일 이름에서 추출
    if not title:
        title = os.path.splitext(file.filename)[0]
    
    # 논문 정보 저장 (LangChain 통합 이전 임시 저장)
    new_paper = models.Paper(
        title=title,
        user_id=user.id,
        original_content="", # 임시 빈 문자열, LangChain으로 처리 후 업데이트 예정
        pdf_path=file_path
    )
    
    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)
    
    return {"status": "success", "paper_id": new_paper.id, "message": "Paper uploaded successfully"}

@router.post("/save/{paper_id}")
async def save_paper_analysis(
    request: Request,
    paper_id: int,
    original_content: str = Form(...),
    translation: str = Form(None),
    english_summary: str = Form(None),
    korean_summary: str = Form(None),
    db: Session = Depends(get_db)
):
    """논문 분석 결과 저장"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # 논문 존재 확인
    paper = db.query(models.Paper).filter(
        models.Paper.id == paper_id, 
        models.Paper.user_id == user.id
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # 논문 정보 업데이트
    update_data = {
        "original_content": original_content
    }
    
    if translation:
        update_data["translation"] = translation
    
    if english_summary:
        update_data["english_summary"] = english_summary
    
    if korean_summary:
        update_data["korean_summary"] = korean_summary
    
    db.query(models.Paper).filter(models.Paper.id == paper_id).update(update_data)
    db.commit()
    
    return {"status": "success", "message": "Paper analysis saved successfully"}

@router.get("/list")
async def list_papers(
    request: Request,
    db: Session = Depends(get_db)
):
    """사용자의 논문 목록 조회"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    papers = db.query(models.Paper).filter(models.Paper.user_id == user.id).all()
    
    result = []
    for paper in papers:
        result.append({
            "id": paper.id,
            "title": paper.title,
            "created_at": paper.created_at
        })
    
    return result

@router.get("/{paper_id}")
async def get_paper(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db)
):
    """특정 논문 정보 조회"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    paper = db.query(models.Paper).filter(
        models.Paper.id == paper_id, 
        models.Paper.user_id == user.id
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "id": paper.id,
        "title": paper.title,
        "original_content": paper.original_content,
        "translation": paper.translation,
        "summary": paper.summary,
        "references": paper.references,
        "created_at": paper.created_at
    }

@router.delete("/{paper_id}")
async def delete_paper(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db)
):
    """논문 삭제"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    paper = db.query(models.Paper).filter(
        models.Paper.id == paper_id, 
        models.Paper.user_id == user.id
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # PDF 파일 삭제
    if paper.pdf_path and os.path.exists(paper.pdf_path):
        os.remove(paper.pdf_path)
    
    # 데이터베이스에서 삭제
    db.delete(paper)
    db.commit()
    
    return {"status": "success", "message": "Paper deleted successfully"}