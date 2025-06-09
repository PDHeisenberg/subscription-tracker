from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import PyPDF2
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv
import json
import base64
from PIL import Image
import io

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
# Use gemini-1.5-flash which is the latest available model
model = genai.GenerativeModel('gemini-1.5-flash')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        print(f"[DEBUG] Extracted text length with pdfplumber: {len(text)} characters")
    except Exception as e:
        print(f"Error extracting text with pdfplumber: {e}")
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            print(f"[DEBUG] Extracted text length with PyPDF2: {len(text)} characters")
        except Exception as e2:
            print(f"Error extracting text with PyPDF2: {e2}")
    
    # Print first 500 characters for debugging
    if text:
        print(f"[DEBUG] First 500 chars of extracted text: {text[:500]}")
    else:
        print("[DEBUG] No text extracted from PDF!")
    
    return text

def process_with_gemini(text):
    print(f"[DEBUG] Sending {len(text)} characters to Gemini")
    
    prompt = """
    Analyze this bank statement and identify all recurring subscriptions or monthly charges.
    Look for patterns like:
    - Netflix, Spotify, Apple Music, Amazon Prime, Disney+, YouTube Premium
    - Software subscriptions like Adobe, Microsoft, Dropbox
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
        
        print(f"[DEBUG] Gemini response: {result_text[:500]}...")
        
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        
        parsed_result = json.loads(result_text)
        print(f"[DEBUG] Found {len(parsed_result.get('subscriptions', []))} subscriptions")
        return parsed_result
    except Exception as e:
        print(f"[ERROR] Error processing with Gemini: {e}")
        print(f"[ERROR] Raw response: {result_text if 'result_text' in locals() else 'No response'}")
        return {"error": str(e), "subscriptions": [], "total_monthly_cost": 0}

@app.route('/')
def index():
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subscription Finder - AI Bank Statement Analyzer</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-3xl font-bold text-center mb-8">AI Subscription Finder</h1>
            
            <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
                <div class="mb-6">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Upload Bank Statement (PDF)
                    </label>
                    <input type="file" id="pdfFile" accept=".pdf" 
                           class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                </div>
                
                <button onclick="uploadPDF()" 
                        class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-200">
                    Analyze Statement
                </button>
                
                <div id="loading" class="hidden mt-4 text-center">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p class="mt-2 text-gray-600">Analyzing your statement with AI...</p>
                </div>
                
                <div id="results" class="mt-6 hidden">
                    <h2 class="text-xl font-semibold mb-4">Found Subscriptions:</h2>
                    <div id="subscriptionsList" class="space-y-3"></div>
                    <div id="totalCost" class="mt-4 p-4 bg-gray-100 rounded-md font-semibold"></div>
                </div>
                
                <div id="error" class="mt-4 hidden bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded"></div>
            </div>
        </div>
        
        <script>
            async function uploadPDF() {
                const fileInput = document.getElementById('pdfFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    showError('Please select a PDF file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                document.getElementById('loading').classList.remove('hidden');
                document.getElementById('results').classList.add('hidden');
                document.getElementById('error').classList.add('hidden');
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        displayResults(data);
                    } else {
                        showError(data.error || 'An error occurred');
                    }
                } catch (error) {
                    showError('Network error: ' + error.message);
                } finally {
                    document.getElementById('loading').classList.add('hidden');
                }
            }
            
            function displayResults(data) {
                const subscriptionsList = document.getElementById('subscriptionsList');
                const totalCost = document.getElementById('totalCost');
                const results = document.getElementById('results');
                
                subscriptionsList.innerHTML = '';
                
                if (data.subscriptions && data.subscriptions.length > 0) {
                    data.subscriptions.forEach(sub => {
                        const subDiv = document.createElement('div');
                        subDiv.className = 'border border-gray-200 rounded-md p-4';
                        subDiv.innerHTML = `
                            <div class="flex justify-between items-start">
                                <div>
                                    <h3 class="font-semibold">${sub.name}</h3>
                                    <p class="text-sm text-gray-600">Category: ${sub.category}</p>
                                    <p class="text-sm text-gray-600">Frequency: ${sub.frequency}</p>
                                    <p class="text-sm text-gray-600">Last charged: ${sub.date}</p>
                                </div>
                                <div class="text-right">
                                    <p class="text-lg font-semibold">$${sub.amount.toFixed(2)}</p>
                                    <p class="text-xs text-gray-500">Confidence: ${(sub.confidence * 100).toFixed(0)}%</p>
                                </div>
                            </div>
                        `;
                        subscriptionsList.appendChild(subDiv);
                    });
                    
                    totalCost.innerHTML = `Total Monthly Cost: $${data.total_monthly_cost.toFixed(2)}`;
                    results.classList.remove('hidden');
                } else {
                    showError('No subscriptions found in the statement');
                }
            }
            
            function showError(message) {
                const errorDiv = document.getElementById('error');
                errorDiv.textContent = message;
                errorDiv.classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            text = extract_text_from_pdf(filepath)
            
            if not text.strip():
                return jsonify({'error': 'Could not extract text from PDF'}), 400
            
            result = process_with_gemini(text)
            
            os.remove(filepath)
            
            return jsonify(result)
        
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8080)