import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from typing import Optional
import uuid

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

BUCKET_NAME = settings.AWS_S3_BUCKET

# Upload a file
def upload_file(file_bytes: bytes, filename: str, content_type: str, user_id: Optional[int] = None) -> str:
    """
    Uploads file to S3 and returns the file key
    """
    file_key = f"{user_id}/{uuid.uuid4()}_{filename}" if user_id else f"{uuid.uuid4()}_{filename}"
    try:
        s3_client.put_object(Bucket=BUCKET_NAME, Key=file_key, Body=file_bytes, ContentType=content_type)
    except ClientError as e:
        raise Exception(f"S3 upload failed: {e}")
    return file_key

# Generate presigned URL for download
def generate_presigned_url(file_key: str, expires_in: int = 3600) -> str:
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": file_key},
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        raise Exception(f"S3 presigned URL generation failed: {e}")

# Delete a file
def delete_file(file_key: str):
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_key)
    except ClientError as e:
        raise Exception(f"S3 delete failed: {e}")
