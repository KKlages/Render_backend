from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json

app = Flask(__name__)

# Create .bpmnlintrc during startup
BPMNLINT_CONFIG = '''{
  "extends": "bpmnlint:recommended",
  "rules": {
    "label-required": "error",
    "no-implicit-split": "error",
    "no-implicit-join": "error",
    "single-blank-start-event": "error",
    "single-end-event": "error"
  }
}'''

def ensure_config():
    config_path = '.bpmnlintrc'
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write(BPMNLINT_CONFIG)

@app.route('/validate', methods=['POST'])
def validate_bpmn():
    try:
        ensure_config()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        with tempfile.NamedTemporaryFile(suffix='.bpmn', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            result = subprocess.run(
                ['npx', 'bpmnlint', temp_path],
                capture_output=True,
                text=True
            )
            
            print("bpmnlint stdout:", result.stdout)
            print("bpmnlint stderr:", result.stderr)
            print("Return code:", result.returncode)
            
            if result.returncode == 0:
                return jsonify({'message': 'No errors found'})
            else:
                return jsonify({'errors': result.stderr})
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
