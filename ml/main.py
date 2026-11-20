
from src.data_loader import (
    load_excel,
    extract_main_dataset,
    analyze_distribution,
    analyze_class_thresholds,
)

from src.visualization import visualize_distribution
from src.preprocessing import (create_target_label, validate_dataset, prepare_features_target)


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

    X, y = prepare_features_target(dataset)

if __name__ == "__main__":
    main()
