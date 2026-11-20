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