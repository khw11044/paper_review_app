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
    """백그라운드에서 PDF 처리 작업을 실행하는 함수"""
    try:
        # 환경변수 설정
        os.environ["OPENAI_API_KEY"] = openai_api_key
        os.environ["UPSTAGE_API_KEY"] = upstage_api_key
        
        # PDF 분석 스크립트 실행
        result = subprocess.run(
            ["python", "main.py", "--file_path", pdf_path, "--model", "gpt-4o-mini"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 결과 파일 경로 생성
        base_dir = os.path.splitext(pdf_path)[0]
        filename = os.path.basename(pdf_path).split('.')[0]
        
        # 생성된 파일 경로
        original_md = f"{base_dir}/{filename}.md"
        english_summary = f"{base_dir}/{filename}_summary_en.md"
        translation = f"{base_dir}/{filename}_trans.md"
        korean_summary = f"{base_dir}/{filename}_summary_ko.md"
        
        # 파일 내용 읽기
        with open(original_md, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        with open(english_summary, 'r', encoding='utf-8') as f:
            english_summary_content = f.read()
            
        with open(translation, 'r', encoding='utf-8') as f:
            translation_content = f.read()
            
        with open(korean_summary, 'r', encoding='utf-8') as f:
            korean_summary_content = f.read()
        
        # 논문 정보 업데이트
        paper = db_session.query(models.Paper).filter(
            models.Paper.id == paper_id, 
            models.Paper.user_id == user_id
        ).first()
        
        if paper:
            paper.original_content = original_content
            paper.english_summary = english_summary_content
            paper.translation = translation_content
            paper.korean_summary = korean_summary_content
            paper.processing_status = "completed"
            db_session.commit()
    except Exception as e:
        # 오류 시 상태 업데이트
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
    """논문 PDF 업로드"""
    # 쿠키에서 사용자 인증
    user = await auth_utils.get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # 두 API 키 모두 확인
    if not user.openai_api:
        raise HTTPException(status_code=400, detail="OpenAI API key is not set. Please set your API keys in the profile page.")
    
    if not user.upstage_api:
        raise HTTPException(status_code=400, detail="Upstage API key is not set. Please set your API keys in the profile page.")
    
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
    
    # 논문 정보 저장
    new_paper = models.Paper(
        title=title,
        user_id=user.id,
        original_content="", # 초기 빈 문자열
        pdf_path=file_path,
        processing_status="processing"  # 처리 상태 추가
    )
    
    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)
    
    # 백그라운드에서 PDF 처리 작업 시작
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
async def get_paper_status(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db)
):
    """논문 처리 상태 확인"""
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
        "status": paper.processing_status,
        "error_message": paper.error_message if hasattr(paper, 'error_message') else None
    }