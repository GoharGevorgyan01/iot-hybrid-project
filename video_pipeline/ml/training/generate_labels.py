
from pathlib import Path
import pandas as pd

# Resolve project root
CURRENT_FILE = Path(__file__).resolve()
VIDEO_PIPELINE_DIR = CURRENT_FILE.parents[1]

INPUT_PATH = VIDEO_PIPELINE_DIR / "ml" / "event_dataset_raw.csv"
OUTPUT_PATH = VIDEO_PIPELINE_DIR / "ml" / "event_dataset_labeled.csv"
def assign_label(row):
    """
    Rule-based pseudo-labeling logic for transmission decision.
    """

    # Strong, stable fire event → SEND_FULL
    if (
        row["max_confidence"] >= 0.85
        and row["consecutive_fire_ratio"] >= 0.75
        and row["detection_density_5s"] >= 0.10
        and row["fire_smoke_ratio"] >= 0.50
        and row["blur_score"] < 700
    ):
        return "SEND_FULL"

    # Moderate or uncertain event → SEND_METADATA
    if (
        row["max_confidence"] >= 0.65
        and row["detection_density_5s"] >= 0.04
        and row["blur_score"] < 1000
    ):
        return "SEND_METADATA"

    # Weak / noisy event → DROP
    return "DROP"
def main():
    df = pd.read_csv(INPUT_PATH)

    df["transmission_decision"] = df.apply(assign_label, axis=1)

    df.to_csv(OUTPUT_PATH, index=False)

    print("✅ Labeled dataset saved to:", OUTPUT_PATH)
    print("\nLabel distribution:")
    print(df["transmission_decision"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    main()