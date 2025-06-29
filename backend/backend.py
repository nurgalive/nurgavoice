from fastapi import FastAPI, File, UploadFile, HTTPException, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import json
import aiofiles
from pathlib import Path
from tasks import celery_app
from tasks import transcribe_and_summarize
from config import Config
import asyncio
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

# Create FastAPI app
app = FastAPI(
    title="NurgaVoice API", 
    version="1.0.0",
    description="Audio/Video Transcription & Summarization API"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

def setup_unicode_fonts():
    """Setup Unicode fonts for PDF generation"""
    try:
        # Try to register DejaVu Sans font which supports Cyrillic
        # This font is commonly available on Linux systems
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Arial Unicode MS.ttf',  # macOS
            'C:/Windows/Fonts/arial.ttf',  # Windows
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Unicode', font_path))
                return True
                
        # Fallback: use built-in fonts
        print("Warning: No Unicode font found, using built-in fonts. Cyrillic characters may not display correctly.")
        return False
        
    except Exception as e:
        print(f"Warning: Could not register Unicode font: {e}")
        return False

def create_unicode_styles():
    """Create paragraph styles with Unicode font support"""
    styles = getSampleStyleSheet()
    
    # Check if Unicode font is available
    font_available = False
    try:
        # Test if our Unicode font was registered
        from reportlab.pdfbase.pdfmetrics import getFont
        getFont('Unicode')
        font_available = True
    except Exception:
        pass
    
    if font_available:
        # Create custom styles with Unicode font
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        
        title_style = ParagraphStyle(
            'UnicodeTitle',
            parent=styles['Title'],
            fontName='Unicode',
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'UnicodeHeading1',
            parent=styles['Heading1'],
            fontName='Unicode',
            fontSize=14,
            spaceAfter=6,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'UnicodeNormal',
            parent=styles['Normal'],
            fontName='Unicode',
            fontSize=10,
            spaceAfter=6
        )
        
        return {
            'Title': title_style,
            'Heading1': heading_style,
            'Normal': normal_style
        }
    else:
        # Use default styles
        return {
            'Title': styles['Title'],
            'Heading1': styles['Heading1'],
            'Normal': styles['Normal']
        }

# Setup fonts on startup
setup_unicode_fonts()

# CORS middleware for cross-origin requests (frontend on different domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Local development
        "https://*.netlify.app",  # Netlify deployments
        "https://nurgavoice.netlify.app",  # Your specific Netlify domain
        "https://nurgavoice.online",  # Your production domain
        "https://loved-magpie-routinely.ngrok-free.app",  # ngrok URL
        "*"  # Allow all origins in development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add middleware to handle ngrok-specific headers and security
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Request size limiting (50MB)
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > Config.MAX_FILE_SIZE:
            return Response("Request too large", status_code=413)
    
    # Authentication for API endpoints (skip health check and OPTIONS requests)
    if request.method != "OPTIONS" and request.url.path not in ["/health", "/api/info"]:
        # Check API key for protected endpoints
        if request.url.path.startswith(("/upload", "/status", "/download", "/ws")):
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            if api_key != Config.API_KEY:
                return Response("Unauthorized - Invalid API Key", status_code=401)
    
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # CORS headers for preflight requests
    if request.method == "OPTIONS":
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_update(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_json(message)
            except Exception:
                self.disconnect(task_id)

manager = ConnectionManager()

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > Config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {Config.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Check file extension
    if file.filename:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            )

# API Info endpoint
@app.get("/api/info")
async def get_api_info():
    """Get API information including model details"""
    # Get current LLM model info
    current_llm_model = None
    llm_model_name = "Unknown"
    llm_model_description = "Model information not available"
    
    # Find the current model in the available models
    for model_key, model_info in Config.AVAILABLE_LLAMA_MODELS.items():
        if model_info["path"] == Config.LLAMA_MODEL_PATH:
            current_llm_model = model_key
            llm_model_name = model_key.upper().replace("-", " ")
            llm_model_description = model_info["description"]
            break
    
    # If model not found in available models, use filename
    if current_llm_model is None:
        model_filename = Path(Config.LLAMA_MODEL_PATH).name
        llm_model_name = model_filename.replace(".gguf", "").replace("_", " ").upper()
    
    return {
        "whisper_model": Config.WHISPER_MODEL,
        "llm_model_name": llm_model_name,
        "llm_model_description": llm_model_description,
        "max_file_size_mb": Config.MAX_FILE_SIZE // (1024*1024),
        "supported_languages": Config.SUPPORTED_LANGUAGES,
        "language_names": Config.LANGUAGE_NAMES,
        "summary_lengths": Config.SUMMARY_LENGTHS,
        "allowed_extensions": list(Config.ALLOWED_EXTENSIONS),
        "diarization_enabled": Config.ENABLE_DIARIZATION,
        "diarization_min_speakers": Config.DIARIZATION_MIN_SPEAKERS,
        "diarization_max_speakers": Config.DIARIZATION_MAX_SPEAKERS
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "nurgavoice-api"}

# Handle CORS preflight requests explicitly
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle CORS preflight requests"""
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.post("/upload")
@limiter.limit("3/minute")  # Rate limit: 3 uploads per minute per IP
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    summary_length: str = Form("medium"),
    enable_summary: str = Form("true"),
    enable_diarization: str = Form("false"),
    min_speakers: int = Form(1),
    max_speakers: int = Form(10)
):
    """Upload and process audio/video file"""
    try:
        # Validate file
        validate_file(file)
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Ensure upload directory exists
        upload_dir = Path(Config.UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / f"{task_id}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Convert enable_summary and enable_diarization to boolean
        enable_summary_bool = enable_summary.lower() in ('true', '1', 'yes', 'on')
        enable_diarization_bool = enable_diarization.lower() in ('true', '1', 'yes', 'on')
        
        # Validate diarization settings
        if enable_diarization_bool and not Config.ENABLE_DIARIZATION:
            raise HTTPException(status_code=400, detail="Speaker diarization is not enabled on this server")
        
        # Clamp speaker range to configured limits
        min_speakers = max(Config.DIARIZATION_MIN_SPEAKERS, min(min_speakers, Config.DIARIZATION_MAX_SPEAKERS))
        max_speakers = max(min_speakers, min(max_speakers, Config.DIARIZATION_MAX_SPEAKERS))
        
        # Start background task
        task = transcribe_and_summarize.delay(
            str(file_path),
            language,
            summary_length,
            enable_summary_bool,
            task_id,
            enable_diarization_bool,
            min_speakers,
            max_speakers
        )
        
        # Store task mapping
        await store_task_info(task_id, {
            "celery_task_id": task.id,
            "file_path": str(file_path),
            "filename": file.filename,
            "language": language,
            "summary_length": summary_length,
            "enable_summary": enable_summary_bool,
            "enable_diarization": enable_diarization_bool,
            "min_speakers": min_speakers,
            "max_speakers": max_speakers
        })
        
        return {"task_id": task_id, "status": "started"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get processing status"""
    try:
        task_info = await get_task_info(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")
        
        celery_task = celery_app.AsyncResult(task_info["celery_task_id"])
        
        if celery_task.state == 'PENDING':
            return {"state": "PENDING", "progress": 0}
        elif celery_task.state == 'PROGRESS':
            return {
                "state": "PROGRESS",
                "progress": celery_task.info.get('progress', 0),
                "step": celery_task.info.get('step', 'Processing...')
            }
        elif celery_task.state == 'SUCCESS':
            return {"state": "SUCCESS", "result": celery_task.result}
        elif celery_task.state == 'FAILURE':
            return {"state": "FAILURE", "error": str(celery_task.info)}
        else:
            return {"state": celery_task.state, "info": celery_task.info}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str, api_key: str = ""):
    """WebSocket endpoint for real-time updates"""
    # Validate API key
    if api_key != Config.API_KEY:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    await manager.connect(websocket, task_id)
    
    try:
        task_info = await get_task_info(task_id)
        if not task_info:
            await websocket.send_json({"state": "ERROR", "error": "Task not found"})
            return
        
        celery_task = celery_app.AsyncResult(task_info["celery_task_id"])
        
        # Send initial status
        await websocket.send_json({"state": "CONNECTED"})
        
        # Poll for updates
        while True:
            if celery_task.state == 'PENDING':
                await websocket.send_json({"state": "PENDING", "progress": 0})
            elif celery_task.state == 'PROGRESS':
                await websocket.send_json({
                    "state": "PROGRESS",
                    "progress": celery_task.info.get('progress', 0),
                    "step": celery_task.info.get('step', 'Processing...')
                })
            elif celery_task.state == 'SUCCESS':
                await websocket.send_json({"state": "SUCCESS", "result": celery_task.result})
                break
            elif celery_task.state == 'FAILURE':
                await websocket.send_json({"state": "FAILURE", "error": str(celery_task.info)})
                break
            
            await asyncio.sleep(1)  # Poll every second
            
    except WebSocketDisconnect:
        manager.disconnect(task_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"state": "ERROR", "error": str(e)})
    finally:
        manager.disconnect(task_id)

@app.get("/download/{task_id}/{format}")
async def download_file(task_id: str, format: str):
    """Download processed results"""
    try:
        task_info = await get_task_info(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")
        
        celery_task = celery_app.AsyncResult(task_info["celery_task_id"])
        
        if celery_task.state != 'SUCCESS':
            raise HTTPException(status_code=400, detail="Task not completed successfully")
        
        result = celery_task.result
        
        if format == "txt":
            return create_txt_response(result, task_id)
        elif format == "md":
            return create_md_response(result, task_id)
        elif format == "pdf":
            return create_pdf_response(result, task_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

def create_txt_response(result, task_id):
    """Create TXT file response"""
    content = []
    
    # Add summary if available
    if result.get('summary'):
        content.append("SUMMARY")
        content.append("=" * 50)
        content.append(result['summary'])
        content.append("")
    
    # Add transcription
    if result.get('transcription', {}).get('text'):
        content.append("TRANSCRIPTION")
        content.append("=" * 50)
        content.append(result['transcription']['text'])
        content.append("")
    
    # Add metadata
    if result.get('metadata'):
        content.append("METADATA")
        content.append("=" * 50)
        for key, value in result['metadata'].items():
            content.append(f"{key}: {value}")
        content.append("")
    
    # Add timestamped transcription if available
    if result.get('transcription', {}).get('segments'):
        content.append("TIMESTAMPED TRANSCRIPTION")
        content.append("=" * 50)
        for segment in result['transcription']['segments']:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '')
            speaker = segment.get('speaker', None)
            start_time = f"{int(start//60)}:{int(start%60):02d}"
            end_time = f"{int(end//60)}:{int(end%60):02d}"
            
            if speaker:
                content.append(f"[{start_time} - {end_time}] {speaker}: {text}")
            else:
                content.append(f"[{start_time} - {end_time}] {text}")
        content.append("")
    
    txt_content = "\n".join(content)
    
    return Response(
        content=txt_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=transcription_{task_id}.txt"}
    )

def create_md_response(result, task_id):
    """Create Markdown file response"""
    content = []
    
    # Add summary if available
    if result.get('summary'):
        content.append("# Summary")
        content.append("")
        content.append(result['summary'])
        content.append("")
    
    # Add transcription
    if result.get('transcription', {}).get('text'):
        content.append("# Transcription")
        content.append("")
        content.append(result['transcription']['text'])
        content.append("")
    
    # Add metadata
    if result.get('metadata'):
        content.append("# Metadata")
        content.append("")
        for key, value in result['metadata'].items():
            content.append(f"**{key}**: {value}")
        content.append("")
    
    # Add timestamped transcription if available
    if result.get('transcription', {}).get('segments'):
        content.append("# Timestamped Transcription")
        content.append("")
        for segment in result['transcription']['segments']:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '')
            speaker = segment.get('speaker', None)
            start_time = f"{int(start//60)}:{int(start%60):02d}"
            end_time = f"{int(end//60)}:{int(end%60):02d}"
            
            if speaker:
                content.append(f"**[{start_time} - {end_time}] {speaker}:** {text}")
            else:
                content.append(f"**[{start_time} - {end_time}]** {text}")
            content.append("")  # Add empty line after each timestamp entry
        content.append("")
    
    md_content = "\n".join(content)
    
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=transcription_{task_id}.md"}
    )

def create_pdf_response(result, task_id):
    """Create PDF file response"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = create_unicode_styles()
    story = []
    
    # Title
    story.append(Paragraph("Transcription Results", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Summary
    if result.get('summary'):
        story.append(Paragraph("Summary", styles['Heading1']))
        story.append(Paragraph(result['summary'], styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Transcription
    if result.get('transcription', {}).get('text'):
        story.append(Paragraph("Transcription", styles['Heading1']))
        story.append(Paragraph(result['transcription']['text'], styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Metadata
    if result.get('metadata'):
        story.append(Paragraph("Metadata", styles['Heading1']))
        for key, value in result['metadata'].items():
            story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Add timestamped transcription if available
    if result.get('transcription', {}).get('segments'):
        story.append(Paragraph("Timestamped Transcription", styles['Heading1']))
        for segment in result['transcription']['segments']:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '')
            speaker = segment.get('speaker', None)
            # Format timestamp similar to other formats
            start_time = f"{int(start//60)}:{int(start%60):02d}"
            end_time = f"{int(end//60)}:{int(end%60):02d}"
            
            if speaker:
                timestamp_text = f"<b>[{start_time} - {end_time}] {speaker}:</b> {text}"
            else:
                timestamp_text = f"<b>[{start_time} - {end_time}]</b> {text}"
            story.append(Paragraph(timestamp_text, styles['Normal']))
        story.append(Spacer(1, 12))
    
    doc.build(story)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=transcription_{task_id}.pdf"}
    )

# Helper functions for task management
async def store_task_info(task_id: str, info: dict):
    """Store task information"""
    results_dir = Path(Config.RESULTS_DIR)
    results_dir.mkdir(exist_ok=True)
    
    task_file = results_dir / f"{task_id}_task.json"
    async with aiofiles.open(task_file, 'w') as f:
        await f.write(json.dumps(info, indent=2))

async def get_task_info(task_id: str) -> Optional[dict]:
    """Get task information"""
    results_dir = Path(Config.RESULTS_DIR)
    task_file = results_dir / f"{task_id}_task.json"
    
    if not task_file.exists():
        return None
    
    async with aiofiles.open(task_file, 'r') as f:
        content = await f.read()
        return json.loads(content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
