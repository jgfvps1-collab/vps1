# Cell 1: Install packages
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "psutil"])

# Cell 2: Setup worker
import os
import time
import json
import requests
import psutil
from datetime import datetime

# Configuration
RAILWAY_URL = "https://colab-vps-coordinator.onrender.com/"  # Replace with your Railway URL
WORKER_ID = f"kaggle-worker-{int(time.time())}"

print(f"Kaggle Worker ID: {WORKER_ID}")
print(f"CPU Cores: {psutil.cpu_count()}")
print(f"RAM: {psutil.virtual_memory().total // (1024**3)} GB")

# Cell 3: Worker functions
def register_with_coordinator():
    """Register this Kaggle worker"""
    registration_data = {
        "worker_id": WORKER_ID,
        "worker_url": "kaggle-internal",  # Kaggle doesn't expose external URLs
        "capabilities": {
            "cpu_cores": psutil.cpu_count(),
            "ram_gb": psutil.virtual_memory().total // (1024**3),
            "gpu_available": check_gpu_available(),
            "worker_type": "kaggle"
        }
    }
    
    try:
        response = requests.post(
            f"{RAILWAY_URL}/api/worker/register",
            json=registration_data,
            timeout=10
        )
        print(f"Registration response: {response.json()}")
        return True
    except Exception as e:
        print(f"Registration failed: {e}")
        return False

def check_gpu_available():
    """Check if GPU is available"""
    try:
        import tensorflow as tf
        return len(tf.config.list_physical_devices('GPU')) > 0
    except:
        return False

def poll_for_tasks():
    """Poll coordinator for tasks"""
    while True:
        try:
            response = requests.get(
                f"{RAILWAY_URL}/api/tasks/get",
                params={"worker_id": WORKER_ID},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('tasks', [])
                
                for task in tasks:
                    if can_handle_task(task):
                        print(f"Processing task: {task['id']}")
                        result = process_task(task)
                        print(f"Task {task['id']} completed: {result}")
            
            # Send heartbeat
            requests.post(
                f"{RAILWAY_URL}/api/worker/heartbeat",
                json={"worker_id": WORKER_ID},
                timeout=10
            )
            
        except Exception as e:
            print(f"Polling error: {e}")
        
        time.sleep(30)  # Poll every 30 seconds

def can_handle_task(task):
    """Check if this worker can handle the task"""
    task_type = task.get('type', '')
    
    # Kaggle is good for:
    # - Large dataset processing (30 GB RAM)
    # - ML training with different GPU architecture
    # - Data analysis tasks
    
    if task_type in ['large_dataset', 'ml_training', 'data_analysis']:
        return True
    
    if task.get('requires_high_ram', False) and psutil.virtual_memory().total > 25 * (1024**3):
        return True
    
    return False

def process_task(task):
    """Process task using Kaggle's resources"""
    task_type = task.get('type', 'unknown')
    
    if task_type == 'large_dataset':
        return process_large_dataset(task)
    elif task_type == 'ml_training':
        return train_model(task)
    elif task_type == 'data_analysis':
        return analyze_data(task)
    else:
        return {"error": "Unknown task type", "worker": WORKER_ID}

def process_large_dataset(task):
    """Process large datasets using Kaggle's 30 GB RAM"""
    import pandas as pd
    import numpy as np
    
    # Simulate processing large dataset
    data_size = task.get('data_size', 1000000)
    
    # Create large dataframe (Kaggle can handle this)
    df = pd.DataFrame({
        'col1': np.random.randn(data_size),
        'col2': np.random.randn(data_size),
        'col3': np.random.randint(0, 100, data_size)
    })
    
    # Process data
    result = {
        'mean_col1': df['col1'].mean(),
        'std_col2': df['col2'].std(),
        'unique_col3': df['col3'].nunique(),
        'processed_rows': len(df),
        'worker': WORKER_ID,
        'ram_used_gb': psutil.virtual_memory().used // (1024**3)
    }
    
    return result

def train_model(task):
    """Train ML model using Kaggle's GPU"""
    if not check_gpu_available():
        return {"error": "No GPU available", "worker": WORKER_ID}
    
    import tensorflow as tf
    
    # Simple model training example
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu', input_shape=(10,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy')
    
    # Generate sample data
    X = tf.random.normal((1000, 10))
    y = tf.random.uniform((1000, 1))
    
    # Train model
    history = model.fit(X, y, epochs=5, verbose=0)
    
    return {
        "model_trained": True,
        "final_loss": float(history.history['loss'][-1]),
        "worker": WORKER_ID,
        "gpu_used": "Tesla P100"
    }

# Cell 4: Start worker
print("🚀 Starting Kaggle worker...")

if register_with_coordinator():
    print("✅ Registered successfully!")
    print("🔄 Starting task polling...")
    poll_for_tasks()
else:
    print("❌ Registration failed!")
