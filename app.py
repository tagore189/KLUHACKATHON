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
from database.db import create_user, verify_user, get_db
from pymongo import errors as mongo_errors

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.secret_key = os.environ.get('SECRET_KEY', 'visionclaim-dev-key-2024')

# Initialize Gemini client
init_client(os.environ.get('GOOGLE_API_KEY'))


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
                    return redirect(url_for('estimate'))
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
                return redirect(url_for('estimate'))
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

        return jsonify(report)

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    upload_dir = ensure_upload_dir()
    return send_from_directory(upload_dir, filename)


@app.route('/api/demo', methods=['POST'])
def demo_analysis():
    """Run analysis on a demo image."""
    demo_dir = os.path.join(app.static_folder, 'demo_images')
    demo_image = request.json.get('image', 'demo1.jpg')
    filepath = os.path.join(demo_dir, demo_image)

    if not os.path.exists(filepath):
        # Use simulated data for demo
        from utils.detection import simulate_damage_detection
        detection_result = simulate_damage_detection(None)
        severity_assessment = assess_severity(detection_result.get('damages', []))
        cost_estimate = estimate_costs(
            detection_result.get('damages', []), 
            severity_assessment,
            target_currency=session.get('currency', 'INR')
        )
        report = generate_report(detection_result, severity_assessment, cost_estimate, image_filename='demo')
        report['image_url'] = '/static/demo_images/demo1.jpg'
        return jsonify(report)

    detection_result = detect_damage(filepath)
    severity_assessment = assess_severity(detection_result.get('damages', []))
    cost_estimate = estimate_costs(
        detection_result.get('damages', []), 
        severity_assessment,
        target_currency=session.get('currency', 'INR')
    )
    report = generate_report(detection_result, severity_assessment, cost_estimate, image_filename=demo_image)
    report['image_url'] = f'/static/demo_images/{demo_image}'
    return jsonify(report)


if __name__ == '__main__':
    ensure_upload_dir()
    app.run(debug=True, host='0.0.0.0', port=5000)
