
Create a Python web application that performs audio/video transcription and summarization with the following requirements:

Build a FastAPI web interface that allows users to:

Upload audio/video files (supported formats: mp3, wav, mp4, avi)
Display transcription progress in real-time
Show the final transcription and summary results
Maximum file size: 100MB
Implement the backend functionality to:

Use whisperx or fast-whisper for accurate speech-to-text transcription
Process the transcription through llama.cpp to generate a concise summary
Handle file validation and error cases
Store results temporarily for user download
Technical specifications:

Use async processing for long-running tasks
Implement proper error handling and user feedback
Include a simple, responsive UI with progress indicators
Add support for multiple languages in transcription
Provide options to adjust summary length (short/medium/long)
Output format:

Display transcription and summary in separate, clearly formatted sections
Allow downloading results as TXT or PDF
Include timestamps in transcription where applicable
Please provide the complete implementation with proper documentation and setup instructions.