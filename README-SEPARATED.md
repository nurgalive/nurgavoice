# NurgaVoice - Separated Frontend & Backend

NurgaVoice is an AI-powered audio/video transcription and summarization service, now with a separated architecture for flexible deployment.

## 🏗️ Architecture

- **Frontend**: Static web application (deployed on Netlify)
- **Backend**: FastAPI REST API with Celery workers (served via ngrok)
- **Communication**: REST API calls and WebSocket connections

## 🚀 Quick Start

### Backend Setup (Local + ngrok)

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Redis**:
   ```bash
   # Ubuntu/Debian
   sudo systemctl start redis-server
   
   # Or using Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

4. **Start backend services**:
   ```bash
   ./start.sh
   ```

5. **Expose via ngrok**:
   ```bash
   ngrok http 8000
   ```

   Copy the ngrok URL (e.g., `https://abc123.ngrok-free.app`)

### Frontend Deployment (Netlify)

#### Option 1: Direct Netlify Deployment

1. **Connect to Netlify**:
   - Connect your GitHub repository to Netlify
   - Set publish directory to `frontend`
   - Set build command to `echo "No build needed"`

2. **Configure environment variables** in Netlify:
   - `VITE_API_BASE_URL`: Your ngrok URL
   - `VITE_API_KEY`: `nurgavoice-demo-key-2025` (or your custom key)

#### Option 2: Local Testing

```bash
cd frontend
python -m http.server 3000
```

Visit `http://localhost:3000` and enter your ngrok URL when prompted.

## 📁 Project Structure

```
nurgavoice/
├── frontend/                 # Frontend static files
│   ├── index.html           # Main HTML file
│   ├── js/
│   │   ├── config.js        # Configuration management
│   │   └── app.js           # Main application logic
│   ├── css/
│   │   └── style.css        # Styles
│   ├── netlify.toml         # Netlify configuration
│   └── README.md            # Frontend documentation
├── backend/                  # Backend API
│   ├── backend.py           # FastAPI application
│   ├── tasks.py             # Celery tasks
│   ├── config.py            # Configuration
│   ├── start.sh             # Startup script
│   └── README.md            # Backend documentation
├── DEPLOYMENT.md            # Detailed deployment guide
└── README.md               # This file
```

## ⚙️ Configuration

### Backend Configuration

Set these environment variables or update `config.py`:

- `NURGAVOICE_API_KEY`: API authentication key
- `CELERY_BROKER_URL`: Redis URL for Celery
- `CELERY_RESULT_BACKEND`: Redis URL for results

### Frontend Configuration

The frontend automatically detects the environment:

- **Development**: Prompts for API URL
- **Production**: Uses environment variables from Netlify

## 🔧 Features

### Frontend Features

- ✅ Modern, responsive web interface
- ✅ Real-time upload progress
- ✅ WebSocket support with polling fallback
- ✅ Multiple file format support
- ✅ Automatic API URL configuration
- ✅ Download results in TXT, MD, PDF formats

### Backend Features

- ✅ FastAPI REST API
- ✅ Celery background processing
- ✅ WebSocket real-time updates
- ✅ Rate limiting and authentication
- ✅ Multiple export formats
- ✅ CORS support for cross-origin requests

## 🌐 Deployment Options

### Backend Deployment

- **Recommended**: Local + ngrok (free, easy setup)
- **Alternatives**: Heroku, Railway, DigitalOcean, AWS EC2

### Frontend Deployment

- **Recommended**: Netlify (free tier, automatic deployments)
- **Alternatives**: Vercel, GitHub Pages, Cloudflare Pages

## 🔒 Security

- API key authentication
- CORS configuration
- Rate limiting
- File size and type validation
- HTTPS support (ngrok + Netlify)

## 📖 Documentation

- [`frontend/README.md`](frontend/README.md) - Frontend specific documentation
- [`backend/README.md`](backend/README.md) - Backend specific documentation
- [`DEPLOYMENT.md`](DEPLOYMENT.md) - Detailed deployment guide

## 🛠️ Development

### Prerequisites

- Python 3.8+
- Redis
- ngrok account (free tier available)
- Netlify account (free tier available)

### Local Development

1. **Backend**: Run `backend/start.sh`
2. **Frontend**: Serve `frontend/` directory
3. **Connect**: Configure frontend to use local backend

## 📊 Monitoring

### Health Checks

- Backend: `GET https://your-ngrok-url.ngrok-free.app/health`
- Frontend: Visit your Netlify URL

### Logs

- Backend: Console output or log files
- Celery: Worker output
- Frontend: Browser developer console

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both frontend and backend
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting sections in the documentation
2. Verify your ngrok tunnel is active
3. Check API key configuration
4. Review browser console for frontend issues
5. Check backend logs for API issues

## 🔄 Migration from Monolithic Version

If upgrading from the previous monolithic version:

1. Your existing `config.py`, `tasks.py` remain compatible
2. Models and data directories can be copied to `backend/`
3. Frontend is completely new - no migration needed
4. Update any scripts to use the new architecture

---

**🎤 NurgaVoice** - Powered by WhisperX & Llama.cpp
