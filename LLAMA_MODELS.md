# Llama Model Management Guide

## Overview

This guide explains how to choose, download, and configure Llama models for your transcription and summarization service.

## Quick Start

### 1. Download a Recommended Model
```bash
python download_models.py recommended
```

### 2. List Available Models
```bash
python download_models.py list
```

### 3. Download a Specific Model
```bash
python download_models.py download llama2-7b-chat-q4
```

### 4. Check Installed Models
```bash
python download_models.py installed
```

## Model Selection Guide

### Size vs Performance Trade-offs

| Model Size | RAM Required | Quality | Speed | Best For |
|------------|--------------|---------|-------|----------|
| 7B Q4_0    | 4-6GB       | Good    | Fast  | General use, development |
| 7B Q5_0    | 5-7GB       | Better  | Medium| Production, better quality |
| 13B Q4_0   | 8-10GB      | High    | Slower| High-quality summaries |
| 13B Q5_0   | 10-12GB     | Higher  | Slow  | Best quality |

### Quantization Levels Explained

- **Q4_0**: 4-bit quantization, smallest files, good quality
- **Q5_0**: 5-bit quantization, larger files, better quality
- **Q8_0**: 8-bit quantization, large files, excellent quality
- **F16**: Full precision, largest files, best quality

### Recommended Models

#### For General Summarization
- **Llama 2 7B Chat Q4_0**: Best balance of speed and quality
- **Llama 2 7B Chat Q5_0**: Better quality, slightly slower

#### For Code-Related Content
- **Code Llama 7B Q4_0**: Optimized for understanding code and technical content

#### For Better Assistant Behavior
- **Vicuna 7B Q4_0**: Fine-tuned for helpful responses

## Configuration

### Basic Configuration

Edit `config.py` to set your preferred model:

```python
# Basic model path
LLAMA_MODEL_PATH = "models/llama-2-7b-chat.q4_0.gguf"

# Model parameters
LLAMA_MODEL_CONTEXT_SIZE = 4096  # Context window size
LLAMA_MODEL_THREADS = 4          # CPU threads (adjust based on your CPU)
LLAMA_MODEL_MAX_TOKENS = 512     # Max tokens for summary generation
```

### Advanced Configuration

Use the available models dictionary for easy switching:

```python
# In your application code
from tasks import load_llama_model

# Load default model
model = load_llama_model()

# Load specific model
model = load_llama_model("llama2-7b-chat")
```

## Model Sources

### Official Sources
- **Hugging Face**: https://huggingface.co/models?library=gguf
- **Llama.cpp Models**: https://github.com/ggerganov/llama.cpp#models

### Popular Model Collections
- **TheBloke**: High-quality quantized models
- **Microsoft**: Official model releases
- **Meta**: Original Llama releases

## Performance Optimization

### CPU Optimization
```python
# Adjust threads based on your CPU cores
LLAMA_MODEL_THREADS = os.cpu_count() // 2  # Use half of available cores
```

### Memory Optimization
```python
# Enable memory mapping for faster loading
use_mmap=True

# Disable memory locking if you have limited RAM
use_mlock=False

# Adjust batch size based on available RAM
n_batch=256  # Smaller batch for less RAM usage
```

### Context Size Tuning
```python
# Smaller context for faster inference
LLAMA_MODEL_CONTEXT_SIZE = 2048  # Good for summaries

# Larger context for better understanding
LLAMA_MODEL_CONTEXT_SIZE = 4096  # Better for complex content
```

## Troubleshooting

### Model Not Loading
1. Check if the model file exists: `ls -la models/`
2. Verify file permissions: `chmod 644 models/*.gguf`
3. Check available RAM: `free -h`
4. Try a smaller model (Q4_0 instead of Q5_0)

### Out of Memory Errors
1. Reduce context size: `LLAMA_MODEL_CONTEXT_SIZE = 1024`
2. Reduce threads: `LLAMA_MODEL_THREADS = 2`
3. Use a smaller model
4. Enable swap if available

### Slow Performance
1. Increase threads (up to CPU cores): `LLAMA_MODEL_THREADS = 8`
2. Enable memory mapping: `use_mmap=True`
3. Use SSD storage for model files
4. Consider GPU acceleration (if available)

## GPU Acceleration (Optional)

If you have a CUDA-compatible GPU, you can install GPU support:

```bash
# Install CUDA version of llama-cpp-python
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

Then modify the model loading:
```python
llama_model = Llama(
    model_path=model_path,
    n_ctx=context_size,
    n_gpu_layers=32,  # Number of layers to offload to GPU
    verbose=False,
)
```

## Best Practices

1. **Start Small**: Begin with 7B Q4_0 models for testing
2. **Monitor Resources**: Watch RAM and CPU usage during inference
3. **Test Quality**: Evaluate summary quality with your specific content
4. **Backup Models**: Keep working models backed up
5. **Version Control**: Track which model versions work best for your use case

## Example Usage

```python
# Load and use a model
from tasks import load_llama_model, generate_summary

# Load the default model
model = load_llama_model()

# Generate a summary
text = "Your long text here..."
summary = generate_summary(text, length="medium")
print(summary)
```
