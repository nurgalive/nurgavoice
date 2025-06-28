# Environment Variable Setup

## Prerequisites

Make sure `python-dotenv` is installed (it's already in requirements.txt):

```bash
pip install python-dotenv
```

The application automatically loads `.env` files thanks to the configuration in `config.py`.

## Setting up the API Key

The application uses environment variables for configuration. The most important one is the API key for security.

### Method 1: Using .env file (Recommended for development)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and set your API key:
   ```bash
   NURGAVOICE_API_KEY=your-secure-api-key-here
   ```

3. Generate a secure API key (recommended for production):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

### Method 2: Export environment variable directly

```bash
export NURGAVOICE_API_KEY="your-secure-api-key-here"
```

### Method 3: Set when running the application

```bash
NURGAVOICE_API_KEY="your-secure-api-key-here" python main.py
```

### Method 4: Docker environment

```bash
docker run -e NURGAVOICE_API_KEY="your-secure-api-key-here" your-app
```

Or in docker-compose.yml:
```yaml
environment:
  - NURGAVOICE_API_KEY=your-secure-api-key-here
```

## Using the API Key

Once set, the API key can be used in requests:

### Via Header:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/upload
```

### Via Query Parameter:
```bash
curl "http://localhost:8000/upload?api_key=your-api-key"
```

## Security Notes

- **Always change the default API key in production!**
- Use a long, random string for the API key
- Keep your API key secret and don't commit it to version control
- The `.env` file is already in `.gitignore` to prevent accidental commits
