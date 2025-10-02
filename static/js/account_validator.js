document.addEventListener('DOMContentLoaded', function() {
    // Modal 相關變數
    const loginButton = document.querySelector('button[data-bs-target="#loginModal"]');
    const registerButton = document.querySelector('button[data-bs-target="#registerModal"]');
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');

    // 只有當這些元素存在時才初始化 Modal
    if (loginModal && registerModal) {
        const loginModalInstance = new bootstrap.Modal(loginModal);
        const registerModalInstance = new bootstrap.Modal(registerModal);

        // 監聽按鈕點擊事件
        loginButton?.addEventListener('click', function() {
            loginModalInstance.show();
        });

        registerButton?.addEventListener('click', function() {
            registerModalInstance.show();
        });

        // Modal 切換邏輯
        loginModal.querySelector('.link-danger')?.addEventListener('click', function(e) {
            e.preventDefault();
            loginModalInstance.hide();
            registerModalInstance.show();
        });

        registerModal.querySelector('.link-danger')?.addEventListener('click', function(e) {
            e.preventDefault();
            registerModalInstance.hide();
            loginModalInstance.show();
        });

        // 表單驗證
        initializeLoginValidation(loginModal);
        initializeRegisterValidation(registerModal);

        // Modal 隱藏時重置表單
        [loginModal, registerModal].forEach(modal => {
            modal.addEventListener('hidden.bs.modal', function() {
                resetModalForm(this);
            });
        });
    }
});

// 登入表單驗證
function initializeLoginValidation(modal) {
    const form = modal.querySelector('form');
    const inputs = form?.querySelectorAll('input');

    form?.addEventListener('submit', function(e) {
        e.preventDefault();
        let isValid = validateLoginForm(inputs);
        if (isValid) {
            form.submit();
        }
    });

    // 即時驗證
    inputs?.forEach(input => {
        input.addEventListener('input', function() {
            validateLoginInput(this);
        });
    });
}

// 註冊表單驗證
function initializeRegisterValidation(modal) {
    const form = modal.querySelector('form');
    const inputs = form?.querySelectorAll('input');

    form?.addEventListener('submit', function(e) {
        e.preventDefault();
        let isValid = validateRegisterForm(inputs);
        if (isValid) {
            form.submit();
        }
    });

    // 即時驗證
    inputs?.forEach(input => {
        input.addEventListener('input', function() {
            validateRegisterInput(this);
        });
    });
}

// 驗證登入表單
function validateLoginForm(inputs) {
    let isValid = true;
    inputs.forEach(input => {
        if (!validateLoginInput(input)) {
            isValid = false;
        }
    });
    return isValid;
}

// 驗證註冊表單
function validateRegisterForm(inputs) {
    let isValid = true;
    const password = Array.from(inputs).find(input => input.name === 'registerPassword');
    const confirmPassword = Array.from(inputs).find(input => input.name === 'registerConfirmPassword');

    inputs.forEach(input => {
        if (!validateRegisterInput(input)) {
            isValid = false;
        }
    });

    // 密碼匹配驗證
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        setInvalidFeedback(confirmPassword, '密碼不匹配');
        isValid = false;
    }

    return isValid;
}

// 驗證單個登入輸入欄位
function validateLoginInput(input) {
    if (!input.value.trim()) {
        setInvalidFeedback(input, `請輸入${getFieldLabel(input)}`);
        return false;
    }
    clearInvalidFeedback(input);
    return true;
}

// 驗證單個註冊輸入欄位
function validateRegisterInput(input) {
    const value = input.value.trim();
    if (!value) {
        setInvalidFeedback(input, `請輸入${getFieldLabel(input)}`);
        return false;
    }

    // 額外的欄位驗證規則
    if (input.name === 'registerAccount' && value.length > 16) {
        setInvalidFeedback(input, '帳號不能超過16個字元');
        return false;
    }
    if (input.name === 'registerPassword' && value.length > 16) {
        setInvalidFeedback(input, '密碼不能超過16個字元');
        return false;
    }
    if (input.name === 'registerNickname' && value.length > 16) {
        setInvalidFeedback(input, '暱稱不能超過16個字元');
        return false;
    }

    clearInvalidFeedback(input);
    return true;
}

// 設置錯誤提示
function setInvalidFeedback(input, message) {
    input.classList.add('is-invalid');
    input.classList.remove('is-valid');
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = message;
    }
}

// 清除錯誤提示
function clearInvalidFeedback(input) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = '';
    }
}

// 獲取欄位標籤文字
function getFieldLabel(input) {
    const label = input.previousElementSibling;
    return label ? label.textContent.trim() : '';
}

// 重置 Modal 表單
function resetModalForm(modal) {
    const form = modal.querySelector('form');
    if (form) {
        form.reset();
        form.querySelectorAll('.is-invalid, .is-valid').forEach(input => {
            input.classList.remove('is-invalid', 'is-valid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(feedback => {
            feedback.textContent = '';
        });
    }
}