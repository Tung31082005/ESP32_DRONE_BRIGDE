# -*- coding: utf-8 -*-
"""Fix all encoding corruption in the project files."""
import re

# ============================================================
# 1. Rewrite video.html from scratch (completely corrupted)
# ============================================================
video_html = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DroneBridge FPV Video</title>
    <style>
        body { margin: 0; padding: 0; background-color: #111; color: #fff; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; height: 100vh; }
        .top-bar { width: 100%; display: flex; justify-content: space-between; padding: 10px 20px; box-sizing: border-box; background-color: #222; }
        .top-bar h2 { margin: 0; font-size: 18px; }
        .rssi { font-weight: bold; color: #4caf50; }
        .video-container { flex: 1; display: flex; justify-content: center; align-items: center; width: 100%; overflow: hidden; position: relative; }
        img#stream { max-width: 100%; max-height: 100%; object-fit: contain; }
        canvas#captureCanvas { display: none; }
        .controls { width: 100%; padding: 15px; box-sizing: border-box; background-color: #222; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
        button, select { padding: 10px 15px; font-size: 16px; border: none; border-radius: 5px; background-color: #3166FF; color: white; cursor: pointer; }
        button:hover, select:hover { background-color: #204dbf; }
        button.recording { background-color: #f44336; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }
        .back-btn { background-color: #555; }
        #warning { display: none; position: absolute; top: 10px; left: 50%; transform: translateX(-50%); background-color: rgba(255, 0, 0, 0.8); color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; font-size: 20px; animation: blink 1s infinite; z-index: 100; pointer-events: none; }
    </style>
</head>
<body>
    <div class="top-bar">
        <h2>FPV Video</h2>
        <div class="rssi" id="rssi-text">WiFi RSSI: <span id="rssi-val">--</span> dBm</div>
    </div>
    
    <div class="video-container">
        <div id="warning">WEAK SIGNAL! RETURN NOW!</div>
        <img id="stream" src="" crossorigin="anonymous">
        <canvas id="captureCanvas"></canvas>
    </div>

    <div class="controls">
        <button class="back-btn" onclick="window.location.href='/'">Back</button>
        <button id="toggleCamBtn" style="background-color: #ff9800; border-color: #ff9800;">Pause Camera</button>
        <button id="flashBtn">Flash LED: OFF</button>
        <select id="resSelect">
            <option value="4">160x120 (Lowest)</option>
            <option value="5">320x240 (Low)</option>
            <option value="8" selected>640x480 (Normal)</option>
            <option value="10">800x600 (High)</option>
        </select>
        <button id="photoBtn">Snapshot</button>
        <button id="recordBtn">Record Video</button>
    </div>

    <script>
        const camIP = window.location.protocol + '//' + window.location.hostname + ':81';
        const ctrlIP = window.location.protocol + '//' + window.location.hostname + ':82';
        const streamImg = document.getElementById('stream');
        
        // Power on camera hardware before loading stream
        fetch(ctrlIP + '/cam_power?state=1').then(() => {
            streamImg.src = camIP + '/stream';
        });
        
        let isCamActive = true;
        let flashState = false;

        // Toggle Camera Power (hardware on/off)
        document.getElementById('toggleCamBtn').addEventListener('click', (e) => {
            isCamActive = !isCamActive;
            if (isCamActive) {
                fetch(ctrlIP + '/cam_power?state=1').then(() => {
                    streamImg.src = camIP + '/stream?' + new Date().getTime();
                });
                e.target.innerText = 'Pause Camera';
                e.target.style.backgroundColor = '#ff9800';
            } else {
                fetch(ctrlIP + '/cam_power?state=0');
                streamImg.src = '';
                e.target.innerText = 'Resume Camera';
                e.target.style.backgroundColor = '#4caf50';
            }
        });

        // Auto-reconnect on stream error
        streamImg.onerror = () => {
            if (!isCamActive) return;
            console.log("Stream lost. Reconnecting...");
            setTimeout(() => {
                if (isCamActive) streamImg.src = camIP + '/stream?' + new Date().getTime();
            }, 1500);
        };
        
        // Update RSSI every 2 seconds
        setInterval(() => {
            fetch(ctrlIP + '/rssi').then(r => r.json()).then(data => {
                let rssi = data.rssi;
                let rssiEl = document.getElementById('rssi-val');
                let rssiTextEl = document.getElementById('rssi-text');
                let warningEl = document.getElementById('warning');
                
                if (rssi !== 0) {
                    rssiEl.innerText = rssi;
                    if (rssi < -80) {
                        rssiTextEl.style.color = '#f44336';
                        warningEl.style.display = 'block';
                    } else if (rssi < -70) {
                        rssiTextEl.style.color = '#ffeb3b';
                        warningEl.style.display = 'none';
                    } else {
                        rssiTextEl.style.color = '#4caf50';
                        warningEl.style.display = 'none';
                    }
                } else {
                    rssiEl.innerText = '--';
                    warningEl.style.display = 'none';
                }
            }).catch(() => {});
        }, 2000);

        // Flash LED toggle
        document.getElementById('flashBtn').addEventListener('click', (e) => {
            flashState = !flashState;
            fetch(`${ctrlIP}/light?val=${flashState ? 1 : 0}`);
            e.target.innerText = `Flash LED: ${flashState ? 'ON' : 'OFF'}`;
        });

        // Resolution change
        document.getElementById('resSelect').addEventListener('change', (e) => {
            fetch(`${ctrlIP}/resolution?val=${e.target.value}`).then(() => {
                setTimeout(() => {
                    streamImg.src = camIP + '/stream?' + new Date().getTime();
                }, 1000);
            });
        });

        // Take snapshot and save to device
        document.getElementById('photoBtn').addEventListener('click', () => {
            const img = document.getElementById('stream');
            const canvas = document.getElementById('captureCanvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            
            try {
                const link = document.createElement('a');
                link.download = `FPV_Snapshot_${Date.now()}.jpg`;
                link.href = canvas.toDataURL('image/jpeg', 0.9);
                link.click();
            } catch (e) {
                window.open(canvas.toDataURL('image/jpeg', 0.9));
            }

            // Reconnect stream if browser drops connection during download
            setTimeout(() => {
                if (isCamActive && (!img.complete || img.naturalWidth === 0)) {
                    img.src = camIP + '/stream?' + new Date().getTime();
                }
            }, 1500);
        });

        // Record video to device
        let mediaRecorder;
        let recordedChunks = [];
        let isRecording = false;
        let animationId;

        const img = document.getElementById('stream');
        const canvas = document.getElementById('captureCanvas');
        const ctx = canvas.getContext('2d');

        function drawToCanvas() {
            if (isRecording) {
                if (img.naturalWidth) {
                    if (canvas.width !== img.naturalWidth) {
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                    }
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                }
                // Limit to ~15fps to reduce CPU load on phone
                animationId = setTimeout(drawToCanvas, 66); 
            }
        }

        document.getElementById('recordBtn').addEventListener('click', (e) => {
            if (!isRecording) {
                isRecording = true;
                e.target.innerText = 'Stop Recording';
                e.target.classList.add('recording');
                
                canvas.width = img.naturalWidth || 640;
                canvas.height = img.naturalHeight || 480;
                
                const stream = canvas.captureStream(15);
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
                recordedChunks = [];
                
                mediaRecorder.ondataavailable = (ev) => {
                    if (ev.data.size > 0) recordedChunks.push(ev.data);
                };
                
                mediaRecorder.onstop = () => {
                    const blob = new Blob(recordedChunks, { type: 'video/webm' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `FPV_Video_${Date.now()}.webm`;
                    link.click();
                    URL.revokeObjectURL(url);
                };
                
                drawToCanvas();
                mediaRecorder.start();
            } else {
                isRecording = false;
                clearTimeout(animationId);
                mediaRecorder.stop();
                e.target.innerText = 'Record Video';
                e.target.classList.remove('recording');
                
                // Reconnect stream if browser drops connection during download
                setTimeout(() => {
                    if (isCamActive && (!img.complete || img.naturalWidth === 0)) {
                        img.src = camIP + '/stream?' + new Date().getTime();
                    }
                }, 1500);
            }
        });
    </script>
</body>
</html>
'''

with open('frontend/video.html', 'w', encoding='utf-8') as f:
    f.write(video_html)
print("OK: video.html rewritten")

# ============================================================
# 2. Fix index.html - replace corrupted button text + dis_console labels
# ============================================================
with open('frontend/index.html', 'r', encoding='utf-8', errors='replace') as f:
    idx = f.read()

# Fix the camera FPV button (corrupted Vietnamese emoji+text)
idx = re.sub(
    r'>[^<]*M[^<]*CAMERA FPV</a>',
    '>OPEN CAMERA FPV</a>',
    idx
)

# Fix dis_console labels
idx = idx.replace('Disable Console Output (Yeu cau khoi dong lai)', 'Disable Console Log (Requires Reboot)')
idx = idx.replace('Mo Console (Nha Log bao loi)', 'Console ON (Show system logs)')
idx = idx.replace('Tat Console (Luong MAVLink tinh khiet)', 'Console OFF (Clean MAVLink only)')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(idx)
print("OK: index.html fixed")

# ============================================================
# 3. Fix camera_stream.c - replace corrupted Vietnamese comments with English
# ============================================================
with open('main/camera_stream.c', 'r', encoding='utf-8', errors='replace') as f:
    cam = f.read()

# Fix all corrupted comments
replacements = [
    # stream_handler comment about skipping frame
    (r'//\s*L.*?Stream!', '// Camera error or power loss, skip this frame without dropping the stream connection'),
    # light_handler section comment
    (r'// HTTP Handler cho.*?Flash', '// HTTP Handler for Flash LED control'),
    # resolution_handler section comment  
    (r'// HTTP Handler cho thay.*?gi.*?\n', '// HTTP Handler for resolution change\n'),
    # PWDN comment in start_camera_stream
    (r'//\s*K.*?Camera\n', '// Pull PWDN pin HIGH to completely power off camera sensor\n'),
    # Default camera off comment
    (r'//\s*M\?c.*?pin\n', '// Camera is OFF by default at boot to save power\n'),
    # Control server comment
    (r'//\s*Kh.*?81\)', '// Start Camera control server on port 82 (separate from Stream on port 81)'),
    # Fix indentation bug: httpd_config_t was missing indentation
]

for pattern, replacement in replacements:
    cam = re.sub(pattern, replacement, cam)

# Fix the indentation bug
cam = cam.replace('\nhttpd_config_t httpd_config = HTTPD_DEFAULT_CONFIG();',
                   '\n    httpd_config_t httpd_config = HTTPD_DEFAULT_CONFIG();')

with open('main/camera_stream.c', 'w', encoding='utf-8') as f:
    f.write(cam)
print("OK: camera_stream.c fixed")

# ============================================================
# 4. Fix main.c - replace corrupted Vietnamese comments with English
# ============================================================
with open('main/main.c', 'r', encoding='utf-8', errors='replace') as f:
    main = f.read()

# Fix camera startup comment
main = re.sub(r'//\s*Kh.*?Port 81\)', '// Start Camera module (Video Stream on Port 81)', main)

# Fix console disable comment block
main = re.sub(
    r'// N.*?QGroundControl\.',
    '// If user enabled "Disable Console", mute ALL system logs\n'
    '    // so that the UART output is pure MAVLink without any ASCII log noise.',
    main
)

with open('main/main.c', 'w', encoding='utf-8') as f:
    f.write(main)
print("OK: main.c fixed")

print("\nAll encoding issues fixed!")
