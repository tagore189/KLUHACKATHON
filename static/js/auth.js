/* VisionClaim — Auth Page JS */

// ── Password visibility toggle ────────────────────────────────────────────────
function setupPasswordToggle(toggleId, inputId) {
    const toggle = document.getElementById(toggleId);
    const input = document.getElementById(inputId);
    if (!toggle || !input) return;

    toggle.addEventListener('click', () => {
        const isText = input.type === 'text';
        input.type = isText ? 'password' : 'text';
        toggle.querySelector('.eye-icon').style.opacity = isText ? '1' : '0.4';
    });
}
setupPasswordToggle('togglePassword', 'password');
setupPasswordToggle('toggleSignupPassword', 'password');

// ── Password strength meter ───────────────────────────────────────────────────
const pwInput = document.getElementById('password');
const strengthBars = document.getElementById('passwordStrength');
const strengthLabel = document.getElementById('strengthLabel');

function getStrength(pw) {
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    return Math.min(score, 4);
}

if (pwInput && strengthBars) {
    pwInput.addEventListener('input', () => {
        const pw = pwInput.value;
        if (!pw) {
            strengthBars.className = 'password-strength';
            strengthLabel.textContent = 'Enter a password';
            return;
        }
        const score = getStrength(pw);
        const levels = ['', 'strength-weak', 'strength-fair', 'strength-good', 'strength-strong'];
        const labels = ['', 'Weak', 'Fair', 'Good', 'Strong 💪'];
        strengthBars.className = 'password-strength ' + levels[score];
        strengthLabel.textContent = labels[score];
    });
}

// ── Confirm password match ────────────────────────────────────────────────────
const confirmInput = document.getElementById('confirm_password');
const matchIndicator = document.getElementById('matchIndicator');

if (confirmInput && matchIndicator && pwInput) {
    confirmInput.addEventListener('input', () => {
        const match = pwInput.value === confirmInput.value;
        matchIndicator.style.display = confirmInput.value ? 'block' : 'none';
        matchIndicator.textContent = match ? '✓ Passwords match' : '✗ Passwords do not match';
        matchIndicator.className = 'match-indicator ' + (match ? 'match-ok' : 'match-bad');
        confirmInput.classList.toggle('input-success', match && !!confirmInput.value);
        confirmInput.classList.toggle('input-error', !match && !!confirmInput.value);
    });
}

// ── Form submit loading state ─────────────────────────────────────────────────
document.querySelectorAll('.auth-form').forEach(form => {
    form.addEventListener('submit', () => {
        const btn = form.querySelector('.auth-submit');
        const text = btn?.querySelector('.btn-text');
        const arrow = btn?.querySelector('.btn-arrow');
        const spinner = btn?.querySelector('.btn-spinner');
        if (!btn) return;
        btn.disabled = true;
        if (text) text.textContent = 'Please wait…';
        if (arrow) arrow.style.display = 'none';
        if (spinner) spinner.style.display = 'inline-flex';
    });
});

// ── Input focus label ─────────────────────────────────────────────────────────
document.querySelectorAll('.form-input').forEach(input => {
    input.addEventListener('focus', () => {
        input.closest('.form-group')?.querySelector('.input-icon')
            ?.setAttribute('stroke', 'var(--blue-400)');
    });
    input.addEventListener('blur', () => {
        input.closest('.form-group')?.querySelector('.input-icon')
            ?.setAttribute('stroke', 'currentColor');
    });
});

// ── Social buttons (demo alert) ───────────────────────────────────────────────
document.querySelectorAll('.social-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        alert('Social login is not configured yet. Please use email & password.');
    });
});
