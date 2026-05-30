"""Skill discovery and progressive disclosure."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class SkillRecord:
    name: str
    description: str
    path: Path
    source_repo: str | None = None
    source_url: str | None = None
    license_note: str | None = None


def parse_frontmatter(content: str) -> dict[str, str]:
    match = _FRONTMATTER.match(content)
    if not match:
        return {}
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


class SkillRegistry:
    def __init__(self, skills_dir: Path, manifest_path: Path | None = None) -> None:
        self.skills_dir = skills_dir
        self.manifest_path = manifest_path

    def discover(self) -> list[SkillRecord]:
        records: list[SkillRecord] = []
        for skill_md in sorted(self.skills_dir.glob("**/SKILL.md")):
            content = skill_md.read_text(encoding="utf-8")
            meta = parse_frontmatter(content)
            name = meta.get("name", skill_md.parent.name)
            description = meta.get("description", "")
            records.append(
                SkillRecord(
                    name=name,
                    description=description,
                    path=skill_md,
                )
            )
        if self.manifest_path and self.manifest_path.exists():
            records.extend(self._load_manifest())
        return records

    def load_body(self, skill_name: str) -> str:
        for record in self.discover():
            if record.name == skill_name:
                return record.path.read_text(encoding="utf-8")
        raise KeyError(f"Skill not found: {skill_name}")

    def catalog_for_prompt(self) -> str:
        lines = ["Available skills (name — description):"]
        for record in self.discover():
            lines.append(f"- {record.name} — {record.description}")
        return "\n".join(lines)

    def _load_manifest(self) -> list[SkillRecord]:
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        records: list[SkillRecord] = []
        for entry in data.get("skills", []):
            path = self.skills_dir / entry["relative_path"]
            if not path.exists():
                continue
            records.append(
                SkillRecord(
                    name=entry["name"],
                    description=entry.get("description", ""),
                    path=path,
                    source_repo=entry.get("source_repo"),
                    source_url=entry.get("source_url"),
                    license_note=entry.get("license_note"),
                )
            )
        return records
