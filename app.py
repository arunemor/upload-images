import os
from flask import Flask, request, render_template
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Flask app setup
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Read AWS credentials and bucket info from environment
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Validate environment variables
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME]):
    raise EnvironmentError("❌ One or more AWS environment variables are missing.")

# Create S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Allow only image files
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        file = request.files.get('image')

        if not file or file.filename == '':
            return render_template('upload.html', error="❌ No file selected.")

        if not allowed_file(file.filename):
            return render_template('upload.html', error="❌ File type not allowed.")

        try:
            filename = secure_filename(file.filename)
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(local_path)

            s3.upload_file(local_path, S3_BUCKET_NAME, filename, ExtraArgs={'ACL': 'public-read'})
            file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"
            return render_template('upload.html', message=f"✅ Upload successful!<br><a href='{file_url}' target='_blank'>View Image</a>")
        except Exception as e:
            return render_template('upload.html', error=f"❌ Upload failed: {str(e)}")

    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)
