import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline

from src.config import (
    CLASS_LABELS,
    N_ESTIMATORS,
    N_SPLITS,
    RANDOM_STATE,
    TEMPORAL_TEST_YEAR,
    TEST_SIZE,
)
from src.preprocessing import build_preprocessor
from src.utils import print_section


def build_baseline_pipeline():
    """Pipeline Random Forest Baseline (model final penelitian)."""

    return Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", RandomForestClassifier(
            n_estimators=N_ESTIMATORS,
            class_weight="balanced",
            random_state=RANDOM_STATE
        ))
    ])


def evaluate_model(y_true, y_pred):
    """Mencetak accuracy, macro F1, classification report, dan confusion matrix."""

    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(
        y_true,
        y_pred,
        labels=CLASS_LABELS,
        average="macro",
        zero_division=0
    )

    print(f"\nAccuracy : {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"Macro F1 : {macro_f1:.4f}")

    print("\nClassification Report:")
    print(classification_report(
        y_true,
        y_pred,
        labels=CLASS_LABELS,
        zero_division=0
    ))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred, labels=CLASS_LABELS))

    return {"accuracy": accuracy, "macro_f1": macro_f1}


def run_holdout_evaluation(X, y):
    """
    Evaluasi Random Forest Baseline dengan random train-test split
    (80:20, stratified). Mengembalikan model terlatih dan jumlah data training.
    """

    print_section("EVALUASI RANDOM FOREST BASELINE (HOLD-OUT 80:20)")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(f"\nData training : {len(X_train)} observasi")
    print(f"Data testing  : {len(X_test)} observasi")

    model = build_baseline_pipeline()
    model.fit(X_train, y_train)

    evaluate_model(y_test, model.predict(X_test))

    return model, len(X_train)


def run_cross_validation(X, y):
    """Stratified 5-Fold Cross-Validation pada seluruh data."""

    print_section("CROSS-VALIDATION")

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    results = cross_validate(
        build_baseline_pipeline(),
        X,
        y,
        cv=cv,
        scoring={
            "accuracy": "accuracy",
            "precision_macro": "precision_macro",
            "recall_macro": "recall_macro",
            "f1_macro": "f1_macro"
        },
        n_jobs=-1
    )

    fold_scores = pd.DataFrame(
        {
            "Accuracy": results["test_accuracy"],
            "Precision": results["test_precision_macro"],
            "Recall": results["test_recall_macro"],
            "Macro F1": results["test_f1_macro"],
        },
        index=pd.RangeIndex(1, N_SPLITS + 1, name="Fold")
    )

    print("\nHasil setiap Fold:")
    print(fold_scores.round(4).to_string())

    # ddof=0 agar standar deviasi sama dengan hasil sebelumnya (numpy .std()).
    summary = pd.DataFrame({
        "Mean": fold_scores.mean(),
        "Std": fold_scores.std(ddof=0)
    })

    print_section("RATA-RATA CROSS-VALIDATION")
    print(summary.round(4).to_string())


def run_temporal_validation(X, y):
    """Training pada tahun < 2025 (2020, 2021, 2024), testing pada tahun 2025."""

    print_section("TEMPORAL VALIDATION (TRAIN 2020, 2021, 2024 | TEST 2025)")

    train_mask = X["Tahun"] < TEMPORAL_TEST_YEAR
    test_mask = X["Tahun"] == TEMPORAL_TEST_YEAR

    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]

    print("\nPembagian Dataset Temporal:")
    print(f"Data Training : {len(X_train)} observasi "
          f"(tahun {sorted(X_train['Tahun'].unique())})")
    print(f"Data Testing  : {len(X_test)} observasi "
          f"(tahun {sorted(X_test['Tahun'].unique())})")

    print("\nDistribusi kelas data testing:")
    print(y_test.value_counts())

    model = build_baseline_pipeline()
    model.fit(X_train, y_train)

    print_section("HASIL EVALUASI TEMPORAL")
    evaluate_model(y_test, model.predict(X_test))


def _feature_group(feature_name):
    """Kelompok asal fitur hasil encoding. Error jika nama tidak dikenali."""

    # Menghapus prefix ColumnTransformer, misalnya:
    # categorical__Kecamatan_Kakas -> Kecamatan_Kakas
    # numerical__Tahun -> Tahun
    feature_name = feature_name.split("__", maxsplit=1)[-1]

    if feature_name.startswith("Kecamatan_"):
        return "Kecamatan"

    if feature_name.startswith("Jenis_Bencana_"):
        return "Jenis Bencana"

    if feature_name == "Tahun":
        return "Tahun"

    raise ValueError(f"Fitur tidak dikenali: {feature_name}")


def analyze_feature_importance(model, n_train):
    """
    Feature importance (impurity-based) dari model baseline hasil hold-out.
    Menunjukkan kontribusi prediktif, bukan hubungan sebab-akibat.
    """

    print_section("FEATURE IMPORTANCE RANDOM FOREST")

    classifier = model.named_steps["classifier"]
    feature_names = model.named_steps["preprocessor"].get_feature_names_out()

    importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": classifier.feature_importances_
    }).sort_values(by="Importance", ascending=False)

    print("\nRanking Feature Importance:")
    print(importance_df.to_string(index=False))

    print("\n10 Fitur Paling Berpengaruh:")
    print(importance_df.head(10).to_string(index=False))

    print_section("FEATURE IMPORTANCE BERDASARKAN KELOMPOK")

    importance_df["Group"] = importance_df["Feature"].apply(_feature_group)

    grouped_importance = (
        importance_df.groupby("Group")["Importance"]
        .sum()
        .sort_values(ascending=False)
    )

    print("\nImportance setiap kelompok fitur:")
    for group, importance in grouped_importance.items():
        print(f"{group:<20}: {importance:.4f} ({importance * 100:.2f}%)")

    print("\nInformasi model:")
    print(f"Jumlah decision tree : {classifier.n_estimators}")
    print(f"Jumlah fitur         : {classifier.n_features_in_}")
    print(f"Jumlah data training : {n_train}")