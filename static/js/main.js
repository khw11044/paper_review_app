// 공통 JavaScript 기능

// 토큰 관리 함수
function getToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('access_token='));
    if (cookie) {
        return cookie.split('=')[1];
    }
    return null;
}

// 인증이 필요한 API 호출을 위한 기본 fetch 함수
async function fetchWithAuth(url, options = {}) {
    const token = getToken();
    
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    const headers = {
        ...options.headers,
        'Authorization': token
    };
    
    return fetch(url, {
        ...options,
        headers,
        credentials: 'include'
    });
}

// 플래시 메시지 표시 함수
function showFlashMessage(message, type = 'success') {
    // 기존 메시지 제거
    const existingMessages = document.querySelectorAll('.flash-message');
    existingMessages.forEach(el => el.remove());
    
    // 새 메시지 생성
    const flashMessage = document.createElement('div');
    flashMessage.className = `flash-message fixed top-4 right-4 p-4 rounded-lg shadow-lg fade-in z-50 ${
        type === 'success' ? 'bg-green-100 text-green-800 border-green-300' :
        type === 'error' ? 'bg-red-100 text-red-800 border-red-300' :
        'bg-blue-100 text-blue-800 border-blue-300'
    }`;
    
    // 메시지 내용
    flashMessage.innerHTML = `
        <div class="flex items-center">
            <span class="mr-2">
                ${type === 'success' ? '<i class="fas fa-check-circle"></i>' :
                type === 'error' ? '<i class="fas fa-exclamation-circle"></i>' :
                '<i class="fas fa-info-circle"></i>'}
            </span>
            <span>${message}</span>
            <button class="ml-4 text-gray-500 hover:text-gray-700 focus:outline-none" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // DOM에 추가
    document.body.appendChild(flashMessage);
    
    // 자동 제거 타이머
    setTimeout(() => {
        if (flashMessage.parentElement) {
            flashMessage.classList.remove('fade-in');
            flashMessage.style.opacity = '0';
            flashMessage.style.transition = 'opacity 0.5s ease-in-out';
            
            setTimeout(() => {
                if (flashMessage.parentElement) {
                    flashMessage.remove();
                }
            }, 500);
        }
    }, 5000);
}

// DOM이 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 모바일 메뉴 토글 (필요한 경우)
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // URL 쿼리 파라미터에서 메시지 확인
    const urlParams = new URLSearchParams(window.location.search);
    const successMsg = urlParams.get('success');
    const errorMsg = urlParams.get('error');
    
    if (successMsg) {
        showFlashMessage(decodeURIComponent(successMsg), 'success');
        
        // URL에서 쿼리 파라미터 제거
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (errorMsg) {
        showFlashMessage(decodeURIComponent(errorMsg), 'error');
        
        // URL에서 쿼리 파라미터 제거
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});