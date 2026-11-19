
from pathlib import Path
import pandas as pd

# Menentukan direktori utama project ML
BASE_DIR = Path(__file__).resolve().parent.parent

# Lokasi file Excel
DATA_PATH = BASE_DIR / "data" / "raw" / "data_bencana_minahasa.xlsx"


def load_excel():
    """
    Membaca workbook Excel dan menampilkan
    seluruh nama sheet yang tersedia.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {DATA_PATH}"
        )

    excel_data = pd.ExcelFile(DATA_PATH)

    print("=" * 60)
    print("DAFTAR SHEET DATASET")
    print("=" * 60)

    for index, sheet in enumerate(excel_data.sheet_names, start=1):
        print(f"{index}. {sheet}")

    return excel_data


def inspect_sheet(excel_data, sheet_name):
    """
    Membaca dan menampilkan informasi dasar
    dari sheet Excel yang dipilih.
    """

    df = pd.read_excel(
        excel_data,
        sheet_name=sheet_name,
        header=None
    )

    print("\n" + "=" * 60)
    print(f"PEMERIKSAAN SHEET: {sheet_name}")
    print("=" * 60)

    print("\nUkuran dataset:")
    print(f"Jumlah baris  : {df.shape[0]}")
    print(f"Jumlah kolom  : {df.shape[1]}")

    print("\n10 baris pertama:")
    print(df.head(10).to_string(index=False, header=False))

    print("\nTipe data setiap kolom:")
    print(df.dtypes.to_string())

    print("\nJumlah nilai kosong setiap kolom:")
    print(df.isnull().sum().to_string())

    return df


def extract_main_dataset(excel_data):
    """
    Mengambil data kecamatan dari sheet utama
    dan mengubahnya menjadi format long.
    """

    sheet_name = "Desa Terdampak Bencana (4.3.3)"

    df = pd.read_excel(
        excel_data,
        sheet_name=sheet_name,
        header=None
    )

    # Mengambil baris data kecamatan saja.
    # Baris Excel 6-30 = indeks Python 5-29.
    data = df.iloc[5:30].copy()

    # Menentukan nama kolom berdasarkan struktur Excel.
    columns = [
        "Kecamatan",
        "Banjir_2020",
        "Banjir_2021",
        "Banjir_2024",
        "Banjir_2025",
        "Gempa Bumi_2020",
        "Gempa Bumi_2021",
        "Gempa Bumi_2024",
        "Gempa Bumi_2025",
        "Tanah Longsor_2020",
        "Tanah Longsor_2021",
        "Tanah Longsor_2024",
        "Tanah Longsor_2025"
    ]

    data.columns = columns

    # Mengubah kolom jumlah menjadi tipe numerik.
    value_columns = columns[1:]

    for column in value_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Mengubah format wide menjadi long.
    long_data = data.melt(
        id_vars=["Kecamatan"],
        var_name="Jenis_Tahun",
        value_name="Jumlah_Desa_Terdampak"
    )

    # Memisahkan nama bencana dan tahun.
    long_data[["Jenis_Bencana", "Tahun"]] = (
        long_data["Jenis_Tahun"]
        .str.rsplit("_", n=1, expand=True)
    )

    long_data["Tahun"] = long_data["Tahun"].astype(int)

    # Menghapus kolom sementara.
    long_data = long_data.drop(
        columns=["Jenis_Tahun"]
    )

    # Mengatur urutan kolom.
    long_data = long_data[
        [
            "Kecamatan",
            "Tahun",
            "Jenis_Bencana",
            "Jumlah_Desa_Terdampak"
        ]
    ]

    # Mengurutkan data.
    long_data = long_data.sort_values(
        by=["Kecamatan", "Tahun", "Jenis_Bencana"]
    ).reset_index(drop=True)

    return long_data


def analyze_distribution(dataset):
    """
    Menganalisis distribusi jumlah desa terdampak.
    """

    print("\n" + "=" * 70)
    print("STATISTIK DESKRIPTIF")
    print("=" * 70)

    print(
        dataset["Jumlah_Desa_Terdampak"]
        .describe()
        .to_string()
    )

    print("\n" + "=" * 70)
    print("DISTRIBUSI FREKUENSI JUMLAH DESA TERDAMPAK")
    print("=" * 70)

    frequency = (
        dataset["Jumlah_Desa_Terdampak"]
        .value_counts()
        .sort_index()
    )

    print(frequency.to_string())

    print("\n" + "=" * 70)
    print("STATISTIK BERDASARKAN JENIS BENCANA")
    print("=" * 70)

    disaster_stats = (
        dataset.groupby("Jenis_Bencana")[
            "Jumlah_Desa_Terdampak"
        ]
        .agg([
            "count",
            "min",
            "max",
            "mean",
            "median",
            "std"
        ])
    )

    print(disaster_stats.to_string())

    print("\n" + "=" * 70)
    print("STATISTIK BERDASARKAN TAHUN")
    print("=" * 70)

    year_stats = (
        dataset.groupby("Tahun")[
            "Jumlah_Desa_Terdampak"
        ]
        .agg([
            "count",
            "min",
            "max",
            "mean",
            "median"
        ])
    )

    print(year_stats.to_string())


def analyze_class_thresholds(dataset):
    """
    Menganalisis kandidat batas kelas berdasarkan
    distribusi nilai positif.
    """

    values = dataset["Jumlah_Desa_Terdampak"]

    # Memisahkan nilai nol dan nilai positif.
    zero_data = values[values == 0]
    positive_data = values[values > 0]

    print("\n" + "=" * 70)
    print("ANALISIS KANDIDAT BATAS KELAS")
    print("=" * 70)

    print(f"\nTotal observasi       : {len(values)}")
    print(f"Observasi bernilai 0  : {len(zero_data)}")
    print(f"Observasi positif     : {len(positive_data)}")

    # Statistik nilai positif.
    print("\nSTATISTIK NILAI POSITIF")
    print(positive_data.describe().to_string())

    # Persentil untuk kandidat pembagian tiga kelas.
    quantiles = positive_data.quantile(
        [1/3, 2/3]
    )

    lower_limit = quantiles.iloc[0]
    upper_limit = quantiles.iloc[1]

    print("\nKANDIDAT BATAS BERDASARKAN QUANTILE")
    print(f"Batas kuantil pertama : {lower_limit}")
    print(f"Batas kuantil kedua   : {upper_limit}")

    # Menghitung jumlah observasi setiap kandidat kelas.
    low = values[values <= lower_limit]

    medium = values[
        (values > lower_limit) &
        (values <= upper_limit)
    ]

    high = values[values > upper_limit]

    print("\nDISTRIBUSI KANDIDAT KELAS")
    print(f"Dampak Rendah  : {len(low)}")
    print(f"Dampak Sedang  : {len(medium)}")
    print(f"Dampak Tinggi  : {len(high)}")

    # Frekuensi nilai positif.
    print("\nFREKUENSI NILAI POSITIF")

    print(
        positive_data.value_counts()
        .sort_index()
        .to_string()
    )

    # Persentase setiap kandidat kelas.
    print("\nPERSENTASE KANDIDAT KELAS")

    for name, count in [
        ("Dampak Rendah", len(low)),
        ("Dampak Sedang", len(medium)),
        ("Dampak Tinggi", len(high))
    ]:
        percentage = count / len(values) * 100

        print(
            f"{name}: {percentage:.2f}%"
        )


