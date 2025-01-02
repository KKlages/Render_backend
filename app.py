from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json

app = Flask(__name__)

# Simplified bpmnlint configuration
BPMNLINT_CONFIG = '''{
  "extends": "bpmnlint:recommended"
}'''

def initialize_bpmnlint():
    """Initialize bpmnlint during application startup"""
    try:
        subprocess.run(['npm', 'install', 'bpmnlint'], check=True)
        ensure_config()
    except Exception as e:
        print(f"Failed to initialize bpmnlint: {e}")
        raise

def ensure_config():
    config_path = '.bpmnlintrc'
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write(BPMNLINT_CONFIG)

# Initialize on startup
initialize_bpmnlint()

@app.route('/validate', methods=['POST'])
def validate_bpmn():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.bpmn'):
            return jsonify({'error': 'Invalid file type. Only .bpmn files are allowed'}), 400
        
        with tempfile.NamedTemporaryFile(suffix='.bpmn', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            result = subprocess.run(
                ['npx', 'bpmnlint', temp_path],
                capture_output=True,
                text=True,
                timeout=30  # Add timeout to prevent hanging
            )
            
            print("bpmnlint stdout:", result.stdout)
            print("bpmnlint stderr:", result.stderr)
            print("Return code:", result.returncode)
            
            if result.returncode == 0:
                return jsonify({'message': 'No errors found'})
            else:
                return jsonify({
                    'errors': result.stdout if result.stdout else result.stderr,
                    'return_code': result.returncode
                })
                
        finally:
            # Always clean up the temporary file
            try:
                os.remove(temp_path)
            except OSError:
                pass
                
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Validation timed out'}), 408
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)
