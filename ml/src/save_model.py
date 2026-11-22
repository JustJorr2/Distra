
import json
from pathlib import Path

import joblib
import sklearn

from src.data_loader import extract_main_dataset, load_excel
from src.modeling import build_baseline_pipeline
from src.preprocessing import create_target_label, prepare_features_target
from src.config import CLASS_LABELS, FEATURE_COLUMNS, TARGET_COLUMN


def save_final_model():
    print("=" * 60)
    print("FINAL MODEL TRAINING")
    print("=" * 60)

    # 1. Load dataset
    excel_data = load_excel()
    dataset = extract_main_dataset(excel_data)
    dataset = create_target_label(dataset)

    # 2. Prepare features and target
    X, y = prepare_features_target(dataset)

    print(f"\nTotal observations : {len(X)}")
    print(f"Features         : {FEATURE_COLUMNS}")
    print(f"Target           : {TARGET_COLUMN}")

    # 3. Build final pipeline
    model = build_baseline_pipeline()

    # 4. Train using the entire dataset
    print("\nTraining final Random Forest model...")
    model.fit(X, y)

    print("Training completed.")

    # 5. Create output directory
    project_dir = Path(__file__).resolve().parent.parent
    model_dir = project_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    # 6. Save complete pipeline
    model_path = model_dir / "random_forest_final.joblib"
    joblib.dump(model, model_path)

    # 7. Save model metadata
    metadata = {
        "model_name": "Random Forest",
        "model_type": "classification",
        "training_samples": len(X),
        "features": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
        "class_labels": CLASS_LABELS,
        "random_state": 42,
        "n_estimators": 100,
        "class_weight": "balanced",
        "sklearn_version": sklearn.__version__,
    }

    metadata_path = model_dir / "model_metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    # 8. Display results
    print("\n" + "=" * 60)
    print("FINAL MODEL SAVED")
    print("=" * 60)
    print(f"Model    : {model_path}")
    print(f"Metadata : {metadata_path}")
    print(f"Samples  : {len(X)}")
    print(f"Classes  : {CLASS_LABELS}")


if __name__ == "__main__":
    save_final_model()
