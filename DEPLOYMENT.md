# NurgaVoice Deployment Guide

This guide explains how to deploy NurgaVoice with a separated frontend and backend architecture.

## Architecture Overview

- **Frontend**: Static files deployed on Netlify
- **Backend**: FastAPI application served via ngrok
- **Communication**: REST API calls and WebSocket connections

## Backend Deployment (ngrok)

### Prerequisites

1. Python 3.8+
2. Redis (for Celery)
3. ngrok account and client

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Redis** (required for Celery):
   ```bash
   # On Ubuntu/Debian
   sudo systemctl start redis-server
   
   # Or using Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

3. **Start Celery worker**:
   ```bash
   celery -A tasks worker --loglevel=info
   ```

4. **Start the backend API**:
   ```bash
   # Using the new backend-only file
   python backend.py
   
   # Or using uvicorn directly
   uvicorn backend:app --host 0.0.0.0 --port 8000
   ```

5. **Expose via ngrok**:
   ```bash
   ngrok http 8000
   ```

   Note the ngrok URL (e.g., `https://abc123.ngrok-free.app`)

### Environment Variables

Create a `.env` file in the backend directory:

```env
NURGAVOICE_API_KEY=your-secure-api-key-here
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Frontend Deployment (Netlify)

### Option 1: Direct Deployment

1. **Prepare the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Deploy to Netlify**:
   - Connect your GitHub repository to Netlify
   - Set the publish directory to `frontend`
   - Set build command to: `echo "No build needed"`

3. **Configure environment variables** in Netlify dashboard:
   - `VITE_API_BASE_URL`: Your ngrok URL (e.g., `https://abc123.ngrok-free.app`)
   - `VITE_API_KEY`: Same API key as backend

### Option 2: Manual Configuration

If you don't set environment variables, the frontend will prompt users to enter the API URL manually when they first visit the site.

## Configuration

### Backend Configuration

Key configuration options in `config.py`:

- `API_KEY`: Authentication key for API access
- `MAX_FILE_SIZE`: Maximum upload file size
- `WHISPER_MODEL`: Whisper model to use
- `LLAMA_MODEL_PATH`: Path to LLM model

### Frontend Configuration

The frontend automatically adapts to different environments:

- **Development**: Defaults to `http://localhost:8000`
- **Production**: Uses environment variables or prompts user

## Security Considerations

1. **API Key Management**:
   - Use a strong, unique API key
   - Keep it secret and rotate regularly
   - Use environment variables, not hardcoded values

2. **CORS Configuration**:
   - Update `allow_origins` in backend to restrict to your Netlify domain
   - Remove `"*"` from allowed origins in production

3. **HTTPS**:
   - ngrok provides HTTPS by default
   - Netlify provides HTTPS by default

## Monitoring and Maintenance

### Backend Monitoring

1. **Health Check**:
   ```bash
   curl https://your-ngrok-url.ngrok-free.app/health
   ```

2. **API Info**:
   ```bash
   curl https://your-ngrok-url.ngrok-free.app/api/info
   ```

### Logs

- Backend logs: Check console output or redirect to file
- Celery logs: Check worker output
- Frontend logs: Browser developer console

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - The app automatically falls back to polling
   - Check ngrok tunnel status
   - Verify API key configuration

2. **Upload Failures**:
   - Check file size limits
   - Verify API key
   - Check network connectivity

3. **Processing Stuck**:
   - Check Celery worker status
   - Verify Redis connection
   - Check available disk space

### Debug Mode

Enable debug logging in the backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Considerations

1. **Scalability**:
   - Use multiple Celery workers
   - Consider using a proper message broker (RabbitMQ)
   - Implement load balancing

2. **Persistence**:
   - Use persistent storage for uploads
   - Implement proper backup strategy
   - Consider database for task metadata

3. **Security**:
   - Implement rate limiting
   - Add request validation
   - Use proper authentication/authorization

## Cost Optimization

1. **ngrok**: Free tier has limitations; consider paid plan for production
2. **Netlify**: Free tier is generous for static sites
3. **Computing**: Consider cloud GPU instances for better performance

## Alternative Deployment Options

### Backend Alternatives
- Heroku
- Railway
- DigitalOcean App Platform
- AWS EC2 with public IP
- Google Cloud Run

### Frontend Alternatives
- Vercel
- GitHub Pages
- AWS S3 + CloudFront
- Cloudflare Pages
