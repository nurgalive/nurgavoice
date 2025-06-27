// NurgaVoice JavaScript Application
class NurgaVoiceApp {
    constructor() {
        this.currentTaskId = null;
        this.websocket = null;
        this.isProcessing = false;
        
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // Form elements
        this.uploadForm = document.getElementById('uploadForm');
        this.fileInput = document.getElementById('fileInput');
        this.uploadBtn = document.getElementById('uploadBtn');
        
        // Progress elements
        this.progressSection = document.getElementById('progressSection');
        this.progressBar = document.getElementById('progressBar');
        this.statusMessage = document.getElementById('statusMessage');
        this.uploadPrompt = document.getElementById('uploadPrompt');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        
        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.summaryContent = document.getElementById('summaryContent');
        this.transcriptionContent = document.getElementById('transcriptionContent');
        this.metadataContent = document.getElementById('metadataContent');
        this.timestampSection = document.getElementById('timestampSection');
        this.timestampContent = document.getElementById('timestampContent');
        
        // Download elements
        this.downloadTxt = document.getElementById('downloadTxt');
        this.downloadPdf = document.getElementById('downloadPdf');
        
        // Error elements
        this.errorSection = document.getElementById('errorSection');
        this.errorMessage = document.getElementById('errorMessage');
    }

    bindEvents() {
        this.uploadForm.addEventListener('submit', (e) => this.handleUpload(e));
        this.downloadTxt.addEventListener('click', () => this.downloadFile('txt'));
        this.downloadPdf.addEventListener('click', () => this.downloadFile('pdf'));
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            // Validate file size
            // const maxSize = 100 * 1024 * 1024; // 100MB
            const maxSize = 1024 * 1024 * 1024; // 1024MB
            if (file.size > maxSize) {
                this.showError('File size exceeds 1024MB limit.');
                this.fileInput.value = '';
                return;
            }

            // Validate file type
            const allowedTypes = ['.mp3', '.wav', '.mp4', '.avi', '.m4a', '.flac', '.ogg'];
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            if (!allowedTypes.includes(fileExtension)) {
                this.showError('Unsupported file format. Please use MP3, WAV, MP4, AVI, M4A, FLAC, or OGG.');
                this.fileInput.value = '';
                return;
            }

            this.hideError();
        }
    }

    async handleUpload(event) {
        event.preventDefault();
        
        if (this.isProcessing) {
            return;
        }

        const formData = new FormData(this.uploadForm);
        const file = formData.get('file');
        
        if (!file || file.size === 0) {
            this.showError('Please select a file to upload.');
            return;
        }

        console.log('Starting upload process...');
        console.log('File:', file.name, 'Size:', file.size);
        console.log('Current location:', window.location.href);
        
        this.startProcessing(file.name);

        try {
            console.log('Making fetch request to /upload...');
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            console.log('Response received:', response.status, response.statusText);

            if (!response.ok) {
                // Try to get error details from response
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (parseError) {
                    // If we can't parse JSON, use the text response
                    try {
                        const errorText = await response.text();
                        if (errorText) {
                            errorMessage = errorText;
                        }
                    } catch (textError) {
                        // Keep the original HTTP error message
                    }
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            console.log('Upload successful, task ID:', data.task_id);
            
            this.currentTaskId = data.task_id;
            this.connectWebSocket();
            
        } catch (error) {
            console.error('Upload error:', error);
            this.stopProcessing();
            
            // Provide more specific error messages
            let errorMessage = error.message;
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                errorMessage = 'Network error: Unable to connect to server. Please check your internet connection.';
            } else if (error.message.includes('insecure') || error.message.includes('mixed content')) {
                errorMessage = 'Security error: Mixed content detected. This may be due to HTTPS/HTTP protocol mismatch.';
            }
            
            this.showError(`Upload failed: ${errorMessage}`);
        }
    }

    startProcessing(filename) {
        this.isProcessing = true;
        this.hideError();
        this.hideResults();
        
        // Update UI
        this.uploadPrompt.style.display = 'none';
        this.progressSection.style.display = 'block';
        this.fileInfo.style.display = 'block';
        this.fileName.textContent = filename;
        
        // Disable upload button
        this.uploadBtn.disabled = true;
        this.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        
        // Reset progress
        this.updateProgress(0, 'Starting upload...');
    }

    stopProcessing() {
        this.isProcessing = false;
        
        // Re-enable upload button
        this.uploadBtn.disabled = false;
        this.uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Upload & Process';
        
        // Close websocket
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }

    connectWebSocket() {
        if (!this.currentTaskId) return;

        // Check if we're running through ngrok
        const isNgrok = window.location.hostname.includes('ngrok');
        
        // Use secure WebSocket (wss://) if page is served over HTTPS, otherwise use ws://
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/${this.currentTaskId}`;
        
        console.log('WebSocket URL:', wsUrl);
        console.log('Page protocol:', window.location.protocol);
        console.log('Is ngrok:', isNgrok);
        
        try {
            this.websocket = new WebSocket(wsUrl);
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            // For ngrok, immediately fall back to polling
            this.fallbackToPolling();
            return;
        }

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.websocket.onopen = () => {
            console.log('WebSocket connection established');
        };

        this.websocket.onclose = (event) => {
            console.log('WebSocket connection closed', event.code, event.reason);
            if (this.isProcessing) {
                console.log('Falling back to polling due to WebSocket closure');
                this.fallbackToPolling();
            }
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (this.isProcessing) {
                console.log('Falling back to polling due to WebSocket error');
                // For ngrok or any WebSocket error, immediately fall back to polling
                this.websocket = null; // Clear the websocket reference
                this.fallbackToPolling();
            }
        };
    }

    fallbackToPolling() {
        if (!this.currentTaskId || !this.isProcessing) return;

        console.log('Starting polling fallback for task:', this.currentTaskId);
        
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${this.currentTaskId}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('Polling status:', data);
                
                this.handleStatusUpdate(data);
                
                if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
                    clearInterval(pollInterval);
                }
            } catch (error) {
                console.error('Polling error:', error);
                clearInterval(pollInterval);
                this.showError(`Connection error: ${error.message}. Please try again.`);
                this.stopProcessing();
            }
        }, 2000);
    }

    handleWebSocketMessage(data) {
        this.handleStatusUpdate(data);
    }

    handleStatusUpdate(data) {
        switch (data.state) {
            case 'PROGRESS':
                this.updateProgress(data.progress || 0, data.step || 'Processing...');
                break;
            case 'SUCCESS':
                // Make sure we pass the actual result data
                this.handleSuccess(data.result || data);
                break;
            case 'FAILURE':
                this.handleFailure(data.error);
                break;
        }
    }

    updateProgress(progress, message) {
        this.progressBar.style.width = `${progress}%`;
        this.progressBar.textContent = `${progress}%`;
        this.statusMessage.textContent = message;
        
        // Add animation class
        if (progress < 100) {
            this.progressBar.classList.add('progress-bar-animated');
        } else {
            this.progressBar.classList.remove('progress-bar-animated');
        }
    }

    handleSuccess(result) {
        this.stopProcessing();
        this.updateProgress(100, 'Complete!');
        
        setTimeout(() => {
            this.displayResults(result);
        }, 1000);
    }

    handleFailure(error) {
        this.stopProcessing();
        this.showError(`Processing failed: ${error}`);
    }

    displayResults(result) {
        // Hide progress section
        this.progressSection.style.display = 'none';
        
        // Show results section
        this.resultsSection.style.display = 'block';
        
        // Display summary with fallback
        if (result && result.summary) {
            this.summaryContent.textContent = result.summary;
        } else {
            this.summaryContent.textContent = 'No summary available';
        }
        
        // Display transcription with fallback
        if (result && result.transcription && result.transcription.text) {
            this.transcriptionContent.textContent = result.transcription.text;
        } else {
            this.transcriptionContent.textContent = 'No transcription available';
        }
        
        // Display metadata
        if (result && result.metadata) {
            this.displayMetadata(result.metadata);
        }
        
        // Display timestamped transcription if available
        if (result && result.transcription && result.transcription.segments && result.transcription.segments.length > 0) {
            this.displayTimestampedTranscription(result.transcription.segments);
        }
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    displayMetadata(metadata) {
        if (!metadata) return;
        
        let metadataHtml = '';
        
        if (metadata.file_name) {
            metadataHtml += `
                <div class="col-md-3 mb-2">
                    <div class="metadata-item">
                        <div class="metadata-label">File Name</div>
                        <div>${metadata.file_name}</div>
                    </div>
                </div>
            `;
        }
        
        if (metadata.language) {
            metadataHtml += `
                <div class="col-md-3 mb-2">
                    <div class="metadata-item">
                        <div class="metadata-label">Language</div>
                        <div>${metadata.language.toUpperCase()}</div>
                    </div>
                </div>
            `;
        }
        
        if (metadata.summary_length) {
            metadataHtml += `
                <div class="col-md-3 mb-2">
                    <div class="metadata-item">
                        <div class="metadata-label">Summary Length</div>
                        <div>${metadata.summary_length}</div>
                    </div>
                </div>
            `;
        }
        
        if (metadata.duration) {
            const duration = Math.round(metadata.duration);
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            metadataHtml += `
                <div class="col-md-3 mb-2">
                    <div class="metadata-item">
                        <div class="metadata-label">Duration</div>
                        <div>${minutes}:${seconds.toString().padStart(2, '0')}</div>
                    </div>
                </div>
            `;
        }
        
        this.metadataContent.innerHTML = metadataHtml;
    }

    displayTimestampedTranscription(segments) {
        let timestampHtml = '';
        
        segments.forEach(segment => {
            const start = segment.start || 0;
            const end = segment.end || 0;
            const text = segment.text || '';
            
            const startTime = this.formatTime(start);
            const endTime = this.formatTime(end);
            
            timestampHtml += `
                <div class="mb-2">
                    <span class="text-primary fw-bold">[${startTime} - ${endTime}]</span>
                    <span class="ms-2">${text}</span>
                </div>
            `;
        });
        
        this.timestampContent.innerHTML = timestampHtml;
        this.timestampSection.style.display = 'block';
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    downloadFile(format) {
        if (!this.currentTaskId) return;
        
        const url = `/download/${this.currentTaskId}/${format}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `transcription_${this.currentTaskId}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorSection.style.display = 'block';
        this.errorSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideError() {
        this.errorSection.style.display = 'none';
    }

    hideResults() {
        this.resultsSection.style.display = 'none';
        this.timestampSection.style.display = 'none';
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NurgaVoiceApp();
});
