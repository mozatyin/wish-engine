"""Domain Configuration — defines an expert's behavior through data, not code."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProblemType:
    name: str
    keywords: list[str]
    severity: str
    approach: str


@dataclass
class DomainConfig:
    domain: str
    name: str
    core_principle: str
    problem_types: list[ProblemType]
    forbidden_phrases: list[str]
    dos: list[str]
    donts: list[str]
    soul_search_strategy: str
    age_adaptations: dict[str, str] = field(default_factory=dict)


def load_domain(path: str | Path) -> DomainConfig:
    data = json.loads(Path(path).read_text())
    return DomainConfig(
        domain=data["domain"],
        name=data.get("name", data["domain"]),
        core_principle=data.get("core_principle", ""),
        problem_types=[
            ProblemType(name=k, keywords=v.get("keywords", []),
                       severity=v.get("severity", "medium"),
                       approach=v.get("approach", ""))
            for k, v in data.get("problem_types", {}).items()
        ],
        forbidden_phrases=data.get("forbidden_phrases", []),
        dos=data.get("dos", []),
        donts=data.get("donts", []),
        soul_search_strategy=data.get("soul_search_strategy", ""),
        age_adaptations=data.get("age_adaptations", {}),
    )


def load_all_domains(config_dir: str | Path) -> dict[str, DomainConfig]:
    configs = {}
    for f in sorted(Path(config_dir).glob("*.json")):
        try:
            cfg = load_domain(f)
            configs[cfg.domain] = cfg
        except Exception:
            pass
    return configs
