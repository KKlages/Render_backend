from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simplified bpmnlint configuration
BPMNLINT_CONFIG = '''{
  "extends": "bpmnlint:recommended"
}'''

def ensure_config():
    config_path = '.bpmnlintrc'
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            f.write(BPMNLINT_CONFIG)
        logger.info(f"Created bpmnlint config at {config_path}")

def verify_bpmnlint():
    """Verify bpmnlint installation"""
    try:
        # Check if bpmnlint is in node_modules
        if os.path.exists('node_modules/bpmnlint'):
            logger.info("Found bpmnlint in node_modules")
        else:
            logger.error("bpmnlint not found in node_modules")
        
        # Check if bpmnlint is executable
        result = subprocess.run(['which', 'bpmnlint'], capture_output=True, text=True)
        logger.info(f"bpmnlint path: {result.stdout}")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying bpmnlint: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    bpmnlint_status = verify_bpmnlint()
    return jsonify({
        'status': 'healthy',
        'bpmnlint_available': bpmnlint_status
    }), 200

@app.route('/validate', methods=['POST'])
def validate_bpmn():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.bpmn'):
            return jsonify({'error': 'Invalid file type. Only .bpmn files are allowed'}), 400
        
        # Verify bpmnlint before proceeding
        if not verify_bpmnlint():
            return jsonify({'error': 'bpmnlint not properly installed'}), 500
        
        with tempfile.NamedTemporaryFile(suffix='.bpmn', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Log the command being executed
            cmd = ['bpmnlint', temp_path]
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            logger.debug(f"bpmnlint stdout: {result.stdout}")
            logger.debug(f"bpmnlint stderr: {result.stderr}")
            logger.debug(f"Return code: {result.returncode}")
            
            if result.returncode == 0:
                return jsonify({'message': 'No errors found'})
            else:
                return jsonify({
                    'errors': result.stdout if result.stdout else result.stderr,
                    'return_code': result.returncode
                })
                
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
                
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Validation timed out'}), 408
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Ensure configuration on startup
ensure_config()
verify_bpmnlint()

if __name__ == '__main__':
    app.run(debug=True)
