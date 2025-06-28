#!/usr/bin/env python3
"""
Test script to check if Llama is using GPU acceleration
"""

import sys
import os
sys.path.append('/home/azat/projects/nurgavoice')

from tasks import load_llama_model
import GPUtil

def test_llama_gpu():
    print("🧪 Testing Llama GPU acceleration...")
    print("=" * 50)
    
    # Check GPU before loading
    print("🔍 GPU status before loading model:")
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]
        print(f"   GPU: {gpu.name}")
        print(f"   Memory: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")
        print(f"   Utilization: {gpu.load * 100:.1f}%")
    else:
        print("   No GPU detected")
    
    print("\n🤖 Loading Llama model...")
    
    # Load the model (this should use GPU if available)
    model = load_llama_model()
    
    if model is None:
        print("❌ Failed to load model")
        return
    
    print("\n🔍 GPU status after loading model:")
    if gpus:
        gpu = gpus[0]
        print(f"   GPU: {gpu.name}")
        print(f"   Memory: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB (+{gpu.memoryUsed - gpus[0].memoryUsed if 'initial_memory' in locals() else 'N/A'}MB)")
        print(f"   Utilization: {gpu.load * 100:.1f}%")
    
    print("\n🧠 Testing inference with monitoring...")
    
    # Test prompt
    test_prompt = "<start_of_turn>user\nWhat is artificial intelligence?<end_of_turn>\n<start_of_turn>model\n"
    
    print("📝 Generating response...")
    
    # Monitor GPU during inference
    try:
        response = model(
            test_prompt,
            max_tokens=50,
            temperature=0.7,
            stop=["<end_of_turn>"],
            stream=False
        )
        
        if isinstance(response, dict) and "choices" in response:
            generated_text = response["choices"][0]["text"].strip()
        else:
            generated_text = str(response).strip()
        
        print(f"✅ Response generated: {generated_text[:100]}...")
        
        # Check GPU after inference
        print("\n🔍 GPU status after inference:")
        if gpus:
            gpu = gpus[0]
            print(f"   GPU: {gpu.name}")
            print(f"   Memory: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")
            print(f"   Utilization: {gpu.load * 100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error during inference: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 How to monitor GPU usage in real-time:")
    print("   1. Open another terminal")
    print("   2. Run: watch -n 1 nvidia-smi")
    print("   3. Look for GPU memory usage and utilization")
    print("   4. When Llama uses GPU, you'll see memory increase and utilization spikes")

if __name__ == "__main__":
    test_llama_gpu()
