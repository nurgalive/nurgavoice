import os

class Config:
    # File upload settings
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.mp4', '.avi', '.m4a', '.flac'}
    UPLOAD_DIR = "uploads"
    RESULTS_DIR = "results"
    
    # AI Models
    WHISPER_MODEL = "base"  # options: tiny, base, small, medium, large
    
    # Llama model configuration
    LLAMA_MODEL_PATH = "models/llama-7b-chat.q4_0.bin"
    LLAMA_MODEL_CONTEXT_SIZE = 2048  # Context window size
    LLAMA_MODEL_THREADS = 4  # Number of CPU threads to use
    LLAMA_MODEL_MAX_TOKENS = 512  # Max tokens for generation
    
    # Available Llama models (for easy switching)
    AVAILABLE_LLAMA_MODELS = {
        "llama2-7b-chat": {
            "path": "models/llama-2-7b-chat.q4_0.gguf",
            "description": "Llama 2 7B Chat - Good balance of speed and quality",
            "context_size": 4096,
            "recommended_threads": 4
        },
        "llama2-13b-chat": {
            "path": "models/llama-2-13b-chat.q4_0.gguf",
            "description": "Llama 2 13B Chat - Higher quality, more resource intensive",
            "context_size": 4096,
            "recommended_threads": 6
        },
        "codellama-7b": {
            "path": "models/codellama-7b-instruct.q4_0.gguf",
            "description": "Code Llama 7B - Optimized for code generation",
            "context_size": 16384,
            "recommended_threads": 4
        }
    }
    
    # Redis settings
    REDIS_URL = "redis://localhost:6379/0"
    
    # Celery settings
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Language support
    SUPPORTED_LANGUAGES = {
        'auto': 'Auto-detect',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese'
    }
    
    # Summary options
    SUMMARY_LENGTHS = {
        'short': 'Short (1-2 sentences)',
        'medium': 'Medium (1 paragraph)',
        'long': 'Long (multiple paragraphs)'
    }

# Create necessary directories
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.RESULTS_DIR, exist_ok=True)
os.makedirs("models", exist_ok=True)
