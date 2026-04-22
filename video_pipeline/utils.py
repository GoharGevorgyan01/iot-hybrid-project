import cv2
import numpy as np
import os


def compute_brightness(frame):
    """Compute average brightness of the frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def compute_blur(frame):
    """Compute blur score using Laplacian variance."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_resolution(frame):
    """Return resolution as string WIDTHxHEIGHT."""
    h, w = frame.shape[:2]
    return f"{w}x{h}"


def compute_file_size_kb(file_path):
    """Compute file size in KB."""
    size_bytes = os.path.getsize(file_path)
    return float(size_bytes / 1024)


def compute_motion(prev_frame, curr_frame):
    """Compute motion level between two frames."""
    if prev_frame is None:
        return 0.0

    gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(gray1, gray2)
    return float(np.mean(diff))