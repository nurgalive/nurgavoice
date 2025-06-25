#!/usr/bin/env python3
"""
Script to download and manage Llama models for the transcription service.
"""

import os
import sys
import requests
from pathlib import Path

# Popular GGUF model URLs (these are examples - replace with actual URLs)
POPULAR_MODELS = {
    "llama2-7b-chat-q4": {
        "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf",
        "filename": "llama-2-7b-chat.q4_0.gguf",
        "size": "3.8GB",
        "description": "Llama 2 7B Chat (Q4_0 quantization) - Good balance of quality and speed"
    },
    "llama2-7b-chat-q5": {
        "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q5_0.gguf",
        "filename": "llama-2-7b-chat.q5_0.gguf",
        "size": "4.6GB",
        "description": "Llama 2 7B Chat (Q5_0 quantization) - Better quality than Q4"
    },
    "codellama-7b-q4": {
        "url": "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.q4_0.gguf",
        "filename": "codellama-7b-instruct.q4_0.gguf",
        "size": "3.8GB",
        "description": "Code Llama 7B Instruct (Q4_0) - Optimized for code generation and understanding"
    },
    "vicuna-7b-q4": {
        "url": "https://huggingface.co/TheBloke/vicuna-7B-v1.5-GGUF/resolve/main/vicuna-7b-v1.5.q4_0.gguf",
        "filename": "vicuna-7b-v1.5.q4_0.gguf",
        "size": "3.8GB",
        "description": "Vicuna 7B v1.5 (Q4_0) - Fine-tuned for helpful assistant behavior"
    }
}


def download_file(url: str, destination: str, description: str = ""):
    """Download a file with progress bar"""
    print(f"Downloading {description}...")
    print(f"URL: {url}")
    print(f"Destination: {destination}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="")
        
        print(f"\n✅ Successfully downloaded {description}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error downloading {description}: {e}")
        if os.path.exists(destination):
            os.remove(destination)
        return False


def list_models():
    """List available models"""
    print("Available Llama models to download:")
    print("=" * 50)
    
    for key, model in POPULAR_MODELS.items():
        print(f"🔹 {key}")
        print(f"   Description: {model['description']}")
        print(f"   Size: {model['size']}")
        print(f"   Filename: {model['filename']}")
        print()


def list_installed_models():
    """List already installed models"""
    models_dir = Path("models")
    if not models_dir.exists():
        print("No models directory found.")
        return
    
    model_files = list(models_dir.glob("*.gguf")) + list(models_dir.glob("*.bin"))
    
    if not model_files:
        print("No models installed.")
        return
    
    print("Installed models:")
    print("=" * 30)
    for model_file in model_files:
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"🔹 {model_file.name} ({size_mb:.1f}MB)")


def download_model(model_key: str):
    """Download a specific model"""
    if model_key not in POPULAR_MODELS:
        print(f"❌ Model '{model_key}' not found.")
        print("Available models:")
        for key in POPULAR_MODELS.keys():
            print(f"  - {key}")
        return False
    
    model = POPULAR_MODELS[model_key]
    destination = os.path.join("models", model["filename"])
    
    if os.path.exists(destination):
        print(f"✅ Model {model_key} already exists at {destination}")
        return True
    
    return download_file(model["url"], destination, model["description"])


def update_config(model_key: str):
    """Update config.py to use the downloaded model"""
    if model_key not in POPULAR_MODELS:
        print(f"❌ Model '{model_key}' not found.")
        return
    
    model = POPULAR_MODELS[model_key]
    new_path = f"models/{model['filename']}"
    
    print("💡 To use this model, update your config.py:")
    print(f"   LLAMA_MODEL_PATH = \"{new_path}\"")
    
    # Optionally, we could automatically update the config file here
    # but it's safer to let the user do it manually


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python download_models.py list              # List available models")
        print("  python download_models.py installed         # List installed models")
        print("  python download_models.py download <model>  # Download a specific model")
        print("  python download_models.py recommended       # Download recommended model")
        print()
        list_models()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_models()
    elif command == "installed":
        list_installed_models()
    elif command == "download":
        if len(sys.argv) < 3:
            print("❌ Please specify a model to download")
            list_models()
        else:
            model_key = sys.argv[2]
            if download_model(model_key):
                update_config(model_key)
    elif command == "recommended":
        print("Downloading recommended model: llama2-7b-chat-q4")
        if download_model("llama2-7b-chat-q4"):
            update_config("llama2-7b-chat-q4")
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
