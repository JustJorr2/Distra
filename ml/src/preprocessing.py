from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from src.config import (
    CATEGORICAL_FEATURES,
    EXPECTED_OBSERVATIONS,
    FEATURE_COLUMNS,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
)
from src.utils import print_section


def classify_impact(value):
    """
    Mengklasifikasikan dampak bencana berdasarkan jumlah desa terdampak.

    Batas kelas (tetap):
    - Rendah : 0-1 desa
    - Sedang : 2-3 desa
    - Tinggi : >= 4 desa
    """

    if value <= 1:
        return "Dampak Rendah"

    elif value <= 3:
        return "Dampak Sedang"

    else:
        return "Dampak Tinggi"


def create_target_label(dataset):
    """
    Membuat kolom target Dampak berdasarkan batas kelas tetap
    (lihat classify_impact). Batas ditetapkan dari analisis kandidat
    kuantil nilai positif (lihat analyze_class_thresholds).
    """

    dataset = dataset.copy()

    dataset[TARGET_COLUMN] = dataset["Jumlah_Desa_Terdampak"].apply(
        classify_impact
    )

    print_section("HASIL PEMBENTUKAN LABEL DAMPAK")

    print("\nDistribusi kelas:")
    print(dataset[TARGET_COLUMN].value_counts())

    print("\nPersentase kelas:")
    print(
        dataset[TARGET_COLUMN].value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

    return dataset


def validate_dataset(dataset):
    print_section("VALIDASI DATASET HASIL PREPROCESSING")

    # 1. Ukuran dataset
    print("\nUkuran dataset:")
    print(f"Jumlah baris : {dataset.shape[0]}")
    print(f"Jumlah kolom : {dataset.shape[1]}")

    # 2. Missing value
    print("\nMissing values:")
    print(dataset.isnull().sum())

    # 3. Data duplikat (seluruh kolom dan kunci observasi)
    duplicate_count = dataset.duplicated().sum()
    duplicate_key_count = dataset.duplicated(subset=FEATURE_COLUMNS).sum()

    print("\nData duplikat:")
    print(f"Seluruh kolom           : {duplicate_count}")
    print(f"Kecamatan-Tahun-Bencana : {duplicate_key_count}")

    # 4. Kesesuaian label dengan jumlah desa
    print("\nValidasi label berdasarkan jumlah desa:")
    print(
        dataset.groupby(TARGET_COLUMN)["Jumlah_Desa_Terdampak"]
        .agg(["min", "max", "count"])
    )

    # 5. Tipe data
    print("\nTipe data:")
    print(dataset.dtypes)

    # 6. Status validasi
    print("\nStatus validasi:")

    if dataset.isnull().sum().sum() == 0:
        print("Tidak terdapat missing value.")
    else:
        print("Terdapat missing value.")

    if duplicate_count == 0 and duplicate_key_count == 0:
        print("Tidak terdapat data duplikat.")
    else:
        print(
            f"Terdapat data duplikat "
            f"(seluruh kolom: {duplicate_count}, "
            f"kunci observasi: {duplicate_key_count})."
        )

    if len(dataset) == EXPECTED_OBSERVATIONS:
        print(f"Jumlah observasi sesuai: {EXPECTED_OBSERVATIONS} data.")
    else:
        print(f"Jumlah observasi tidak sesuai: {len(dataset)}.")

    return dataset


def prepare_features_target(dataset):
    """
    Memisahkan fitur (X) dan target (y) untuk pemodelan Random Forest.
    Jumlah_Desa_Terdampak tidak termasuk fitur (mencegah data leakage).
    """

    X = dataset[FEATURE_COLUMNS].copy()
    y = dataset[TARGET_COLUMN].copy()

    print_section("PEMISAHAN FITUR DAN TARGET")

    print("\nFitur X:")
    print(X.head())

    print("\nTarget y:")
    print(y.head())

    print("\nUkuran fitur:")
    print(X.shape)

    print("\nUkuran target:")
    print(y.shape)

    print("\nKolom fitur:")
    print(X.columns.tolist())

    return X, y


def build_preprocessor():
    """
    Preprocessor tunggal untuk seluruh evaluasi:
    One-Hot Encoding untuk fitur kategorik, Tahun dipertahankan numerik.

    - sparse_threshold=0      : keluaran dense (setara encode_features lama).
    - verbose_feature_names_out=False : nama fitur tanpa prefix
      (Kecamatan_..., Jenis_Bencana_..., Tahun) untuk feature importance.
    """

    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            (
                "numerical",
                "passthrough",
                NUMERICAL_FEATURES,
            ),
        ],
        sparse_threshold=0,
        verbose_feature_names_out=False,
    )