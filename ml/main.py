import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from src.data_loader import (
    load_excel,
    extract_main_dataset,
    analyze_distribution,
    analyze_class_thresholds,
)

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

from sklearn.model_selection import (train_test_split, StratifiedKFold, cross_validate, GridSearchCV, RandomizedSearchCV)
from src.visualization import visualize_distribution
from src.preprocessing import (create_target_label, validate_dataset, prepare_features_target,  encode_features, OneHotEncoder)
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

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

    # ==========================================
    # ANALISIS POLA KECAMATAN DAN JENIS BENCANA
    # ==========================================

    print("\n" + "=" * 60)
    print("ANALISIS POLA KECAMATAN DAN JENIS BENCANA")
    print("=" * 60)

    # Rata-rata jumlah desa terdampak
    impact_pattern = dataset.pivot_table(
        index="Kecamatan",
        columns="Jenis_Bencana",
        values="Jumlah_Desa_Terdampak",
        aggfunc="mean",
        fill_value=0
    )

    print("\nRata-rata desa terdampak pada setiap kecamatan dan jenis bencana:")
    print(impact_pattern.round(2))


    # ==========================================
    # DISTRIBUSI KELAS DAMPAK
    # ==========================================

    class_pattern = dataset.pivot_table(
        index="Kecamatan",
        columns="Jenis_Bencana",
        values="Dampak",
        aggfunc=lambda x: (x == "Dampak Tinggi").sum(),
        fill_value=0
    )

    print("\nJumlah kelas Dampak Tinggi pada setiap kecamatan dan jenis bencana:")
    print(class_pattern)


    # ==========================================
    # TOTAL DESA TERDAMPAK
    # ==========================================

    total_pattern = dataset.pivot_table(
        index="Kecamatan",
        columns="Jenis_Bencana",
        values="Jumlah_Desa_Terdampak",
        aggfunc="sum",
        fill_value=0
    )

    print("\nTotal desa terdampak pada setiap kecamatan dan jenis bencana:")
    print(total_pattern)

    # ==========================================
    # ANALISIS JUMLAH DESA TERDAMPAK PER TAHUN
    # ==========================================

    print("\n" + "=" * 60)
    print("ANALISIS JUMLAH DESA TERDAMPAK PER TAHUN")
    print("=" * 60)

    yearly_impact = dataset.groupby("Tahun")["Jumlah_Desa_Terdampak"].agg(
        ["count", "mean", "median", "min", "max", "sum"]
    )

    print("\nStatistik jumlah desa terdampak per tahun:")
    print(yearly_impact.round(2))

    # ==========================================
    # ANALISIS POLA DAMPAK BERDASARKAN KECAMATAN
    # ==========================================

    print("\n" + "=" * 60)
    print("ANALISIS DAMPAK BERDASARKAN KECAMATAN")
    print("=" * 60)

    impact_by_district = (
        dataset.groupby("Kecamatan")["Jumlah_Desa_Terdampak"]
        .agg(["count", "mean", "sum", "max"])
        .sort_values("mean", ascending=False)
    )

    print("\nStatistik dampak per kecamatan:")
    print(impact_by_district.round(2))


    # ==========================================
    # ANALISIS POLA DAMPAK BERDASARKAN JENIS BENCANA
    # ==========================================

    print("\n" + "=" * 60)
    print("ANALISIS DAMPAK BERDASARKAN JENIS BENCANA")
    print("=" * 60)

    impact_by_disaster = (
        dataset.groupby("Jenis_Bencana")["Jumlah_Desa_Terdampak"]
        .agg(["count", "mean", "median", "sum", "max"])
        .sort_values("mean", ascending=False)
    )

    print("\nStatistik dampak per jenis bencana:")
    print(impact_by_disaster.round(2))


    # ==========================================
    # DISTRIBUSI KELAS DAMPAK PER KECAMATAN
    # ==========================================

    print("\n" + "=" * 60)
    print("DISTRIBUSI KELAS DAMPAK PER KECAMATAN")
    print("=" * 60)

    district_class_distribution = (
        dataset.groupby(["Kecamatan", "Dampak"])
        .size()
        .unstack(fill_value=0)
    )

    print("\nJumlah kelas dampak pada setiap kecamatan:")
    print(district_class_distribution)


    # ==========================================
    # ANALISIS BERDASARKAN JENIS BENCANA
    # ==========================================

    print("\n" + "=" * 60)
    print("RATA-RATA DESA TERDAMPAK BERDASARKAN TAHUN DAN JENIS BENCANA")
    print("=" * 60)

    yearly_disaster_impact = (
        dataset.groupby(["Tahun", "Jenis_Bencana"])["Jumlah_Desa_Terdampak"]
        .mean()
        .unstack()
    )

    print("\nRata-rata jumlah desa terdampak:")
    print(yearly_disaster_impact.round(2))


    # ==========================================
    # DISTRIBUSI KELAS DAMPAK BERDASARKAN TAHUN
    # ==========================================

    print("\n" + "=" * 60)
    print("DISTRIBUSI KELAS DAMPAK BERDASARKAN TAHUN")
    print("=" * 60)

    yearly_distribution = (
        dataset.groupby(["Tahun", "Dampak"])
        .size()
        .unstack(fill_value=0)
    )

    print("\nJumlah data setiap kelas per tahun:")
    print(yearly_distribution)

    yearly_percentage = (
        yearly_distribution.div(
            yearly_distribution.sum(axis=1),
            axis=0
        ) * 100
    )

    print("\nPersentase kelas setiap tahun:")
    print(yearly_percentage.round(2))


    validate_dataset(dataset)

    # Pemisahan fitur dan target
    X, y = prepare_features_target(dataset)

    # ==========================================
    # PREPROCESSING CONFIGURATION
    # ==========================================

    categorical_features = ["Kecamatan", "Jenis_Bencana"]
    numerical_features = ["Tahun"]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features
            ),
            (
                "numerical",
                "passthrough",
                numerical_features
            )
        ]
    )


    # ==========================================
    # TEMPORAL VALIDATION (TRAIN 2020-2024, TEST 2025)
    # ==========================================

    print("\n" + "=" * 60)
    print("TEMPORAL VALIDATION")
    print("=" * 60)

    # Memisahkan data berdasarkan tahun
    train_mask = X["Tahun"] < 2025
    test_mask = X["Tahun"] == 2025

    X_temporal_train = X[train_mask]
    X_temporal_test = X[test_mask]

    y_temporal_train = y[train_mask]
    y_temporal_test = y[test_mask]

    # Menampilkan ukuran dataset
    print("\nPembagian Dataset Temporal:")
    print(f"Data Training : {len(X_temporal_train)} observasi")
    print(f"Data Testing : {len(X_temporal_test)} observasi")

    print("\nTahun Training:")
    print(sorted(X_temporal_train["Tahun"].unique()))

    print("\nTahun Testing:")
    print(sorted(X_temporal_test["Tahun"].unique()))

    # ==========================================
    # PREPROCESSING DAN MODEL
    # ==========================================

    temporal_model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced"
        ))
    ])

    # Training menggunakan data historis
    temporal_model.fit(
        X_temporal_train,
        y_temporal_train
    )

    # Prediksi data 2025
    y_temporal_pred = temporal_model.predict(
        X_temporal_test
    )

    # ==========================================
    # EVALUASI TEMPORAL
    # ==========================================

    print("\n" + "=" * 60)
    print("HASIL EVALUASI TEMPORAL")
    print("=" * 60)

    temporal_accuracy = accuracy_score(
        y_temporal_test,
        y_temporal_pred
    )

    print(f"\nAccuracy : {temporal_accuracy:.4f}")
    print(f"Accuracy : {temporal_accuracy * 100:.2f}%")

    print("\nClassification Report:")
    print(classification_report(
        y_temporal_test,
        y_temporal_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ],
        zero_division=0
    ))

    print("\nConfusion Matrix:")
    print(confusion_matrix(
        y_temporal_test,
        y_temporal_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ]
    ))



    # ==============================
    # CROSS-VALIDATION
    # ==============================

    print("\n" + "=" * 60)
    print("CROSS-VALIDATION")
    print("=" * 60)

    # Pipeline preprocessing + Random Forest
    cv_model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced"
        ))
    ])

    # Stratified 5-Fold Cross-Validation
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    # Metrik evaluasi
    scoring = {
        "accuracy": "accuracy",
        "precision_macro": "precision_macro",
        "recall_macro": "recall_macro",
        "f1_macro": "f1_macro"
    }

    # Jalankan Cross-Validation
    cv_results = cross_validate(
        cv_model,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=-1
    )

    # Tampilkan hasil setiap fold
    print("\nHasil setiap Fold:")

    for i in range(5):
        print(f"\nFold {i + 1}:")
        print(f"Accuracy     : {cv_results['test_accuracy'][i]:.4f}")
        print(f"Precision    : {cv_results['test_precision_macro'][i]:.4f}")
        print(f"Recall       : {cv_results['test_recall_macro'][i]:.4f}")
        print(f"Macro F1    : {cv_results['test_f1_macro'][i]:.4f}")

    # Rata-rata hasil Cross-Validation
    print("\n" + "=" * 60)
    print("RATA-RATA CROSS-VALIDATION")
    print("=" * 60)

    print(
        f"Mean Accuracy  : "
        f"{cv_results['test_accuracy'].mean():.4f}"
    )

    print(
        f"Mean Precision : "
        f"{cv_results['test_precision_macro'].mean():.4f}"
    )

    print(
        f"Mean Recall    : "
        f"{cv_results['test_recall_macro'].mean():.4f}"
    )

    print(
        f"Mean Macro F1  : "
        f"{cv_results['test_f1_macro'].mean():.4f}"
    )

    print("\nStandar Deviasi:")
    print(
        f"Accuracy Std  : "
        f"{cv_results['test_accuracy'].std():.4f}"
    )

    print(
        f"Macro F1 Std  : "
        f"{cv_results['test_f1_macro'].std():.4f}"
    )


    # Pembagian training dan testing
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )


    # ==============================
    # FINAL MODEL OPTIMIZATION
    # ==============================

    print("\n" + "=" * 60)
    print("FINAL RANDOM FOREST OPTIMIZATION")
    print("=" * 60)

    # ==========================================
    # BASELINE MODEL
    # ==========================================

    baseline_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced"
        ))
    ])

    baseline_pipeline.fit(X_train, y_train)

    y_baseline_pred = baseline_pipeline.predict(X_test)

    baseline_accuracy = accuracy_score(
        y_test,
        y_baseline_pred
    )

    baseline_report = classification_report(
        y_test,
        y_baseline_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ],
        output_dict=True,
        zero_division=0
    )

    baseline_f1 = baseline_report["macro avg"]["f1-score"]

    # ==========================================
    # PARAMETER SEARCH
    # ==========================================

    param_distributions = {
        "classifier__n_estimators": [100, 200, 300],
        "classifier__max_depth": [None, 4, 6, 8],
        "classifier__max_features": ["sqrt", 0.5, 1.0],
        "classifier__min_samples_split": [2, 4, 6],
        "classifier__min_samples_leaf": [1, 2, 3]
    }

    optimization_cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    optimization_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            random_state=42,
            class_weight="balanced"
        ))
    ])

    randomized_search = RandomizedSearchCV(
        estimator=optimization_pipeline,
        param_distributions=param_distributions,
        n_iter=60,
        scoring="f1_macro",
        cv=optimization_cv,
        random_state=42,
        n_jobs=-1,
        verbose=1,
        return_train_score=True
    )

    # ==========================================
    # TRAINING OPTIMIZED MODEL
    # ==========================================

    randomized_search.fit(X_train, y_train)

    optimized_model = randomized_search.best_estimator_

    y_optimized_pred = optimized_model.predict(X_test)

    optimized_accuracy = accuracy_score(
        y_test,
        y_optimized_pred
    )

    optimized_report = classification_report(
        y_test,
        y_optimized_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ],
        output_dict=True,
        zero_division=0
    )

    optimized_f1 = optimized_report["macro avg"]["f1-score"]

    # ==========================================
    # OPTIMIZATION RESULTS
    # ==========================================

    print("\n" + "=" * 60)
    print("HASIL HYPERPARAMETER OPTIMIZATION")
    print("=" * 60)

    print("\nParameter Terbaik:")
    print(randomized_search.best_params_)

    print("\nBest CV Macro F1:")
    print(f"{randomized_search.best_score_:.4f}")

    print("\nClassification Report Optimized Model:")
    print(classification_report(
        y_test,
        y_optimized_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ],
        zero_division=0
    ))

    print("\nConfusion Matrix Optimized Model:")
    print(confusion_matrix(
        y_test,
        y_optimized_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ]
    ))

    # ==========================================
    # BASELINE VS OPTIMIZED
    # ==========================================

    comparison = pd.DataFrame({
        "Model": [
            "Random Forest Baseline",
            "Random Forest Optimized"
        ],
        "Accuracy": [
            baseline_accuracy,
            optimized_accuracy
        ],
        "Macro F1": [
            baseline_f1,
            optimized_f1
        ]
    })

    print("\n" + "=" * 60)
    print("PERBANDINGAN BASELINE DAN OPTIMIZED MODEL")
    print("=" * 60)

    print(comparison.round(4).to_string(index=False))

    print("\nSelisih Accuracy:")
    print(f"{(optimized_accuracy - baseline_accuracy) * 100:+.2f}%")

    print("\nSelisih Macro F1:")
    print(f"{(optimized_f1 - baseline_f1) * 100:+.2f}%")

    print("\nOptimasi model selesai.")

    
    # ==============================
    # FINAL HYPERPARAMETER OPTIMIZATION
    # ==============================

    print("\n" + "=" * 60)
    print("FINAL RANDOM FOREST OPTIMIZATION")
    print("=" * 60)

    # Pipeline preprocessing dan Random Forest
    optimization_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            random_state=42,
            class_weight="balanced"
        ))
    ])

    # Ruang pencarian parameter
    param_distributions = {
        "classifier__n_estimators": [100, 200, 300],
        "classifier__max_depth": [None, 4, 6, 8],
        "classifier__max_features": ["sqrt", 0.5, 1.0],
        "classifier__min_samples_split": [2, 4, 6],
        "classifier__min_samples_leaf": [1, 2, 3]
    }

    # Stratified 5-Fold CV
    optimization_cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    # Randomized Search
    randomized_search = RandomizedSearchCV(
        estimator=optimization_pipeline,
        param_distributions=param_distributions,
        n_iter=60,
        scoring="f1_macro",
        cv=optimization_cv,
        random_state=42,
        n_jobs=-1,
        verbose=1,
        return_train_score=True
    )

    # Jalankan optimasi pada data training
    randomized_search.fit(X_train, y_train)

    # ==============================
    # HASIL OPTIMASI
    # ==============================

    print("\nParameter Terbaik:")
    print(randomized_search.best_params_)

    print("\nBest Cross-Validation Macro F1:")
    print(f"{randomized_search.best_score_:.4f}")

    # Model hasil optimasi
    optimized_model = randomized_search.best_estimator_

    # ==============================
    # EVALUASI FINAL OPTIMIZED MODEL
    # ==============================

    print("\n" + "=" * 60)
    print("EVALUASI FINAL OPTIMIZED RANDOM FOREST")
    print("=" * 60)

    y_optimized_pred = optimized_model.predict(X_test)

    optimized_accuracy = accuracy_score(
        y_test,
        y_optimized_pred
    )

    print(f"\nAccuracy: {optimized_accuracy:.4f}")
    print(f"Accuracy: {optimized_accuracy * 100:.2f}%")

    print("\nClassification Report:")

    print(classification_report(
        y_test,
        y_optimized_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ],
        zero_division=0
    ))

    print("\nConfusion Matrix:")

    print(confusion_matrix(
        y_test,
        y_optimized_pred,
        labels=[
            "Dampak Rendah",
            "Dampak Sedang",
            "Dampak Tinggi"
        ]
    ))

    # ==============================
    # PERBANDINGAN BASELINE VS OPTIMIZED
    # ==============================

    print("\n" + "=" * 60)
    print("PERBANDINGAN MODEL")
    print("=" * 60)

    print(f"Baseline Accuracy   : {baseline_accuracy:.4f}")
    print(f"Optimized Accuracy : {optimized_accuracy:.4f}")

    print(f"Baseline Macro F1  : {baseline_f1:.4f}")
    print(f"Optimized Macro F1 : {optimized_f1:.4f}")

    print("\nSelisih Accuracy:")
    print(f"{(optimized_accuracy - baseline_accuracy) * 100:+.2f}%")

    print("\nSelisih Macro F1:")
    print(f"{(optimized_f1 - baseline_f1) * 100:+.2f}%")

    print("\nOptimasi selesai.")

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

    # ==============================
    # FEATURE IMPORTANCE
    # ==============================

    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE RANDOM FOREST")
    print("=" * 60)

    # Mengambil nilai feature importance
    importance_values = model.feature_importances_

    # Mengambil nama fitur setelah encoding
    feature_names = X_train.columns

    # Menggabungkan nama fitur dan nilai importance
    importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importance_values
    })

    # Mengurutkan berdasarkan importance tertinggi
    importance_df = importance_df.sort_values(
        by="Importance",
        ascending=False
    )

    # Menampilkan seluruh ranking fitur
    print("\nRanking Feature Importance:")
    print(importance_df.to_string(index=False))

    # Menampilkan 10 fitur teratas
    print("\n10 Fitur Paling Berpengaruh:")
    print(importance_df.head(10).to_string(index=False))

    # ==============================
    # GROUPED FEATURE IMPORTANCE
    # ==============================

    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE BERDASARKAN KELOMPOK")
    print("=" * 60)

    # Mengelompokkan fitur berdasarkan kategori aslinya
    importance_df["Group"] = importance_df["Feature"].apply(
        lambda feature:
        "Kecamatan" if feature.startswith("Kecamatan_")
        else "Jenis Bencana" if feature.startswith("Jenis_Bencana_")
        else "Tahun"
    )

    # Menjumlahkan importance dalam setiap kelompok
    grouped_importance = (
        importance_df.groupby("Group")["Importance"]
        .sum()
        .sort_values(ascending=False)
    )

    # Menghitung persentase
    grouped_percentage = grouped_importance * 100

    # Menampilkan hasil
    print("\nImportance setiap kelompok fitur:")

    for group, importance in grouped_importance.items():
        print(
            f"{group:<20}: "
            f"{importance:.4f} ({importance * 100:.2f}%)"
        )

    print("\nModel berhasil dilatih.")
    print(f"Jumlah decision tree : {model.n_estimators}")
    print(f"Jumlah fitur        : {model.n_features_in_}")
    print(f"Jumlah data training: {len(X_train)}")

    # ==========================================
    # EVALUASI MODEL
    # ==========================================

    print("\n" + "=" * 60)
    print("EVALUASI MODEL RANDOM FOREST")
    print("=" * 60)

    # Prediksi data testing
    y_pred = model.predict(X_test)

    # Accuracy
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy: {accuracy:.4f}")
    print(f"Accuracy: {accuracy * 100:.2f}%")

    # Classification Report
    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            zero_division=0
        )
    )

    # Confusion Matrix
    labels = [
        "Dampak Rendah",
        "Dampak Sedang",
        "Dampak Tinggi"
    ]

    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=labels
    )

    print("\nConfusion Matrix:")
    print(cm)

if __name__ == "__main__":
    main()
