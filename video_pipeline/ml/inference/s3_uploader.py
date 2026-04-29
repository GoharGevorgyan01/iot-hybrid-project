import boto3
from pathlib import Path

from aws_config import S3_BUCKET_NAME, S3_IMAGE_PREFIX


s3_client = boto3.client("s3")


def upload_image_to_s3(image_path, event_id, camera_id):
    """Upload representative image to S3 and return S3 key."""

    image_path = Path(image_path)

    if not image_path.exists():
        print(f"[S3] Image not found: {image_path}")
        return None

    s3_key = f"{S3_IMAGE_PREFIX}{camera_id}/event_{event_id}_{image_path.name}"

    s3_client.upload_file(
        str(image_path),
        S3_BUCKET_NAME,
        s3_key
    )

    print(f"[S3] Uploaded image to s3://{S3_BUCKET_NAME}/{s3_key}")

    return s3_key