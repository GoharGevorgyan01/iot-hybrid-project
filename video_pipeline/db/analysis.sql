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