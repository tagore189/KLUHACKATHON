/**
 * estimate.js
 * Handles file uploads, AI analysis integration, and real-time result rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    initUpload();
    initResultActions();
    if (typeof initCurrencySelector === 'function') initCurrencySelector();
});

let _selectedFile = null;

/* --------- File Upload --------- */
function initUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const removeBtn = document.getElementById('removeImage');

    if (!uploadZone || !fileInput || !analyzeBtn) return;

    uploadZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    ['dragleave', 'drop'].forEach(evt => {
        uploadZone.addEventListener(evt, () => uploadZone.classList.remove('drag-over'));
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    analyzeBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        if (!_selectedFile) return;
        await runFileAnalysis(_selectedFile);
    });

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            resetUpload();
        });
    }
}

function handleFile(file) {
    if (!file) return;

    const analyzeBtn = document.getElementById('analyzeBtn');
    const previewWrap = document.getElementById('uploadPreview');
    const previewImg = document.getElementById('previewImage');
    const uploadContent = document.getElementById('uploadContent');
    const fileInput = document.getElementById('fileInput');

    const maxBytes = 16 * 1024 * 1024;
    if (file.size > maxBytes) {
        alert('File too large. Max allowed size is 16MB.');
        if (fileInput) fileInput.value = '';
        return;
    }

    if (!file.type.startsWith('image/')) {
        alert('Please upload a valid image file.');
        if (fileInput) fileInput.value = '';
        return;
    }

    _selectedFile = file;
    if (analyzeBtn) analyzeBtn.disabled = false;

    if (previewWrap && previewImg && uploadContent) {
        const reader = new FileReader();
        reader.onload = () => {
            previewImg.src = reader.result;
            previewWrap.style.display = 'block';
            uploadContent.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
}

function resetUpload() {
    _selectedFile = null;
    const analyzeBtn = document.getElementById('analyzeBtn');
    const previewWrap = document.getElementById('uploadPreview');
    const uploadContent = document.getElementById('uploadContent');
    const fileInput = document.getElementById('fileInput');
    const previewImg = document.getElementById('previewImage');

    if (analyzeBtn) analyzeBtn.disabled = true;
    if (fileInput) fileInput.value = '';
    if (previewImg) previewImg.src = '';
    if (previewWrap) previewWrap.style.display = 'none';
    if (uploadContent) uploadContent.style.display = 'block';
}

function showResults() {
    const panel = document.getElementById('resultsPanel');
    if (panel) panel.style.display = 'block';
    panel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showLoading() {
    const loading = document.getElementById('loadingState');
    const content = document.getElementById('resultsContent');
    if (loading) loading.style.display = 'block';
    if (content) content.style.display = 'none';

    ['step1', 'step2', 'step3', 'step4'].forEach((id, idx) => {
        const el = document.getElementById(id);
        if (el) el.classList.toggle('active', idx === 0);
    });
}

async function simulateLoadingSteps() {
    const steps = ['step1', 'step2', 'step3', 'step4'].map(id => document.getElementById(id)).filter(Boolean);
    for (let i = 0; i < steps.length; i++) {
        steps.forEach((s, idx) => s.classList.toggle('active', idx <= i));
        // short delay so the UI updates even on fast responses
        // eslint-disable-next-line no-await-in-loop
        await new Promise(r => setTimeout(r, 350));
    }
}

async function runFileAnalysis(file) {
    showResults();
    showLoading();

    try {
        const fd = new FormData();
        fd.append('image', file);

        const response = await fetch('/api/analyze', { method: 'POST', body: fd });
        const data = await response.json().catch(() => ({}));

        await simulateLoadingSteps();

        if (!response.ok) {
            showError(data?.error || 'Analysis failed. Please try another image.');
            return;
        }

        displayReport(data);
    } catch (err) {
        await simulateLoadingSteps();
        showError('Network error while analyzing. Please try again.');
    }
}

function showError(message) {
    const loading = document.getElementById('loadingState');
    const content = document.getElementById('resultsContent');
    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';

    const banner = document.getElementById('recommendationBanner');
    if (banner) banner.className = 'recommendation-banner review';
    const recStatus = document.getElementById('recStatus');
    const recMessage = document.getElementById('recMessage');
    if (recStatus) recStatus.textContent = 'ERROR';
    if (recMessage) recMessage.textContent = message;
}

/** Display the analysis results */
function displayReport(report) {
    if (!report) return;

    document.getElementById('loadingState').style.display = 'none';
    const { damage_assessment, cost_estimate, image_url } = report;
    document.getElementById('resultsContent').style.display = 'block';

    // Recommendation banner
    const banner = document.getElementById('recommendationBanner');
    const rec = report.recommendation;
    banner.className = `recommendation-banner ${rec.status === 'PRE-APPROVED' ? 'approved' : 'review'}`;

    document.getElementById('recStatus').textContent = rec.status;

    document.getElementById('recStatus').style.color = rec.status_color;
    document.getElementById('recMessage').textContent = rec.message;

    // Report header
    document.getElementById('reportId').textContent = report.report_id;
    document.getElementById('reportDate').textContent = new Date(report.generated_at).toLocaleString();

    // Vehicle info
    document.getElementById('vehicleType').textContent = capitalize(report.vehicle_info.type);
    document.getElementById('vehicleColor').textContent = capitalize(report.vehicle_info.color);
    document.getElementById('vehicleDrivable').textContent = report.vehicle_info.drivable ? 'Yes' : 'No';

    const sevEl = document.getElementById('overallSeverity');
    sevEl.textContent = `${damage_assessment.severity_icon} ${damage_assessment.overall_severity}`;
    sevEl.style.color = damage_assessment.severity_color;

    // Damage assessment
    document.getElementById('assessSummary').textContent = damage_assessment.summary;

    const damageList = document.getElementById('damageList');
    damageList.innerHTML = '';
    (damage_assessment.damages || []).forEach(d => {
        const item = document.createElement('div');
        item.className = 'damage-item';
        item.innerHTML = `
            <div class="damage-info">
                <span class="part-name">${d.part.replace('_', ' ').toUpperCase()}</span>
                <span class="damage-type">${d.damage_type.toUpperCase()}</span>
            </div>
            <div class="damage-meta">
                <span class="severity-badge" style="background: ${getSeverityColor(d.severity)}22; color: ${getSeverityColor(d.severity)}">
                    ${d.severity.toUpperCase()}
                </span>
                <span class="cost-tag">${(cost_estimate?.symbol || '₹')}${Number(d.part_cost || 0).toLocaleString()}</span>
            </div>
        `;
        damageList.appendChild(item);
    });

    // Cost summary
    const summary = cost_estimate;
    const symbol = summary.symbol || '₹';
    document.getElementById('costTable').innerHTML = `
        <div class="cost-row"><span>Parts</span><span>${symbol}${Number(summary.total_parts || 0).toLocaleString()}</span></div>
        <div class="cost-row"><span>Labor</span><span>${symbol}${Number(summary.total_labor || 0).toLocaleString()}</span></div>
        <div class="cost-row"><span>Paint</span><span>${symbol}${Number(summary.total_paint || 0).toLocaleString()}</span></div>
        <div class="cost-row"><span>Tax (18%)</span><span>${symbol}${Number(summary.tax || 0).toLocaleString()}</span></div>
    `;

    document.getElementById('costSummary').innerHTML = `
        <div class="grand-total">
            <span>Estimated Total</span>
            <span>${symbol}${Number(summary.total || 0).toLocaleString()}</span>
        </div>
    `;

    document.getElementById('repairDays').textContent = `${report.estimated_repair_days} Business Days`;

    // Next steps
    const nextSteps = document.getElementById('nextSteps');
    nextSteps.innerHTML = '';
    rec.next_steps.forEach(step => {
        const div = document.createElement('div');
        div.className = 'step-item';
        div.innerHTML = `<span class="step-bullet"></span><span>${step}</span>`;
        nextSteps.appendChild(div);
    });

    // Main image
    const mainImg = document.getElementById('analyzedImage');
    if (mainImg && image_url) {
        mainImg.src = image_url;
        mainImg.onload = () => {
            mainImg.style.opacity = '1';
        };
    }
}


/* --------- Helpers --------- */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getSeverityColor(sev) {
    switch (sev.toLowerCase()) {
        case 'minor': return '#22c55e';
        case 'moderate': return '#f59e0b';
        case 'severe': return '#ef4444';
        default: return '#94a3b8';
    }
}

function initResultActions() {
    const downloadBtn = document.getElementById('downloadReport');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            window.print();
        });
    }

    const shareBtn = document.getElementById('shareReport');
    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            const url = window.location.href;
            navigator.clipboard.writeText(url).then(() => {
                alert('Report link copied to clipboard!');
            });
        });
    }

    const newBtn = document.getElementById('newAnalysisBtn');
    if (newBtn) {
        newBtn.addEventListener('click', () => {
            window.location.reload();
        });
    }
}

