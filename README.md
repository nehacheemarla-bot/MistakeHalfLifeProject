# Mistake Half-Life Calculator

A premium learning analytics platform that models the rate at which errors decrease through repeated practice. Track mistakes by type, visualize decay curves, unlock achievements, and get AI-powered study assistance.

## ✨ Features

### Core
- **Multi-Type Mistake Tracking** — Track 5+ mistake categories simultaneously per day
- **Custom Mistake Types** — Add your own categories beyond the defaults 
- **Half-Life Calculator** — Calculate predicted mistake decay with `N(t) = N₀ × (½)^(t/t½)`

### Analytics & Visualization
- **Stacked Bar Charts** — Visualize mistakes by type over time
- **Doughnut Chart** — See type distribution at a glance
- **AI Prediction Graphs** — Future mistake trend predictions per type
- **Correct vs Mistaken Decay Curve** — Compare theoretical decay models
- **Radar Chart** — Spider chart showing mistake frequency by type
- **Daily Trend Line** — Total mistakes with moving average overlay

### Gamification
- **🔥 Streak Tracking** — Track consecutive days of logging
- **🏆 Achievements System** — Unlock badges for milestones (First Entry, Week Warrior, Perfect Day, etc.)
- **📊 Learning Progress Bar** — Animated shimmer progress indicator

### AI Features
- **Study Assistant** — AI-powered chat (OpenAI GPT-4o-mini + local fallback)
- **Personalized Advice** — AI incorporates your mistake data for tailored recommendations

### Platform
- **Admin Panel** — View all users and their data (admin role)
- **PDF Export** — Download polished mistake reports
- **CSV Export** — Export raw data for spreadsheet analysis
- **Dark/Light Mode** — Smooth theme toggling
- **Toast Notifications** — Beautiful success/error/info feedback
- **Responsive Design** — Works on mobile, tablet, and desktop
- **Keyboard Shortcuts** — Ctrl+Enter to submit, Esc to close sidebar

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3 (Glassmorphism), JavaScript, Chart.js |
| **Backend** | Python, Flask, Flask-SQLAlchemy, Flask-CORS |
| **Database** | SQLite |
| **AI** | OpenAI GPT-4o-mini (with smart local fallback) |
| **Fonts** | Inter, JetBrains Mono (Google Fonts) |

## 🚀 Local Setup

```bash
# 1. Install backend dependencies
cd backend
pip install -r requirements.txt

# 2. (Optional) Set OpenAI API key for AI chat
set OPENAI_API_KEY=your-key-here

# 3. Start the backend server
python app.py

# 4. Open frontend in browser
# Open frontend/index.html in your browser
```

**Default admin login**: `admin` / `admin123`

## 📁 Project Structure

```
MistakeHalfLifeProject/
├── README.md
├── .gitignore
├── backend/
│   ├── app.py              # Flask API server (v2.0)
│   ├── requirements.txt    # Python dependencies
│   ├── render.yaml         # Render deployment config
│   └── Procfile            # Process file for deployment
└── frontend/
    └── index.html          # Premium SPA (HTML + CSS + JS)
```

## 🌐 Deployment

### Backend (Render.com)

1. Push project to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set **Root Directory**: `backend`
5. Set **Build Command**: `pip install -r requirements.txt`
6. Set **Start Command**: `gunicorn app:app`
7. Add environment variable: `OPENAI_API_KEY` (optional)

### Frontend (Netlify / Vercel)

1. Update the `API` constant in `frontend/index.html` with your Render URL
2. Deploy `frontend/` directory to any static host

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | — | Create account |
| POST | `/login` | — | Login, get token |
| POST | `/reset-password` | — | Reset password |
| GET | `/mistakes` | ✅ | Get user's entries |
| POST | `/mistakes` | ✅ | Add day's mistakes |
| DELETE | `/mistakes/<id>` | ✅ | Delete an entry |
| DELETE | `/mistakes` | ✅ | Clear all history |
| GET | `/stats` | ✅ | Get aggregate stats |
| GET | `/export/csv` | ✅ | Export data as CSV |
| POST | `/chat` | ✅ | Study assistant |
| GET | `/admin/users` | 👑 | List all users |
| GET | `/admin/user/<id>/mistakes` | 👑 | View user's data |
| GET | `/health` | — | Health check |
