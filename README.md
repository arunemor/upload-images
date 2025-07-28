# upload-images


                                              Lambda Function

import boto3
import os
from PIL import Image
import io
import urllib.parse

s3 = boto3.client('s3')
RESIZED_BUCKET = os.environ.get('RESIZED_BUCKET')

def resize_image(image_data, image_format):
img = Image.open(io.BytesIO(image_data))
img.thumbnail((800, 800))
buffer = io.BytesIO()
img.save(buffer, format=image_format, quality=85)
buffer.seek(0)
return buffer

def lambda_handler(event, context):
try:
record = event['Records'][0]
src_bucket = record['s3']['bucket']['name']
src_key = urllib.parse.unquote_plus(record['s3']['object']['key'])

print(f"📥 Source Bucket: {src_bucket}")
print(f"📂 Source Key: {src_key}")

response = s3.get_object(Bucket=src_bucket, Key=src_key)
data = response['Body'].read()

# Fallback to JPEG if image format is unknown
try:
img = Image.open(io.BytesIO(data))
image_format = img.format or 'JPEG'
img.close()
except Exception as e:
return {
'statusCode': 400,
'body': f"❌ Error detecting image format: {str(e)}"
}

# Resize and upload
resized_image = resize_image(data, image_format)
dst_key = f"resized/{os.path.basename(src_key)}"

s3.put_object(
Bucket=RESIZED_BUCKET,
Key=dst_key,
Body=resized_image,
ContentType=f"image/{image_format.lower()}",
ACL="public-read"
)

return {
'statusCode': 200,
'body': f"✅ Resized image uploaded to s3://{RESIZED_BUCKET}/{dst_key}"
}

except s3.exceptions.NoSuchKey:
return {
'statusCode': 404,
'body': "❌ File not found in S3 (NoSuchKey)"
}
except Exception as e:
return {
'statusCode': 500,
'body': f"❌ Lambda error: {str(e)}"
}



                                                                json.event


{
  "Records": [
    {
      "eventVersion": "2.0",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-1",
      "eventTime": "1970-01-01T00:00:00.000Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {
        "principalId": "EXAMPLE"
      },
      "requestParameters": {
        "sourceIPAddress": "127.0.0.1"
      },
      "responseElements": {
        "x-amz-request-id": "EXAMPLE123456789",
        "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "testConfigRule",
        "bucket": {
          "name": "uploadimage20",
          "ownerIdentity": {
            "principalId": "EXAMPLE"
          },
          "arn": "arn:aws:s3:::example-bucket"
        },
        "object": {
          "key": "2-azure-landing-zone-architecture-diagram-hub-spoke_microsoft-zones.png",
          "size": 1024,
          "eTag": "0123456789abcdef0123456789abcdef",
          "sequencer": "0A1B2C3D4E5F678901"
        }
      }
    }
  ]
}