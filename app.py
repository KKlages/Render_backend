from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json

app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate_bpmn():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.bpmn', delete=False) as temp_file:
        file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        # Run bpmnlint
        result = subprocess.run(
            ['npx', 'bpmnlint', temp_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return jsonify({'message': 'No errors found'})
        else:
            return jsonify({'errors': result.stderr})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(temp_path)

if __name__ == '__main__':
    app.run()
