from flask import Flask, request, jsonify
import subprocess
import os
import uuid
import base64


app = Flask(__name__)


@app.route('/convert', methods=['POST'])
def convert_to_pdf():
    if request.is_json:
        data = request.get_json()
        if 'filename' not in data or 'content' not in data:
            return jsonify({'error': 'Missing filename or content in JSON.'}), 400

        filename = data['filename']
        content = base64.b64decode(data['content'])
    else:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        filename = file.filename
        content = file.read()



    input_dir = "/shared/input"
    output_dir = "/shared/output"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    unique_id = str(uuid.uuid4())
    input_file_path = os.path.normpath(os.path.join(input_dir, f"{unique_id}_{filename}"))

    if not input_file_path.startswith(os.path.normpath(input_dir)):
        return jsonify({'error': f'Parameter \"filename\" is invalid.'}), 400

    with open(input_file_path, 'wb') as f:
        f.write(content)

    try:
        subprocess.run([
            'soffice',
            '--headless', '--invisible', '--nodefault', '--nofirststartwizard', '--nolockcheck', '--nologo', '--norestore',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_file_path
        ], check=True)

        output_file_name = os.path.splitext(os.path.basename(input_file_path))[0] + '.pdf'
        output_file_path = os.path.join(output_dir, output_file_name)

        if not os.path.exists(output_file_path):
            raise FileNotFoundError("Conversion failed: PDF not created.")

        file_size = os.path.getsize(output_file_path)

        return jsonify({
            'status': 'success',
            'pdf_path': output_file_path,
            'file_size': file_size
        })

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Conversion failed: An internal error has occurred.'}), 500

    finally:
        if os.path.exists(input_file_path):
            os.remove(input_file_path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
