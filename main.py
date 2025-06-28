from fastapi import FastAPI, File, UploadFile, HTTPException, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import uuid
import json
import aiofiles
from pathlib import Path
from tasks import celery_app, transcribe_and_summarize
from config import Config
import asyncio
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI(title="Audio/Video Transcription & Summarization", version="1.0.0")

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

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["loved-magpie-routinely.ngrok-free.app", "localhost", "127.0.0.1"]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://loved-magpie-routinely.ngrok-free.app",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],  # Restrict to your ngrok domain only
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only necessary methods
    allow_headers=["Content-Type"],
)

# Add middleware to handle ngrok-specific headers and security
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Request size limiting (50MB)
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > Config.MAX_FILE_SIZE:
            return Response("Request too large", status_code=413)
    
    # Authentication for API endpoints (skip main page and static files)
    if not (request.url.path.startswith("/static") or request.url.path in ["/", "/health"]):
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
    
    # For ngrok, allow mixed content in development
    if "ngrok" in str(request.url.hostname or ""):
        response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    
    return response

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    """Main web interface"""
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
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "languages": Config.SUPPORTED_LANGUAGES,  # For form dropdown
        "language_names": Config.LANGUAGE_NAMES,  # For display mapping
        "summary_lengths": Config.SUMMARY_LENGTHS,
        "max_size_mb": Config.MAX_FILE_SIZE // (1024*1024),
        "whisper_model": Config.WHISPER_MODEL,
        "llm_model_name": llm_model_name,
        "llm_model_description": llm_model_description,
        "api_key": Config.API_KEY  # Pass API key to template for JavaScript
    })

@app.post("/upload")
@limiter.limit("3/minute")  # Rate limit: 3 uploads per minute per IP
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    summary_length: str = Form("medium")
):
    """Upload file and start transcription task"""
    validate_file(file)
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_path = os.path.join(Config.UPLOAD_DIR, f"{task_id}_{file.filename}")
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Start transcription task
        task = transcribe_and_summarize.delay(file_path, language, summary_length)
        
        return {
            "task_id": task.id,
            "message": "File uploaded successfully. Transcription started.",
            "filename": file.filename
        }
    
    except Exception as e:
        # Cleanup uploaded file on error
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not delete uploaded file {file_path} after upload error: {cleanup_error}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.get("/upload")
async def upload_info():
    """Info endpoint for upload - shows when accessed directly"""
    return {
        "message": "Upload endpoint - use POST method with multipart/form-data",
        "method": "POST",
        "expected_fields": {
            "file": "Audio/video file to transcribe",
            "language": "Language code (optional, default: 'auto')",
            "summary_length": "Summary length (optional, default: 'medium')"
        },
        "supported_formats": list(Config.ALLOWED_EXTENSIONS),
        "max_file_size_mb": Config.MAX_FILE_SIZE // (1024*1024),
        "web_interface": "Visit the main page at / to use the web interface"
    }

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get transcription task status"""
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is waiting to be processed'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'step': task.info.get('step', ''),
            'progress': task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:  # FAILURE
        response = {
            'state': task.state,
            'error': str(task.info)
        }
    
    return response

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket for real-time updates"""
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Check task status
            task = celery_app.AsyncResult(task_id)
            
            if task.state == 'PROGRESS':
                await manager.send_update(task_id, {
                    'state': task.state,
                    'step': task.info.get('step', ''),
                    'progress': task.info.get('progress', 0)
                })
            elif task.state in ['SUCCESS', 'FAILURE']:
                if task.state == 'SUCCESS':
                    await manager.send_update(task_id, {
                        'state': task.state,
                        'result': task.result
                    })
                else:
                    await manager.send_update(task_id, {
                        'state': task.state,
                        'error': str(task.info)
                    })
                break
            
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        manager.disconnect(task_id)

@app.get("/download/{task_id}/{format}")
async def download_result(task_id: str, format: str):
    """Download transcription results"""
    if format not in ['txt', 'pdf']:
        raise HTTPException(status_code=400, detail="Format must be 'txt' or 'pdf'")
    
    result_file = os.path.join(Config.RESULTS_DIR, f"{task_id}.json")
    if not os.path.exists(result_file):
        raise HTTPException(status_code=404, detail="Result not found")
    
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if format == 'txt':
        # Create TXT file
        content = f"TRANSCRIPTION\n{'='*50}\n\n"
        content += data['transcription']['text'] + "\n\n"
        content += f"SUMMARY\n{'='*50}\n\n"
        content += data['summary'] + "\n\n"
        content += f"METADATA\n{'='*50}\n\n"
        content += f"File: {data['metadata']['file_name']}\n"
        content += f"Language: {data['metadata']['language']}\n"
        content += f"Summary Length: {data['metadata']['summary_length']}\n"
        
        if data['metadata'].get('duration'):
            content += f"Duration: {data['metadata']['duration']:.2f} seconds\n"
        
        # Add timestamps if available
        if data['transcription'].get('segments'):
            content += f"\n\nTIMESTAMPED TRANSCRIPTION\n{'='*50}\n\n"
            for segment in data['transcription']['segments']:
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '')
                content += f"[{start:.2f}s - {end:.2f}s] {text}\n"
        
        filename = f"transcription_{task_id}.txt"
        file_path = os.path.join(Config.RESULTS_DIR, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return FileResponse(
            file_path, 
            filename=filename,
            media_type='text/plain'
        )
    
    elif format == 'pdf':
        # Create PDF file with Unicode support
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Get Unicode-compatible styles
        custom_styles = create_unicode_styles()
        
        # Title
        story.append(Paragraph("Transcription and Summary Report", custom_styles['Title']))
        story.append(Spacer(1, 12))
        
        # Metadata
        story.append(Paragraph("Metadata", custom_styles['Heading1']))
        story.append(Paragraph(f"<b>File:</b> {data['metadata']['file_name']}", custom_styles['Normal']))
        story.append(Paragraph(f"<b>Language:</b> {data['metadata']['language']}", custom_styles['Normal']))
        story.append(Paragraph(f"<b>Summary Length:</b> {data['metadata']['summary_length']}", custom_styles['Normal']))
        
        if data['metadata'].get('duration'):
            story.append(Paragraph(f"<b>Duration:</b> {data['metadata']['duration']:.2f} seconds", custom_styles['Normal']))
        
        story.append(Spacer(1, 12))
        
        # Summary
        story.append(Paragraph("Summary", custom_styles['Heading1']))
        # Escape HTML characters and handle Unicode text properly
        summary_text = data['summary'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(summary_text, custom_styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Transcription
        story.append(Paragraph("Full Transcription", custom_styles['Heading1']))
        # Escape HTML characters and handle Unicode text properly
        transcription_text = data['transcription']['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(transcription_text, custom_styles['Normal']))
        
        # Add timestamped transcription if available
        if data['transcription'].get('segments'):
            story.append(Spacer(1, 12))
            story.append(Paragraph("Timestamped Transcription", custom_styles['Heading1']))
            
            for segment in data['transcription']['segments']:
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                timestamp_text = f"[{start:.2f}s - {end:.2f}s] {text}"
                story.append(Paragraph(timestamp_text, custom_styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        filename = f"transcription_{task_id}.pdf"
        file_path = os.path.join(Config.RESULTS_DIR, filename)
        
        with open(file_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        return FileResponse(
            file_path, 
            filename=filename,
            media_type='application/pdf'
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
