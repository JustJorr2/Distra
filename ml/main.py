
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

    X, y, encoder = encode_features(dataset)

    # export_dataset(dataset)
    
    # Pembagian data training dan testing
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print("\n" + "=" * 60)
    print("PEMBAGIAN DATA TRAINING DAN TESTING")
    print("=" * 60)

    print(f"Jumlah data training : {len(X_train)}")
    print(f"Jumlah data testing  : {len(X_test)}")

    print("\nDistribusi target training:")
    print(y_train.value_counts())

    print("\nDistribusi target testing:")
    print(y_test.value_counts())

if __name__ == "__main__":
    main()
