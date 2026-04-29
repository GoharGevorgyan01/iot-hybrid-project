import boto3
from pathlib import Path

from aws_config import S3_BUCKET_NAME, S3_IMAGE_PREFIX


s3_client = boto3.client("s3")


def upload_image_to_s3(image_path, event_id, camera_id):
    """Upload representative image to S3 and return the S3 object key."""

    image_path = Path(image_path)

    if not image_path.exists():
        print(f"[S3] Image not found: {image_path}")
        return None

    s3_key = f"{S3_IMAGE_PREFIX}{camera_id}/event_{event_id}_{image_path.name}"

    try:
        s3_client.upload_file(
            str(image_path),
            S3_BUCKET_NAME,
            s3_key,
        )

        print(f"[S3] Uploaded image to s3://{S3_BUCKET_NAME}/{s3_key}")
        return s3_key

    except Exception as error:
        print(f"[S3] Failed to upload image: {error}")
        return None


def generate_presigned_url(s3_key, expiration=3600):
    """Generate a temporary URL for an uploaded S3 image."""

    if not s3_key:
        print("[S3] Cannot generate presigned URL: s3_key is missing")
        return None

    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": s3_key,
            },
            ExpiresIn=expiration,
        )

        print(f"[S3] Presigned URL generated for: {s3_key}")
        return url

    except Exception as error:
        print(f"[S3] Failed to generate presigned URL: {error}")
        return None