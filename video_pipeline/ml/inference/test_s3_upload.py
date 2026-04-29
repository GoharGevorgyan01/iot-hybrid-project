from s3_uploader import upload_image_to_s3


TEST_IMAGE_PATH = "video_pipeline/output/saved_frames/cam01_frame_77.jpg"

s3_key = upload_image_to_s3(
    image_path=TEST_IMAGE_PATH,
    event_id=0,
    camera_id="cam01"
)

print("S3 key:", s3_key)