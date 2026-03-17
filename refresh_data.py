"""
refresh_data.py — Auto-download latest Inside Airbnb Austin data
================================================================
Run manually:     python refresh_data.py
Run on schedule:  cron, GitHub Actions, or Streamlit Cloud secrets

Downloads both listings.csv and calendar.csv.gz from Inside Airbnb.
Falls back gracefully if the site is down or URL changes.
"""

import urllib.request
import gzip
import shutil
import os
import json
from datetime import datetime

# Inside Airbnb data URLs for Austin
# These follow the pattern: http://data.insideairbnb.com/united-states/tx/austin/{date}/data/
# The "visualisations" folder has the simplified CSVs we need
BASE_URLS = [
    "https://data.insideairbnb.com/united-states/tx/austin",
]

# Files we want
FILES = {
    "listings": "listings.csv",
    "calendar": "calendar.csv.gz",
    "reviews":  "reviews.csv.gz",       # optional, for future use
}

DATA_DIR = "data"
META_FILE = os.path.join(DATA_DIR, "refresh_meta.json")


def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def get_latest_date_slug():
    """
    Inside Airbnb organizes data by date like /2025-09-08/visualisations/
    We try recent dates to find the latest available snapshot.
    """
    from datetime import timedelta
    today = datetime.now()
    # Try the last 6 months of possible snapshot dates (they publish ~quarterly)
    candidates = []
    for days_back in range(0, 180, 1):
        d = today - timedelta(days=days_back)
        candidates.append(d.strftime("%Y-%m-%d"))
    return candidates


def download_file(url, dest_path, timeout=30):
    """Download a file with basic error handling."""
    try:
        print(f"  Trying: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(dest_path, 'wb') as f:
                shutil.copyfileobj(response, f)
        size = os.path.getsize(dest_path)
        print(f"  ✅ Downloaded: {dest_path} ({size:,} bytes)")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


def decompress_gz(gz_path, csv_path):
    """Decompress a .gz file to .csv"""
    try:
        with gzip.open(gz_path, 'rb') as f_in:
            with open(csv_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"  Decompressed: {csv_path}")
        return True
    except Exception as e:
        print(f"  Decompress failed: {e}")
        return False


def refresh():
    """Main refresh function. Downloads latest data from Inside Airbnb."""
    ensure_dir()
    print("=" * 60)
    print("PriceScope ATX — Data Refresh")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    date_slugs = get_latest_date_slug()
    results = {}

    for file_key, filename in FILES.items():
        if file_key == "reviews":
            continue  # skip reviews for now, not critical

        print(f"\n📥 Downloading {file_key}...")
        dest = os.path.join(DATA_DIR, filename)
        found = False

        for date_slug in date_slugs:
            # Try both the visualisations path and the data path
            urls = [
                f"{BASE_URLS[0]}/{date_slug}/visualisations/{filename}",
                f"{BASE_URLS[0]}/{date_slug}/data/{filename}",
            ]
            for url in urls:
                if download_file(url, dest):
                    found = True
                    results[file_key] = {
                        "url": url, "date": date_slug,
                        "size": os.path.getsize(dest),
                        "downloaded_at": datetime.now().isoformat()
                    }

                    # Decompress .gz files
                    if filename.endswith('.gz'):
                        csv_dest = os.path.join(DATA_DIR, filename.replace('.gz', ''))
                        decompress_gz(dest, csv_dest)
                        results[file_key]["decompressed"] = csv_dest

                    break
            if found:
                break

        if not found:
            print(f"  ⚠️ Could not download {file_key} from any date. Using existing file if available.")
            results[file_key] = {"status": "not_found"}

    # Also copy the local listings file if we have one and didn't download fresh
    if results.get("listings", {}).get("status") == "not_found":
        for fallback in ['listings_1_.csv', 'listings(1).csv', 'listings.csv']:
            if os.path.exists(fallback):
                dest = os.path.join(DATA_DIR, 'listings.csv')
                shutil.copy2(fallback, dest)
                print(f"\n📋 Using local fallback: {fallback} → {dest}")
                results["listings"] = {"source": "local_fallback", "file": fallback}
                break

    # Save metadata
    with open(META_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Refresh complete. Metadata saved to {META_FILE}")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    refresh()
