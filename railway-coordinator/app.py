from flask import Flask, request, jsonify
import os
import json
import redis
from datetime import datetime

app = Flask(__name__)

# In-memory storage (Railway provides Redis addon for $0)
active_workers = {}
task_queue = []

@app.route('/')
def home():
    return '''
    <h1>🚀 Colab VPS Coordinator</h1>
    <p>Status: Online 24/7</p>
    <p>Active Workers: ''' + str(len(active_workers)) + '''</p>
    <p><a href="/status">View Status</a></p>
    '''

@app.route('/status')
def status():
    return jsonify({
        "coordinator": "online",
        "active_workers": list(active_workers.keys()),
        "pending_tasks": len(task_queue),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/worker/register', methods=['POST'])
def register_worker():
    """Workers register themselves here"""
    data = request.json
    worker_id = data.get('worker_id')
    worker_url = data.get('worker_url')
    capabilities = data.get('capabilities', {})
    
    active_workers[worker_id] = {
        "url": worker_url,
        "capabilities": capabilities,
        "last_seen": datetime.now().isoformat(),
        "status": "active"
    }
    
    return jsonify({"status": "registered", "worker_id": worker_id})

@app.route('/api/worker/heartbeat', methods=['POST'])
def worker_heartbeat():
    """Workers send heartbeat to stay active"""
    data = request.json
    worker_id = data.get('worker_id')
    
    if worker_id in active_workers:
        active_workers[worker_id]["last_seen"] = datetime.now().isoformat()
        return jsonify({"status": "acknowledged"})
    
    return jsonify({"status": "unknown_worker"}), 404

@app.route('/api/task/submit', methods=['POST'])
def submit_task():
    """Submit task to be processed"""
    task = request.json
    task['id'] = len(task_queue) + 1
    task['submitted_at'] = datetime.now().isoformat()
    task['status'] = 'pending'
    
    task_queue.append(task)
    
    # Try to assign immediately
    assigned_worker = assign_task(task)
    
    return jsonify({
        "task_id": task['id'], 
        "status": "queued",
        "assigned_to": assigned_worker
    })

@app.route('/api/tasks/get', methods=['GET'])
def get_pending_tasks():
    """Workers poll for tasks"""
    worker_id = request.args.get('worker_id')
    
    # Find tasks this worker can handle
    available_tasks = [t for t in task_queue if t['status'] == 'pending']
    
    return jsonify({"tasks": available_tasks[:5]})  # Return up to 5 tasks

def assign_task(task):
    """Assign task to best available worker"""
    # Simple assignment logic - can be enhanced
    for worker_id, worker_info in active_workers.items():
        if worker_info['status'] == 'active':
            return worker_id
    return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
