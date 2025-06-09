# AI Subscription Tracker

A modern subscription management app powered by AI that automatically detects recurring payments from bank statements using Google's Gemini AI.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![Gemini](https://img.shields.io/badge/Gemini-1.5_Flash-orange.svg)

## ✨ Features

- 🤖 **AI-Powered PDF Analysis** - Upload bank statements and let Gemini AI automatically detect subscriptions
- 🔐 **Google OAuth Authentication** - Secure login with Google accounts
- 📊 **Analytics Dashboard** - Beautiful charts showing spending breakdown by category
- 💳 **Subscription Management** - Add, edit, and track all your subscriptions
- 🎨 **Modern UI** - Custom color palette with responsive design
- ⭐ **Popular Services Catalog** - Quick add Netflix, ChatGPT, Spotify, and more
- 📱 **Responsive Design** - Works perfectly on desktop and mobile

## 🎨 Design

The app features a custom color palette:
- **Orange** (#FF5B04) - Primary actions
- **Midnight Green** (#075056) - Secondary elements
- **Gunmetal** (#233038) - Dark text
- **Ivory Cream** (#FDF6E3) - Background
- **Sand Yellow** (#F4D47C) - Accents
- **Light Silver** (#D3DBDD) - Muted elements

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Cloud Project with OAuth 2.0 configured
- Gemini API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/subscription-tracker.git
cd subscription-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```env
GEMINI_API_KEY=your-gemini-api-key
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

4. Configure Google OAuth:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Add these redirect URIs:
     - `http://localhost:8080/api/auth/callback`
     - `http://127.0.0.1:8080/api/auth/callback`

5. Run the app:
```bash
python app_modern.py
```

6. Open http://localhost:8080 in your browser

## 📸 Screenshots

### Landing Page
Beautiful landing page with feature highlights and Google sign-in.

### Dashboard
- Monthly/yearly spending overview
- Active subscriptions list
- Category breakdown chart
- Quick actions

### AI Upload
Drag & drop PDF bank statements for automatic subscription detection.

## 🛠️ Technology Stack

- **Backend**: Flask 3.0
- **Database**: SQLite with SQLAlchemy
- **Authentication**: Flask-Login + Google OAuth
- **AI**: Google Gemini 1.5 Flash
- **Frontend**: Vanilla JavaScript, Tailwind CSS
- **Charts**: Chart.js
- **PDF Processing**: PyPDF2, pdfplumber

## 📁 Project Structure

```
subscription-ai-app/
├── app_modern.py          # Main Flask application
├── templates/
│   └── index.html        # Single page application
├── static/
│   ├── css/             # Styles (if any)
│   └── js/
│       └── app.js       # Frontend JavaScript
├── uploads/             # Temporary PDF storage
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (not in git)
└── README.md           # This file
```

## 🔧 API Endpoints

- `GET /` - Main application page
- `GET /api/auth/login` - Google OAuth login
- `GET /api/auth/callback` - OAuth callback
- `GET /api/auth/logout` - Logout
- `GET /api/user` - Get current user
- `GET/POST /api/subscriptions` - Manage subscriptions
- `PUT/DELETE /api/subscriptions/<id>` - Update/delete subscription
- `POST /api/upload` - Upload PDF for AI analysis
- `GET /api/analytics` - Get spending analytics
- `GET /api/catalog` - Get popular services

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful document analysis
- Flask community for the excellent framework
- Chart.js for beautiful visualizations