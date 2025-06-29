// Configuration for NurgaVoice Frontend
class NurgaVoiceConfig {
    constructor() {
        // Default configuration - will be overridden by environment variables
        this.DEFAULT_CONFIG = {
            // API Configuration - Set to null to force user input
            API_BASE_URL: 'https://loved-magpie-routinely.ngrok-free.app',
            API_KEY: 'W--jR-7hR7w9DJyOOMU24pURPiIaGN9qt2a5iAMv55k',
            
            // File Upload Settings
            MAX_FILE_SIZE_MB: 512,
            ALLOWED_EXTENSIONS: ['.mp3', '.wav', '.mp4', '.avi', '.m4a', '.flac', '.ogg'],
            
            // Language Settings
            SUPPORTED_LANGUAGES: {
                'auto': 'Auto-detect',
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'zh': 'Chinese',
                'ja': 'Japanese',
                'ko': 'Korean',
                'ar': 'Arabic',
                'hi': 'Hindi',
                'tr': 'Turkish',
                'pl': 'Polish',
                'nl': 'Dutch',
                'sv': 'Swedish',
                'da': 'Danish',
                'no': 'Norwegian',
                'fi': 'Finnish'
            },
            
            // Summary Length Options
            SUMMARY_LENGTHS: {
                'short': 'Short (1-2 sentences)',
                'medium': 'Medium (1 paragraph)',
                'long': 'Long (2-3 paragraphs)',
                'detailed': 'Detailed (multiple paragraphs)'
            },
            
            // Model Information (will be fetched from API)
            MODELS: {
                whisper: 'Loading...',
                llm: 'Loading...',
                llm_description: 'Model information not available'
            }
        };
        
        // Load configuration from environment variables or use defaults
        this.loadConfig();
    }
    
    loadConfig() {
        // Check for environment variables (set by build process or runtime)
        const envApiUrl = this.getEnvVar('VITE_API_BASE_URL') || this.getEnvVar('REACT_APP_API_BASE_URL');
        const envApiKey = this.getEnvVar('VITE_API_KEY') || this.getEnvVar('REACT_APP_API_KEY');
        
        // Production detection
        const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
        
        // Set API base URL - prioritize environment variables, then stored URL, then prompt
        if (envApiUrl) {
            this.API_BASE_URL = envApiUrl;
            console.log('Using API URL from environment:', this.API_BASE_URL);
        } else {
            // Check for stored URL first
            const storedUrl = localStorage.getItem('nurgavoice_api_url');
            if (storedUrl) {
                this.API_BASE_URL = storedUrl;
                console.log('Using stored API URL:', this.API_BASE_URL);
            } else {
                // No URL configured - will prompt user when needed
                this.API_BASE_URL = null;
                console.log('No API URL configured - will prompt user');
            }
        }
        
        // Set API key - prioritize environment variables
        if (envApiKey) {
            this.API_KEY = envApiKey;
            console.log('Using API key from environment: [SET]');
        } else {
            // Use default configuration
            this.API_KEY = this.DEFAULT_CONFIG.API_KEY;
            console.log('Using default API key: [SET]');
        }
        
        // Copy other default configurations
        this.MAX_FILE_SIZE_MB = this.DEFAULT_CONFIG.MAX_FILE_SIZE_MB;
        this.ALLOWED_EXTENSIONS = this.DEFAULT_CONFIG.ALLOWED_EXTENSIONS;
        this.SUPPORTED_LANGUAGES = this.DEFAULT_CONFIG.SUPPORTED_LANGUAGES;
        this.SUMMARY_LENGTHS = this.DEFAULT_CONFIG.SUMMARY_LENGTHS;
        this.MODELS = this.DEFAULT_CONFIG.MODELS;
        
        // Log configuration (hide sensitive info)
        console.log('NurgaVoice Config loaded:', {
            API_BASE_URL: this.API_BASE_URL || '[NOT SET]',
            API_KEY: this.API_KEY ? `${this.API_KEY.substring(0, 8)}...` : '[NOT SET]',
            MAX_FILE_SIZE_MB: this.MAX_FILE_SIZE_MB
        });
    }
    
    getEnvVar(name) {
        // Only try to get environment variable from window object (browser environment)
        return window?.[name] || null;
    }
    
    detectOrPromptApiUrl() {
        // Check if there's a stored API URL
        const storedUrl = localStorage.getItem('nurgavoice_api_url');
        if (storedUrl) {
            return storedUrl;
        }
        
        // If not found, we'll prompt the user later
        return null;
    }
    
    promptForApiUrl() {
        const currentUrl = localStorage.getItem('nurgavoice_api_url') || '';
        const userInput = prompt(
            'Please enter your NurgaVoice API URL (e.g., https://your-ngrok-url.ngrok-free.app):\n\nNote: Make sure your backend server is running and the ngrok tunnel is active.\n\nCommon ngrok URL format: https://[random-string].ngrok-free.app',
            currentUrl
        );
        
        if (userInput && userInput.trim()) {
            const cleanUrl = userInput.trim().replace(/\/$/, ''); // Remove trailing slash
            localStorage.setItem('nurgavoice_api_url', cleanUrl);
            this.API_BASE_URL = cleanUrl;
            console.log('API URL updated to:', cleanUrl);
            return cleanUrl;
        }
        
        return null;
    }
    
    // Test API connectivity with proper authentication
    async testApiConnection() {
        if (!this.API_BASE_URL) {
            // Prompt for API URL if not set
            this.API_BASE_URL = this.promptForApiUrl();
            if (!this.API_BASE_URL) {
                throw new Error('API URL not configured');
            }
        }
        
        if (!this.API_KEY) {
            throw new Error('API key not configured');
        }
        
        try {
            console.log('Testing API connection to:', this.API_BASE_URL);
            console.log('Using API key:', this.API_KEY ? `${this.API_KEY.substring(0, 8)}...` : '[NOT SET]');
            
            const response = await fetch(this.getApiUrl('/api/info'), {
                method: 'GET',
                headers: {
                    'X-API-Key': this.API_KEY,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout: 10000 // 10 second timeout
            });
            
            console.log('API response status:', response.status);
            console.log('API response headers:', Object.fromEntries(response.headers.entries()));
            
            if (response.status === 401) {
                throw new Error(`Authentication failed (401). Please check your API key. Current key: ${this.API_KEY ? `${this.API_KEY.substring(0, 8)}...` : '[NOT SET]'}`);
            }
            
            if (response.status === 403) {
                throw new Error('Access forbidden (403). Your API key may not have the required permissions.');
            }
            
            if (!response.ok) {
                const errorText = await response.text().catch(() => 'Unknown error');
                throw new Error(`API returned ${response.status}: ${response.statusText}. Details: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('API connection test successful:', data);
            return true;
        } catch (error) {
            console.error('API connection test failed:', error);
            
            // Provide more specific error messages
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                throw new Error('Network error: Cannot reach the API server. The ngrok tunnel may be inactive or the URL may be incorrect. Please check your backend server and update the API URL.');
            }
            
            throw error;
        }
    }
    
    getApiUrl(endpoint) {
        if (!this.API_BASE_URL) {
            this.API_BASE_URL = this.promptForApiUrl();
            if (!this.API_BASE_URL) {
                throw new Error('API URL not configured. Please refresh and enter your API URL.');
            }
        }
        
        return `${this.API_BASE_URL}${endpoint}`;
    }
    
    getWebSocketUrl(endpoint) {
        if (!this.API_BASE_URL) {
            this.API_BASE_URL = this.promptForApiUrl();
            if (!this.API_BASE_URL) {
                throw new Error('API URL not configured. Please refresh and enter your WebSocket URL.');
            }
        }
        
        // Convert HTTP(S) to WS(S)
        const wsUrl = this.API_BASE_URL.replace(/^https?:/, this.API_BASE_URL.startsWith('https:') ? 'wss:' : 'ws:');
        return `${wsUrl}${endpoint}`;
    }
    
    // Method to clear stored configuration and prompt for new URL
    resetApiUrl() {
        localStorage.removeItem('nurgavoice_api_url');
        this.API_BASE_URL = null;
        return this.promptForApiUrl();
    }
    
    // Method to fetch model information from the API
    async fetchModelInfo() {
        try {
            console.log('Fetching model info from:', this.getApiUrl('/api/info'));
            const response = await fetch(this.getApiUrl('/api/info'), {
                headers: {
                    'X-API-Key': this.API_KEY,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });
            
            if (response.status === 401) {
                console.error('Authentication failed when fetching model info');
                throw new Error('Authentication failed. Please check your API key.');
            }
            
            if (response.ok) {
                const data = await response.json();
                this.MODELS = {
                    whisper: data.whisper_model || 'Unknown',
                    llm: data.llm_model_name || 'Unknown',
                    llm_description: data.llm_model_description || 'Model information not available'
                };
                return this.MODELS;
            } else {
                console.warn('Failed to fetch model information:', response.status, response.statusText);
            }
        } catch (error) {
            console.warn('Could not fetch model information:', error);
        }
        
        return this.MODELS;
    }
}

// Create global configuration instance
window.CONFIG = new NurgaVoiceConfig();