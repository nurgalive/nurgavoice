#!/usr/bin/env python3
"""
Setup script for NurgaVoice application
Downloads required models and sets up the environment
"""

import os
import sys
import subprocess
import urllib.request
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def download_file(url, filename, description):
    """Download a file with progress"""
    print(f"🔄 {description}...")
    try:
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, (downloaded * 100) // total_size)
                print(f"\r   Progress: {percent}% ({downloaded}/{total_size} bytes)", end='')
        
        urllib.request.urlretrieve(url, filename, progress_hook)
        print(f"\n✅ {description} completed successfully")
        return True
    except Exception as e:
        print(f"\n❌ {description} failed: {e}")
        return False

def main():
    print("🚀 NurgaVoice Setup Script")
    print("=" * 50)
    
    # Create directories
    print("📁 Creating directories...")
    directories = ['uploads', 'results', 'models', 'static/css', 'static/js', 'templates']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")
    
    # Check if virtual environment exists
    venv_python = "./venv/bin/python"
    if not os.path.exists(venv_python):
        print("📦 Creating virtual environment...")
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            print("❌ Failed to create virtual environment.")
            sys.exit(1)
    
    # Check if pip is available in venv
    if not run_command(f"{venv_python} -m pip --version", "Checking pip installation in virtual environment"):
        print("❌ pip is not available in virtual environment.")
        sys.exit(1)
    
    # Install requirements using venv pip
    if not run_command(f"{venv_python} -m pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install requirements. Please check the error above.")
        print("💡 The dependency conflict has been fixed. Try running the setup again.")
        sys.exit(1)
    
    # Download Whisper models
    print("\n🎤 Setting up Whisper models...")
    whisper_setup = """
import whisperx
try:
    model = whisperx.load_model('base')
    print('Whisper base model loaded successfully')
except Exception as e:
    print(f'Error loading Whisper model: {e}')
"""
    
    if not run_command(f"{venv_python} -c \"{whisper_setup}\"", "Loading Whisper base model"):
        print("⚠️  Whisper model setup failed. You may need to download it manually.")
    
    # Download Llama model (optional)
    print("\n🦙 Setting up Llama model...")
    llama_model_path = "models/llama-2-7b-chat.q4_0.bin"
    
    if not os.path.exists(llama_model_path):
        print("Would you like to download a Llama model for summarization? (y/n)")
        response = input().lower().strip()
        
        if response in ['y', 'yes']:
            # This is a placeholder URL - replace with actual model URL
            model_url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/resolve/main/llama-2-7b-chat.q4_0.bin"
            if download_file(model_url, llama_model_path, "Downloading Llama model"):
                print("✅ Llama model downloaded successfully")
            else:
                print("⚠️  Llama model download failed. Summarization will be disabled.")
        else:
            print("⚠️  Skipping Llama model download. Summarization will be disabled.")
    else:
        print("✅ Llama model already exists")
    
    # Check Redis availability
    print("\n🔴 Checking Redis...")
    if run_command("redis-cli ping", "Testing Redis connection"):
        print("✅ Redis is running")
    else:
        print("⚠️  Redis is not running. Please start Redis server:")
        print("   - Ubuntu/Debian: sudo systemctl start redis-server")
        print("   - macOS: brew services start redis")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Start Redis if not already running")
    print(f"2. Start Celery worker: {venv_python} -m celery -A tasks.celery_app worker --loglevel=info")
    print(f"3. Start the application: {venv_python} -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    print("4. Open http://localhost:8000 in your browser")
    print("\nOr simply run: ./start.sh (which handles all the steps automatically)")

if __name__ == "__main__":
    main()
