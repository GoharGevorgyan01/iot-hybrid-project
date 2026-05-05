USE iot_video_pipeline;

-- =========================================================
-- SECTION 1: OVERALL SYSTEM PERFORMANCE SUMMARY
-- =========================================================
-- This block provides a global overview of system runtime behavior.
-- Used for high-level performance evaluation in the thesis.
SELECT
    COUNT(*) AS total_measured_frames,
    ROUND(AVG(inference_ms), 2)   AS avg_inference_ms,
    ROUND(MIN(inference_ms), 2)   AS min_inference_ms,
    ROUND(MAX(inference_ms), 2)   AS max_inference_ms,
    ROUND(AVG(processing_ms), 2)  AS avg_processing_ms,
    ROUND(AVG(db_insert_ms), 2)   AS avg_db_insert_ms
FROM performance_metrics;
-- =========================================================
-- SECTION 2: CPU AND MEMORY USAGE ANALYSIS
-- =========================================================
-- Evaluates resource consumption during continuous video processing.
-- Demonstrates feasibility of edge deployment.

SELECT
    ROUND(AVG(cpu_percent), 2) AS avg_cpu_percent,
    ROUND(MAX(cpu_percent), 2) AS max_cpu_percent,
    ROUND(AVG(memory_mb), 2)   AS avg_memory_mb,
    ROUND(MAX(memory_mb), 2)   AS max_memory_mb
FROM performance_metrics;
-- =========================================================
-- SECTION 3: PERFORMANCE PER VIDEO (CAMERA SIMULATION)
-- =========================================================
-- Each video is treated as a separate camera stream.
-- This allows comparison of performance under different conditions.
SELECT
    v.video_name,
    v.camera_name,
    COUNT(pm.metric_id) AS processed_frames,
    ROUND(AVG(pm.inference_ms), 2)  AS avg_inference_ms,
    ROUND(AVG(pm.processing_ms), 2) AS avg_processing_ms,
    ROUND(AVG(pm.cpu_percent), 2)   AS avg_cpu_percent
FROM performance_metrics pm
JOIN frames f ON pm.frame_id = f.frame_id
JOIN videos v ON f.video_id = v.video_id
GROUP BY v.video_name, v.camera_name
ORDER BY avg_processing_ms DESC;
-- =========================================================
-- SECTION 4: BOTTLENECK ANALYSIS
-- =========================================================
-- Identifies which pipeline component contributes most to latency.
SELECT
    ROUND(AVG(inference_ms), 2) AS yolo_inference_ms,
    ROUND(AVG(db_insert_ms), 2) AS db_insert_ms,
    ROUND(
        AVG(processing_ms - inference_ms - db_insert_ms), 2
    ) AS other_processing_overhead_ms
FROM performance_metrics;
-- =========================================================
-- SECTION 5: TEMPORAL STABILITY CHECK
-- =========================================================
-- Used later for correlation with detection history.
-- Provides time-ordered performance behavior.
SELECT
    pm.measured_at,
    pm.inference_ms,
    pm.processing_ms,
    pm.cpu_percent,
    pm.memory_mb
FROM performance_metrics pm
ORDER BY pm.measured_at;
-- =========================================================
-- SECTION 6: OPTIONAL - PERFORMANCE VS DETECTION CONFIDENCE
-- =========================================================
-- Helps study whether high-confidence detections affect performance.
SELECT
    d.object_type,
    ROUND(AVG(pm.inference_ms), 2) AS avg_inference_ms,
    ROUND(AVG(d.confidence), 2)    AS avg_confidence
FROM performance_metrics pm
JOIN frames f ON pm.frame_id = f.frame_id
JOIN detections d ON f.frame_id = d.frame_id
GROUP BY d.object_type;

-------------------------------------------------------------
USE iot_video_pipeline;
-- =========================================
-- Total counts
-- =========================================
-- Total videos processed
SELECT COUNT(*) AS total_videos FROM videos;
-- Total saved frames
SELECT COUNT(*) AS total_frames FROM frames;
-- Total detections
SELECT COUNT(*) AS total_detections FROM detections;

-- =========================================
-- Detection distribution
-- =========================================
-- Count fire vs smoke detections
SELECT object_type, COUNT(*) AS count
FROM detections
GROUP BY object_type;

select count(*) As count
from frames;
SELECT COUNT(*) AS total_detections FROM detections;


-- =========================================
-- Confidence statistics
-- =========================================
-- Average, min, max confidence
SELECT 
    AVG(confidence) AS avg_confidence,
    MIN(confidence) AS min_confidence,
    MAX(confidence) AS max_confidence
FROM detections;

-- =========================================
-- Frames per video
-- =========================================
-- Number of saved frames per video
SELECT v.video_name, COUNT(f.frame_id) AS frame_count
FROM videos v
JOIN frames f ON v.video_id = f.video_id
GROUP BY v.video_name;


-- =========================================
-- Performance metrics summary
-- =========================================
-- Average performance metrics
SELECT 
    AVG(inference_ms) AS avg_inference,
    AVG(processing_ms) AS avg_processing,
    AVG(db_insert_ms) AS avg_db,
    AVG(cpu_percent) AS avg_cpu,
    AVG(memory_mb) AS avg_memory
FROM performance_metrics;

-- =========================================
-- Detection per frame
-- =========================================
-- How many detections per frame
SELECT frame_id, COUNT(*) AS detections_per_frame
FROM detections
GROUP BY frame_id
ORDER BY detections_per_frame DESC
LIMIT 10;

-- ամեն video → քանի frame է պահվել → 1 վայրկյանում միջինը քանիսը
SELECT 
    v.video_name,
    v.camera_name,
    v.duration_sec,
    v.fps,
    v.total_frames,
    COUNT(f.frame_id) AS saved_frames,
    ROUND(COUNT(f.frame_id) / v.duration_sec, 2) AS saved_frames_per_sec
FROM videos v
LEFT JOIN frames f ON v.video_id = f.video_id
GROUP BY 
    v.video_id,
    v.video_name,
    v.camera_name,
    v.duration_sec,
    v.fps,
    v.total_frames;
    
-- Detection density
-- cam01 → fire քանի հատ/sec

SELECT 
    v.video_name,
    d.object_type,
    COUNT(d.detection_id) AS detection_count,
    ROUND(COUNT(d.detection_id) / v.duration_sec, 2) AS detections_per_sec
FROM videos v
JOIN frames f ON v.video_id = f.video_id
JOIN detections d ON f.frame_id = d.frame_id
GROUP BY v.video_name, d.object_type, v.duration_sec;

--------------------
SELECT COUNT(*) FROM frames;
SELECT COUNT(*) FROM detections;
SELECT object_type, COUNT(*) FROM detections GROUP BY object_type;
SELECT video_id, COUNT(*) as frame_count FROM frames GROUP BY video_id;
SELECT frame_id, timestamp FROM frames LIMIT 10;

--------------
-- =========================================================
-- ML FEATURE INSPECTION
-- =========================================================

-- Confidence range
SELECT 
    ROUND(MIN(confidence), 3) AS min_confidence,
    ROUND(AVG(confidence), 3) AS avg_confidence,
    ROUND(MAX(confidence), 3) AS max_confidence
FROM detections;

-- Detection count per frame
SELECT 
    COUNT(*) AS total_frame_groups,
    ROUND(AVG(detection_count), 2) AS avg_detections_per_frame,
    MIN(detection_count) AS min_detections_per_frame,
    MAX(detection_count) AS max_detections_per_frame
FROM (
    SELECT frame_id, COUNT(*) AS detection_count
    FROM detections
    GROUP BY frame_id
) t;

-- Fire/smoke count per frame
SELECT 
    frame_id,
    SUM(object_type = 'fire') AS fire_count,
    SUM(object_type = 'smoke') AS smoke_count,
    COUNT(*) AS object_count,
    ROUND(MAX(confidence), 3) AS max_confidence,
    ROUND(AVG(confidence), 3) AS avg_confidence
FROM detections
GROUP BY frame_id
ORDER BY object_count DESC
LIMIT 20;

-- Bounding box area range
SELECT 
    ROUND(MIN(bbox_width * bbox_height), 2) AS min_bbox_area,
    ROUND(AVG(bbox_width * bbox_height), 2) AS avg_bbox_area,
    ROUND(MAX(bbox_width * bbox_height), 2) AS max_bbox_area
FROM detections;

-- Frame quality ranges
SELECT
    ROUND(MIN(brightness), 2) AS min_brightness,
    ROUND(AVG(brightness), 2) AS avg_brightness,
    ROUND(MAX(brightness), 2) AS max_brightness,
    ROUND(MIN(blur_score), 2) AS min_blur,
    ROUND(AVG(blur_score), 2) AS avg_blur,
    ROUND(MAX(blur_score), 2) AS max_blur,
    ROUND(MIN(motion_level), 2) AS min_motion,
    ROUND(AVG(motion_level), 2) AS avg_motion,
    ROUND(MAX(motion_level), 2) AS max_motion
FROM frames;

-- Saved frames per video
SELECT 
    v.video_name,
    v.duration_sec,
    v.fps,
    v.total_frames,
    COUNT(f.frame_id) AS saved_frames,
    ROUND(COUNT(f.frame_id) / v.duration_sec, 2) AS saved_frames_per_sec
FROM videos v
LEFT JOIN frames f ON v.video_id = f.video_id
GROUP BY v.video_id, v.video_name, v.duration_sec, v.fps, v.total_frames;

-- Detection distribution per video
SELECT 
    v.video_name,
    d.object_type,
    COUNT(*) AS detection_count,
    ROUND(COUNT(*) / v.duration_sec, 2) AS detections_per_sec
FROM videos v
JOIN frames f ON v.video_id = f.video_id
JOIN detections d ON f.frame_id = d.frame_id
GROUP BY v.video_name, d.object_type, v.duration_sec;