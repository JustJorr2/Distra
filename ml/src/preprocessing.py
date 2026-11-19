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