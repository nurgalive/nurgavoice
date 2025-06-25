#!/usr/bin/env python3
"""
Test script to verify Gemma 3 model configuration and functionality.
"""

from config import Config
from tasks import load_llama_model, generate_summary
import os

def main():
    print("=" * 60)
    print("Gemma 3 Model Configuration Test")
    print("=" * 60)
    
    # Check configuration
    print(f"✅ Default model path: {Config.LLAMA_MODEL_PATH}")
    print(f"✅ Context size: {Config.LLAMA_MODEL_CONTEXT_SIZE}")
    print(f"✅ Threads: {Config.LLAMA_MODEL_THREADS}")
    print(f"✅ Max tokens: {Config.LLAMA_MODEL_MAX_TOKENS}")
    
    # Check if model file exists
    if os.path.exists(Config.LLAMA_MODEL_PATH):
        print(f"✅ Model file exists")
        file_size = os.path.getsize(Config.LLAMA_MODEL_PATH) / (1024 * 1024)
        print(f"✅ Model file size: {file_size:.1f} MB")
    else:
        print(f"❌ Model file not found at: {Config.LLAMA_MODEL_PATH}")
        return
    
    print("\n" + "=" * 60)
    print("Testing Model Loading")
    print("=" * 60)
    
    # Test model loading
    try:
        model = load_llama_model()
        if model:
            print("✅ Model loaded successfully!")
        else:
            print("❌ Model failed to load")
            return
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    print("\n" + "=" * 60)
    print("Testing Summary Generation")
    print("=" * 60)
    
    # Test summary generation
    test_texts = {
        "short": "Artificial intelligence is revolutionizing many industries. Machine learning algorithms can now perform complex tasks that previously required human intelligence. This technology has applications in healthcare, finance, transportation, and many other fields.",
        "medium": "Climate change is one of the most pressing issues of our time. Rising global temperatures are causing ice caps to melt, sea levels to rise, and weather patterns to become more extreme. Scientists around the world are working on solutions to reduce greenhouse gas emissions and develop renewable energy sources. Governments are implementing policies to encourage clean energy adoption and reduce carbon footprints.",
        "long": "The history of computing spans several decades and has transformed how we live and work. Early computers were room-sized machines that could only perform basic calculations. The invention of the transistor in the 1940s made computers smaller and more efficient. The development of integrated circuits in the 1960s led to even smaller computers. The personal computer revolution of the 1970s and 1980s brought computing to homes and small businesses. The internet, developed in the 1990s, connected computers worldwide and enabled the information age. Today, we carry powerful computers in our pockets as smartphones, and cloud computing allows us to access vast computational resources from anywhere."
    }
    
    for length, text in test_texts.items():
        print(f"\n--- Testing {length} summary ---")
        print(f"Original text: {text[:100]}...")
        try:
            summary = generate_summary(text, length)
            print(f"Summary: {summary}")
            print("✅ Summary generation successful")
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
    
    print("\n" + "=" * 60)
    print("Available Models")
    print("=" * 60)
    
    for model_name, model_config in Config.AVAILABLE_LLAMA_MODELS.items():
        status = "✅ Available" if os.path.exists(model_config["path"]) else "❌ Not found"
        print(f"{model_name}: {status}")
        print(f"  Path: {model_config['path']}")
        print(f"  Description: {model_config['description']}")
        print()

if __name__ == "__main__":
    main()
