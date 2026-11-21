"""
ARSIP: hyperparameter optimization (RandomizedSearchCV).

Tidak dipanggil dari main.py. Hasil: Accuracy 61,67%, Macro F1 0,4221,
lebih rendah dari Random Forest Baseline (75%, 0,5420), sehingga baseline
dipilih sebagai model final. File ini hanya untuk dokumentasi/reproduksi.

Jalankan dari folder ml/:  python -m experiments.hyperparameter_search
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    train_test_split,
)
from sklearn.pipeline import Pipeline

from src.config import N_SPLITS, RANDOM_STATE, TEST_SIZE
from src.data_loader import extract_main_dataset, load_excel
from src.modeling import build_baseline_pipeline, evaluate_model
from src.preprocessing import (
    build_preprocessor,
    create_target_label,
    prepare_features_target,
)

PARAM_DISTRIBUTIONS = {
    "classifier__n_estimators": [100, 200, 300],
    "classifier__max_depth": [None, 4, 6, 8],
    "classifier__max_features": ["sqrt", 0.5, 1.0],
    "classifier__min_samples_split": [2, 4, 6],
    "classifier__min_samples_leaf": [1, 2, 3]
}


def main():

    dataset = create_target_label(extract_main_dataset(load_excel()))
    X, y = prepare_features_target(dataset)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print("\n=== BASELINE ===")
    baseline = build_baseline_pipeline().fit(X_train, y_train)
    baseline_metrics = evaluate_model(y_test, baseline.predict(X_test))

    search = RandomizedSearchCV(
        estimator=Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", RandomForestClassifier(
                random_state=RANDOM_STATE,
                class_weight="balanced"
            ))
        ]),
        param_distributions=PARAM_DISTRIBUTIONS,
        n_iter=60,
        scoring="f1_macro",
        cv=StratifiedKFold(
            n_splits=N_SPLITS,
            shuffle=True,
            random_state=RANDOM_STATE
        ),
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1,
        return_train_score=True
    )
    search.fit(X_train, y_train)

    print("\n=== OPTIMIZED ===")
    print("Parameter terbaik:", search.best_params_)
    print(f"Best CV Macro F1: {search.best_score_:.4f}")
    optimized_metrics = evaluate_model(
        y_test,
        search.best_estimator_.predict(X_test)
    )

    print("\n=== SELISIH (Optimized - Baseline) ===")
    print(f"Accuracy: {(optimized_metrics['accuracy'] - baseline_metrics['accuracy']) * 100:+.2f}%")
    print(f"Macro F1: {(optimized_metrics['macro_f1'] - baseline_metrics['macro_f1']) * 100:+.2f}%")


if __name__ == "__main__":
    main()