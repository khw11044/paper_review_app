// static/js/mypage.js
document.addEventListener('DOMContentLoaded', function() {
    setupFormHandlers();
});

function setupFormHandlers() {
    // API 키 폼 제출
    document.getElementById('api-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        try {
            const response = await fetch('/user/update', {
                method: 'POST',
                body: formData,
                credentials: 'include'  // 쿠키를 요청에 포함
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    alert('API 키가 성공적으로 저장되었습니다.');
                } else {
                    alert('오류가 발생했습니다. 다시 시도해주세요.');
                }
            } else {
                if (response.status === 401) {
                    alert('세션이 만료되었습니다. 다시 로그인해주세요.');
                    window.location.href = '/login';
                } else {
                    alert('오류가 발생했습니다. 다시 시도해주세요.');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert('오류가 발생했습니다. 다시 시도해주세요.');
        }
    });
    
    // 프로필 폼 제출
    document.getElementById('profile-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        try {
            const response = await fetch('/user/update', {
                method: 'POST',
                body: formData,
                credentials: 'include'  // 쿠키를 요청에 포함
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    alert('프로필 정보가 성공적으로 저장되었습니다.');
                } else {
                    alert('오류가 발생했습니다. 다시 시도해주세요.');
                }
            } else {
                if (response.status === 401) {
                    alert('세션이 만료되었습니다. 다시 로그인해주세요.');
                    window.location.href = '/login';
                } else {
                    alert('오류가 발생했습니다. 다시 시도해주세요.');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert('오류가 발생했습니다. 다시 시도해주세요.');
        }
    });
}