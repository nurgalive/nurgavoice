import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Security
    API_KEY = os.getenv("NURGAVOICE_API_KEY", "nurgavoice-demo-key-2025")  # Change default for production!
    
    # File upload settings
    MAX_FILE_SIZE = 512 * 1024 * 1024  # 512MB - reduced for demo safety
    ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.mp4', '.avi', '.m4a', '.flac', '.ogg'}
    UPLOAD_DIR = "uploads"
    RESULTS_DIR = "results"
    
    # File cleanup settings
    DELETE_UPLOADED_FILES_AFTER_PROCESSING = True  # Set to False to keep uploaded files
    # Note: Keeping uploaded files may be useful for debugging, reprocessing, or audit purposes
    # but will consume more disk space over time
    
    # AI Models
    WHISPER_MODEL = "base"  # options: tiny, base, small, medium, large
    
    # Speaker Diarization settings
    ENABLE_DIARIZATION = True  # Set to False to disable diarization capability
    DIARIZATION_MIN_SPEAKERS = 1  # Minimum number of speakers to detect
    DIARIZATION_MAX_SPEAKERS = 10  # Maximum number of speakers to detect
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")  # Required for pyannote.audio models
    
    # LLM model configuration (now using Gemma 3 as default)
    LLAMA_MODEL_PATH = "models/ggml-org_gemma-3-1b-it-GGUF_gemma-3-1b-it-Q4_K_M.gguf"
    LLAMA_MODEL_CONTEXT_SIZE = 32768  # Gemma 3 supports larger context
    LLAMA_MODEL_THREADS = 4  # Appropriate for 1B model
    LLAMA_MODEL_MAX_TOKENS = 512  # Max tokens for generation
    
    # Available LLM models (for easy switching)
    AVAILABLE_LLAMA_MODELS = {
        "gemma3-1b": {
            "path": "models/ggml-org_gemma-3-1b-it-GGUF_gemma-3-1b-it-Q4_K_M.gguf",
            "description": "Gemma 3 1B Instruct - Fast and efficient instruction-following model",
            "context_size": 32768,
            "recommended_threads": 8
        },
        "gemma3-12b": {
            "path": "models/gemma-3-12b-it-Q4_K_M.gguf",
            "description": "Gemma 3 12B Instruct - High quality instruction-following model",
            "context_size": 32768,
            "recommended_threads": 8
        }
    }
    
    # Redis settings
    REDIS_URL = "redis://localhost:6379/0"
    
    # Celery settings
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Language support for form selection
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
    
    # Extended language mapping for display (includes languages that Whisper might detect)
    LANGUAGE_NAMES = {
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
        'zh': 'Chinese',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'tr': 'Turkish',
        'pl': 'Polish',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish',
        'he': 'Hebrew',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'ms': 'Malay',
        'uk': 'Ukrainian',
        'cs': 'Czech',
        'sk': 'Slovak',
        'hu': 'Hungarian',
        'ro': 'Romanian',
        'bg': 'Bulgarian',
        'hr': 'Croatian',
        'sr': 'Serbian',
        'sl': 'Slovenian',
        'et': 'Estonian',
        'lv': 'Latvian',
        'lt': 'Lithuanian',
        'ca': 'Catalan',
        'eu': 'Basque',
        'gl': 'Galician',
        'mt': 'Maltese',
        'cy': 'Welsh',
        'ga': 'Irish',
        'is': 'Icelandic',
        'mk': 'Macedonian',
        'sq': 'Albanian',
        'af': 'Afrikaans',
        'sw': 'Swahili',
        'am': 'Amharic',
        'az': 'Azerbaijani',
        'be': 'Belarusian',
        'bn': 'Bengali',
        'bs': 'Bosnian',
        'el': 'Greek',
        'fa': 'Persian',
        'hy': 'Armenian',
        'ka': 'Georgian',
        'kk': 'Kazakh',
        'ky': 'Kyrgyz',
        'lo': 'Lao',
        'mn': 'Mongolian',
        'my': 'Myanmar',
        'ne': 'Nepali',
        'ps': 'Pashto',
        'si': 'Sinhala',
        'ta': 'Tamil',
        'te': 'Telugu',
        'tg': 'Tajik',
        'tk': 'Turkmen',
        'ur': 'Urdu',
        'uz': 'Uzbek',
        'yo': 'Yoruba',
        'zu': 'Zulu',
        'unknown': 'Unknown'
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
