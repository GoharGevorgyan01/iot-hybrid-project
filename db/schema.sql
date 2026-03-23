DROP DATABASE IF EXISTS fire_smoke_db;
-- ============================================
-- Database for IoT Fire/Smoke Detection System
-- Thesis Project
-- ============================================

CREATE DATABASE IF NOT EXISTS fire_smoke_db;
USE fire_smoke_db;

-- ============================================
-- Table: cameras
-- Stores information about IoT cameras / data sources
-- ============================================
CREATE TABLE IF NOT EXISTS cameras (
    camera_id VARCHAR(50) PRIMARY KEY,  -- Unique camera/device identifier
    location VARCHAR(100),              -- Logical location (lab, warehouse, etc.)
    fps INT,                            -- Frames per second of camera
    status VARCHAR(20)                  -- active / inactive
);

-- ============================================
-- Table: frames
-- Stores extracted features from each image/frame
-- ============================================
CREATE TABLE IF NOT EXISTS frames (
    frame_id INT AUTO_INCREMENT PRIMARY KEY, -- Unique frame ID
    file_name VARCHAR(255),                  -- Image file name
    file_path TEXT,                          -- Path to image file
    frame_size_kb FLOAT,                     -- Image size in KB
    resolution VARCHAR(50),                  -- Resolution (e.g., 1920x1080)
    brightness FLOAT,                        -- Average brightness
    blur_score FLOAT,                        -- Blur metric
    motion_level FLOAT,                      -- Simulated motion level
    camera_id VARCHAR(50),                   -- Source camera/device
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
);

-- ============================================
-- Table: detections
-- Stores YOLO detection results (fire/smoke)
-- ============================================
CREATE TABLE IF NOT EXISTS detections (
    detection_id INT AUTO_INCREMENT PRIMARY KEY,
    frame_id INT,                            -- Related frame
    object_type ENUM('fire','smoke'),        -- Detected object type
    confidence FLOAT,                        -- Detection confidence
    bbox_x FLOAT,                            -- Bounding box X
    bbox_y FLOAT,                            -- Bounding box Y
    bbox_width FLOAT,                        -- Bounding box width
    bbox_height FLOAT,                       -- Bounding box height
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id)
);

-- ============================================
-- Table: network_metrics
-- Stores network conditions for each frame transmission
-- ============================================
CREATE TABLE IF NOT EXISTS network_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    frame_id INT,
    latency_ms FLOAT,                        -- Transmission latency
    packet_loss FLOAT,                       -- Packet loss percentage
    bandwidth_usage_kb FLOAT,                -- Data size transmitted
    qos_level INT,                           -- MQTT QoS level (0,1,2)
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id)
);

-- ============================================
-- Table: model_performance
-- Stores performance metrics for YOLO models
-- Used to compare YOLOv5, YOLOv8, etc.
-- ============================================
CREATE TABLE IF NOT EXISTS model_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_version VARCHAR(50),               -- Model name/version
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    accuracy FLOAT,
    inference_time_ms FLOAT,
    evaluation_date DATE
);

-- ============================================
-- Table: transmission_decisions
-- Stores AI decision engine results
-- Determines how data should be transmitted
-- ============================================
CREATE TABLE IF NOT EXISTS transmission_decisions (
    decision_id INT AUTO_INCREMENT PRIMARY KEY,
    frame_id INT,
    priority_level VARCHAR(20),              -- high / medium / low
    transmission_action VARCHAR(50),         -- send / compress / drop
    selected_qos INT,                        -- MQTT QoS selected
    destination VARCHAR(50),                 -- cloud / edge / local
    reason_text TEXT,                        -- Why decision was made
    alert_flag BOOLEAN,                      -- Should trigger alert?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id)
);

-- ============================================
-- Table: alerts
-- Stores alert/notification events
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    frame_id INT,
    alert_type VARCHAR(50),                  -- fire / smoke / network
    alert_message TEXT,
    severity VARCHAR(20),                    -- low / medium / high
    sent_to VARCHAR(100),                    -- email / telegram / dashboard
    alert_status VARCHAR(20),                -- sent / pending
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id)
);

USE fire_smoke_db;
SHOW TABLES;

ALTER TABLE frames
ADD COLUMN dataset_split VARCHAR(20) AFTER camera_id;
USE fire_smoke_db;

INSERT IGNORE INTO cameras (camera_id, location, fps, status)
VALUES
('camera_1', 'AoF_Source', 30, 'active'),
('camera_2', 'PublicDataset_Source', 25, 'active'),
('camera_3', 'WEB_Source', 20, 'active'),
('camera_unknown', 'Unknown_Source', 15, 'inactive');
-- ==========================================================
-- YOLO Experiment Tracking Schema Update
--
-- This ALTER TABLE extends the model_performance table to store
-- experiment configuration parameters and evaluation metrics
-- for YOLO object detection models.
ALTER TABLE model_performance
ADD COLUMN run_name VARCHAR(100) AFTER model_version,
ADD COLUMN epochs INT AFTER run_name,
ADD COLUMN image_size INT AFTER epochs,
ADD COLUMN batch_size INT AFTER image_size,
ADD COLUMN map50 FLOAT AFTER recall_score,
ADD COLUMN map50_95 FLOAT AFTER map50,
ADD COLUMN dataset_split VARCHAR(20) AFTER inference_time_ms,
ADD COLUMN notes TEXT AFTER dataset_split;
-------------------------------------------
select * 
from cameras;

describe frames;
----------------------------------------
USE fire_smoke_db;

SELECT * FROM cameras;

SELECT COUNT(*) FROM frames;

SELECT dataset_split, COUNT(*) AS total_frames
FROM frames
GROUP BY dataset_split;

SELECT frame_id, file_name, camera_id, dataset_split
FROM frames
LIMIT 20;

SELECT *
FROM frames
LIMIT 5;

SELECT COUNT(*) FROM frames;
SELECT dataset_split, COUNT(*) FROM frames GROUP BY dataset_split;

USE fire_smoke_db;

SELECT COUNT(*) FROM network_metrics;

SELECT qos_level, COUNT(*) AS total_rows
FROM network_metrics
GROUP BY qos_level;

SELECT * FROM network_metrics
LIMIT 10;

select *
from alerts
limit 10;
select *
from cameras
limit 10;
select *
from detections
limit 10;
select *
from frames
limit 10;
select *
from model_performance
limit 10;
select *
from network_metrics
limit 10;
select *
from transmission_decisions
limit 10;