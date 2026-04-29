import os
import requests
from datetime import datetime
from typing import Any, Dict, Optional


def format_qos(qos: object) -> str:
    """Format QoS value for Telegram alert."""

    qos_str = str(qos)

    if qos_str == "0":
        return "LOW (0)"
    if qos_str == "1":
        return "MEDIUM (1)"
    if qos_str == "2":
        return "HIGH (2)"

    return qos_str

def build_alert_message(event_data: Dict[str, Any], s3_image_key: Optional[str] = None) -> str:
    """Build Telegram message text for a critical SEND_FULL event."""

    event_time = event_data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    camera_id = event_data.get("camera_id", "N/A")
    event_type = event_data.get("type", event_data.get("event_type", "FIRE"))
    confidence = event_data.get("confidence", "N/A")
    consecutive_frames = event_data.get("consecutive_frames", "N/A")
    decision = event_data.get("decision", "SEND_FULL")
    qos = event_data.get("qos", event_data.get("qos_level", "N/A"))
    event_id = event_data.get("event_id", "N/A")
    risk_score = event_data.get("risk_score", "N/A")

    return (
        "🔥 FIRE ALERT\n\n"
        f"📅 Time: {event_time}\n"
        f"🎥 Camera: {camera_id}\n"
        f"🎯 Type: {event_type}\n"
        f"📊 Confidence: {confidence}\n"
        f"📈 Risk score: {risk_score}\n"
        f"🔥 Fire persistence ratio: {consecutive_frames}\n"
        f"📡 QoS: {format_qos(qos)}\n\n"
        f"⚡ Decision: {decision}\n"
        f"🗂 Event ID: {event_id}\n"
        f"☁️ S3 Key: {s3_image_key or 'N/A'}"
    )


def send_alert(event_data: Dict[str, Any], s3_image_key: Optional[str] = None) -> bool:
    """Send text-only Telegram alert."""

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[Telegram] TELEGRAM_TOKEN or TELEGRAM_CHAT_ID is missing")
        return False

    message = build_alert_message(event_data, s3_image_key)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("[Telegram] Text alert sent successfully")
            return True

        print(f"[Telegram] Text alert failed: {response.status_code} - {response.text}")
        return False

    except requests.RequestException as error:
        print(f"[Telegram] Text alert request error: {error}")
        return False


def send_photo_alert(
    event_data: Dict[str, Any],
    image_url: str,
    s3_image_key: Optional[str] = None,
) -> bool:
    """Send Telegram photo alert using an image URL."""

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[Telegram] TELEGRAM_TOKEN or TELEGRAM_CHAT_ID is missing")
        return False

    caption = build_alert_message(event_data, s3_image_key)
    url = f"https://api.telegram.org/bot{token}/sendPhoto"

    payload = {
        "chat_id": chat_id,
        "photo": image_url,
        "caption": caption,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)

        if response.status_code == 200:
            print("[Telegram] Photo alert sent successfully")
            return True

        print(f"[Telegram] Photo alert failed: {response.status_code} - {response.text}")
        return False

    except requests.RequestException as error:
        print(f"[Telegram] Photo alert request error: {error}")
        return False


def send_critical_alert(
    event_data: Dict[str, Any],
    s3_image_key: Optional[str] = None,
    image_url: Optional[str] = None,
) -> bool:
    """
    Send the best available Telegram alert.

    If image_url exists, send photo + caption.
    If image_url is missing or photo sending fails, send text-only alert.
    """

    if image_url:
        photo_sent = send_photo_alert(event_data, image_url, s3_image_key)

        if photo_sent:
            return True

        print("[Telegram] Falling back to text-only alert")

    return send_alert(event_data, s3_image_key)