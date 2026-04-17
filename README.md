# Mistake Half-Life Calculator

A learning analytics platform that models the rate at which errors decrease through repeated practice. Track mistakes by type, visualize decay curves, get AI-powered study assistance, and measure learning effectiveness.

## Features

- **Multi-Type Mistake Tracking** — Track 5+ mistake categories simultaneously per day
- **Stacked Bar Charts** — Visualize mistakes by type over time
- **AI Prediction Graphs** — See predicted future mistake trends per type
- **Correct vs Mistaken Decay Curve** — Compare theoretical decay models
- **Study Assistant** — AI-powered chat (OpenAI + local fallback)
- **Admin Panel** — View all users and their mistake data
- **PDF Export** — Download mistake reports
- **Dark/Light Mode** — Toggle themes

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Backend**: Python, Flask, Flask-SQLAlchemy
- **Database**: SQLite
- **AI**: OpenAI GPT-4o-mini (with local fallback)

## Local Setup

```bash
# 1. Install dependencies
cd .vscode/backend
pip install -r requirements.txt

# 2. (Optional) Set OpenAI API key
set OPENAI_API_KEY=your-key-here

# 3. Start the backend
python app.py

# 4. Open frontend in browser
# Open .vscode/index.html in your browser
```

**Default admin login**: `admin` / `admin123`

## Deployment

### Backend (Render.com)

1. Push project to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set **Root Directory**: `.vscode/backend`
5. Set **Build Command**: `pip install -r requirements.txt`
6. Set **Start Command**: `gunicorn app:app`
7. Add environment variable: `OPENAI_API_KEY` (optional)

### Frontend (Netlify)

1. Update `const API = "https://your-render-url.onrender.com"` in `index.html`
2. Go to [netlify.com](https://netlify.com) → drag & drop your `index.html`

## Project Structure

```
MistakeHalfLifeProject/
├── .gitignore
├── README.md
└── .vscode/
    ├── index.html          # Frontend (HTML + CSS + JS)
    └── backend/
        ├── app.py           # Flask API server
        ├── requirements.txt # Python dependencies
        └── Procfile         # Render deployment config
```
