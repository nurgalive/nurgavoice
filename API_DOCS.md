# NurgaVoice API Documentation

## Overview

NurgaVoice is a FastAPI-based web application that provides audio/video transcription and AI-powered summarization services. The application uses WhisperX for speech-to-text conversion and Llama.cpp for text summarization.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required for the API endpoints.

## API Endpoints

### 1. Health Check

**GET** `/health`

Check if the service is running and healthy.

**Response:**
```json
{
    "status": "healthy",
    "message": "Service is running"
}
```

### 2. Main Web Interface

**GET** `/`

Returns the main HTML interface for the application.

**Response:** HTML page

### 3. Upload File for Processing

**POST** `/upload`

Upload an audio or video file for transcription and summarization.

**Parameters:**
- `file` (form-data, required): Audio/video file to process
- `language` (form-data, optional): Language code for transcription (default: "auto")
- `summary_length` (form-data, optional): Summary length preference (default: "medium")

**Supported file formats:**
- Audio: MP3, WAV, M4A, FLAC
- Video: MP4, AVI

**File size limit:** 100MB

**Language options:**
- `auto`: Auto-detect
- `en`: English
- `es`: Spanish
- `fr`: French
- `de`: German
- `it`: Italian
- `pt`: Portuguese
- `ru`: Russian
- `ja`: Japanese
- `ko`: Korean
- `zh`: Chinese

**Summary length options:**
- `short`: 1-2 sentences
- `medium`: 1 paragraph
- `long`: Multiple paragraphs

**Success Response:**
```json
{
    "task_id": "uuid-string",
    "message": "File uploaded successfully. Transcription started.",
    "filename": "example.mp3"
}
```

**Error Response:**
```json
{
    "detail": "Error message describing the issue"
}
```

### 4. Check Task Status

**GET** `/status/{task_id}`

Check the status of a transcription task.

**Parameters:**
- `task_id` (path, required): Task ID returned from upload endpoint

**Response:**

For pending tasks:
```json
{
    "state": "PENDING",
    "status": "Task is waiting to be processed"
}
```

For tasks in progress:
```json
{
    "state": "PROGRESS",
    "step": "Transcribing",
    "progress": 65
}
```

For completed tasks:
```json
{
    "state": "SUCCESS",
    "result": {
        "transcription": {
            "text": "Full transcription text...",
            "segments": [
                {
                    "start": 0.0,
                    "end": 3.5,
                    "text": "Hello world"
                }
            ],
            "language": "en"
        },
        "summary": "AI-generated summary of the content...",
        "metadata": {
            "file_name": "example.mp3",
            "language": "en",
            "summary_length": "medium",
            "duration": 120.5
        }
    }
}
```

For failed tasks:
```json
{
    "state": "FAILURE",
    "error": "Error message"
}
```

### 5. WebSocket for Real-time Updates

**WebSocket** `/ws/{task_id}`

Connect to receive real-time updates about task progress.

**Parameters:**
- `task_id` (path, required): Task ID to monitor

**Messages:**
The WebSocket will send JSON messages with the same format as the status endpoint.

### 6. Download Results

**GET** `/download/{task_id}/{format}`

Download the transcription and summary results.

**Parameters:**
- `task_id` (path, required): Task ID
- `format` (path, required): Download format ("txt" or "pdf")

**Response:** File download

## Error Codes

- `400 Bad Request`: Invalid file format or parameters
- `404 Not Found`: Task ID not found
- `413 Payload Too Large`: File size exceeds 100MB limit
- `500 Internal Server Error`: Server-side processing error

## Processing Steps

The application processes files through the following steps:

1. **File Upload** (0-10%): File is uploaded and validated
2. **Loading Models** (10-20%): AI models are loaded into memory
3. **Processing File** (20-30%): Video files are converted to audio if needed
4. **Loading Audio** (30-40%): Audio is loaded and preprocessed
5. **Transcribing** (40-60%): Speech-to-text conversion using WhisperX
6. **Aligning Transcript** (60-80%): Timestamp alignment for better accuracy
7. **Generating Summary** (80-90%): AI-powered summarization using Llama
8. **Finalizing** (90-100%): Results are saved and prepared for download

## Usage Examples

### cURL Examples

**Upload a file:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "summary_length=medium"
```

**Check status:**
```bash
curl "http://localhost:8000/status/your-task-id"
```

**Download results:**
```bash
curl -O "http://localhost:8000/download/your-task-id/txt"
```

### Python Example

```python
import requests
import time

# Upload file
with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    data = {'language': 'auto', 'summary_length': 'medium'}
    response = requests.post('http://localhost:8000/upload', files=files, data=data)

task_id = response.json()['task_id']

# Poll for completion
while True:
    status = requests.get(f'http://localhost:8000/status/{task_id}').json()
    
    if status['state'] == 'SUCCESS':
        print("Transcription complete!")
        print("Summary:", status['result']['summary'])
        break
    elif status['state'] == 'FAILURE':
        print("Error:", status['error'])
        break
    else:
        print(f"Progress: {status.get('progress', 0)}%")
        time.sleep(2)

# Download results
pdf_response = requests.get(f'http://localhost:8000/download/{task_id}/pdf')
with open('results.pdf', 'wb') as f:
    f.write(pdf_response.content)
```

### JavaScript Example

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('language', 'auto');
formData.append('summary_length', 'medium');

const uploadResponse = await fetch('/upload', {
    method: 'POST',
    body: formData
});

const { task_id } = await uploadResponse.json();

// WebSocket for real-time updates
const ws = new WebSocket(`ws://localhost:8000/ws/${task_id}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.state === 'PROGRESS') {
        updateProgress(data.progress, data.step);
    } else if (data.state === 'SUCCESS') {
        displayResults(data.result);
    } else if (data.state === 'FAILURE') {
        showError(data.error);
    }
};
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## File Storage

- Uploaded files are temporarily stored in the `uploads/` directory
- Results are stored in the `results/` directory
- Files are automatically cleaned up after processing (uploaded files) or after download (results)

## Model Configuration

The application uses the following models by default:
- **Whisper**: base model (configurable in `config.py`)
- **Llama**: 7B chat model (path configurable in `config.py`)

## Monitoring

- Use the `/health` endpoint for health checks
- Monitor Celery workers for background task processing
- Check Redis connection for task queue status
