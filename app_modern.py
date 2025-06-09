from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from datetime import datetime, timedelta
import os
import json
from werkzeug.utils import secure_filename
import PyPDF2
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

CORS(app, supports_credentials=True)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Gemini setup
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    profile_pic = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    billing_cycle = db.Column(db.String(20), default='monthly')
    category = db.Column(db.String(50))
    next_billing_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    logo_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    detected_from = db.Column(db.String(50))  # 'manual', 'pdf', 'email'
    confidence = db.Column(db.Float, default=1.0)

class StatementUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    subscriptions_found = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Subscription catalog with logos
SUBSCRIPTION_CATALOG = {
    'netflix': {'name': 'Netflix', 'category': 'streaming', 'logo': '🎬'},
    'spotify': {'name': 'Spotify', 'category': 'streaming', 'logo': '🎵'},
    'amazon prime': {'name': 'Amazon Prime', 'category': 'streaming', 'logo': '📦'},
    'disney': {'name': 'Disney+', 'category': 'streaming', 'logo': '🏰'},
    'chatgpt': {'name': 'ChatGPT Plus', 'category': 'software', 'logo': '🤖'},
    'adobe': {'name': 'Adobe Creative Cloud', 'category': 'software', 'logo': '🎨'},
    'microsoft': {'name': 'Microsoft 365', 'category': 'software', 'logo': '📊'},
    'dropbox': {'name': 'Dropbox', 'category': 'storage', 'logo': '☁️'},
    'apple': {'name': 'Apple Services', 'category': 'various', 'logo': '🍎'},
    'google': {'name': 'Google Services', 'category': 'various', 'logo': '🔍'},
}

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error with pdfplumber: {e}")
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
        except Exception as e2:
            print(f"Error with PyPDF2: {e2}")
    
    return text

def process_with_gemini(text):
    prompt = """
    Analyze this bank statement and identify all recurring subscriptions or monthly charges.
    Look for patterns like:
    - Netflix, Spotify, Apple Music, Amazon Prime, Disney+, YouTube Premium
    - Software subscriptions like Adobe, Microsoft, Dropbox, ChatGPT
    - Utilities, phone bills, internet services
    - Any recurring monthly or annual charges
    
    For each subscription found, extract:
    1. Service/Company name
    2. Amount charged
    3. Date of charge
    4. Frequency (if determinable)
    5. Category (streaming, software, utilities, etc.)
    
    Return the results as a JSON array with the following structure:
    {
        "subscriptions": [
            {
                "name": "Service Name",
                "amount": 9.99,
                "date": "2024-01-15",
                "frequency": "monthly",
                "category": "streaming",
                "confidence": 0.95
            }
        ],
        "total_monthly_cost": 99.99
    }
    
    Only return valid JSON, no additional text.
    """
    
    try:
        response = model.generate_content([prompt, text])
        result_text = response.text.strip()
        
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        
        return json.loads(result_text)
    except Exception as e:
        print(f"Error processing with Gemini: {e}")
        return {"error": str(e), "subscriptions": [], "total_monthly_cost": 0}

def get_subscription_info(name):
    """Get subscription info from catalog"""
    name_lower = name.lower()
    for key, info in SUBSCRIPTION_CATALOG.items():
        if key in name_lower:
            return info
    return {'name': name, 'category': 'other', 'logo': '💳'}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        # Check if user exists, if not create
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                email=user_info['email'],
                name=user_info.get('name'),
                profile_pic=user_info.get('picture')
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect('/')
    
    return redirect('/')

@app.route('/api/auth/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/api/user')
@login_required
def get_user():
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'profile_pic': current_user.profile_pic
    })

@app.route('/api/subscriptions', methods=['GET', 'POST'])
@login_required
def handle_subscriptions():
    if request.method == 'GET':
        subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': sub.id,
            'name': sub.name,
            'amount': sub.amount,
            'currency': sub.currency,
            'billing_cycle': sub.billing_cycle,
            'category': sub.category,
            'next_billing_date': sub.next_billing_date.isoformat() if sub.next_billing_date else None,
            'is_active': sub.is_active,
            'logo_url': sub.logo_url,
            'detected_from': sub.detected_from,
            'confidence': sub.confidence
        } for sub in subscriptions])
    
    elif request.method == 'POST':
        data = request.json
        
        # Get subscription info from catalog
        sub_info = get_subscription_info(data.get('name', ''))
        
        subscription = Subscription(
            user_id=current_user.id,
            name=sub_info['name'],
            amount=data.get('amount', 0),
            currency=data.get('currency', 'USD'),
            billing_cycle=data.get('billing_cycle', 'monthly'),
            category=sub_info['category'],
            next_billing_date=datetime.strptime(data['next_billing_date'], '%Y-%m-%d').date() if data.get('next_billing_date') else None,
            is_active=data.get('is_active', True),
            logo_url=sub_info.get('logo'),
            detected_from=data.get('detected_from', 'manual'),
            confidence=data.get('confidence', 1.0)
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({'id': subscription.id, 'message': 'Subscription added successfully'}), 201

@app.route('/api/subscriptions/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def handle_subscription(id):
    subscription = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'PUT':
        data = request.json
        subscription.name = data.get('name', subscription.name)
        subscription.amount = data.get('amount', subscription.amount)
        subscription.billing_cycle = data.get('billing_cycle', subscription.billing_cycle)
        subscription.category = data.get('category', subscription.category)
        subscription.is_active = data.get('is_active', subscription.is_active)
        
        if data.get('next_billing_date'):
            subscription.next_billing_date = datetime.strptime(data['next_billing_date'], '%Y-%m-%d').date()
        
        db.session.commit()
        return jsonify({'message': 'Subscription updated successfully'})
    
    elif request.method == 'DELETE':
        db.session.delete(subscription)
        db.session.commit()
        return jsonify({'message': 'Subscription deleted successfully'})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Extract text from PDF
            text = extract_text_from_pdf(filepath)
            
            if not text.strip():
                return jsonify({'error': 'Could not extract text from PDF'}), 400
            
            # Process with Gemini
            result = process_with_gemini(text)
            
            # Save upload record
            upload = StatementUpload(
                user_id=current_user.id,
                filename=filename,
                processed=True,
                subscriptions_found=len(result.get('subscriptions', []))
            )
            db.session.add(upload)
            
            # Add found subscriptions to database
            for sub_data in result.get('subscriptions', []):
                # Check if subscription already exists
                existing = Subscription.query.filter_by(
                    user_id=current_user.id,
                    name=sub_data['name']
                ).first()
                
                if not existing:
                    sub_info = get_subscription_info(sub_data['name'])
                    
                    subscription = Subscription(
                        user_id=current_user.id,
                        name=sub_info['name'],
                        amount=sub_data['amount'],
                        currency='USD',
                        billing_cycle=sub_data.get('frequency', 'monthly'),
                        category=sub_info['category'],
                        logo_url=sub_info.get('logo'),
                        detected_from='pdf',
                        confidence=sub_data.get('confidence', 0.9)
                    )
                    db.session.add(subscription)
            
            db.session.commit()
            
            # Clean up file
            os.remove(filepath)
            
            return jsonify(result)
        
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/analytics')
@login_required
def get_analytics():
    subscriptions = Subscription.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # Calculate analytics
    total_monthly = 0
    total_yearly = 0
    by_category = {}
    
    for sub in subscriptions:
        monthly_amount = sub.amount
        if sub.billing_cycle == 'yearly':
            monthly_amount = sub.amount / 12
        elif sub.billing_cycle == 'weekly':
            monthly_amount = sub.amount * 4.33
        
        total_monthly += monthly_amount
        total_yearly += monthly_amount * 12
        
        if sub.category not in by_category:
            by_category[sub.category] = 0
        by_category[sub.category] += monthly_amount
    
    return jsonify({
        'total_monthly': round(total_monthly, 2),
        'total_yearly': round(total_yearly, 2),
        'by_category': {k: round(v, 2) for k, v in by_category.items()},
        'subscription_count': len(subscriptions),
        'average_subscription': round(total_monthly / len(subscriptions), 2) if subscriptions else 0
    })

@app.route('/api/catalog')
def get_catalog():
    return jsonify([
        {
            'name': info['name'],
            'category': info['category'],
            'logo': info['logo'],
            'suggested_price': {
                'netflix': 15.99,
                'spotify': 9.99,
                'amazon prime': 14.99,
                'disney': 13.99,
                'chatgpt': 20.00,
                'adobe': 54.99,
                'microsoft': 9.99,
                'dropbox': 11.99,
                'apple': 9.99,
                'google': 6.99
            }.get(key, 9.99)
        }
        for key, info in SUBSCRIPTION_CATALOG.items()
    ])

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=8080)