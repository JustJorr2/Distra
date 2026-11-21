from src.analysis import analyze_impact_patterns
from src.data_loader import (
    analyze_class_thresholds,
    analyze_distribution,
    extract_main_dataset,
    load_excel,
)
from src.modeling import (
    analyze_feature_importance,
    run_cross_validation,
    run_holdout_evaluation,
    run_temporal_validation,
)
from src.preprocessing import (
    create_target_label,
    prepare_features_target,
    validate_dataset,
)
from src.visualization import visualize_distribution


def main():

    # 1. Memuat dataset
    excel_data = load_excel()
    dataset = extract_main_dataset(excel_data)

    # 2. Eksplorasi data (statistik deskriptif per jenis bencana dan tahun)
    analyze_distribution(dataset)
    visualize_distribution(dataset)
    analyze_class_thresholds(dataset)

    # 3. Pembentukan target dan analisis pola dampak
    dataset = create_target_label(dataset)
    analyze_impact_patterns(dataset)

    # 4. Validasi dataset dan pemisahan fitur-target
    validate_dataset(dataset)
    X, y = prepare_features_target(dataset)

    # 5. Evaluasi Random Forest Baseline (model final)
    model, n_train = run_holdout_evaluation(X, y)
    run_cross_validation(X, y)
    run_temporal_validation(X, y)

    # 6. Feature importance
    analyze_feature_importance(model, n_train)


if __name__ == "__main__":
    main()