import mysql.connector

def get_connection():
    """Create MySQL database connection."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="esgogiknem1",  
        database="iot_video_pipeline"
    )