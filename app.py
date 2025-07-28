import os
import requests
from flask import Flask, request, render_template
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from mimetypes import guess_extension

# Load environment variables
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_IMAGE_BUCKET_NAME")  # use only this

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME]):
    raise EnvironmentError("❌ Missing AWS credentials or image bucket name in .env")

# S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        file = request.files.get('media')
        file_url = request.form.get('file_url', '').strip()

        # Case 1: Upload from file input
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower()

            if ext not in IMAGE_EXT:
                return render_template('upload.html', error="❌ Unsupported image format.")

            try:
                local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(local_path)

                s3.upload_file(local_path, S3_BUCKET_NAME, filename, ExtraArgs={'ACL': 'public-read'})
                url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"
                return render_template('upload.html', message=f"""
                    ✅ Image uploaded successfully!<br>
                    <a href="{url}" target="_blank" class="btn btn-success btn-sm">View</a>
                    <a href="{url}" download class="btn btn-primary btn-sm">Download</a>
                """)
            except Exception as e:
                return render_template('upload.html', error=f"❌ Upload failed: {str(e)}")

        # Case 2: Upload from image URL
        elif file_url:
            try:
                response = requests.get(file_url, stream=True, timeout=10)
                if response.status_code != 200:
                    return render_template('upload.html', error="❌ Invalid image URL.")

                mime = response.headers.get('Content-Type', '')
                if not mime.startswith('image'):
                    return render_template('upload.html', error="❌ URL is not an image.")

                ext = guess_extension(mime) or '.jpg'
                filename = secure_filename(f"remote_image{ext}")
                local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

                s3.upload_file(local_path, S3_BUCKET_NAME, filename, ExtraArgs={'ACL': 'public-read'})
                url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"
                return render_template('upload.html', message=f"""
                    ✅ Image downloaded and uploaded successfully!<br>
                    <a href="{url}" target="_blank" class="btn btn-success btn-sm">View</a>
                    <a href="{url}" download class="btn btn-primary btn-sm">Download</a>
                """)
            except Exception as e:
                return render_template('upload.html', error=f"❌ URL error: {str(e)}")

        return render_template('upload.html', error="❌ No image file or URL provided.")

    return render_template('upload.html')



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
