// paper_review.js

// 헬퍼 함수: 페이지에서 loading-overlay 요소를 반환
function getLoadingOverlay() {
  return document.getElementById('loading-overlay');
}

// DOMContentLoaded 이벤트
document.addEventListener('DOMContentLoaded', function() {
  // API 키 확인
  if (typeof hasApiKeys !== 'undefined' && !hasApiKeys) {
    showApiKeyWarning();
  }

  // 왼쪽 탭 전환 기능
  const leftTabButtons = document.querySelectorAll('.left-tab-button');
  const leftTabContents = document.querySelectorAll('.left-tab-content');
  leftTabButtons.forEach(button => {
    button.addEventListener('click', () => {
      leftTabButtons.forEach(btn => {
        btn.classList.remove('border-indigo-600', 'text-indigo-600');
        btn.classList.add('border-transparent', 'text-gray-500');
      });
      button.classList.remove('border-transparent', 'text-gray-500');
      button.classList.add('border-indigo-600', 'text-indigo-600');

      const tabId = button.getAttribute('data-tab');
      leftTabContents.forEach(content => {
        content.classList.add('hidden');
      });
      // 각 탭은 id 형식: upload-tab, original-tab, english-summary-tab 등
      document.getElementById(`${tabId}-tab`).classList.remove('hidden');
    });
  });

  // 오른쪽 탭 전환 기능
  const rightTabButtons = document.querySelectorAll('.right-tab-button');
  const rightTabContents = document.querySelectorAll('.right-tab-content');
  rightTabButtons.forEach(button => {
    button.addEventListener('click', () => {
      rightTabButtons.forEach(btn => {
        btn.classList.remove('border-indigo-600', 'text-indigo-600');
        btn.classList.add('border-transparent', 'text-gray-500');
      });
      button.classList.remove('border-transparent', 'text-gray-500');
      button.classList.add('border-indigo-600', 'text-indigo-600');

      const tabId = button.getAttribute('data-tab');
      rightTabContents.forEach(content => {
        content.classList.add('hidden');
      });
      document.getElementById(`${tabId}-tab`).classList.remove('hidden');
    });
  });

  // PDF 파일 업로드 처리 (업로드 탭 전용)
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('pdf-upload');
  const loadingOverlay = getLoadingOverlay();
  if (dropZone && fileInput) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, preventDefaults, false);
    });
    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });
    dropZone.addEventListener('drop', handleDrop, false);
    function handleDrop(e) {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length) {
        handleFiles(files);
      }
    }
    fileInput.addEventListener('change', function() {
      if (fileInput.files.length) {
        handleFiles(fileInput.files);
      }
    });
  }

  // 저장 버튼 이벤트
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

// 진행 상태 애니메이션 함수들
let progressInterval;
function startProgressAnimation() {
  let progress = 5;
  const progressBar = document.getElementById('progress-bar');
  progressInterval = setInterval(() => {
    if (progress < 95) {
      progress += Math.random() * 2;
      progressBar.style.width = `${progress}%`;
    }
  }, 2000);
}
function stopProgressAnimation() {
  clearInterval(progressInterval);
  const progressBar = document.getElementById('progress-bar');
  progressBar.style.width = '100%';
  setTimeout(() => {
    progressBar.style.width = '5%';
  }, 1000);
}

// PDF 처리 상태 확인 함수
function checkPaperStatus(paperId) {
  const loadingOverlay = getLoadingOverlay();
  fetch(`/paper/status/${paperId}`, {
    method: 'GET',
    credentials: 'include'
  })
  .then(response => {
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    return response.json();
  })
  .then(data => {
    if (data.status === 'processing') {
      setTimeout(() => checkPaperStatus(paperId), 3000);
      document.getElementById('loading-status').textContent = '논문 분석 중... 몇 분 정도 소요될 수 있습니다.';
    } else if (data.status === 'completed') {
      stopProgressAnimation();
      loadingOverlay.classList.add('hidden');
      fetchPaperData(paperId);
    } else if (data.status === 'failed') {
      stopProgressAnimation();
      loadingOverlay.classList.add('hidden');
      alert(`논문 처리 실패: ${data.error_message || '알 수 없는 오류'}`);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    stopProgressAnimation();
    loadingOverlay.classList.add('hidden');
    alert('상태 확인 중 오류 발생: ' + error.message);
  });
}

// 파일 처리 및 업로드 함수
function handleFiles(files) {
  const file = files[0];
  const loadingOverlay = getLoadingOverlay();
  if (file.type !== 'application/pdf') {
    alert('PDF 파일만 업로드할 수 있습니다.');
    return;
  }
  loadingOverlay.classList.remove('hidden');
  document.getElementById('loading-status').textContent = '파일 업로드 중...';
  startProgressAnimation();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', file.name.replace('.pdf', ''));
  fetch('/paper/upload', {
    method: 'POST',
    body: formData,
    credentials: 'include'
  })
  .then(response => {
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    return response.json();
  })
  .then(data => {
    if (data.status === 'success') {
      document.getElementById('loading-status').textContent = '논문 분석 시작...';
      checkPaperStatus(data.paper_id);
    } else {
      stopProgressAnimation();
      loadingOverlay.classList.add('hidden');
      alert('파일 업로드 실패: ' + (data.message || '알 수 없는 오류'));
    }
  })
  .catch(error => {
    console.error('Error:', error);
    stopProgressAnimation();
    loadingOverlay.classList.add('hidden');
    alert('파일 업로드 중 오류 발생: ' + error.message);
  });
}

// 논문 데이터 가져오기 및 UI 업데이트 (마크다운 데이터 -> HTML 변환)
function fetchPaperData(paperId) {
  const loadingOverlay = getLoadingOverlay();
  fetch(`/paper/data/${paperId}`, {
    method: 'GET',
    credentials: 'include'
  })
  .then(response => {
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    return response.json();
  })
  .then(data => {
    loadingOverlay.classList.add('hidden');
    updateUIWithPaperData(data, paperId);
  })
  .catch(error => {
    console.error('Error:', error);
    loadingOverlay.classList.add('hidden');
    alert('논문 데이터를 가져오는 중 오류 발생: ' + error.message);
  });
}

// UI 업데이트: 각 탭에 마크다운 콘텐츠를 HTML로 렌더링하여 표시
function updateUIWithPaperData(paper, paperId) {
  const originalContentDiv = document.getElementById('original-content');
  originalContentDiv.innerHTML = marked.parse(paper.original_content || '원본 내용이 없습니다.');

  const englishSummaryDiv = document.getElementById('english-summary-content');
  englishSummaryDiv.innerHTML = marked.parse(paper.english_summary || '영어 요약 데이터가 없습니다.');

  // 오른쪽 탭 콘텐츠 (번역, 한국어 요약) - 해당 탭에도 마크다운 렌더링 적용
  const translationContentDiv = document.getElementById('translation-content');
  translationContentDiv.innerHTML = marked.parse(paper.translation || '번역 데이터가 없습니다.');

  const koreanSummaryDiv = document.getElementById('korean-summary-content');
  koreanSummaryDiv.innerHTML = marked.parse(paper.korean_summary || '한국어 요약 데이터가 없습니다.');

  // 탭 전환: 기본적으로 원본 탭을 활성화
  const originalTabButton = document.querySelector('.left-tab-button[data-tab="original"]');
  if (originalTabButton) originalTabButton.click();

  // 저장 버튼 활성화
  const saveButtonContainer = document.getElementById('save-button-container');
  saveButtonContainer.classList.remove('hidden');
  const saveButton = document.getElementById('save-button');
  saveButton.setAttribute('data-paper-id', paperId);
}

// 논문 분석 결과 저장 함수
function savePaperAnalysis(paperId) {
  const originalContent = document.querySelector('#original-tab .markdown-body')?.innerHTML || '';
  const englishSummary = document.querySelector('#english-summary-tab .markdown-body')?.innerHTML || '';
  const translation = document.querySelector('#translation-tab .markdown-body')?.innerHTML || '';
  const koreanSummary = document.querySelector('#korean-summary-tab .markdown-body')?.innerHTML || '';

  const formData = new FormData();
  formData.append('original_content', originalContent);
  formData.append('english_summary', englishSummary);
  formData.append('translation', translation);
  formData.append('korean_summary', koreanSummary);

  fetch(`/paper/save/${paperId}`, {
    method: 'POST',
    body: formData,
    credentials: 'include'
  })
  .then(response => {
    if (!response.ok) {
      if (response.status === 401) {
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
      window.location.href = '/mypage';
    } else {
      alert('저장에 실패했습니다: ' + (data.message || '알 수 없는 오류'));
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('저장 중 오류 발생: ' + error.message);
  });
}

// API 키 경고 표시 함수
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
          <strong>API 키가 설정되지 않았습니다.</strong> 논문 분석을 위해서는 OpenAI API 키와 Upstage API 키가 모두 필요합니다.
          <a href="/mypage" class="font-medium underline">마이페이지</a>에서 API 키를 설정해주세요.
        </p>
      </div>
    </div>
  `;
  const contentContainer = document.querySelector('.paper-container');
  contentContainer.parentNode.insertBefore(warningDiv, contentContainer);
}
