import subprocess
import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request, BackgroundTasks
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

def process_pdf_background(pdf_path, paper_id, db_session, user_id, openai_api_key, upstage_api_key):
    """
    백그라운드에서 PDF 처리 작업을 실행하는 함수.
    pdf_processor.py를 호출하여 PDF 분석, 요약, 번역 등의 작업을 진행하며,
    paper_id 인자를 함께 전달하여 분석 결과가 해당 Paper 레코드에 업데이트되도록 합니다.
    """
    try:
        os.environ["OPENAI_API_KEY"] = openai_api_key
        os.environ["UPSTAGE_API_KEY"] = upstage_api_key
        
        result = subprocess.run(
            [
                "python", "pdf_processor.py",
                "--file_path", pdf_path,
                "--model", "gpt-4o-mini",
                "--openai_api", openai_api_key,
                "--upstage_api", upstage_api_key,
                "--paper_id", str(paper_id)
            ],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except Exception as e:
        paper = db_session.query(models.Paper).filter(
            models.Paper.id == paper_id,
            models.Paper.user_id == user_id
        ).first()
        if paper:
            paper.processing_status = "failed"
            paper.error_message = str(e)
            db_session.commit()
        print(f"PDF 처리 오류: {str(e)}")

@router.post("/upload")
async def upload_paper(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """논문 PDF 업로드 엔드포인트"""
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    if not user.openai_api:
        raise HTTPException(status_code=400, detail="OpenAI API key is not set. Please set your API keys in the profile page.")
    if not user.upstage_api:
        raise HTTPException(status_code=400, detail="Upstage API key is not set. Please set your API keys in the profile page.")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    if not title:
        title = os.path.splitext(file.filename)[0]
    
    new_paper = models.Paper(
        title=title,
        user_id=user.id,
        original_content="",
        pdf_path=file_path,
        processing_status="processing"
    )
    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)
    
    # paper_id 인자 포함하여 백그라운드 작업 실행
    background_tasks.add_task(
        process_pdf_background,
        file_path,
        new_paper.id,
        db,
        user.id,
        user.openai_api,
        user.upstage_api
    )
    
    return {"status": "success", "paper_id": new_paper.id, "message": "Paper uploaded and processing started"}

@router.get("/status/{paper_id}")
async def get_paper_status(request: Request, paper_id: int, db: Session = Depends(get_db)):
    """Paper 상태와 일부 정보(오류 메시지 등)를 반환하는 엔드포인트"""
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    paper = db.query(models.Paper).filter(
        models.Paper.id == paper_id,
        models.Paper.user_id == user.id
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "id": paper.id,
        "title": paper.title,
        "status": paper.processing_status,
        "error_message": getattr(paper, "error_message", None)
    }

@router.get("/data/{paper_id}")
async def get_paper_data(request: Request, paper_id: int, db: Session = Depends(get_db)):
    """Paper 분석 결과(마크다운 내용)를 JSON으로 반환하는 엔드포인트"""
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    paper = db.query(models.Paper).filter(
        models.Paper.id == paper_id,
        models.Paper.user_id == user.id
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "original_content": paper.original_content,
        "english_summary": paper.english_summary,
        "translation": paper.translation,
        "korean_summary": paper.korean_summary
    }

# 새로 추가된 엔드포인트
@router.post("/save/{paper_id}")
async def save_paper_analysis(
    request: Request,
    paper_id: int, 
    original_content: str = Form(""),
    english_summary: str = Form(""),
    translation: str = Form(""),
    korean_summary: str = Form(""),
    db: Session = Depends(get_db)
):
    """논문 분석 결과 저장 엔드포인트"""
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    paper = db.query(models.Paper).filter(
        models.Paper.id == paper_id,
        models.Paper.user_id == user.id
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # 폼 데이터로 Paper 모델 업데이트
    if original_content:
        paper.original_content = original_content
    if english_summary:
        paper.english_summary = english_summary
    if translation:
        paper.translation = translation
    if korean_summary:
        paper.korean_summary = korean_summary
    
    # 처리 상태를 'completed'로 설정
    paper.processing_status = "completed"
    
    # 변경사항 DB에 반영
    db.commit()
    
    return {"status": "success", "message": "Paper analysis saved successfully"}