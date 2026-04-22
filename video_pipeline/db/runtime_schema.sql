CREATE DATABASE iot_video_pipeline;
USE iot_video_pipeline;

-- =========================================================
-- TABLE: videos
-- Stores metadata for each processed input video
-- =========================================================
CREATE TABLE videos (
    video_id INT AUTO_INCREMENT PRIMARY KEY,     -- Unique video ID
    video_name VARCHAR(255) NOT NULL,            -- Input video file name
    camera_name VARCHAR(100) NOT NULL,           -- Camera/source name
    video_path TEXT NOT NULL,                    -- Input video path
    duration_sec FLOAT,                          -- Video duration in seconds
    fps FLOAT,                                   -- Frames per second
    total_frames INT,                            -- Total frame count
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Processing time
);
-- =========================================================
-- TABLE: frames
-- Stores metadata for saved video frames
-- =========================================================
CREATE TABLE frames (
    frame_id INT AUTO_INCREMENT PRIMARY KEY,     -- Unique frame ID
    video_id INT,                                -- Reference to videos table
    file_name VARCHAR(255) NOT NULL,             -- Saved frame name
    file_path TEXT NOT NULL,                     -- Saved frame path
    frame_size_kb FLOAT,                         -- File size in KB
    resolution VARCHAR(50),                      -- Frame resolution
    brightness FLOAT,                            -- Brightness feature
    blur_score FLOAT,                            -- Blur feature
    motion_level FLOAT,                          -- Motion feature
    camera_id VARCHAR(50),                       -- Camera/source ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Save time
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- =========================================================
-- TABLE: detections
-- Stores detected objects for each frame
-- =========================================================
CREATE TABLE detections (
    detection_id INT AUTO_INCREMENT PRIMARY KEY, -- Unique detection ID
    frame_id INT,                                -- Reference to frames table
    object_type VARCHAR(50),                     -- Detected object (fire, smoke, etc.)
    confidence FLOAT,                            -- Model confidence
    bbox_x FLOAT,
    bbox_y FLOAT,
    bbox_width FLOAT,
    bbox_height FLOAT,                           -- Bounding box
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id) -- Link to frame
);
-- =========================================================
-- TABLE: performance_metrics
-- Stores runtime performance metrics for each saved frame
-- =========================================================
CREATE TABLE performance_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,     -- Unique metric row ID
    frame_id INT,                                 -- Reference to frames table
    inference_ms FLOAT,                           -- YOLO inference time in ms
    processing_ms FLOAT,                          -- Full frame processing time in ms
    db_insert_ms FLOAT,                           -- Database insert time in ms
    cpu_percent FLOAT,                            -- CPU usage percentage
    memory_mb FLOAT,                              -- RAM usage in MB
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Metric timestamp
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id)
);


