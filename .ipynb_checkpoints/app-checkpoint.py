from flask import Flask, request, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/validate', methods=['POST'])
def validate_bpmn():
    try:
        # Ensure bpmnlint is installed
        subprocess.run(['npm', 'install', 'bpmnlint'], check=True)
        
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
            
            if result.returncode == 0:
                return jsonify({'message': 'No errors found'})
            else:
                return jsonify({
                    'errors': result.stdout if result.stdout else result.stderr,
                    'return_code': result.returncode
                })
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
