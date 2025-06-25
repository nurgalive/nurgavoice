#!/usr/bin/env python3
"""
Test script for NurgaVoice application
Run basic tests to ensure the application works correctly
"""

import requests
import time
import sys
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the application. Is it running?")
        return False

def test_main_page():
    """Test the main page loads"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200 and "NurgaVoice" in response.text:
            print("✅ Main page loads correctly")
            return True
        else:
            print(f"❌ Main page test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main page test failed: {e}")
        return False

def create_test_audio():
    """Create a simple test audio file using ffmpeg"""
    test_file = "test_audio.wav"
    try:
        import subprocess
        # Generate a 5-second sine wave audio file
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5',
            '-ar', '16000', '-ac', '1', test_file, '-y'
        ], check=True, capture_output=True)
        print("✅ Test audio file created")
        return test_file
    except subprocess.CalledProcessError:
        print("❌ Could not create test audio file (ffmpeg required)")
        return None
    except FileNotFoundError:
        print("❌ ffmpeg not found. Please install ffmpeg to run upload tests.")
        return None

def test_file_upload():
    """Test file upload functionality"""
    test_file = create_test_audio()
    if not test_file:
        return False
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'audio/wav')}
            data = {'language': 'auto', 'summary_length': 'short'}
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ File upload successful, task ID: {task_id}")
            
            # Test status endpoint
            if task_id:
                status_response = requests.get(f"{BASE_URL}/status/{task_id}")
                if status_response.status_code == 200:
                    print("✅ Status endpoint working")
                else:
                    print("❌ Status endpoint failed")
            
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    print("🧪 NurgaVoice Test Suite")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health_check),
        ("Main Page", test_main_page),
        ("File Upload", test_file_upload),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running {test_name} test...")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Please check the application setup.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
