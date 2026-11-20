from sklearn.preprocessing import OneHotEncoder
import pandas as pd


def classify_impact(value):
    """
    Mengklasifikasikan dampak bencana berdasarkan
    jumlah desa terdampak.
    """

    if value <= 1:
        return "Dampak Rendah"

    elif value <= 3:
        return "Dampak Sedang"

    else:
        return "Dampak Tinggi"


def create_target_label(dataset):
    """
    Membuat kolom target Dampak berdasarkan
    metode Quantile yang telah ditetapkan.
    """

    dataset = dataset.copy()

    dataset["Dampak"] = dataset["Jumlah_Desa_Terdampak"].apply(
        classify_impact
    )

    print("\n" + "=" * 60)
    print("HASIL PEMBENTUKAN LABEL DAMPAK")
    print("=" * 60)

    print("\nDistribusi kelas:")
    print(dataset["Dampak"].value_counts())

    print("\nPersentase kelas:")
    print(
        dataset["Dampak"].value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

    return dataset

def validate_dataset(dataset):
    print("\n" + "=" * 60)
    print("VALIDASI DATASET HASIL PREPROCESSING")
    print("=" * 60)

    # 1. Informasi ukuran dataset
    print("\nUkuran dataset:")
    print(f"Jumlah baris : {dataset.shape[0]}")
    print(f"Jumlah kolom  : {dataset.shape[1]}")

    # 2. Pemeriksaan missing value
    print("\nMissing values:")
    print(dataset.isnull().sum())

    # 3. Pemeriksaan data duplikat
    duplicate_count = dataset.duplicated().sum()

    print("\nData duplikat:")
    print(duplicate_count)

    # 4. Distribusi target
    print("\nDistribusi target:")
    print(dataset["Dampak"].value_counts())

    # 5. Persentase target
    print("\nPersentase target:")
    print(
        dataset["Dampak"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

    # 6. Pemeriksaan label berdasarkan jumlah desa
    print("\nValidasi label berdasarkan jumlah desa:")
    print(
        dataset.groupby("Dampak")["Jumlah_Desa_Terdampak"]
        .agg(["min", "max", "count"])
    )

    # 7. Informasi tipe data
    print("\nTipe data:")
    print(dataset.dtypes)

    # 8. Validasi kondisi dataset
    print("\nStatus validasi:")

    if dataset.isnull().sum().sum() == 0:
        print("Tidak terdapat missing value.")
    else:
        print("Terdapat missing value.")

    if duplicate_count == 0:
        print("Tidak terdapat data duplikat.")
    else:
        print(f"Terdapat {duplicate_count} data duplikat.")

    if len(dataset) == 300:
        print("Jumlah observasi sesuai: 300 data.")
    else:
        print(f"Jumlah observasi tidak sesuai: {len(dataset)}.")

    return dataset

def prepare_features_target(dataset):
    """
    Memisahkan fitur (X) dan target (y)
    untuk pemodelan Random Forest.
    """

    feature_columns = [
        "Kecamatan",
        "Tahun",
        "Jenis_Bencana"
    ]

    target_column = "Dampak"

    X = dataset[feature_columns].copy()
    y = dataset[target_column].copy()

    print("\n" + "=" * 60)
    print("PEMISAHAN FITUR DAN TARGET")
    print("=" * 60)

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

    print("\nDistribusi target:")
    print(y.value_counts())

    return X, y

def encode_features(X_train, X_test):

    print("\n" + "=" * 60)
    print("ENCODING FITUR")
    print("=" * 60)

    categorical_columns = ["Kecamatan", "Jenis_Bencana"]

    # Encoder hanya mempelajari kategori dari data training
    encoder = OneHotEncoder(
        sparse_output=False,
        handle_unknown="ignore"
    )

    # Fit dan transform data training
    train_encoded = encoder.fit_transform(
        X_train[categorical_columns]
    )

    # Transform data testing menggunakan encoder training
    test_encoded = encoder.transform(
        X_test[categorical_columns]
    )

    # Nama fitur hasil encoding
    encoded_columns = encoder.get_feature_names_out(
        categorical_columns
    )

    # Membuat DataFrame training
    X_train_encoded = pd.DataFrame(
        train_encoded,
        columns=encoded_columns,
        index=X_train.index
    )

    # Membuat DataFrame testing
    X_test_encoded = pd.DataFrame(
        test_encoded,
        columns=encoded_columns,
        index=X_test.index
    )

    # Menambahkan fitur Tahun yang bersifat numerik
    X_train_encoded["Tahun"] = X_train["Tahun"]
    X_test_encoded["Tahun"] = X_test["Tahun"]

    print("\nUkuran data training setelah encoding:")
    print(X_train_encoded.shape)

    print("\nUkuran data testing setelah encoding:")
    print(X_test_encoded.shape)

    print("\nNama fitur:")
    print(X_train_encoded.columns.tolist())

    return X_train_encoded, X_test_encoded, encoder