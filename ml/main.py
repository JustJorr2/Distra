
from sklearn.ensemble import RandomForestClassifier

from src.data_loader import (
    load_excel,
    extract_main_dataset,
    analyze_distribution,
    analyze_class_thresholds,
)

from sklearn.model_selection import train_test_split
from src.visualization import visualize_distribution
from src.preprocessing import (create_target_label, validate_dataset, prepare_features_target,  encode_features)

# def export_dataset(dataset):
#     output_path = "ml/data/processed/dataset_300_observasi.xlsx"

#     dataset.to_excel(
#         output_path,
#         index=False,
#         sheet_name="Dataset Bencana"
#     )

#     print("\nDataset berhasil diekspor!")
#     print(f"Lokasi file: {output_path}")
    # export_dataset(dataset)


def main():

    excel_data = load_excel()

    dataset = extract_main_dataset(excel_data)

    # Analisis statistik deskriptif.
    analyze_distribution(dataset)

    # Visualisasi distribusi.
    visualize_distribution(dataset)

    # Analisis kandidat batas kelas.
    analyze_class_thresholds(dataset)

    dataset = create_target_label(dataset)

    validate_dataset(dataset)

    # Pemisahan fitur dan target
    X, y = prepare_features_target(dataset)

    # Pembagian training dan testing
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Encoding
    X_train, X_test, encoder = encode_features(
        X_train,
        X_test
    )

    print("\n" + "=" * 60)
    print("PELATIHAN MODEL RANDOM FOREST")
    print("=" * 60)

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    print("\nModel berhasil dilatih.")
    print(f"Jumlah decision tree : {model.n_estimators}")
    print(f"Jumlah fitur        : {model.n_features_in_}")
    print(f"Jumlah data training: {len(X_train)}")

if __name__ == "__main__":
    main()
