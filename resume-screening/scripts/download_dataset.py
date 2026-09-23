"""
Download the Kaggle Resume Dataset.

Dataset: "Resume Dataset" by Snehaan Bhawal
URL: https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset

Prerequisites:
    1. Install the Kaggle CLI: pip install kaggle
    2. Create a Kaggle API token:
       - Go to https://www.kaggle.com/settings → API → Create New Token
       - This downloads a `kaggle.json` file
    3. Place `kaggle.json` in:
       - Windows: C:\\Users\\<username>\\.kaggle\\kaggle.json
       - Linux/Mac: ~/.kaggle/kaggle.json
    4. Run this script: python scripts/download_dataset.py

Usage:
    python scripts/download_dataset.py [--output-dir data/raw]
"""

import argparse
import os
import sys
import zipfile


def download_dataset(output_dir: str = "data/raw") -> None:
    """Download and extract the Kaggle Resume Dataset."""
    dataset_slug = "snehaanbhawal/resume-dataset"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("ERROR: kaggle package not installed. Run: pip install kaggle")
        sys.exit(1)

    # Check for kaggle.json
    kaggle_dir = os.path.join(os.path.expanduser("~"), ".kaggle")
    kaggle_json = os.path.join(kaggle_dir, "kaggle.json")
    if not os.path.exists(kaggle_json):
        print(
            f"ERROR: Kaggle credentials not found at {kaggle_json}\n"
            "Instructions:\n"
            "  1. Go to https://www.kaggle.com/settings → API → Create New Token\n"
            "  2. Place the downloaded kaggle.json in:\n"
            f"     {kaggle_dir}/\n"
            "  3. Re-run this script."
        )
        sys.exit(1)

    print(f"Authenticating with Kaggle API ...")
    api = KaggleApi()
    api.authenticate()

    print(f"Downloading dataset '{dataset_slug}' to '{output_dir}' ...")
    api.dataset_download_files(dataset_slug, path=output_dir, unzip=False)

    # Unzip
    zip_files = [f for f in os.listdir(output_dir) if f.endswith(".zip")]
    for zf in zip_files:
        zip_path = os.path.join(output_dir, zf)
        print(f"Extracting {zf} ...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(output_dir)
        os.remove(zip_path)

    print(f"Dataset downloaded and extracted to '{output_dir}'.")
    print("Files:")
    for f in os.listdir(output_dir):
        fpath = os.path.join(output_dir, f)
        size_mb = os.path.getsize(fpath) / (1024 * 1024) if os.path.isfile(fpath) else 0
        print(f"  {f} ({size_mb:.1f} MB)" if os.path.isfile(fpath) else f"  {f}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Kaggle Resume Dataset")
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Directory to save the dataset (default: data/raw)",
    )
    args = parser.parse_args()
    download_dataset(args.output_dir)
