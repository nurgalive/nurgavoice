# NurgaVoice Frontend

This is the frontend for NurgaVoice - an AI-powered audio/video transcription and summarization service.

## Features

- Modern, responsive web interface
- Real-time upload progress
- WebSocket support with polling fallback
- Support for multiple audio/video formats
- Automatic summary generation
- Download results in multiple formats (TXT, MD, PDF)

## Deployment

This frontend is designed to be deployed on Netlify while the backend runs separately (e.g., via ngrok).

### Netlify Deployment

1. Connect your repository to Netlify
2. Set the build directory to `frontend`
3. Configure environment variables in Netlify dashboard:
   - `VITE_API_BASE_URL`: Your backend API URL (e.g., `https://your-ngrok-url.ngrok-free.app`)
   - `VITE_API_KEY`: Your API key (same as backend)

### Environment Variables

- `VITE_API_BASE_URL`: Backend API base URL
- `VITE_API_KEY`: API key for authentication

**Important**: Environment variables must be configured for the application to work. The application will not prompt users for configuration.

## Local Development

To run locally:

```bash
cd frontend
python -m http.server 3000
```

Or use any static file server of your choice.

## Configuration

The frontend automatically configures itself based on environment variables. The configuration includes:

- API base URL and authentication (via environment variables)
- Supported file formats and size limits
- Language options
- Summary length options

## Browser Support

- Modern browsers with ES6+ support
- WebSocket support (with polling fallback)
- File API support for upload progress

## Security

- Content Security Policy (CSP) headers
- XSS protection
- Frame options for clickjacking protection
- Secure cross-origin requests
