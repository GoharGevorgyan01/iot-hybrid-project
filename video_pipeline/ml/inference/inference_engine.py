import joblib
import pandas as pd


MODEL_PATH = "video_pipeline/ml/models/final_xgboost_model.pkl"
ENCODER_PATH = "video_pipeline/ml/models/label_encoder.pkl"


FEATURES = [
    "max_confidence",
    "avg_confidence",
    "object_count",
    "fire_smoke_ratio",
    "bbox_area_ratio",
    "detection_density_5s",
    "detection_density_10s",
    "avg_confidence_5s",
    "consecutive_fire_ratio",
    "bbox_area_growth",
    "brightness",
    "blur_score",
    "motion_level",
]


class MLDecisionEngine:
    """Load trained model and predict transmission decision."""

    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.encoder = joblib.load(ENCODER_PATH)

    def predict(self, feature_dict):
        """Predict DROP / SEND_METADATA / SEND_FULL."""
        input_df = pd.DataFrame([feature_dict])[FEATURES]

        prediction_encoded = self.model.predict(input_df)[0]
        prediction_label = self.encoder.inverse_transform([prediction_encoded])[0]

        return prediction_label