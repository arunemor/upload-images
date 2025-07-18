import os
from flask import Flask, request, render_template
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load AWS keys from .env
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AWS S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template('upload.html', error="No file part in the request.")

        file = request.files['image']
        if file.filename == '':
            return render_template('upload.html', error="No file selected.")

        if file:
            filename = secure_filename(file.filename)
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(local_path)

            try:
                s3.upload_file(local_path, BUCKET_NAME, filename, ExtraArgs={'ACL': 'public-read'})
                file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
                message = f"✅ Image uploaded! <br><a href='{file_url}' target='_blank'>View Image</a>"
                return render_template('upload.html', message=message)
            except Exception as e:
                return render_template('upload.html', error=f"❌ Upload failed: {e}")

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
