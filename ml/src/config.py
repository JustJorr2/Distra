"""Konstanta penelitian. Satu tempat untuk semua nilai yang dipakai berulang."""

RANDOM_STATE = 42
N_ESTIMATORS = 100
N_SPLITS = 5
TEST_SIZE = 0.2
TEMPORAL_TEST_YEAR = 2025
EXPECTED_OBSERVATIONS = 300

TARGET_COLUMN = "Dampak"
FEATURE_COLUMNS = ["Kecamatan", "Tahun", "Jenis_Bencana"]
CATEGORICAL_FEATURES = ["Kecamatan", "Jenis_Bencana"]
NUMERICAL_FEATURES = ["Tahun"]

CLASS_LABELS = [
    "Dampak Rendah",
    "Dampak Sedang",
    "Dampak Tinggi",
]