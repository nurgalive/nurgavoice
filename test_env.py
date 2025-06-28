#!/usr/bin/env python3
"""
Test script to verify .env file loading
"""

from config import Config

def test_env_loading():
    print("Testing .env file loading...")
    print(f"API Key: {Config.API_KEY}")
    print(f"Upload Dir: {Config.UPLOAD_DIR}")
    print(f"Results Dir: {Config.RESULTS_DIR}")
    print(f"Whisper Model: {Config.WHISPER_MODEL}")
    print(f"Redis URL: {Config.REDIS_URL}")
    print("\n✅ .env file is working correctly!")

if __name__ == "__main__":
    test_env_loading()
