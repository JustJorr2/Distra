
from src.data_loader import (
    load_excel,
    extract_main_dataset,
    analyze_distribution
)

from src.visualization import visualize_distribution


def main():

    # Membaca dataset
    excel_data = load_excel()

    # Mengekstrak data utama
    dataset = extract_main_dataset(excel_data)

    # Analisis statistik deskriptif
    analyze_distribution(dataset)

    # Membuat visualisasi
    visualize_distribution(dataset)


if __name__ == "__main__":
    main()
