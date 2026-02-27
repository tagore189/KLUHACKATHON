"""Flask application for VisionClaim Motor Claim Estimator."""
import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, session
from dotenv import load_dotenv

from utils.preprocessing import allowed_file, preprocess_image, ensure_upload_dir, get_image_metadata
from utils.detection import detect_damage, init_client
from utils.severity import assess_severity
from utils.cost_estimator import estimate_costs, load_cost_data
from utils.report_generator import generate_report
from database.db import create_user, verify_user, get_db, save_scan, get_user_scans, get_scan
from pymongo import errors as mongo_errors

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.secret_key = os.environ.get('SECRET_KEY', 'visionclaim-dev-key-2024')

# Initialize OpenAI client
init_client(os.environ.get('OPENAI_API_KEY'))


@app.context_processor
def inject_currency():
    """Injects currency information into all templates."""
    cost_data = load_cost_data()
    exchange_rates = cost_data.get('exchange_rates', {})
    selected_currency = session.get('currency', 'INR')
    
    currency_info = exchange_rates.get(selected_currency, exchange_rates.get('INR'))
    
    return {
        'selected_currency': selected_currency,
        'currency_symbol': currency_info.get('symbol', '₹'),
        'exchange_rates': exchange_rates
    }


@app.route('/api/set_currency', methods=['POST'])
def set_currency():
    """Sets the user's preferred currency."""
    currency_code = request.json.get('currency')
    cost_data = load_cost_data()
    if currency_code in cost_data.get('exchange_rates', {}):
        session['currency'] = currency_code
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid currency'}), 400


@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page — authenticates against MongoDB."""
    if session.get('user'):
        return redirect(url_for('estimate'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter your email and password.', 'error')
        else:
            try:
                user = verify_user(email, password)
                if user:
                    session['user'] = user
                    flash(f'Welcome back, {user["first_name"]}! 👋', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid email or password. Please try again.', 'error')
            except Exception as e:
                flash('Could not connect to database. Please try again later.', 'error')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Sign-up page — creates a new user in MongoDB."""
    if session.get('user'):
        return redirect(url_for('estimate'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name', '').strip()
        email      = request.form.get('email', '').strip()
        password   = request.form.get('password', '')
        confirm_pw = request.form.get('confirm_password', '')

        if not first_name or not email or not password:
            flash('Please fill in all required fields.', 'error')
        elif password != confirm_pw:
            flash('Passwords do not match. Please try again.', 'error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
        else:
            try:
                user = create_user(first_name, last_name, email, password)
                session['user'] = user
                flash(f'Account created! Welcome to VisionClaim, {first_name} 🎉', 'success')
                return redirect(url_for('dashboard'))
            except ValueError as e:
                flash(str(e), 'error')
            except Exception as e:
                flash('Could not create account. Please try again later.', 'error')

    return render_template('signup.html')


@app.route('/logout')
def logout():
    """Log out and clear session."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/estimate')
def estimate():
    """Upload & estimate page."""
    return render_template('estimate.html')


@app.route('/dashboard')
def dashboard():
    """User scan history dashboard."""
    if not session.get('user'):
        flash('Please log in to view your dashboard.', 'info')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    scans = get_user_scans(user_id)
    
    # Process scans for display
    for scan in scans:
        scan['id_str'] = str(scan['_id'])
        # Extract meaningful info for cards
        report = scan.get('data', {})
        v_info = report.get('vehicle_info', {})
        scan['vehicle_name'] = f"{v_info.get('color', 'Vehicle').title()} {v_info.get('type', 'Scan').title()}"
        scan['total_cost'] = report.get('cost_estimate', {}).get('total', 0)
        scan['currency_symbol'] = report.get('cost_estimate', {}).get('symbol', '₹')
        scan['date_formatted'] = scan['created_at'].strftime('%b %d, %Y')
        scan['fault_count'] = len(report.get('damage_assessment', {}).get('damages', []))

    return render_template('dashboard.html', scans=scans)


@app.route('/analysis/<scan_id>')
def detailed_analysis(scan_id):
    """Detailed AI Damage Analysis view."""
    if not session.get('user'):
        return redirect(url_for('login'))
        
    scan = get_scan(scan_id, user_id=session['user']['id'])
    if not scan:
        flash('Scan not found.', 'error')
        return redirect(url_for('dashboard'))
        
    scan['id_str'] = str(scan.get('_id', ''))
    report = scan.get('data', {})
    # Add display helpers if needed
    return render_template('analysis.html', scan=scan, report=report)


@app.route('/payouts/<scan_id>')
def payouts(scan_id):
    """Settlement and Payouts view."""
    if not session.get('user'):
        return redirect(url_for('login'))
        
    scan = get_scan(scan_id, user_id=session['user']['id'])
    if not scan:
        flash('Scan not found.', 'error')
        return redirect(url_for('dashboard'))
        
    scan['id_str'] = str(scan.get('_id', ''))
    report = scan.get('data', {})
    return render_template('payouts.html', scan=scan, report=report)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint for image analysis."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, webp, bmp'}), 400

    try:
        # Save uploaded file
        upload_dir = ensure_upload_dir()
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # Preprocess
        preprocess_image(filepath)

        # Get image metadata
        metadata = get_image_metadata(filepath)

        # Detect damage
        detection_result = detect_damage(filepath)

        if not detection_result.get('vehicle_detected', False):
            return jsonify({
                'error': 'No vehicle detected in the image. Please upload a clear photo of a damaged vehicle.'
            }), 400

        # Assess severity
        severity_assessment = assess_severity(detection_result.get('damages', []))

        # Estimate costs
        cost_estimate = estimate_costs(
            detection_result.get('damages', []),
            severity_assessment,
            target_currency=session.get('currency', 'INR')
        )

        # Generate report
        report = generate_report(
            detection_result,
            severity_assessment,
            cost_estimate,
            image_filename=filename
        )

        report['image_url'] = f'/uploads/{filename}'
        report['image_metadata'] = metadata

        # Persist to database if logged in
        if session.get('user'):
            try:
                scan_db_id = save_scan(session['user']['id'], report)
                report['scan_db_id'] = scan_db_id
            except Exception as db_err:
                print(f"Failed to save scan: {db_err}")

        return jsonify(report)

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    upload_dir = ensure_upload_dir()
    return send_from_directory(upload_dir, filename)


if __name__ == '__main__':
    ensure_upload_dir()
    app.run(debug=True, host='0.0.0.0', port=5000)
