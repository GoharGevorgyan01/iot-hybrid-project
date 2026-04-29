import boto3
from pathlib import Path

from aws_config import S3_BUCKET_NAME, S3_IMAGE_PREFIX


PROJECT_ROOT = Path(__file__).resolve().parents[3]
s3_client = boto3.client("s3")


def resolve_image_path(image_path):
    """Resolve image path for both Windows and Docker/Linux."""

    if not image_path:
        return None

    # Normalize Windows backslashes to Linux/portable slashes
    raw_path = str(image_path).strip().replace("\\", "/")
    candidate_path = Path(raw_path)

    if candidate_path.is_absolute():
        return candidate_path

    # /app in Docker, C:/Users/User/Desktop/project locally
    project_root = Path(__file__).resolve().parents[3]

    path_from_project_root = project_root / candidate_path
    if path_from_project_root.exists():
        return path_from_project_root

    path_from_video_pipeline_root = project_root / "video_pipeline" / candidate_path
    if path_from_video_pipeline_root.exists():
        return path_from_video_pipeline_root

    print(f"[S3] Tried path 1: {path_from_project_root}")
    print(f"[S3] Tried path 2: {path_from_video_pipeline_root}")

    return path_from_project_root


def upload_image_to_s3(image_path, event_id, camera_id):
    """Upload representative image to S3 and return the S3 object key."""

    resolved_path = resolve_image_path(image_path)
    print(f"[S3] Raw image path: {image_path}")
    print(f"[S3] Resolved image path: {resolved_path}")
    if resolved_path is None:
        print(f"[S3] Image path is missing for event {event_id}")
        return None

    if not resolved_path.exists():
        print(f"[S3] Image not found: {resolved_path}")
        return None

    s3_key = f"{S3_IMAGE_PREFIX}{camera_id}/event_{event_id}_{resolved_path.name}"

    try:
        s3_client.upload_file(
            str(resolved_path),
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