// NurgaVoice JavaScript Application
class NurgaVoiceApp {
    constructor() {
        this.currentTaskId = null;
        this.websocket = null;
        this.isProcessing = false;
        this.processingStartTime = null;
        
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
        this.uploadProgressSection = document.getElementById('uploadProgressSection');
        this.uploadProgressBar = document.getElementById('uploadProgressBar');
        this.processingProgressSection = document.getElementById('processingProgressSection');
        this.progressBar = document.getElementById('progressBar');
        this.statusMessage = document.getElementById('statusMessage');
        this.uploadPrompt = document.getElementById('uploadPrompt');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.completionInfo = document.getElementById('completionInfo');
        this.processingTime = document.getElementById('processingTime');
        this.completionTime = document.getElementById('completionTime');
        
        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.summaryContent = document.getElementById('summaryContent');
        this.transcriptionContent = document.getElementById('transcriptionContent');
        this.metadataContent = document.getElementById('metadataContent');
        this.timestampSection = document.getElementById('timestampSection');
        this.timestampContent = document.getElementById('timestampContent');
        
        // Download elements
        this.downloadTxt = document.getElementById('downloadTxt');
        this.downloadMd = document.getElementById('downloadMd');
        this.downloadPdf = document.getElementById('downloadPdf');
        
        // Error elements
        this.errorSection = document.getElementById('errorSection');
        this.errorMessage = document.getElementById('errorMessage');
        
        // Summary toggle elements
        this.enableSummary = document.getElementById('enableSummary');
        this.summaryOptionsDiv = document.getElementById('summaryOptionsDiv');
    }

    bindEvents() {
        this.uploadForm.addEventListener('submit', (e) => this.handleUpload(e));
        this.downloadTxt.addEventListener('click', () => this.downloadFile('txt'));
        this.downloadMd.addEventListener('click', () => this.downloadFile('md'));
        this.downloadPdf.addEventListener('click', () => this.downloadFile('pdf'));
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.enableSummary.addEventListener('change', (e) => this.handleSummaryToggle(e));
    }

    // Get audio duration from file
    getAudioDuration(file) {
        return new Promise((resolve, reject) => {
            const audio = document.createElement('audio');
            const url = URL.createObjectURL(file);
            
            audio.addEventListener('loadedmetadata', () => {
                URL.revokeObjectURL(url);
                resolve(audio.duration);
            });
            
            audio.addEventListener('error', () => {
                URL.revokeObjectURL(url);
                reject(new Error('Could not load audio file'));
            });
            
            // Set timeout to prevent hanging
            setTimeout(() => {
                URL.revokeObjectURL(url);
                reject(new Error('Timeout loading audio metadata'));
            }, 10000);
            
            audio.src = url;
        });
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            // Validate file size
            // const maxSize = 100 * 1024 * 1024; // 100MB
            const maxSize = 512 * 1024 * 1024; // 512MB
            if (file.size > maxSize) {
                this.showError('File size exceeds 512MB limit.');
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

            // Check audio duration and automatically disable summary if too short
            try {
                const duration = await this.getAudioDuration(file);
                console.log('Audio duration:', duration, 'seconds');
                
                if (duration < 30) {
                    // Auto-disable summary for short audio files
                    this.enableSummary.checked = false;
                    this.handleSummaryToggle({ target: { checked: false } });
                    
                    // Show a brief message to inform the user
                    this.showInfo(`Audio is ${Math.round(duration)} seconds. Summary disabled for files shorter than 30 seconds.`);
                }
            } catch (error) {
                console.warn('Could not determine audio duration:', error.message);
                // Continue without duration check if we can't determine it
            }

            this.hideError();
        }
    }

    handleSummaryToggle(event) {
        const summaryEnabled = event.target.checked;
        
        // Show/hide summary length options with smooth transition
        if (summaryEnabled) {
            this.summaryOptionsDiv.style.display = 'block';
            this.summaryOptionsDiv.style.opacity = '0';
            setTimeout(() => {
                this.summaryOptionsDiv.style.opacity = '1';
            }, 10);
        } else {
            this.summaryOptionsDiv.style.opacity = '0';
            setTimeout(() => {
                this.summaryOptionsDiv.style.display = 'none';
            }, 300);
        }
        
        console.log('Summary generation:', summaryEnabled ? 'enabled' : 'disabled');
    }

    async handleUpload(event) {
        event.preventDefault();
        
        if (this.isProcessing) {
            return;
        }

        const formData = new FormData(this.uploadForm);
        const file = formData.get('file');
        
        // Explicitly handle checkbox value (unchecked checkboxes are not included in FormData)
        const enableSummaryChecked = this.enableSummary.checked;
        formData.set('enable_summary', enableSummaryChecked.toString());
        
        console.log('Summary enabled:', enableSummaryChecked);
        
        if (!file || file.size === 0) {
            this.showError('Please select a file to upload.');
            return;
        }

        console.log('Starting upload process...');
        console.log('File:', file.name, 'Size:', file.size);
        console.log('Current location:', window.location.href);
        
        this.startProcessing(file.name);

        // Use XMLHttpRequest for upload progress tracking
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const uploadPercent = Math.round((e.loaded / e.total) * 100);
                    this.updateUploadProgress(uploadPercent);
                }
            });
            
            // Handle upload completion
            xhr.upload.addEventListener('load', () => {
                this.updateUploadProgress(100);
                this.hideUploadProgress();
                console.log('Upload completed, waiting for server response...');
            });
            
            // Handle response
            xhr.addEventListener('load', () => {
                try {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        const data = JSON.parse(xhr.responseText);
                        console.log('Upload successful, task ID:', data.task_id);
                        
                        this.currentTaskId = data.task_id;
                        this.connectWebSocket();
                        resolve(data);
                    } else {
                        // Try to get error details from response
                        let errorMessage = `HTTP ${xhr.status}: ${xhr.statusText}`;
                        try {
                            const errorData = JSON.parse(xhr.responseText);
                            errorMessage = errorData.detail || errorMessage;
                        } catch (parseError) {
                            // If we can't parse JSON, use the response text
                            if (xhr.responseText) {
                                errorMessage = xhr.responseText;
                            }
                        }
                        throw new Error(errorMessage);
                    }
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
                    reject(error);
                }
            });
            
            // Handle network errors
            xhr.addEventListener('error', () => {
                console.error('Network error during upload');
                this.stopProcessing();
                this.showError('Network error: Unable to connect to server. Please check your internet connection.');
                reject(new Error('Network error'));
            });
            
            // Handle timeout
            xhr.addEventListener('timeout', () => {
                console.error('Upload timeout');
                this.stopProcessing();
                this.showError('Upload timeout: The file upload took too long. Please try again with a smaller file.');
                reject(new Error('Upload timeout'));
            });
            
            // Set up the request
            xhr.open('POST', '/upload');
            xhr.setRequestHeader('X-API-Key', window.CONFIG.API_KEY);
            xhr.timeout = 300000; // 5 minutes timeout
            
            // Start the upload
            xhr.send(formData);
        });
    }

    startProcessing(filename) {
        this.isProcessing = true;
        this.processingStartTime = new Date();
        this.hideError();
        this.hideInfo();
        this.hideResults();
        
        // Update UI
        this.uploadPrompt.style.display = 'none';
        this.progressSection.style.display = 'block';
        this.uploadProgressSection.style.display = 'block';
        this.processingProgressSection.style.display = 'block';
        this.fileInfo.style.display = 'block';
        this.completionInfo.style.display = 'none';
        this.fileName.textContent = filename;
        
        // Disable upload button
        this.uploadBtn.disabled = true;
        this.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
        
        // Reset progress bars
        this.updateUploadProgress(0);
        this.updateProgress(0, 'Preparing upload...');
        
        // Reset progress bar styling
        this.progressBar.classList.remove('bg-success');
        this.progressBar.classList.add('progress-bar-animated', 'progress-bar-striped');
        this.uploadProgressBar.classList.add('progress-bar-animated', 'progress-bar-striped');
    }

    updateUploadProgress(progress) {
        if (this.uploadProgressBar) {
            this.uploadProgressBar.style.width = `${progress}%`;
            this.uploadProgressBar.textContent = `${progress}%`;
            
            if (progress >= 100) {
                this.uploadProgressBar.classList.remove('progress-bar-animated');
                this.uploadProgressBar.classList.add('bg-success');
                // Update button text when upload completes
                this.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            }
        }
    }

    hideUploadProgress() {
        setTimeout(() => {
            if (this.uploadProgressSection) {
                this.uploadProgressSection.style.display = 'none';
            }
        }, 2000); // Hide after 2 seconds to show completion
    }

    stopProcessing() {
        this.isProcessing = false;
        
        // Re-enable upload button
        this.uploadBtn.disabled = false;
        this.uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Upload & Process';
        
        // Hide upload progress section
        if (this.uploadProgressSection) {
            this.uploadProgressSection.style.display = 'none';
        }
        
        // Close websocket
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }

    connectWebSocket() {
        if (!this.currentTaskId) return;

        // Update UI to show we're starting processing
        this.updateProgress(10, 'Starting processing...');

        // Check if we're running through ngrok
        const isNgrok = window.location.hostname.includes('ngrok');
        
        // Use secure WebSocket (wss://) if page is served over HTTPS, otherwise use ws://
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/${this.currentTaskId}?api_key=${encodeURIComponent(window.CONFIG.API_KEY)}`;
        
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
                const response = await fetch(`/status/${this.currentTaskId}`, {
                    headers: {
                        'X-API-Key': window.CONFIG.API_KEY
                    }
                });
                
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
        
        // Add animation class for processing
        if (progress < 100) {
            this.progressBar.classList.add('progress-bar-animated');
        } else {
            this.progressBar.classList.remove('progress-bar-animated');
        }
    }

    handleSuccess(result) {
        this.stopProcessing();
        this.updateProgress(100, 'Complete!');
        
        // Calculate processing time
        const processingEndTime = new Date();
        const processingDuration = Math.round((processingEndTime - this.processingStartTime) / 1000);
        const processingTimeText = this.formatDuration(processingDuration);
        const completionTimeText = processingEndTime.toLocaleTimeString();
        
        // Show completion information
        this.statusMessage.style.display = 'none';
        this.completionInfo.style.display = 'block';
        this.processingTime.textContent = processingTimeText;
        this.completionTime.textContent = completionTimeText;
        
        // Remove progress bar animation and make it green
        this.progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
        this.progressBar.classList.add('bg-success');
        
        setTimeout(() => {
            this.displayResults(result);
        }, 2000); // Show completion status for 2 seconds before showing results
    }

    handleFailure(error) {
        this.stopProcessing();
        this.showError(`Processing failed: ${error}`);
    }

    displayResults(result) {
        // Keep progress section visible to show completion status
        // this.progressSection.style.display = 'none'; // Commented out
        
        // Show results section
        this.resultsSection.style.display = 'block';
        
        // Display summary with fallback and handle disabled summary
        if (result && result.metadata && result.metadata.summary_enabled === false) {
            let summaryMessage = 'Summary generation was disabled for this transcription.';
            let iconClass = 'fas fa-info-circle';
            let messageClass = 'summary-disabled';
            
            // Check if it was auto-disabled due to short audio
            if (result.metadata.auto_disabled_reason) {
                summaryMessage = `Summary was automatically disabled: ${result.metadata.auto_disabled_reason}`;
                iconClass = 'fas fa-clock';
                messageClass = 'summary-auto-disabled';
            } else if (result.metadata.summary_requested === true) {
                // User requested summary but it was disabled for another reason
                summaryMessage = 'Summary generation was disabled during processing.';
            }
            
            this.summaryContent.innerHTML = `<div class="${messageClass}"><i class="${iconClass} me-2"></i>${summaryMessage}</div>`;
        } else if (result && result.summary) {
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
            // Get the full language name from the mappings, fallback to uppercase code
            const languageName = window.CONFIG.LANGUAGES && window.CONFIG.LANGUAGES[metadata.language] 
                ? window.CONFIG.LANGUAGES[metadata.language] 
                : metadata.language.toUpperCase();
            
            metadataHtml += `
                <div class="col-md-3 mb-2">
                    <div class="metadata-item">
                        <div class="metadata-label">Language</div>
                        <div>${languageName}</div>
                    </div>
                </div>
            `;
        }
        
        if (metadata.summary_enabled !== undefined) {
            if (metadata.summary_enabled && metadata.summary_length) {
                metadataHtml += `
                    <div class="col-md-3 mb-2">
                        <div class="metadata-item">
                            <div class="metadata-label">Summary Length</div>
                            <div>${metadata.summary_length}</div>
                        </div>
                    </div>
                `;
            } else if (!metadata.summary_enabled) {
                let summaryStatusText = "Disabled";
                let summaryStatusClass = "text-muted";
                
                // Check if it was auto-disabled
                if (metadata.auto_disabled_reason) {
                    summaryStatusText = `Auto-disabled (${metadata.auto_disabled_reason})`;
                    summaryStatusClass = "text-warning";
                } else if (metadata.summary_requested === true) {
                    summaryStatusText = "Disabled during processing";
                    summaryStatusClass = "text-info";
                }
                
                metadataHtml += `
                    <div class="col-md-3 mb-2">
                        <div class="metadata-item">
                            <div class="metadata-label">Summary</div>
                            <div class="${summaryStatusClass}">${summaryStatusText}</div>
                        </div>
                    </div>
                `;
            }
        } else if (metadata.summary_length) {
            // Fallback for older results without summary_enabled field
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
        
        const url = `/download/${this.currentTaskId}/${format}?api_key=${encodeURIComponent(window.CONFIG.API_KEY)}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `transcription_${this.currentTaskId}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    showError(message) {
        this.hideInfo(); // Hide info messages when showing error
        this.errorMessage.textContent = message;
        this.errorSection.style.display = 'block';
        this.errorSection.scrollIntoView({ behavior: 'smooth' });
    }

    showInfo(message) {
        // Create a temporary info message element if it doesn't exist
        let infoSection = document.getElementById('infoSection');
        if (!infoSection) {
            infoSection = document.createElement('div');
            infoSection.id = 'infoSection';
            infoSection.className = 'alert alert-info alert-dismissible fade show mt-3';
            infoSection.innerHTML = `
                <span id="infoMessage"></span>
                <button type="button" class="btn-close" aria-label="Close"></button>
            `;
            
            // Insert after error section or at the beginning of the form
            const errorSection = this.errorSection;
            if (errorSection && errorSection.parentNode) {
                errorSection.parentNode.insertBefore(infoSection, errorSection.nextSibling);
            } else {
                const uploadForm = this.uploadForm;
                if (uploadForm && uploadForm.parentNode) {
                    uploadForm.parentNode.insertBefore(infoSection, uploadForm);
                }
            }
            
            // Add click handler for close button
            const closeBtn = infoSection.querySelector('.btn-close');
            closeBtn.addEventListener('click', () => {
                this.hideInfo();
            });
        }
        
        const infoMessage = document.getElementById('infoMessage');
        if (infoMessage) {
            infoMessage.textContent = message;
        }
        infoSection.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideInfo();
        }, 5000);
    }

    hideInfo() {
        const infoSection = document.getElementById('infoSection');
        if (infoSection) {
            infoSection.style.display = 'none';
        }
    }

    hideError() {
        this.errorSection.style.display = 'none';
        this.hideInfo(); // Also hide info messages
    }

    hideResults() {
        this.resultsSection.style.display = 'none';
        this.timestampSection.style.display = 'none';
    }

    formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds} second${seconds !== 1 ? 's' : ''}`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            if (remainingSeconds === 0) {
                return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
            } else {
                return `${minutes}m ${remainingSeconds}s`;
            }
        } else {
            const hours = Math.floor(seconds / 3600);
            const remainingMinutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = seconds % 60;
            let result = `${hours}h`;
            if (remainingMinutes > 0) result += ` ${remainingMinutes}m`;
            if (remainingSeconds > 0) result += ` ${remainingSeconds}s`;
            return result;
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NurgaVoiceApp();
});
