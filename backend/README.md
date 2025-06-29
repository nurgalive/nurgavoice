# NurgaVoice Backend

This is the backend API for NurgaVoice - an AI-powered audio/video transcription and summarization service.

## Features

- FastAPI-based REST API
- WebSocket support for real-time updates
- Celery-based background task processing
- Support for multiple audio/video formats
- PDF, Markdown, and TXT export formats
- Rate limiting and authentication
- CORS support for cross-origin requests

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Redis** (required for Celery):
   ```bash
   redis-server
   ```

3. **Start the backend**:
   ```bash
   ./start.sh
   ```

4. **Expose via ngrok**:
   ```bash
   ngrok http 8000
   ```

## API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `GET /api/info` - Get API and model information
- `POST /upload` - Upload and process audio/video files
- `GET /status/{task_id}` - Get processing status
- `GET /download/{task_id}/{format}` - Download results
- `WebSocket /ws/{task_id}` - Real-time updates

### Authentication

All API endpoints (except `/health` and `/api/info`) require authentication via API key:

- Header: `X-API-Key: your-api-key`
- Query parameter: `?api_key=your-api-key`

## Configuration

Key configuration options in `config.py`:

- `API_KEY`: Authentication key for API access
- `MAX_FILE_SIZE`: Maximum upload file size (default: 512MB)
- `WHISPER_MODEL`: Whisper model to use (default: "base")
- `LLAMA_MODEL_PATH`: Path to LLM model for summarization
- `CELERY_BROKER_URL`: Redis URL for Celery
- `CELERY_RESULT_BACKEND`: Redis URL for results

## Environment Variables

Create a `.env` file:

```env
NURGAVOICE_API_KEY=your-secure-api-key-here
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Development

### Manual Startup

1. Start Redis:
   ```bash
   redis-server
   ```

2. Start Celery worker:
   ```bash
   celery -A tasks worker --loglevel=info
   ```

3. Start FastAPI app:
   ```bash
   python backend.py
   # or
   uvicorn backend:app --reload --host 0.0.0.0 --port 8000
   ```

### API Documentation

When running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Support

Build and run with Docker:

```bash
docker build -t nurgavoice-backend .
docker run -p 8000:8000 nurgavoice-backend
```

## Production Deployment

For production deployment, consider:

1. Using a proper WSGI server (Gunicorn + Uvicorn)
2. Setting up proper Redis configuration
3. Using environment-specific configuration
4. Implementing proper logging
5. Setting up monitoring and health checks

## Troubleshooting

### Common Issues

1. **Celery worker not starting**: Check Redis connection
2. **Out of memory**: Reduce model size or increase available RAM
3. **Slow processing**: Consider using GPU acceleration
4. **Upload failures**: Check file size limits and disk space

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
