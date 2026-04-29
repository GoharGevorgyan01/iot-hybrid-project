CREATE DATABASE fire_smoke_db;
USE fire_smoke_db;
CREATE TABLE frames (
    frame_id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255),
    file_path TEXT,
    frame_size_kb FLOAT,
    resolution VARCHAR(50),
    brightness FLOAT,
    blur_score FLOAT,
    motion_level FLOAT,
    camera_id VARCHAR(50)
);
CREATE TABLE cameras (
    camera_id VARCHAR(50) PRIMARY KEY,
    location VARCHAR(100),
    fps INT,
    status VARCHAR(20)
);

CREATE TABLE detections (
    detection_id INT AUTO_INCREMENT PRIMARY KEY,
    frame_id INT,
    object_type ENUM('fire','smoke'),
    confidence FLOAT,
    bbox_x FLOAT,
    bbox_y FLOAT,
    bbox_width FLOAT,
    bbox_height FLOAT,
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id)
);
SELECT * FROM detections;

CREATE TABLE network_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,  -- Յուրաքանչյուր network measurement-ի unique ID
    frame_id INT,                               -- Կապը frames table-ի հետ, ցույց է տալիս ո՞ր frame-ի համար է տվյալ measurement-ը
    latency_ms FLOAT,                           -- Frame-ի փոխանցման ուշացումը milliseconds-ով
    packet_loss FLOAT,                          -- Packet-ների կորուստը transmission-ի ժամանակ (%)
    bandwidth_usage_kb FLOAT,                   -- Որքան KB տվյալ է փոխանցվել տվյալ frame-ի համար
    qos_level INT,                              -- QoS մակարդակը (0 = best effort, 1 = at least once, 2 = exactly once)
    FOREIGN KEY (frame_id) REFERENCES frames(frame_id)  -- Foreign key կապ՝ հստակ ցույց է տալիս, որ measurement-ը առնչվում է կոնկրետ frame-ին
);
SELECT * FROM network_metrics;
CREATE TABLE model_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- Unique ID
    model_version VARCHAR(50),                -- Model version, օրինակ YOLOv8-small
    precision_score FLOAT,                     -- Precision metric
    recall_score FLOAT,                        -- Recall metric
    f1_score FLOAT,                            -- F1 score
    accuracy FLOAT,                            -- Total accuracy
    evaluation_date DATE                        -- Evaluation ամսաթիվը
);
SELECT * FROM model_performance;


SELECT * FROM cameras;
SHOW CREATE TABLE frames;
SELECT COUNT(*) FROM frames;
DELETE FROM frames;
COMMIT;
SELECT * FROM frames;
SELECT * FROM frames
limit 5;
DELETE FROM frames;

