# Speaker Diarization Implementation

## Overview
Speaker diarization has been successfully added to your NurgaVoice transcription service. This feature allows the system to identify and separate different speakers in audio recordings, providing enhanced transcripts with speaker labels.

## What's Been Added

### 1. Configuration Updates (`config.py`)
- Added diarization enable/disable setting
- Configurable minimum and maximum speaker detection limits
- HuggingFace token configuration for accessing pyannote models

### 2. API Enhancements (`backend.py`)
- New API parameters for controlling diarization:
  - `enable_diarization`: Boolean to enable/disable speaker diarization
  - `min_speakers`: Minimum number of speakers to detect (1-10)
  - `max_speakers`: Maximum number of speakers to detect (1-10)
- Updated response formats (TXT, MD, PDF) to include speaker labels
- Enhanced API info endpoint to report diarization capabilities

### 3. Core Processing (`tasks.py`)
- Integrated WhisperX's speaker diarization functionality
- Added speaker detection and labeling to transcription segments
- Enhanced metadata to include speaker information
- Proper error handling for diarization failures

## How to Use

### Environment Setup
1. **HuggingFace Token** (Required for diarization):
   ```bash
   export HUGGINGFACE_TOKEN="your_huggingface_token_here"
   ```
   - Get your token from: https://huggingface.co/settings/tokens
   - Accept the user agreement for pyannote models at: https://huggingface.co/pyannote/speaker-diarization

### API Usage

When uploading a file, include the diarization parameters:

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@your_audio.mp3" \
  -F "language=auto" \
  -F "summary_length=medium" \
  -F "enable_summary=true" \
  -F "enable_diarization=true" \
  -F "min_speakers=2" \
  -F "max_speakers=5"
```

### Output Format

With diarization enabled, your transcripts will include speaker labels:

**Text Format:**
```
[00:15 - 00:18] SPEAKER_00: Hello, how are you today?
[00:18 - 00:22] SPEAKER_01: I'm doing great, thanks for asking.
[00:22 - 00:25] SPEAKER_00: That's wonderful to hear.
```

**Markdown Format:**
```markdown
**[00:15 - 00:18] SPEAKER_00:** Hello, how are you today?
**[00:18 - 00:22] SPEAKER_01:** I'm doing great, thanks for asking.
**[00:22 - 00:25] SPEAKER_00:** That's wonderful to hear.
```

## Configuration Options

In `config.py`:
```python
# Speaker Diarization settings
ENABLE_DIARIZATION = True  # Set to False to disable diarization capability
DIARIZATION_MIN_SPEAKERS = 1  # Minimum number of speakers to detect
DIARIZATION_MAX_SPEAKERS = 10  # Maximum number of speakers to detect
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")  # Required for pyannote.audio models
```

## Performance Notes

1. **Processing Time**: Diarization adds additional processing time (typically 20-50% longer)
2. **Memory Usage**: Requires additional GPU/CPU memory for the diarization model
3. **Accuracy**: Works best with:
   - Clear audio quality
   - Distinct speaker voices
   - Minimal background noise
   - Audio longer than 30 seconds

## Troubleshooting

### Quick Test
Run the diarization setup test script:
```bash
./test_diarization_setup.sh
```

### Common Issues:

1. **"HuggingFace token not found"**
   - **Solution**: Set the `HUGGINGFACE_TOKEN` environment variable
   - Get your token from: https://huggingface.co/settings/tokens
   - Add to `.env` file: `HUGGINGFACE_TOKEN=your_token_here`

2. **"Diarization failed" or "Model access issue"**
   - **Solution**: Accept the user agreement for the gated model
   - Visit: https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click "Agree and access repository"
   - Make sure you're logged in with the same account as your token

3. **"speakers_detected: 0" in results**
   - This indicates diarization failed silently
   - Check the backend logs for specific error messages
   - Run `./test_diarization_setup.sh` to diagnose issues

4. **No speaker labels in output**
   - Ensure `enable_diarization=true` in your request
   - Check that the audio has multiple distinguishable speakers
   - Verify the min/max speaker settings are appropriate
   - Audio should be at least 30 seconds for best results

### Setup Verification Steps:

1. **Check token is set**:
   ```bash
   echo $HUGGINGFACE_TOKEN
   ```

2. **Test model access**:
   ```bash
   python -c "
   from pyannote.audio import Pipeline
   import os
   Pipeline.from_pretrained('pyannote/speaker-diarization-3.1', 
                           use_auth_token=os.getenv('HUGGINGFACE_TOKEN'))
   print('✅ Model access OK')
   "
   ```

3. **Run full test**:
   ```bash
   ./test_diarization_setup.sh
   ```

### Logs to Watch:
- `🔄 Loading speaker diarization model...`
- `🎭 Starting speaker diarization...`
- `✅ Diarization completed. Detected X speakers`

## Dependencies

The following packages are required (already in requirements.txt):
- `pyannote.audio==3.3.2`
- `pyannote.core==5.0.0` 
- `pyannote.pipeline==3.0.1`
- `whisperx==3.4.1` (with diarization support)

## API Response Structure

The transcription result now includes speaker information:

```json
{
  "transcription": {
    "text": "Full transcript text...",
    "segments": [
      {
        "start": 15.0,
        "end": 18.0,
        "text": "Hello, how are you today?",
        "speaker": "SPEAKER_00"
      }
    ],
    "language": "en"
  },
  "metadata": {
    "diarization_enabled": true,
    "speakers_detected": 2,
    "min_speakers": 1,
    "max_speakers": 10
  }
}
```

Your NurgaVoice service now supports advanced speaker diarization! 🎭
