from src.utils import print_section

VALUE = "Jumlah_Desa_Terdampak"


def analyze_impact_patterns(dataset):
    """
    Analisis eksploratif pola dampak berdasarkan kecamatan,
    jenis bencana, dan tahun. Statistik per tahun dan per jenis bencana
    sudah dicakup oleh analyze_distribution (data_loader.py).
    """

    # ------------------------------------------------------------
    # Pola kecamatan x jenis bencana
    # ------------------------------------------------------------
    print_section("ANALISIS POLA KECAMATAN DAN JENIS BENCANA")

    impact_pattern = dataset.pivot_table(
        index="Kecamatan",
        columns="Jenis_Bencana",
        values=VALUE,
        aggfunc="mean",
        fill_value=0
    )

    print("\nRata-rata desa terdampak pada setiap kecamatan dan jenis bencana:")
    print(impact_pattern.round(2))

    high_impact_pattern = dataset.pivot_table(
        index="Kecamatan",
        columns="Jenis_Bencana",
        values="Dampak",
        aggfunc=lambda x: (x == "Dampak Tinggi").sum(),
        fill_value=0
    )

    print("\nJumlah kategori Dampak Tinggi pada setiap kecamatan dan jenis bencana:")
    print(high_impact_pattern)
    
    total_pattern = dataset.pivot_table(
        index="Kecamatan",
        columns="Jenis_Bencana",
        values=VALUE,
        aggfunc="sum",
        fill_value=0
    )

    print("\nTotal desa terdampak pada setiap kecamatan dan jenis bencana:")
    print(total_pattern)

    # ------------------------------------------------------------
    # Dampak per kecamatan
    # ------------------------------------------------------------
    print_section("ANALISIS DAMPAK BERDASARKAN KECAMATAN")

    impact_by_district = (
        dataset.groupby("Kecamatan")[VALUE]
        .agg(["count", "mean", "sum", "max"])
        .sort_values("mean", ascending=False)
    )

    print("\nStatistik dampak per kecamatan:")
    print(impact_by_district.round(2))

    print_section("DISTRIBUSI KELAS DAMPAK PER KECAMATAN")

    district_class_distribution = (
        dataset.groupby(["Kecamatan", "Dampak"])
        .size()
        .unstack(fill_value=0)
    )

    print("\nJumlah kelas dampak pada setiap kecamatan:")
    print(district_class_distribution)

    # ------------------------------------------------------------
    # Dampak per tahun
    # ------------------------------------------------------------
    print_section("RATA-RATA DESA TERDAMPAK BERDASARKAN TAHUN DAN JENIS BENCANA")

    yearly_disaster_impact = (
        dataset.groupby(["Tahun", "Jenis_Bencana"])[VALUE]
        .mean()
        .unstack()
    )

    print("\nRata-rata jumlah desa terdampak:")
    print(yearly_disaster_impact.round(2))

    print_section("DISTRIBUSI KELAS DAMPAK BERDASARKAN TAHUN")

    yearly_distribution = (
        dataset.groupby(["Tahun", "Dampak"])
        .size()
        .unstack(fill_value=0)
    )

    print("\nJumlah data setiap kelas per tahun:")
    print(yearly_distribution)

    yearly_percentage = (
        yearly_distribution
        .div(yearly_distribution.sum(axis=1), axis=0)
        .mul(100)
    )

    print("\nPersentase kelas setiap tahun:")
    print(yearly_percentage.round(2))