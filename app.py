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

def initialize_bpmnlint():
    """Initialize bpmnlint during application startup"""
    try:
        logger.info("Starting bpmnlint initialization")
        subprocess.run(['npm', 'install', 'bpmnlint'], check=True)
        ensure_config()
        logger.info("bpmnlint initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize bpmnlint: {e}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

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
            # Always clean up the temporary file
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

# Initialize on startup
logger.info("Starting application initialization")
initialize_bpmnlint()
logger.info("Application initialization complete")

if __name__ == '__main__':
    app.run(debug=True)
