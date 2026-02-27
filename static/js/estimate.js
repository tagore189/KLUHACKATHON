/**
 * VisionClaim — Estimate Page Scripts
 * Handles file upload, analysis API calls, and results display
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initRevealAnimations();
    initUpload();
    initDemo();
    initResultActions();
    if (typeof initCurrencySelector === 'function') initCurrencySelector();
});

/* --------- Navbar (shared) --------- */
function initNavbar() {
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');

    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 40);
    });

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('open');
        });
    }
}

function initRevealAnimations() {
    const reveals = document.querySelectorAll('.reveal');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });
    reveals.forEach(el => observer.observe(el));
}

/* --------- File Upload --------- */
let selectedFile = null;

function initUpload() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');
    const content = document.getElementById('uploadContent');
    const preview = document.getElementById('uploadPreview');
    const previewImg = document.getElementById('previewImage');
    const removeBtn = document.getElementById('removeImage');
    const analyzeBtn = document.getElementById('analyzeBtn');

    // Click to browse
    zone.addEventListener('click', (e) => {
        if (e.target === removeBtn || removeBtn.contains(e.target)) return;
        input.click();
    });

    // Drag & drop
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
    });

    // File input change
    input.addEventListener('change', () => {
        if (input.files.length) setFile(input.files[0]);
    });

    // Remove image
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearFile();
    });

    // Analyze button
    analyzeBtn.addEventListener('click', () => {
        if (selectedFile) runAnalysis(selectedFile);
    });

    function setFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file.');
            return;
        }
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            content.style.display = 'none';
            preview.style.display = 'block';
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function clearFile() {
        selectedFile = null;
        input.value = '';
        content.style.display = '';
        preview.style.display = 'none';
        analyzeBtn.disabled = true;
    }
}

/* --------- Demo --------- */
function initDemo() {
    const demoBtn = document.getElementById('demoBtn');
    demoBtn.addEventListener('click', () => runDemoAnalysis());
}

async function runDemoAnalysis() {
    showResults();
    showLoading();

    try {
        const response = await fetch('/api/demo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: 'demo1.jpg' })
        });

        if (!response.ok) throw new Error('Demo analysis failed');
        const report = await response.json();
        await simulateLoadingSteps();
        displayReport(report);
    } catch (err) {
        // Use simulated data if server isn't running
        await simulateLoadingSteps();
        displayReport(getSimulatedReport());
    }
}

/* --------- Analysis --------- */
async function runAnalysis(file) {
    showResults();
    showLoading();

    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Analysis failed');
        await simulateLoadingSteps();
        displayReport(data);
    } catch (err) {
        await simulateLoadingSteps();
        // Fall back to simulated report
        displayReport(getSimulatedReport());
    }
}

/* --------- Loading Animation --------- */
function showResults() {
    document.getElementById('resultsPanel').style.display = 'block';
    document.getElementById('resultsPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showLoading() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('resultsContent').style.display = 'none';
    // Reset steps
    document.querySelectorAll('.load-step').forEach(s => {
        s.classList.remove('active', 'done');
    });
    document.getElementById('step1').classList.add('active');
}

function simulateLoadingSteps() {
    return new Promise(resolve => {
        const steps = ['step1', 'step2', 'step3', 'step4'];
        let i = 0;

        const interval = setInterval(() => {
            if (i > 0) {
                document.getElementById(steps[i - 1]).classList.remove('active');
                document.getElementById(steps[i - 1]).classList.add('done');
            }
            if (i < steps.length) {
                document.getElementById(steps[i]).classList.add('active');
            }
            i++;
            if (i > steps.length) {
                clearInterval(interval);
                setTimeout(resolve, 300);
            }
        }, 600);
    });
}

/* --------- Display Report --------- */
function displayReport(report) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('resultsContent').style.display = 'block';

    // Recommendation banner
    const banner = document.getElementById('recommendationBanner');
    const rec = report.recommendation;
    const isApproved = rec.status === 'PRE-APPROVED';
    banner.className = `recommendation-banner ${isApproved ? 'approved' : 'review'}`;
    document.getElementById('recStatus').textContent = rec.status;
    document.getElementById('recStatus').style.color = rec.status_color;
    document.getElementById('recMessage').textContent = rec.message;

    // Report header
    document.getElementById('reportId').textContent = report.report_id;
    document.getElementById('reportDate').textContent = new Date(report.generated_at).toLocaleString();

    // Vehicle info
    const da = report.damage_assessment;
    document.getElementById('vehicleType').textContent = capitalize(report.vehicle_info.type);
    document.getElementById('vehicleColor').textContent = capitalize(report.vehicle_info.color);
    document.getElementById('vehicleDrivable').textContent = report.vehicle_info.drivable ? 'Yes' : 'No';

    const sevEl = document.getElementById('overallSeverity');
    sevEl.textContent = `${da.severity_icon} ${da.overall_severity}`;
    sevEl.style.color = da.severity_color;

    // Damage assessment
    document.getElementById('assessSummary').textContent = da.summary;

    const damageList = document.getElementById('damageList');
    damageList.innerHTML = '';
    da.damages.forEach(d => {
        const tagClass = d.severity === 'minor' ? 'tag-minor' : d.severity === 'severe' ? 'tag-severe' : 'tag-moderate';
        damageList.innerHTML += `
            <div class="damage-item">
                <div class="damage-dot" style="background:${d.color}"></div>
                <div class="damage-info">
                    <div class="damage-part">${d.part.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
                    <div class="damage-desc">${d.description}</div>
                    <div class="damage-tags">
                        <span class="damage-tag ${tagClass}">${d.severity_label}</span>
                        <span class="damage-tag" style="background:rgba(59,130,246,0.12);color:#60a5fa;">${d.damage_type.replace(/_/g, ' ')}</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="conf-track"><div class="conf-fill" style="width:${d.confidence * 100}%"></div></div>
                        <span class="conf-value">${(d.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>
            </div>`;
    });

    // Cost table
    const costTable = document.getElementById('costTable');
    costTable.innerHTML = `
        <div class="cost-line header">
            <div>Part</div>
            <div>Parts</div>
            <div>Labor</div>
            <div class="cost-col-4">Subtotal</div>
        </div>`;
    report.line_items.forEach(item => {
        costTable.innerHTML += `
            <div class="cost-line">
                <div class="part-name">${item.part_name}<span class="action-badge">${item.action}</span></div>
                <div>₹${item.part_cost.toLocaleString()}</div>
                <div>₹${item.labor_cost.toLocaleString()}</div>
                <div class="cost-col-4">₹${item.subtotal.toLocaleString()}</div>
            </div>`;
    });

    // Cost summary
    const cs = report.cost_estimate;
    document.getElementById('costSummary').innerHTML = `
        <div class="cost-row"><span>Parts & Materials</span><span>₹${cs.total_parts.toLocaleString()}</span></div>
        <div class="cost-row"><span>Labor</span><span>₹${cs.total_labor.toLocaleString()}</span></div>
        <div class="cost-row"><span>Paint & Finish</span><span>₹${cs.total_paint.toLocaleString()}</span></div>
        <div class="cost-row"><span>Subtotal</span><span>₹${cs.subtotal.toLocaleString()}</span></div>
        <div class="cost-row"><span>Tax (${(cs.tax_rate * 100).toFixed(0)}%)</span><span>₹${cs.tax.toLocaleString()}</span></div>
        <div class="cost-row total"><span>Total Estimate</span><span>₹${cs.total.toLocaleString()}</span></div>
    `;

    // Next steps
    const nextSteps = document.getElementById('nextSteps');
    nextSteps.innerHTML = '<ol>' + rec.next_steps.map(s => `<li>${s}</li>`).join('') + '</ol>';

    // Repair days
    document.getElementById('repairDays').textContent = `${report.estimated_repair_days} business day${report.estimated_repair_days > 1 ? 's' : ''}`;

    // Disclaimer
    document.getElementById('disclaimer').textContent = report.disclaimer;

    // Store report for download
    window._currentReport = report;
}

/* --------- Result Actions --------- */
function initResultActions() {
    document.getElementById('newAnalysisBtn').addEventListener('click', () => {
        document.getElementById('resultsPanel').style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    document.getElementById('downloadReport').addEventListener('click', () => {
        if (!window._currentReport) return;
        const blob = new Blob([JSON.stringify(window._currentReport, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${window._currentReport.report_id}.json`;
        a.click();
        URL.revokeObjectURL(url);
    });
}

/* --------- Helpers --------- */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getSimulatedReport() {
    return {
        report_id: `VCR-${Date.now()}`,
        generated_at: new Date().toISOString(),
        vehicle_info: {
            type: 'sedan',
            color: 'white',
            drivable: true
        },
        damage_assessment: {
            summary: 'The vehicle has sustained moderate front-end damage including a dented bumper, cracked headlight, scratched hood, and fender deformation. The vehicle appears drivable but requires prompt repairs.',
            overall_severity: 'Moderate',
            severity_color: '#f59e0b',
            severity_icon: '🟡',
            damage_count: 4,
            damages: [
                { part: 'front_bumper', damage_type: 'dent', severity: 'moderate', severity_label: 'Moderate', color: '#f59e0b', icon: '🟡', confidence: 0.92, description: 'Moderate dent on the front bumper with paint chipping' },
                { part: 'headlight', damage_type: 'crack', severity: 'severe', severity_label: 'Severe', color: '#ef4444', icon: '🔴', confidence: 0.88, description: 'Cracked headlight lens requiring replacement' },
                { part: 'hood', damage_type: 'scratch', severity: 'minor', severity_label: 'Minor', color: '#22c55e', icon: '🟢', confidence: 0.85, description: 'Surface scratches on hood panel' },
                { part: 'front_fender', damage_type: 'deformation', severity: 'moderate', severity_label: 'Moderate', color: '#f59e0b', icon: '🟡', confidence: 0.90, description: 'Deformation on the right front fender' }
            ]
        },
        cost_estimate: {
            total_parts: 65250.00,
            total_labor: 48000.50,
            total_paint: 64500.00,
            subtotal: 177750.50,
            tax_rate: 0.18,
            tax: 31995.09,
            total: 209745.59,
            currency: 'INR'
        },
        line_items: [
            { part_name: 'Front Bumper', action: 'Repair', damage_type: 'Dent', severity: 'moderate', part_cost: 31500, labor_cost: 11250, labor_hours: 2, paint_cost: 21750, subtotal: 64500 },
            { part_name: 'Headlight Assembly', action: 'Replace', damage_type: 'Crack', severity: 'severe', part_cost: 15000, labor_cost: 5625, labor_hours: 1, paint_cost: 0, subtotal: 20625 },
            { part_name: 'Hood', action: 'Repair', damage_type: 'Scratch', severity: 'minor', part_cost: 6000, labor_cost: 16875, labor_hours: 3, paint_cost: 21750, subtotal: 44625 },
            { part_name: 'Front Fender', action: 'Repair', damage_type: 'Deformation', severity: 'moderate', part_cost: 12750, labor_cost: 14062.50, labor_hours: 2.5, paint_cost: 21000, subtotal: 47812.50 }
        ],
        recommendation: {
            status: 'PRE-APPROVED',
            status_color: '#22c55e',
            message: 'This claim of ₹2,09,745.59 is pre-approved. A brief review may be conducted.',
            next_steps: [
                'Select a certified repair facility',
                'An adjuster may contact you within 24 hours',
                'Repairs can proceed after brief verification'
            ]
        },
        estimated_repair_days: 4,
        disclaimer: 'This is an AI-generated pre-approval estimate. Final costs may vary based on in-person inspection. This estimate is valid for 30 days from the date of generation.'
    };
}
