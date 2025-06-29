from celery import Celery
import whisperx
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
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
diarization_model = None  # For speaker diarization


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
                verbose=False,  # Enable verbose to see GPU usage
                # Additional optimizations
                n_batch=512,  # Batch size for processing
                use_mmap=True,  # Use memory mapping for faster loading
                use_mlock=False,  # Don't lock model in RAM (allows swapping)
            )
            
            if gpu_layers > 0:
                print(f"✅ Successfully loaded LLM model with {gpu_layers} GPU layers")
            else:
                print("✅ Successfully loaded LLM model on CPU only")
            print(f"📊 Context size: {context_size}")
            
        except Exception as e:
            print(f"❌ Error loading LLM model: {e}")
            print(f"Make sure the model file exists at: {model_path}")
            print("You can download models from: https://huggingface.co/models")
    elif not os.path.exists(model_path):
        print(f"❌ LLM model not found at: {model_path}")
        print("Please download a compatible model file.")
    
    return llm_model


def load_diarization_model():
    """Load speaker diarization model if not already loaded"""
    global diarization_model
    
    if not Config.ENABLE_DIARIZATION:
        print("🔇 Speaker diarization is disabled in config")
        return None
        
    if diarization_model is None:
        try:
            # Check if HuggingFace token is provided
            if not Config.HUGGINGFACE_TOKEN:
                print("❌ HuggingFace token not found!")
                print("   Speaker diarization requires a HuggingFace token.")
                print("   1. Get your token from: https://huggingface.co/settings/tokens")
                print("   2. Accept model agreement at: https://huggingface.co/pyannote/speaker-diarization-3.1")
                print("   3. Set HUGGINGFACE_TOKEN environment variable")
                return None
            
            # Load WhisperX diarization pipeline
            print("🔄 Loading speaker diarization model...")
            
            # Determine device
            device = "cuda" if os.system("nvidia-smi") == 0 else "cpu"
            print(f"🎯 Loading diarization model on: {device}")
            
            # Load WhisperX DiarizationPipeline
            from whisperx.diarize import DiarizationPipeline
            diarization_model = DiarizationPipeline(
                use_auth_token=Config.HUGGINGFACE_TOKEN, 
                device=device
            )
            
            print("✅ Speaker diarization model loaded successfully")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error loading diarization model: {error_msg}")
            
            if "gated" in error_msg.lower() or "private" in error_msg.lower():
                print("   🔒 This appears to be a model access issue:")
                print("   1. Visit https://huggingface.co/pyannote/speaker-diarization-3.1")
                print("   2. Accept the user agreement for the model")
                print("   3. Make sure your HuggingFace token has appropriate permissions")
            elif "authentication" in error_msg.lower() or "token" in error_msg.lower():
                print("   🔑 This appears to be an authentication issue:")
                print("   1. Check your HuggingFace token is correct")
                print("   2. Get a new token from: https://huggingface.co/settings/tokens")
            
            print("   Speaker diarization will be disabled for this session.")
            return None
    
    return diarization_model


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
    self, 
    file_path: str, 
    language: str = "auto", 
    summary_length: str = "medium", 
    enable_summary: bool = True, 
    task_id: Optional[str] = None,
    enable_diarization: bool = False,
    min_speakers: int = 1,
    max_speakers: int = 10
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

        # Speaker Diarization (if enabled)
        speakers_detected = 0
        if enable_diarization and Config.ENABLE_DIARIZATION:
            self.update_state(
                state="PROGRESS", meta={"step": "Performing speaker diarization", "progress": 70}
            )
            try:
                print(f"🔧 DEBUG: Starting diarization - enable_diarization={enable_diarization}, Config.ENABLE_DIARIZATION={Config.ENABLE_DIARIZATION}")
                diarize_model = load_diarization_model()
                print(f"🔧 DEBUG: Diarization model loaded: {type(diarize_model)}")
                if diarize_model:
                    print("🎭 Starting speaker diarization...")
                    
                    # Step 1: Perform diarization on audio to get speaker segments
                    # Use min/max speakers if specified
                    print(f"🔧 DEBUG: Calling diarization with min_speakers={min_speakers}, max_speakers={max_speakers}")
                    if min_speakers is not None and max_speakers is not None:
                        diarize_segments = diarize_model(audio, min_speakers=min_speakers, max_speakers=max_speakers)
                    else:
                        diarize_segments = diarize_model(audio)
                    
                    print(f"🎯 Diarization completed, found segments: {len(diarize_segments) if hasattr(diarize_segments, '__len__') else 'Unknown'}")
                    print(f"🔧 DEBUG: Diarization segments type: {type(diarize_segments)}")
                    print(f"🔧 DEBUG: Diarization segments preview: {diarize_segments.head() if hasattr(diarize_segments, 'head') else str(diarize_segments)[:200]}")
                    
                    # Step 2: Assign speakers to transcript segments  
                    print("🔧 DEBUG: About to call assign_word_speakers")
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                    print("🔧 DEBUG: assign_word_speakers completed successfully")
                    
                    # Count unique speakers from the result
                    speakers = set()
                    for segment in result["segments"]:
                        if "speaker" in segment and segment["speaker"]:
                            speakers.add(segment["speaker"])
                    speakers_detected = len(speakers)
                    
                    print(f"✅ Speaker assignment completed. Detected {speakers_detected} speakers: {list(speakers)}")
                else:
                    print("⚠️  Diarization model not available, skipping speaker diarization")
                    print("   Check HuggingFace token and model access permissions")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Diarization failed: {error_msg}")
                print(f"🔧 DEBUG: Exception type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                
                if "gated" in error_msg.lower() or "private" in error_msg.lower():
                    print("   🔒 Model access issue - accept user agreement at:")
                    print("   https://huggingface.co/pyannote/speaker-diarization-3.1")
                elif "authentication" in error_msg.lower() or "token" in error_msg.lower():
                    print("   🔑 Authentication issue - check your HuggingFace token")
                elif "unexpected keyword argument" in error_msg.lower():
                    print("   📝 API issue - trying fallback without speaker count limits")
                    try:
                        # Fallback: try without min/max speakers
                        diarize_segments = diarize_model(audio)
                        result = whisperx.assign_word_speakers(diarize_segments, result)
                        
                        # Count speakers
                        speakers = set()
                        for segment in result["segments"]:
                            if "speaker" in segment and segment["speaker"]:
                                speakers.add(segment["speaker"])
                        speakers_detected = len(speakers)
                        
                        print(f"✅ Fallback diarization succeeded. Detected {speakers_detected} speakers: {list(speakers)}")
                    except Exception as fallback_error:
                        print(f"   ❌ Fallback also failed: {fallback_error}")
                
                if speakers_detected == 0:
                    print("   Continuing without speaker information")
        
        print(f"🔧 DEBUG: Final speakers_detected value: {speakers_detected}")

        # Extract text and segments
        full_text = " ".join([segment["text"] for segment in result["segments"]])

        # Calculate audio duration
        audio_duration = len(audio) / 16000 if audio is not None else None
        
        # Backend check: Auto-disable summary for audio shorter than 30 seconds
        original_enable_summary = enable_summary
        if audio_duration is not None and audio_duration < 30:
            if enable_summary:
                print(f"⚠️  Audio duration ({audio_duration:.1f}s) is shorter than 30 seconds. Auto-disabling summary generation.")
            enable_summary = False

        # Generate summary (conditional)
        if enable_summary:
            self.update_state(
                state="PROGRESS", meta={"step": "Generating summary", "progress": 80}
            )
            summary = generate_summary(full_text, summary_length)
        else:
            if original_enable_summary and audio_duration is not None and audio_duration < 30:
                self.update_state(
                    state="PROGRESS", meta={"step": "Skipping summary (audio too short)", "progress": 80}
                )
                summary = f"Summary generation was automatically disabled because the audio is only {audio_duration:.1f} seconds long (minimum 30 seconds required)."
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
                "summary_enabled": enable_summary,  # This now reflects the actual status after backend checks
                "summary_requested": original_enable_summary,  # This shows what the user originally requested
                "duration": audio_duration,
                "auto_disabled_reason": "Audio too short (< 30 seconds)" if original_enable_summary and not enable_summary and audio_duration is not None and audio_duration < 30 else None,
                "diarization_enabled": enable_diarization,
                "speakers_detected": speakers_detected,
                "min_speakers": min_speakers,
                "max_speakers": max_speakers,
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
