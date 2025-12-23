// パスワード表示/非表示のトグル
function togglePasswordVisibility(inputId, toggleButton) {
    const input = document.getElementById(inputId);
    const isPassword = input.type === 'password';
    
    input.type = isPassword ? 'text' : 'password';
    toggleButton.textContent = isPassword ? '�' : '🙈';
}

// アカウント登録処理
const regForm = document.getElementById('registerForm');
if (regForm) {
    regForm.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(regForm);
        const data = Object.fromEntries(formData.entries());

        const res = await fetch('/accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            alert('暗号化して保存しました！');
            location.href = 'index.html';
        } else {
            alert('保存に失敗しました');
        }
    };
}
