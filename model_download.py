
from huggingface_hub import hf_hub_download
from pathlib import Path

# Folder penyimpanan seluruh model
BASE_DIR = Path("C:/Coding/Model AI/Qwen")

# Daftar model Qwen3 dalam format GGUF Q4_K_M
MODELS = [
    {
        "name": "Qwen3-0.6B",
        "repo": "unsloth/Qwen3-0.6B-GGUF",
        "file": "Qwen3-0.6B-Q4_K_M.gguf"
    },
    {
        "name": "Qwen3-1.7B",
        "repo": "ggml-org/Qwen3-1.7B-GGUF",
        "file": "Qwen3-1.7B-Q4_K_M.gguf"
    },
    {
        "name": "Qwen3-4B",
        "repo": "ggml-org/Qwen3-4B-GGUF",
        "file": "Qwen3-4B-Q4_K_M.gguf"
    }
    # {
    #     "name": "Qwen3-8B",
    #     "repo": "Qwen/Qwen3-8B-GGUF",
    #     "file": "Qwen3-8B-Q4_K_M.gguf"
    # }
]

BASE_DIR.mkdir(parents=True, exist_ok=True)

for model in MODELS:
    print("\n" + "=" * 50)
    print(f"Downloading {model['name']}")
    print("=" * 50)

    try:
        save_dir = BASE_DIR / model["name"]
        save_dir.mkdir(parents=True, exist_ok=True)

        model_path = hf_hub_download(
            repo_id=model["repo"],
            filename=model["file"],
            local_dir=str(save_dir)
        )

        print(f"SUCCESS: {model['name']}")
        print(f"Saved at: {model_path}")

    except Exception as error:
        print(f"FAILED: {model['name']}")
        print(f"Error: {error}")

print("\nAll download tasks completed!")
