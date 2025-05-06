document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const resultContainer = document.getElementById('result-container');
    const scanResult = document.getElementById('scan-result');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    
    let scanning = false;
    let videoStream = null;
    
    startButton.addEventListener('click', startScanner);
    stopButton.addEventListener('click', stopScanner);
    
    function startScanner() {
        // Hide any previous results or errors
        resultContainer.style.display = 'none';
        errorContainer.style.display = 'none';
        
        // Get user media and start scanning
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: "environment",
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        })
        .then(function(stream) {
            videoStream = stream;
            video.srcObject = stream;
            video.setAttribute('playsinline', true); // required for iOS
            video.play();
            requestAnimationFrame(tick);
            scanning = true;
            
            startButton.style.display = 'none';
            stopButton.style.display = 'inline-block';
        })
        .catch(function(err) {
            console.error('Error accessing camera:', err);
            errorMessage.textContent = 'Error accessing camera: ' + err.message;
            errorContainer.style.display = 'block';
        });
    }
    
    function stopScanner() {
        if (videoStream) {
            videoStream.getTracks().forEach(track => {
                track.stop();
            });
            videoStream = null;
        }
        scanning = false;
        
        stopButton.style.display = 'none';
        startButton.style.display = 'inline-block';
    }
    
    function tick() {
        if (!scanning) return;
        
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            // Create a temporary canvas to capture a frame from the video
            const canvas = document.createElement('canvas');
            const canvasContext = canvas.getContext('2d');
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvasContext.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            const imageData = canvasContext.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height, {
                inversionAttempts: "dontInvert",
            });
            
            if (code) {
                console.log('QR code detected:', code.data);
                
                // Process the QR code data
                processQRCode(code.data);
                
                // Stop scanning after successful detection
                stopScanner();
                return;
            }
        }
        
        // Continue scanning
        requestAnimationFrame(tick);
    }
    
    function processQRCode(qrData) {
        // Make API call to process the QR code data
        fetch('/api/process-qr-scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ qr_data: qrData }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Check if it's an order QR code that needs redirection
                if (data.type === 'order' && data.redirect_url) {
                    // Show success message briefly before redirecting
                    scanResult.textContent = `${data.message} Redirecting to order status...`;
                    resultContainer.style.display = 'block';
                    
                    // Redirect to the order status page after a short delay
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1500);
                } else {
                    // Show success message for status QR codes
                    scanResult.textContent = data.message;
                    resultContainer.style.display = 'block';
                }
            } else {
                // Show error message
                errorMessage.textContent = data.error || 'Unknown error processing QR code';
                errorContainer.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error processing QR code:', error);
            errorMessage.textContent = 'Error communicating with server: ' + error.message;
            errorContainer.style.display = 'block';
        });
    }
});
