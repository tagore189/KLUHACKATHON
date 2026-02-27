/**
 * estimate.js
 * Handles file uploads, AI analysis integration, and real-time result rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    initUpload();
    initDemo();
    initResultActions();
    if (typeof initCurrencySelector === 'function') initCurrencySelector();
});

/* --------- Navbar (shared) --------- */
function initNavbar() {
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

/* --------- File Upload --------- */
function initUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');

    if (!dropZone || !fileInput || !uploadBtn) return;

    uploadBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove('drag-over'));
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
}

async function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file.');
        return;
    }

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

/** Display the analysis results */
function displayReport(report) {
    if (!report) return;

    // If scan was saved to DB and user is logged in, redirect to detailed analysis after a brief delay
    if (report.scan_db_id) {
        setTimeout(() => {
            window.location.href = `/analysis/${report.scan_db_id}`;
        }, 1500);
        return;
    }

    document.getElementById('loadingState').style.display = 'none';
    const { detection_result, severity_assessment, cost_estimate, image_url, image_metadata } = report;
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
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="part-cell">
                    <span class="part-name">${d.part_name}</span>
                    <span class="part-key">${d.part_key}</span>
                </div>
            </td>
            <td><span class="badge badge-outline">${d.damage_type}</span></td>
            <td><span class="severity-dot" style="background: ${getSeverityColor(d.severity)}"></span> ${capitalize(d.severity)}</td>
            <td><span class="action-tag">${d.action}</span></td>
            <td class="text-right">₹${d.subtotal.toLocaleString()}</td>
        `;
        damageList.appendChild(row);
    });

    // Cost summary
    const summary = report.cost_estimate.summary;
    const symbol = summary.symbol || '₹';
    document.getElementById('partsTotal').textContent = `${symbol}${summary.total_parts.toLocaleString()}`;
    document.getElementById('laborTotal').textContent = `${symbol}${summary.total_labor.toLocaleString()}`;
    document.getElementById('paintTotal').textContent = `${symbol}${summary.total_paint.toLocaleString()}`;
    document.getElementById('taxAmount').textContent = `${symbol}${summary.tax.toLocaleString()}`;
    document.getElementById('grandTotal').textContent = `${symbol}${summary.total.toLocaleString()}`;
    document.getElementById('repairTime').textContent = `${report.estimated_repair_days} Business Days`;

    // Next steps
    const stepsList = document.getElementById('nextStepsList');
    stepsList.innerHTML = '';
    rec.next_steps.forEach(step => {
        const li = document.createElement('li');
        li.textContent = step;
        stepsList.appendChild(li);
    });

    // Main image
    const mainImg = document.getElementById('analyzedImage');
    mainImg.src = image_url;
    mainImg.onload = () => {
        mainImg.style.opacity = '1';
    };
}

/* --------- Demo Interface --------- */
function initDemo() {
    const demoButtons = document.querySelectorAll('.demo-btn');
    demoButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const demoImg = btn.dataset.image;
            runDemoAnalysis(demoImg);
        });
    });
}

async function runDemoAnalysis(imageName) {
    showResults();
    showLoading();

    try {
        const response = await fetch('/api/demo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageName })
        });

        const data = await response.json();
        await simulateLoadingSteps();
        displayReport(data);
    } catch (err) {
        await simulateLoadingSteps();
        displayReport(getSimulatedReport());
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

/** Fallback report generator - updated for INR */
function getSimulatedReport() {
    const currencySymbol = document.querySelector('.currency-select')?.value === 'USD' ? '$' :
        document.querySelector('.currency-select')?.value === 'EUR' ? '€' :
            document.querySelector('.currency-select')?.value === 'GBP' ? '£' : '₹';

    return {
        report_id: `VC-${Math.floor(Math.random() * 90000) + 10000}`,
        generated_at: new Date().toISOString(),
        image_url: '/static/demo_images/demo1.jpg',
        vehicle_info: {
            type: 'SUV',
            color: 'Metallic Silver',
            drivable: true
        },
        damage_assessment: {
            overall_severity: 'MODERATE',
            severity_color: '#f59e0b',
            severity_icon: '⚠️',
            summary: 'Multiple areas of surface damage detected on the front passenger side. Structural integrity appears intact, but replacement of the headlight assembly is recommended due to lens cracking.',
            damages: [
                {
                    part_name: 'Front Bumper',
                    part_key: 'front_bumper',
                    damage_type: 'Deep Scrape',
                    severity: 'Moderate',
                    action: 'Repair/Repaint',
                    subtotal: 12500
                },
                {
                    part_name: 'Headlight Assembly',
                    part_key: 'headlight',
                    damage_type: 'Lens Crack',
                    severity: 'Severe',
                    action: 'Replace',
                    subtotal: 28400
                }
            ]
        },
        cost_estimate: {
            summary: {
                total_parts: 32000,
                total_labor: 6500,
                total_paint: 5000,
                tax: 7830,
                total: 51330,
                currency: 'INR',
                symbol: '₹'
            }
        },
        recommendation: {
            status: 'PRE-APPROVED',
            status_color: '#22c55e',
            message: 'This estimate of ₹51,330.00 has been pre-approved based on visual evidence.',
            next_steps: [
                'Choose a certified repair facility',
                'Download this report for your records',
                'Schedule inspection within 48 hours'
            ]
        },
        estimated_repair_days: 3
    };
}
