from celery import Celery
import whisperx
import os
import json
from pathlib import Path
from typing import Dict, Any
import subprocess
import traceback
from llama_cpp import Llama
from config import Config

# Initialize Celery
celery_app = Celery(
    "transcription_tasks",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)

# Global variables for loaded models
whisper_model = None
llm_model = None  # Renamed from llama_model to be more generic


def cleanup_file(file_path: str, description: str = "file") -> None:
    """Safely delete a file with error handling"""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Deleted {description}: {file_path}")
        except Exception as e:
            print(f"Warning: Could not delete {description} {file_path}: {e}")


def load_whisper_model():
    """Load WhisperX model if not already loaded"""
    global whisper_model
    if whisper_model is None:
        try:
            device = "cuda" if os.system("nvidia-smi") == 0 else "cpu"
            print(f"Running Whisper model on: {device}")
            compute_type = "float16" if device == "cuda" else "int8"
            whisper_model = whisperx.load_model(
                Config.WHISPER_MODEL, device, compute_type=compute_type
            )
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            # Fallback to CPU
            whisper_model = whisperx.load_model(Config.WHISPER_MODEL, "cpu")
    return whisper_model


def load_llama_model(model_name: str | None = None):
    """Load LLM model (Gemma, Llama, etc.) if not already loaded"""
    global llm_model
    
    # Determine which model to load
    if model_name and model_name in Config.AVAILABLE_LLAMA_MODELS:
        model_config = Config.AVAILABLE_LLAMA_MODELS[model_name]
        model_path = model_config["path"]
        context_size = model_config["context_size"]
        threads = model_config["recommended_threads"]
    else:
        model_path = Config.LLAMA_MODEL_PATH
        context_size = Config.LLAMA_MODEL_CONTEXT_SIZE
        threads = Config.LLAMA_MODEL_THREADS
    
    if llm_model is None and os.path.exists(model_path):
        try:
            print(f"Loading LLM model from: {model_path}")
            
            # Detect GPU availability
            gpu_layers = 0
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    print(f"🎮 GPU detected: {gpus[0].name} (Memory: {gpus[0].memoryTotal}MB)")
                    # Use GPU layers based on available VRAM
                    if gpus[0].memoryTotal > 8000:  # > 8GB VRAM
                        gpu_layers = -1  # Use all layers on GPU
                        print("🚀 Using ALL layers on GPU (high VRAM)")
                    elif gpus[0].memoryTotal > 4000:  # > 4GB VRAM
                        gpu_layers = 20  # Use partial layers
                        print("🚀 Using 20 layers on GPU (medium VRAM)")
                    else:
                        gpu_layers = 10  # Use fewer layers
                        print("🚀 Using 10 layers on GPU (low VRAM)")
                else:
                    print("💻 No GPU detected, using CPU only")
            except ImportError:
                # Try alternative GPU detection
                try:
                    result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
                    if result.returncode == 0:
                        print("🎮 NVIDIA GPU detected via nvidia-smi")
                        gpu_layers = 20  # Conservative default
                        print("🚀 Using 20 layers on GPU")
                    else:
                        print("💻 No NVIDIA GPU detected, using CPU only")
                except FileNotFoundError:
                    print("💻 nvidia-smi not found, using CPU only")
            
            llm_model = Llama(
                model_path=model_path,
                n_ctx=context_size,
                n_threads=threads,
                n_gpu_layers=gpu_layers,  # Enable GPU acceleration
                # verbose=True,  # Enable verbose to see GPU usage
                # Additional optimizations
                n_batch=512,  # Batch size for processing
                use_mmap=True,  # Use memory mapping for faster loading
                use_mlock=False,  # Don't lock model in RAM (allows swapping)
            )
            
            if gpu_layers > 0:
                print(f"✅ Successfully loaded LLM model with {gpu_layers} GPU layers")
            else:
                print(f"✅ Successfully loaded LLM model on CPU only")
            print(f"📊 Context size: {context_size}")
            
        except Exception as e:
            print(f"❌ Error loading LLM model: {e}")
            print(f"Make sure the model file exists at: {model_path}")
            print("You can download models from: https://huggingface.co/models")
    elif not os.path.exists(model_path):
        print(f"❌ LLM model not found at: {model_path}")
        print("Please download a compatible model file.")
    
    return llm_model


def convert_to_audio(file_path: str) -> str:
    """Convert video to audio using ffmpeg"""
    audio_path = file_path.rsplit(".", 1)[0] + "_audio.wav"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                file_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                audio_path,
                "-y",
            ],
            check=True,
            capture_output=True,
        )
        return audio_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to convert video to audio: {e}")


def generate_summary(text: str, length: str = "medium") -> str:
    """Generate summary using LLM model (Gemma 3 optimized)"""
    llama = load_llama_model()
    if not llama:
        return "Summary generation unavailable (LLM model not loaded)"

    # Define prompts optimized for Gemma 3's instruction-following format
    prompts = {
        "short": f"<start_of_turn>user\nPlease provide a concise summary of the following text in 1-2 sentences:\n\n{text}<end_of_turn>\n<start_of_turn>model\n",
        "medium": f"<start_of_turn>user\nPlease summarize the following text in one clear paragraph:\n\n{text}<end_of_turn>\n<start_of_turn>model\n",
        "long": f"<start_of_turn>user\nPlease provide a detailed summary of the following text, covering the main points and key details:\n\n{text}<end_of_turn>\n<start_of_turn>model\n",
    }

    prompt = prompts.get(length, prompts["medium"])

    try:
        print("🧠 Starting LLM inference...")
        # Check GPU memory before inference
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                memory_info = result.stdout.strip().split('\n')[0].split(', ')
                used_mb = int(memory_info[0])
                total_mb = int(memory_info[1])
                print(f"🎮 GPU Memory before inference: {used_mb}MB / {total_mb}MB ({used_mb/total_mb*100:.1f}%)")
        except Exception:
            pass
        
        response = llama(
            prompt,
            max_tokens=512 if length == "long" else 256,
            temperature=0.7,
            stop=["<end_of_turn>", "<start_of_turn>"],
            stream=False  # Ensure we get a complete response, not a stream
        )
        
        # Check GPU memory after inference
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                memory_info = result.stdout.strip().split('\n')[0].split(', ')
                used_mb = int(memory_info[0])
                total_mb = int(memory_info[1])
                print(f"🎮 GPU Memory after inference: {used_mb}MB / {total_mb}MB ({used_mb/total_mb*100:.1f}%)")
        except Exception:
            pass
        
        print("✅ LLM inference completed")
        
        # Handle the response correctly based on llama-cpp-python structure
        if isinstance(response, dict) and "choices" in response:
            return response["choices"][0]["text"].strip()
        else:
            return str(response).strip()
    except Exception as e:
        return f"Error generating summary: {e}"


@celery_app.task(bind=True)
def transcribe_and_summarize(
    self, file_path: str, language: str = "auto", summary_length: str = "medium", enable_summary: bool = True
) -> Dict[str, Any]:
    """Main task for transcription and summarization"""
    try:
        # Update task state
        self.update_state(
            state="PROGRESS", meta={"step": "Loading models", "progress": 10}
        )

        # Load Whisper model
        model = load_whisper_model()

        # Check if file is video and convert to audio
        self.update_state(
            state="PROGRESS", meta={"step": "Processing file", "progress": 20}
        )

        file_ext = Path(file_path).suffix.lower()
        if file_ext in [".mp4", ".avi"]:
            audio_path = convert_to_audio(file_path)
        else:
            audio_path = file_path

        # Load audio
        self.update_state(
            state="PROGRESS", meta={"step": "Loading audio", "progress": 30}
        )
        audio = whisperx.load_audio(audio_path)

        # Transcribe
        self.update_state(
            state="PROGRESS", meta={"step": "Transcribing", "progress": 40}
        )

        transcribe_options = {}
        if language != "auto":
            transcribe_options["language"] = language

        result = model.transcribe(audio, batch_size=16, **transcribe_options)
        
        # Extract language - WhisperX should return it in the result dict
        detected_language = 'unknown'
        if isinstance(result, dict):
            detected_language = result.get('language', 'unknown')
            
        print(f"Whisper detected language: {detected_language}")
        
        # Ensure we have a valid language code
        if not detected_language or detected_language == 'None' or detected_language is None:
            detected_language = 'unknown'

        # Align transcript (for better timestamps)
        self.update_state(
            state="PROGRESS", meta={"step": "Aligning transcript", "progress": 60}
        )
        try:
            model_a, metadata = whisperx.load_align_model(
                language_code=detected_language, device=model.device
            )
            aligned_result = whisperx.align(
                result["segments"], model_a, metadata, audio, str(model.device)
            )
            # Update result with aligned segments, but preserve the original language info
            result["segments"] = aligned_result["segments"] if "segments" in aligned_result else aligned_result
            print(f"Alignment completed, preserved language: {detected_language}")
        except Exception as e:
            print(f"Alignment failed: {e}")
            # Continue without alignment

        # Extract text and segments
        full_text = " ".join([segment["text"] for segment in result["segments"]])

        # Generate summary (conditional)
        if enable_summary:
            self.update_state(
                state="PROGRESS", meta={"step": "Generating summary", "progress": 80}
            )
            summary = generate_summary(full_text, summary_length)
        else:
            self.update_state(
                state="PROGRESS", meta={"step": "Skipping summary (disabled)", "progress": 80}
            )
            summary = "Summary generation was disabled by user."

        # Prepare result
        self.update_state(state="PROGRESS", meta={"step": "Finalizing", "progress": 90})

        final_result = {
            "transcription": {
                "text": full_text,
                "segments": result["segments"],
                "language": detected_language,
            },
            "summary": summary,
            "metadata": {
                "file_name": Path(file_path).name,
                "language": detected_language,
                "summary_length": summary_length,
                "summary_enabled": enable_summary,
                "duration": len(audio) / 16000 if audio is not None else None,
            },
        }

        # Save result to file
        result_file = os.path.join(Config.RESULTS_DIR, f"{self.request.id}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)

        # Cleanup temporary files
        if audio_path != file_path:
            cleanup_file(audio_path, "temporary audio file")

        # Cleanup uploaded file if configured to do so
        if Config.DELETE_UPLOADED_FILES_AFTER_PROCESSING:
            cleanup_file(file_path, "uploaded file")

        # Return the final result (don't call update_state with SUCCESS - Celery handles that automatically)
        return final_result

    except Exception as e:
        error_msg = f"Error during transcription: {str(e)}"
        traceback.print_exc()
        
        # Cleanup uploaded file even on failure if configured to do so
        if Config.DELETE_UPLOADED_FILES_AFTER_PROCESSING:
            cleanup_file(file_path, "uploaded file after error")
        
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg, "traceback": traceback.format_exc()},
        )
        raise Exception(error_msg)
