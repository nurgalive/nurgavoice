# Nurgavoice - Audio/Video Transcription and Summarization App

A FastAPI web application that performs automatic speech recognition and text summarization using WhisperX and Llama.cpp.

## Features

- Upload audio/video files (mp3, wav, mp4, avi)
- Real-time transcription progress tracking
- Multi-language support
- AI-powered summarization with adjustable length
- Download results as TXT or PDF
- Responsive web interface

## Setup Instructions

### Prerequisites

1. **Install system dependencies:**

#### Ubuntu/Debian

```bash
https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#ubuntu-installation
```

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
```

```bash
sudo dpkg -i cuda-keyring_1.1-1_all.deb
```

```bash
sudo apt update
```

```bash
sudo apt install ffmpeg redis-server python3-dev 
```

```bash
build-essential libcudnn8 libcudnn8-dev
````

#### macOS

```bash
brew install ffmpeg redis
```

#### Windows (using chocolatey)

```bash
choco install ffmpeg redis
```

2. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

3. **Download Whisper models:**

```bash
# This will download the base model (~140MB)
python -c "import whisperx; whisperx.load_model('base')"
```

4. **Download Llama model:**

```bash
# Download a small model for summarization (adjust URL as needed)
mkdir -p models
wget -O models/llama-7b-chat.q4_0.bin https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/resolve/main/llama-2-7b-chat.q4_0.bin
```

### Running the Application

#### Frontend

1. **Start the frontend server:**

 ```bash
cd frontend
npm install
npm run dev
```

- `npm run build` - Build for production
- `npm run preview` - Preview production build

#### Backend


1. **Start Redis server:**

   ```bash
   redis-server
   ```

2. **Start Celery worker (in another terminal):**

   ```bash
   cd backend
   celery -A tasks worker --loglevel=debug --concurrency=1 --max-tasks-per-child=1
   ```

3. **Start the FastAPI server:**

   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```bash
   cd backend
   python backend.py
   ```


4. **Access the application:**
   Open your browser and navigate to `http://localhost:3000`

## API Endpoints

- `GET /` - Main web interface
- `POST /upload` - Upload audio/video file
- `GET /status/{task_id}` - Check transcription progress
- `GET /download/{task_id}/{format}` - Download results (txt/pdf)
- `WebSocket /ws/{task_id}` - Real-time progress updates

## Configuration

Edit `config.py` to modify:

- File size limits
- Supported file formats
- Model paths
- Redis settings

## Troubleshooting

1. **CUDA issues:** Ensure CUDA is properly installed for GPU acceleration
2. **Memory errors:** Reduce batch size in whisper configuration
3. **Model not found:** Verify model paths in config.py
