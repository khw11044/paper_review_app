
## 앱 구조 

```markdown

paper_review_app/
├── main.py                # FastAPI 메인 애플리케이션
├── database.py            # 데이터베이스 연결 설정
├── auth.py                # 인증 유틸리티
├── models/
│   └── models.py           # 사용자 및 논문 모델
├── routers/
│   ├── auth.py            # 인증 관련 라우터
│   ├── user.py            # 사용자 관련 라우터
│   └── paper.py           # 논문 관련 라우터
├── static/
│   ├── css/               # CSS 파일
│   ├── js/                # JavaScript 파일
│   └── images/            # 이미지 파일
└── templates/             # HTML 템플릿
    ├── base.html          # 기본 템플릿
    ├── index.html         # 홈페이지
    ├── login.html         # 로그인 페이지
    ├── register.html      # 회원가입 페이지
    ├── mypage.html        # 마이페이지
    └── paper_review.html  # 논문 읽기 페이지

```

# 프로젝트 주요 구성 요소

## 메인 애플리케이션

- main.py: FastAPI 앱 설정 및 라우팅
- database.py: SQLite 데이터베이스 연결
- auth.py: JWT 기반 인증 로직

## 데이터베이스 모델

- models/models.py: User와 Paper 모델 정의


## API 라우터

- routers/auth.py: 로그인, 회원가입 등 인증 API
- routers/user.py: 사용자 정보 관리 API
- routers/paper.py: 논문 업로드 및 분석 API


## HTML 템플릿

- templates/base.html: 기본 레이아웃
- templates/index.html: 홈페이지
- templates/login.html & register.html: 인증 페이지
- templates/mypage.html: 사용자 프로필 및 API 키 관리
- templates/paper_review.html: 논문 분석 페이지


## 정적 파일

- static/css/style.css: 커스텀 스타일
- static/js/main.js: 공통 JavaScript 함수


## 가상환경 준비

```
conda create -n paper python=3.11 -y

conda activate paper
```

## 종속성 

```
pip install -r requirements.txt
```