
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns


# Direktori penyimpanan grafik
BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"


def visualize_distribution(dataset):

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")

    # =====================================
    # 1. HISTOGRAM
    # =====================================

    plt.figure(figsize=(9, 5))

    sns.histplot(
        data=dataset,
        x="Jumlah_Desa_Terdampak",
        bins=range(15),
        discrete=True
    )

    plt.title("Distribusi Jumlah Desa Terdampak Bencana")
    plt.xlabel("Jumlah Desa Terdampak")
    plt.ylabel("Frekuensi")
    plt.xticks(range(14))
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / "distribusi_jumlah_desa.png",
        dpi=300
    )

    plt.show()
    plt.close()

    # =====================================
    # 2. BOXPLOT
    # =====================================

    plt.figure(figsize=(9, 5))

    sns.boxplot(
        data=dataset,
        x="Jenis_Bencana",
        y="Jumlah_Desa_Terdampak"
    )

    plt.title("Distribusi Jumlah Desa Terdampak Berdasarkan Jenis Bencana")
    plt.xlabel("Jenis Bencana")
    plt.ylabel("Jumlah Desa Terdampak")
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / "boxplot_jenis_bencana.png",
        dpi=300
    )

    plt.show()
    plt.close()

    # =====================================
    # 3. BAR CHART
    # =====================================

    disaster_mean = (
        dataset.groupby("Jenis_Bencana")[
            "Jumlah_Desa_Terdampak"
        ]
        .mean()
        .reset_index()
    )

    plt.figure(figsize=(9, 5))

    sns.barplot(
        data=disaster_mean,
        x="Jenis_Bencana",
        y="Jumlah_Desa_Terdampak"
    )

    plt.title("Rata-rata Desa Terdampak Berdasarkan Jenis Bencana")
    plt.xlabel("Jenis Bencana")
    plt.ylabel("Rata-rata Jumlah Desa Terdampak")
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR / "rata_rata_jenis_bencana.png",
        dpi=300
    )

    plt.show()
    plt.close()

    print("\nVisualisasi berhasil dibuat.")
    print(f"Lokasi penyimpanan: {REPORT_DIR}")
