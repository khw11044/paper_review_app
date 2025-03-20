document.addEventListener('DOMContentLoaded', function() {
    // 플래시 메시지 표시 함수
    function showFlashMessage(message, type) {
        const existing = document.querySelector('.mypage-flash');
        if (existing) existing.remove();
        
        const flash = document.createElement('div');
        flash.className = `mypage-flash fixed top-4 right-4 p-4 rounded shadow ${
            type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`;
        flash.textContent = message;
        document.body.appendChild(flash);
        
        setTimeout(() => {
            flash.remove();
        }, 5000);
    }

    // 폼 데이터를 AJAX로 제출하는 함수
    async function submitForm(form) {
        const formData = new FormData(form);
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });
            if (!response.ok) {
                throw new Error(`서버 오류: ${response.status}`);
            }
            const result = await response.json();
            showFlashMessage(result.message, 'success');
            // 최신 사용자 정보를 반영하기 위해 페이지 새로 고침
            window.location.reload();
        } catch (error) {
            showFlashMessage(error.message, 'error');
        }
    }

    // 프로필 정보 폼 처리
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm(profileForm);
        });
    }

    // API 키 관리 폼 처리
    const apiForm = document.getElementById('api-form');
    if (apiForm) {
        apiForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm(apiForm);
        });
    }
});
