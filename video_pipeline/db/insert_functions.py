def insert_video(cursor, video_name, camera_name, video_path, duration_sec, fps, total_frames):
    """Insert video metadata into videos table."""
    query = """
    INSERT INTO videos (video_name, camera_name, video_path, duration_sec, fps, total_frames)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (video_name, camera_name, video_path, duration_sec, fps, total_frames))
    return cursor.lastrowid


def insert_frame(cursor, video_id, file_name, file_path, camera_id,
                 frame_size_kb, resolution, brightness, blur_score, motion_level):
    print("INSERT FRAME DEBUG:", video_id, file_name, frame_size_kb, resolution, brightness, blur_score, motion_level)
    """Insert saved frame metadata with features into frames table."""
    query = """
    INSERT INTO frames (
        video_id, file_name, file_path, camera_id,
        frame_size_kb, resolution, brightness, blur_score, motion_level
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        video_id, file_name, file_path, camera_id,
        frame_size_kb, resolution, brightness, blur_score, motion_level
    ))
    return cursor.lastrowid


def insert_detection(cursor, frame_id, object_type, confidence, x, y, w, h):
    """Insert detected object into detections table."""
    query = """
    INSERT INTO detections
    (frame_id, object_type, confidence, bbox_x, bbox_y, bbox_width, bbox_height)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (frame_id, object_type, confidence, x, y, w, h))

def insert_performance_metrics(cursor, frame_id, inference_ms, processing_ms,
                               db_insert_ms, cpu_percent, memory_mb):
    """Insert runtime performance metrics into performance_metrics table."""
    query = """
    INSERT INTO performance_metrics (
        frame_id, inference_ms, processing_ms,
        db_insert_ms, cpu_percent, memory_mb
    )
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        frame_id, inference_ms, processing_ms,
        db_insert_ms, cpu_percent, memory_mb
    ))