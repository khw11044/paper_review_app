// paper_review.js
document.addEventListener('DOMContentLoaded', function() {
    // API 키 확인
    if (typeof hasApiKeys !== 'undefined' && !hasApiKeys) {
        showApiKeyWarning();
    }
    
    // 탭 전환 기능
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // 활성 탭 버튼 스타일 변경
            tabButtons.forEach(btn => {
                btn.classList.remove('border-indigo-600', 'text-indigo-600');
                btn.classList.add('border-transparent', 'text-gray-500');
            });
            button.classList.remove('border-transparent', 'text-gray-500');
            button.classList.add('border-indigo-600', 'text-indigo-600');
            
            // 탭 콘텐츠 전환
            const tabId = button.getAttribute('data-tab');
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
    
    // PDF 파일 업로드 처리
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('pdf-upload');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    if (dropZone && fileInput) {
        // 드래그 앤 드롭 이벤트
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropZone.classList.add('dragover');
        }
        
        function unhighlight() {
            dropZone.classList.remove('dragover');
        }
        
        // 파일 드롭 처리
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length) {
                handleFiles(files);
            }
        }
        
        // 파일 선택 처리
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length) {
                handleFiles(fileInput.files);
            }
        });
    }
    
    // 저장 버튼 이벤트 추가
    const saveButton = document.getElementById('save-button');
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            const paperId = this.getAttribute('data-paper-id');
            if (paperId) {
                savePaperAnalysis(paperId);
            }
        });
    }
});

function handleFiles(files) {
    const file = files[0];
    const loadingOverlay = document.getElementById('loading-overlay');
    
    if (file.type !== 'application/pdf') {
        alert('PDF 파일만 업로드할 수 있습니다.');
        return;
    }
    
    // 로딩 오버레이 표시
    loadingOverlay.classList.remove('hidden');
    document.getElementById('loading-status').textContent = '파일 업로드 중...';
    
    // FormData 생성
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace('.pdf', ''));
    
    // 서버에 업로드
    fetch('/paper/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'  // 쿠키를 요청에 포함
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('loading-status').textContent = '논문 분석 중...';
            
            // 여기서 실제 논문 데이터를 불러오는 요청을 보냅니다
            fetchPaperData(data.paper_id);
        } else {
            loadingOverlay.classList.add('hidden');
            alert('파일 업로드에 실패했습니다: ' + (data.message || '알 수 없는 오류'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        loadingOverlay.classList.add('hidden');
        alert('파일 업로드 중 오류가 발생했습니다: ' + error.message);
    });
}

// 논문 데이터 가져오기
function fetchPaperData(paperId) {
    const loadingOverlay = document.getElementById('loading-overlay');
    
    fetch(`/paper/${paperId}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        loadingOverlay.classList.add('hidden');
        
        // 논문 데이터로 UI 업데이트
        updateUIWithPaperData(data, paperId);
    })
    .catch(error => {
        console.error('Error:', error);
        loadingOverlay.classList.add('hidden');
        alert('논문 데이터를 가져오는 중 오류가 발생했습니다: ' + error.message);
    });
}

// UI 업데이트 함수
function updateUIWithPaperData(paper, paperId) {
    // 원본 내용 업데이트
    const originalContentContainer = document.querySelector('.markdown-body') || 
                                   document.createElement('div');
    originalContentContainer.classList.add('markdown-body');
    originalContentContainer.innerHTML = paper.original_content || '<p>원본 내용이 없습니다.</p>';
    
    if (!document.querySelector('.markdown-body')) {
        const originalPanel = document.querySelector('#drop-zone').parentElement;
        originalPanel.innerHTML = '';
        originalPanel.appendChild(originalContentContainer);
    }
    
    // 번역, 요약, 참조 업데이트
    document.getElementById('translation-tab').innerHTML = 
        `<div class="markdown-body">${paper.translation || '<p>번역 데이터가 없습니다.</p>'}</div>`;
    
    document.getElementById('summary-tab').innerHTML = 
        `<div class="markdown-body">${paper.summary || '<p>요약 데이터가 없습니다.</p>'}</div>`;
    
    document.getElementById('references-tab').innerHTML = 
        `<div class="markdown-body">${paper.references || '<p>참조 데이터가 없습니다.</p>'}</div>`;
    
    // 저장 버튼 표시
    const saveButtonContainer = document.getElementById('save-button-container');
    saveButtonContainer.classList.remove('hidden');
    
    // 저장 버튼에 논문 ID 저장
    const saveButton = document.getElementById('save-button');
    saveButton.setAttribute('data-paper-id', paperId);
}

// 논문 분석 결과 저장
function savePaperAnalysis(paperId) {
    // 실제로는 탭에 표시된 결과를 가져와서 저장
    const originalContent = document.querySelector('.markdown-body')?.innerHTML || '';
    const translation = document.querySelector('#translation-tab .markdown-body')?.innerHTML || '';
    const summary = document.querySelector('#summary-tab .markdown-body')?.innerHTML || '';
    const references = document.querySelector('#references-tab .markdown-body')?.innerHTML || '';
    
    const formData = new FormData();
    formData.append('original_content', originalContent);
    formData.append('translation', translation);
    formData.append('summary', summary);
    formData.append('references', references);
    
    fetch(`/paper/save/${paperId}`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                // 인증 오류
                window.location.href = '/login';
                throw new Error('인증이 필요합니다. 다시 로그인해주세요.');
            }
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            alert('논문 분석 결과가 저장되었습니다.');
            // 마이페이지로 리다이렉트
            window.location.href = '/mypage';
        } else {
            alert('저장에 실패했습니다: ' + (data.message || '알 수 없는 오류'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('저장 중 오류가 발생했습니다: ' + error.message);
    });
}

function showApiKeyWarning() {
    const warningDiv = document.createElement('div');
    warningDiv.className = 'bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4';
    warningDiv.innerHTML = `
        <div class="flex">
            <div class="flex-shrink-0">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="ml-3">
                <p class="text-sm">
                    API 키가 설정되지 않았습니다. 논문 분석을 위해 <a href="/mypage" class="font-medium underline">마이페이지</a>에서 API 키를 설정해주세요.
                </p>
            </div>
        </div>
    `;
    
    // 페이지 상단에 경고 메시지 추가
    const contentContainer = document.querySelector('.paper-container');
    contentContainer.parentNode.insertBefore(warningDiv, contentContainer);
}