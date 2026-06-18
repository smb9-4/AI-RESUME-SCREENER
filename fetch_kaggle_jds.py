"""Download 50-100 Kaggle job descriptions per role and save to data/jds/jds.json."""

import argparse
import json
import re
from pathlib import Path

import kagglehub
import pandas as pd

OUTPUT_PATH = Path(__file__).parent / "data" / "jds" / "jds.json"
DEFAULT_PER_ROLE = 100

ROLE_SOURCES = {
    "data_analyst": {
        "dataset": "rithikkotha/data-analyst-jobs-dataset",
        "file_glob": "DataAnalyst Jobs.csv",
        "title_col": "Job Title",
        "company_col": "Company Name",
        "location_col": "Location",
        "description_col": "Job Description",
    },
    "data_scientist": {
        "dataset": "christopherkverne/100k-us-tech-jobs-winter-2024",
        "file_glob": "ds_jobs.xlsx",
        "title_col": "title",
        "company_col": "company",
        "location_col": "location",
        "description_col": "cleaned_description",
        "description_fallback_col": "description",
    },
    "software_engineer": {
        "dataset": "christopherkverne/100k-us-tech-jobs-winter-2024",
        "file_glob": "swe_jobs.xlsx",
        "title_col": "title",
        "company_col": "company",
        "location_col": "location",
        "description_col": "cleaned_description",
        "description_fallback_col": "description",
    },
}


def _normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _find_dataset_file(dataset_path: Path, file_glob: str) -> Path:
    matches = list(dataset_path.rglob(file_glob))
    if not matches:
        raise FileNotFoundError(f"Could not find {file_glob} under {dataset_path}")
    return matches[0]


def _load_role_records(role: str, per_role: int) -> list[dict]:
    source = ROLE_SOURCES[role]
    dataset_path = Path(kagglehub.dataset_download(source["dataset"]))
    data_file = _find_dataset_file(dataset_path, source["file_glob"])

    if data_file.suffix.lower() == ".csv":
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    records: list[dict] = []
    for row_index, row in df.iterrows():
        description = _normalize_text(row.get(source["description_col"]))
        if not description and "description_fallback_col" in source:
            description = _normalize_text(row.get(source["description_fallback_col"]))
        if len(description) < 120:
            continue

        title = _normalize_text(row.get(source["title_col"])) or role.replace("_", " ").title()
        company = _normalize_text(row.get(source["company_col"])) or "Unknown"
        location = _normalize_text(row.get(source["location_col"])) or "Unknown"

        records.append(
            {
                "id": f"{role}_{len(records) + 1:04d}",
                "role": role,
                "title": title,
                "company": company,
                "location": location,
                "description": description,
            }
        )
        if len(records) >= per_role:
            break

    if not records:
        raise RuntimeError(f"No usable job descriptions found for role: {role}")

    return records


def fetch_and_save(per_role: int = DEFAULT_PER_ROLE, output_path: Path = OUTPUT_PATH) -> list[dict]:
    all_records: list[dict] = []
    for role in ROLE_SOURCES:
        print(f"Fetching up to {per_role} JDs for {role}...")
        all_records.extend(_load_role_records(role, per_role))
        print(f"  collected {sum(1 for jd in all_records if jd['role'] == role)} records")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_records)} job descriptions to {output_path}")
    return all_records


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Kaggle job descriptions and build the local JD dataset."
    )
    parser.add_argument(
        "--per-role",
        type=int,
        default=DEFAULT_PER_ROLE,
        help=f"Number of JDs to keep per role (default: {DEFAULT_PER_ROLE}).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_PATH),
        help="Output JSON path for normalized job descriptions.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    fetch_and_save(per_role=args.per_role, output_path=Path(args.output))


if __name__ == "__main__":
    main()
