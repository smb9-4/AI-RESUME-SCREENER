import json
import re
from pathlib import Path
from typing import TypedDict

_JDS_PATH = Path(__file__).parent / "data" / "jds" / "jds.json"

SUPPORTED_ROLES = ("data_analyst", "data_scientist", "software_engineer")


class JobDescription(TypedDict):
    id: str
    role: str
    title: str
    company: str
    location: str
    description: str


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_jds(
    *,
    roles: list[str] | None = None,
    jds_path: Path | None = None,
) -> list[JobDescription]:
    path = jds_path or _JDS_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"JD dataset not found at {path}. "
            "Run: python fetch_kaggle_jds.py"
        )

    with path.open(encoding="utf-8") as f:
        records: list[JobDescription] = json.load(f)

    if roles:
        role_set = {role.lower() for role in roles}
        unknown = role_set - set(SUPPORTED_ROLES)
        if unknown:
            raise ValueError(
                f"Unsupported role(s): {', '.join(sorted(unknown))}. "
                f"Supported: {', '.join(SUPPORTED_ROLES)}"
            )
        records = [jd for jd in records if jd["role"] in role_set]

    return records


def get_jd_by_id(jd_id: str, *, jds_path: Path | None = None) -> JobDescription:
    records = load_jds(jds_path=jds_path)
    for jd in records:
        if jd["id"] == jd_id:
            return jd
    raise ValueError(
        f"JD id not found: {jd_id}. "
        f"Supported roles: {', '.join(SUPPORTED_ROLES)}"
    )


def resolve_jd(
    *,
    jd_id: str | None = None,
    role: str | None = None,
    jds_path: Path | None = None,
) -> JobDescription:
    if jd_id:
        return get_jd_by_id(jd_id, jds_path=jds_path)

    roles = [role] if role else None
    records = load_jds(roles=roles, jds_path=jds_path)
    if not records:
        role_hint = f" for role '{role}'" if role else ""
        raise ValueError(f"No job descriptions found in dataset{role_hint}.")

    return records[0]
