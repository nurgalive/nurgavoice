#!/usr/bin/env python3
"""
Test script to check GPU availability and Llama GPU usage
Run this to verify if your setup can use GPU acceleration
"""

import os
import subprocess
import sys
from pathlib import Path

def check_nvidia_gpu():
    """Check if NVIDIA GPU is available"""
    print("🔍 Checking for NVIDIA GPU...")
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected!")
            print("GPU Information:")
            print(result.stdout)
            return True
        else:
            print("❌ nvidia-smi failed")
            return False
    except FileNotFoundError:
        print("❌ nvidia-smi not found - NVIDIA drivers may not be installed")
        return False

def check_cuda_availability():
    """Check if CUDA is available"""
    print("\n🔍 Checking CUDA availability...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA is available! Devices: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   Device {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            print("❌ CUDA is not available through PyTorch")
            return False
    except ImportError:
        print("⚠️  PyTorch not installed - cannot check CUDA availability")
        return False

def test_llama_gpu():
    """Test Llama with GPU acceleration"""
    print("\n🔍 Testing Llama GPU usage...")
    
    # Import local config to get model path
    try:
        from config import Config
        model_path = Config.LLAMA_MODEL_PATH
    except ImportError:
        print("❌ Cannot import config - make sure you're in the right directory")
        return False
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at: {model_path}")
        print("Please download a model first")
        return False
    
    try:
        from llama_cpp import Llama
        
        print(f"📁 Loading model from: {model_path}")
        
        # Get GPU memory before loading
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                memory_info = result.stdout.strip().split('\n')[0].split(', ')
                used_mb = int(memory_info[0])
                total_mb = int(memory_info[1])
                print(f"🎮 GPU Memory before loading: {used_mb}MB / {total_mb}MB")
        except Exception:
            pass
        
        # Test with different GPU layer configurations
        gpu_configs = [
            {"n_gpu_layers": -1, "name": "All layers on GPU"},
            {"n_gpu_layers": 20, "name": "20 layers on GPU"},
            {"n_gpu_layers": 10, "name": "10 layers on GPU"},
            {"n_gpu_layers": 0, "name": "CPU only"}
        ]
        
        for config in gpu_configs:
            try:
                print(f"\n🧪 Testing: {config['name']}")
                
                # Load model with specific GPU configuration
                llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,  # Smaller context for testing
                    n_gpu_layers=config["n_gpu_layers"],
                    verbose=True,
                    n_batch=512,
                    use_mmap=True,
                    use_mlock=False,
                )
                
                # Get GPU memory after loading
                try:
                    result = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        memory_info = result.stdout.strip().split('\n')[0].split(', ')
                        used_mb = int(memory_info[0])
                        total_mb = int(memory_info[1])
                        print(f"🎮 GPU Memory after loading: {used_mb}MB / {total_mb}MB")
                except Exception:
                    pass
                
                # Test inference
                print("🧠 Testing inference...")
                test_prompt = "Hello, how are you?"
                
                response = llm(
                    test_prompt,
                    max_tokens=50,
                    temperature=0.7,
                    stop=["\n"],
                    stream=False
                )
                
                if isinstance(response, dict) and "choices" in response:
                    output = response["choices"][0]["text"].strip()
                else:
                    output = str(response).strip()
                
                print(f"📝 Response: {output[:100]}...")
                print(f"✅ Success with {config['name']}")
                
                # This configuration works, so we can stop testing
                print(f"\n🎉 Recommended configuration: {config['name']}")
                break
                
            except Exception as e:
                print(f"❌ Failed with {config['name']}: {e}")
                continue
        
        return True
        
    except ImportError:
        print("❌ llama-cpp-python not installed")
        return False
    except Exception as e:
        print(f"❌ Error testing Llama: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 GPU and Llama Configuration Test")
    print("=" * 50)
    
    # Check system requirements
    gpu_available = check_nvidia_gpu()
    cuda_available = check_cuda_availability()
    
    if gpu_available:
        print("\n💡 Recommendations:")
        if cuda_available:
            print("   - Your system has GPU support!")
            print("   - Llama can use GPU acceleration")
            print("   - This will significantly speed up inference")
        else:
            print("   - GPU detected but CUDA may not be properly configured")
            print("   - Llama might still work with GPU but with limited acceleration")
    else:
        print("\n💡 Recommendations:")
        print("   - No GPU detected or drivers not installed")
        print("   - Llama will run on CPU only (slower)")
        print("   - Consider installing NVIDIA drivers and CUDA for better performance")
    
    # Test Llama
    if test_llama_gpu():
        print("\n🎉 Llama GPU test completed successfully!")
    else:
        print("\n❌ Llama GPU test failed")
    
    print("\n📋 How to monitor GPU usage during inference:")
    print("   - Run 'nvidia-smi' in another terminal")
    print("   - Or run 'watch -n 1 nvidia-smi' for continuous monitoring")
    print("   - Look for GPU memory usage and utilization")

if __name__ == "__main__":
    main()
