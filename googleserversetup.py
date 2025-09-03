# Cell 1: Install packages
!pip install flask pyngrok requests psutil GPUtil

# Cell 2: Import libraries
import os
import time
import json
import threading
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from pyngrok import ngrok
import psutil

# Cell 3: Configuration
NGROK_TOKEN = "32ADr6RPxOVvwfxOaQyXVOezV9S_3mvFj2hb9oNdBppRwxLVX"  # Replace with your token
RENDER_URL = "https://colab-vps-coordinator.onrender.com/"  # Replace with your Railway URL
WORKER_ID = f"colab-primary-{int(time.time())}"

# Set ngrok token
ngrok.set_auth_token(NGROK_TOKEN)

print(f"Worker ID: {WORKER_ID}")

# Cell 4: Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return f'''
    <h1>🖥️ Colab Primary Server</h1>
    <p>Worker ID: {WORKER_ID}</p>
    <p>CPU Cores: {psutil.cpu_count()}</p>
    <p>RAM: {psutil.virtual_memory().total // (1024**3)} GB</p>
    <p>GPU Available: {check_gpu_available()}</p>
    <p>Status: Active</p>
    '''

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "worker_id": WORKER_ID,
        "timestamp": datetime.now().isoformat(),
        "resources": {
            "cpu_cores": psutil.cpu_count(),
            "ram_gb": psutil.virtual_memory().total // (1024**3),
            "gpu_available": check_gpu_available()
        }
    })

@app.route('/api/compute', methods=['POST'])
def compute_task():
    """Handle compute tasks"""
    data = request.json
    task_type = data.get('type', 'unknown')
    
    print(f"Processing task: {task_type}")
    
    if task_type == 'cpu_intensive':
        result = handle_cpu_task(data)
    elif task_type == 'gpu_task':
        result = handle_gpu_task(data)
    else:
        result = {"error": "Unknown task type"}
    
    return jsonify(result)

def check_gpu_available():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        return len(gpus) > 0
    except:
        return False

def handle_cpu_task(data):
    """Example CPU task"""
    import numpy as np
    
    # Simulate CPU-intensive work
    size = data.get('size', 1000)
    matrix = np.random.rand(size, size)
    result = np.linalg.det(matrix)
    
    return {
        "result": float(result),
        "processed_on": WORKER_ID,
        "matrix_size": size
    }

def handle_gpu_task(data):
    """Example GPU task"""
    if not check_gpu_available():
        return {"error": "No GPU available"}
    
    # Example TensorFlow task
    try:
        import tensorflow as tf
        
        # Simple GPU computation
        with tf.device('/GPU:0'):
            a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
            b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
            c = tf.matmul(a, b)
        
        return {
            "result": c.numpy().tolist(),
            "processed_on": WORKER_ID,
            "device": "GPU"
        }
    except Exception as e:
        return {"error": str(e)}

  # Cell 5: Start server
def start_server():
    app.run(host='0.0.0.0', port=5000, debug=False)

def register_with_coordinator():
    """Register this worker with the coordinator"""
    registration_data = {
        "worker_id": WORKER_ID,
        "worker_url": public_url,
        "capabilities": {
            "cpu_cores": psutil.cpu_count(),
            "ram_gb": psutil.virtual_memory().total // (1024**3),
            "gpu_available": check_gpu_available(),
            "worker_type": "colab"
        }
    }
    
    try:
        response = requests.post(
            f"{RENDER_URL}/api/worker/register",
            json=registration_data,
            timeout=10
        )
        print(f"Registration response: {response.json()}")
    except Exception as e:
        print(f"Registration failed: {e}")

def send_heartbeat():
    """Send periodic heartbeat"""
    while True:
        try:
            requests.post(
                f"{RENDER_URL}/api/worker/heartbeat",
                json={"worker_id": WORKER_ID},
                timeout=10
            )
            print(f"Heartbeat sent at {datetime.now()}")
        except Exception as e:
            print(f"Heartbeat failed: {e}")
        
        time.sleep(60)  # Send heartbeat every minute

# Start Flask server in background
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

# Wait for server to start
time.sleep(3)

# Expose via ngrok
public_url = ngrok.connect(5000)
print(f"🌍 Server available at: {public_url}")

# Register with coordinator
register_with_coordinator()

# Start heartbeat in background
heartbeat_thread = threading.Thread(target=send_heartbeat)
heartbeat_thread.daemon = True
heartbeat_thread.start()

print("✅ Colab server is running!")
print(f"Access your server: {public_url}")
print(f"Coordinator: {RENDER_URL}")

# Cell 6: Session keeper
def keep_session_alive():
    """Keep Colab session active"""
    start_time = time.time()
    max_session_hours = 12
    
    while True:
        elapsed_hours = (time.time() - start_time) / 3600
        remaining_hours = max_session_hours - elapsed_hours
        
        print(f"Session active: {elapsed_hours:.1f}h elapsed, {remaining_hours:.1f}h remaining")
        
        if remaining_hours < 0.5:  # 30 minutes before limit
            print("⚠️ Session ending soon! Prepare for handover...")
            break
        
        # Random activity to prevent idle timeout
        import numpy as np
        _ = np.random.random((10, 10))
        
        time.sleep(300)  # Check every 5 minutes

# Start session keeper
keep_session_alive()

# Add to your Colab notebooks - ping every 10 minutes
def keep_render_awake():
    while True:
        try:
            requests.get("https://your-app.onrender.com/health")
            print("Pinged coordinator to keep it awake")
        except:
            pass
        time.sleep(600)  # 10 minutes

# Start in background thread
threading.Thread(target=keep_render_awake, daemon=True).start()
