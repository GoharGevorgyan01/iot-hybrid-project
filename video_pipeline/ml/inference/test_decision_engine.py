import pandas as pd

from inference_engine import MLDecisionEngine
from network_policy import simulate_network_metrics, assign_qos


DATASET_PATH = "video_pipeline/ml/training/event_dataset_labeled.csv"


def main():
    """Test ML decision engine with one dataset sample."""

    df = pd.read_csv(DATASET_PATH)

    engine = MLDecisionEngine()

    sample = df.iloc[0].to_dict()

    decision = engine.predict(sample)
    network_metrics = simulate_network_metrics()
    qos = assign_qos(decision, network_metrics)

    print("ML decision:", decision)
    print("Network metrics:", network_metrics)
    print("Assigned QoS:", qos)

    if decision == "DROP":
        action = "Do not publish. Save locally only."
    elif decision == "SEND_METADATA":
        action = "Publish JSON metadata only."
    else:
        action = "Publish JSON + image and trigger alert."

    print("Final action:", action)


if __name__ == "__main__":
    main()