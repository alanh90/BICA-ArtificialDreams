from flask import Flask, render_template, jsonify, request
import time
import threading
import os
from dotenv import load_dotenv
from openai import OpenAI

# Import custom modules
from dream_system import DreamSystem
from memory_system import MemorySystem

app = Flask(__name__)

# Initialize OpenAI client
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def create_client(api_key):
    try:
        # Initialize client without proxy settings
        client = OpenAI(api_key=api_key)
        # Quick validation of client
        client.models.list()
        return client
    except Exception as e:
        print(f"Unexpected error creating OpenAI client: {e}")
        return None


client = create_client(api_key)

# Initialize the systems
memory_system = MemorySystem()
dream_system = DreamSystem(client, memory_system)


# ===========================================================================================
# FLASK ROUTES
# ===========================================================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/dream/state')
def get_dream_state():
    return jsonify(dream_system.get_state())


@app.route('/api/dreams/trigger', methods=['POST'])
def trigger_dream():
    """Manually trigger a dream cycle"""
    result = dream_system.trigger_dream_cycle()

    return jsonify({
        "success": True,
        "result": result,
        "dream_state": dream_system.get_state()
    })


@app.route('/api/memories')
def get_memories():
    """Get recent memories for display"""
    return jsonify({
        "regular": memory_system.get_recent_memories(max_count=20),
        "consolidated": memory_system.get_consolidated_memories(max_count=10),
        "insights": memory_system.get_insights(max_count=10)
    })


@app.route('/api/dreams')
def get_dreams():
    """Get recent dream records"""
    return jsonify(dream_system.get_recent_dreams())


@app.route('/api/memories/bulk', methods=['POST'])
def add_bulk_memories():
    """Add multiple memories at once (for day generator)"""
    data = request.json

    if not data or not data.get('memories'):
        return jsonify({
            "success": False,
            "message": "No memories provided"
        })

    added_count = 0
    for memory_data in data['memories']:
        memory_system.add_memory(
            text=memory_data.get('text', ''),
            source=memory_data.get('source', 'generated'),
            importance=memory_data.get('importance'),
            metadata=memory_data.get('metadata', {})
        )
        added_count += 1

    return jsonify({
        "success": True,
        "message": f"Added {added_count} memories"
    })


@app.route('/api/system/reset', methods=['POST'])
def reset_system():
    """Reset all systems"""
    dream_system.reset()
    memory_system.reset()

    return jsonify({
        "success": True,
        "message": "All systems have been reset"
    })


# ===========================================================================================
# MAIN EXECUTION
# ===========================================================================================

if __name__ == '__main__':
    try:
        # Start the dream system's background thread
        dream_system.start()
        app.run(debug=True, use_reloader=False)
    finally:
        # Make sure to stop all background threads when shutting down
        dream_system.stop()