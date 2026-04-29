import os
from collections import Counter

DATASET_ROOT = r"C:\Users\User\Documents\hmo\tez\smoke-fire-dataset\data"
SUBSETS = ["train", "val", "test"]

CLASS_NAMES = {
    "0": "fire",
    "1": "smoke"
}

def analyze_subset(subset_name):
    images_path = os.path.join(DATASET_ROOT, subset_name, "images")
    labels_path = os.path.join(DATASET_ROOT, subset_name, "labels")

    image_files = [
        f for f in os.listdir(images_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ] if os.path.exists(images_path) else []

    label_files = [
        f for f in os.listdir(labels_path)
        if f.lower().endswith(".txt")
    ] if os.path.exists(labels_path) else []

    class_counter = Counter()
    labeled_images = 0

    for label_file in label_files:
        label_path = os.path.join(labels_path, label_file)

        with open(label_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if lines:
            labeled_images += 1

        for line in lines:
            parts = line.split()
            if len(parts) >= 1:
                class_id = parts[0]
                class_name = CLASS_NAMES.get(class_id, f"unknown_class_{class_id}")
                class_counter[class_name] += 1

    print(f"\n===== {subset_name.upper()} =====")
    print(f"Images: {len(image_files)}")
    print(f"Label files: {len(label_files)}")
    print(f"Labeled images: {labeled_images}")
    print("Class distribution:")
    for class_name, count in class_counter.items():
        print(f"  {class_name}: {count}")

def main():
    print("Dataset analysis started...")
    for subset in SUBSETS:
        analyze_subset(subset)
    print("\nDataset analysis finished.")

if __name__ == "__main__":
    main()