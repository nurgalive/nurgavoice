// Configuration for NurgaVoice Frontend
class NurgaVoiceConfig {
    constructor() {
        // Default configuration - will be overridden by environment variables
        this.DEFAULT_CONFIG = {
            // API Configuration
            API_BASE_URL: 'http://localhost:8000',  // Use local backend for testing
            API_KEY: 'W--jR-7hR7w9DJyOOMU24pURPiIaGN9qt2a5iAMv55k',  // Use the backend's actual API key
            
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
        
        // Set API base URL
        if (envApiUrl) {
            this.API_BASE_URL = envApiUrl;
        } else if (isProduction) {
            // In production, try to detect stored URL or use default
            this.API_BASE_URL = this.detectStoredApiUrl() || this.DEFAULT_CONFIG.API_BASE_URL;
        } else {
            this.API_BASE_URL = this.DEFAULT_CONFIG.API_BASE_URL;
        }
        
        // Set API key
        this.API_KEY = envApiKey || this.DEFAULT_CONFIG.API_KEY;
        
        // Copy other default configurations
        this.MAX_FILE_SIZE_MB = this.DEFAULT_CONFIG.MAX_FILE_SIZE_MB;
        this.ALLOWED_EXTENSIONS = this.DEFAULT_CONFIG.ALLOWED_EXTENSIONS;
        this.SUPPORTED_LANGUAGES = this.DEFAULT_CONFIG.SUPPORTED_LANGUAGES;
        this.SUMMARY_LENGTHS = this.DEFAULT_CONFIG.SUMMARY_LENGTHS;
        
        // Log configuration (hide sensitive info)
        console.log('NurgaVoice Config:', {
            API_BASE_URL: this.API_BASE_URL,
            API_KEY: this.API_KEY ? '[SET]' : '[NOT SET]',
            MAX_FILE_SIZE_MB: this.MAX_FILE_SIZE_MB
        });
    }
    
    getEnvVar(name) {
        // For browser environments, only check window variables
        // Note: process.env doesn't exist in browsers
        return window?.[name] || null;
    }
    
    detectStoredApiUrl() {
        // Check if there's a stored API URL
        const storedUrl = localStorage.getItem('nurgavoice_api_url');
        if (storedUrl) {
            return storedUrl;
        }
        
        // Return null if no URL is configured - no user prompting
        return null;
    }
    
    getApiUrl(endpoint) {
        if (!this.API_BASE_URL) {
            throw new Error('API URL not configured. Please set VITE_API_BASE_URL environment variable or configure API_BASE_URL in the application configuration.');
        }
        
        return `${this.API_BASE_URL}${endpoint}`;
    }
    
    getWebSocketUrl(endpoint) {
        if (!this.API_BASE_URL) {
            throw new Error('API URL not configured. Please set VITE_API_BASE_URL environment variable or configure API_BASE_URL in the application configuration.');
        }
        
        // Convert HTTP(S) to WS(S)
        const wsUrl = this.API_BASE_URL.replace(/^https?:/, this.API_BASE_URL.startsWith('https:') ? 'wss:' : 'ws:');
        return `${wsUrl}${endpoint}`;
    }
    
    // Method to test API connection
    async testApiConnection() {
        try {
            const response = await fetch(this.getApiUrl('/health'), {
                method: 'GET',
                headers: {
                    'X-API-Key': this.API_KEY,
                    'ngrok-skip-browser-warning': 'true'  // Skip ngrok browser warning page
                },
                timeout: 10000 // 10 second timeout
            });
            
            if (response.ok) {
                return true;
            } else {
                throw new Error(`API returned ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('API connection test failed:', error);
            throw new Error(`Unable to connect to backend server: ${error.message}`);
        }
    }

    // Get current environment for debugging
    getEnvironment() {
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const protocol = window.location.protocol;
        const port = window.location.port;
        
        return {
            hostname: window.location.hostname,
            protocol: protocol,
            port: port,
            isLocal: isLocal,
            fullUrl: window.location.href
        };
    }
}

// Create global configuration instance
window.CONFIG = new NurgaVoiceConfig();
