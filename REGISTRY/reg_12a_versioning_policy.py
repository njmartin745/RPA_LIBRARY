"""  
REG-12A: Versioning Policy (Milestone 12.2.1)  
  
Single responsibility:  
- Define a deterministic, reviewable versioning policy for:  
  - workflows  
  - selectors  
  - framework  
- Provide SemVer parsing/validation and optional release checks.  
- Provide deterministic renderers (Markdown/JSON) to support governance docs.  
  
This module does not modify any existing build/release pipeline behavior. It is a  
policy definition that can be invoked by CI/build tooling later.  
"""  
  
from __future__ import annotations  
  
from dataclasses import dataclass  
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Literal  
import json  
  
  
__all__ = [  
    "SemVer",  
    "ComponentPolicy",  
    "VersioningPolicy",  
    "parse_semver",  
    "is_valid_semver",  
    "compare_semver",  
    "bump_semver",  
    "get_versioning_policy",  
    "check_release_versions",  
    "render_versioning_policy_markdown",  
    "versioning_policy_to_json",  
    "write_text_file",  
    "write_versioning_policy_markdown",  
]  
  
  
@dataclass(frozen=True, slots=True, order=True)  
class SemVer:  
    major: int  
    minor: int  
    patch: int  
  
    def __str__(self) -> str:  
        return f"{self.major}.{self.minor}.{self.patch}"  
  
  
@dataclass(frozen=True, slots=True)  
class ComponentPolicy:  
    component_id: str  # e.g. "workflow", "selectors", "framework"  
    scheme: str  # e.g. "semver"  
    production_rules: List[str]  
    bump_guidance: Dict[str, List[str]]  # keys: "major"/"minor"/"patch"  
  
  
@dataclass(frozen=True, slots=True)  
class VersioningPolicy:  
    policy_id: str  
    title: str  
    components: List[ComponentPolicy]  
    bundle_rules: List[str]  
  
  
def parse_semver(version: str) -> SemVer:  
    """  
    Parse strict production SemVer: MAJOR.MINOR.PATCH with non-negative integers.  
    Pre-release/build metadata are intentionally rejected for production governance.  
  
    Raises ValueError on invalid input.  
    """  
    if not isinstance(version, str):  
        raise ValueError("version must be a string")  
  
    parts = version.split(".")  
    if len(parts) != 3:  
        raise ValueError("semver must have format MAJOR.MINOR.PATCH")  
  
    try:  
        major = int(parts[0])  
        minor = int(parts[1])  
        patch = int(parts[2])  
    except ValueError as e:  
        raise ValueError("semver parts must be integers") from e  
  
    if major < 0 or minor < 0 or patch < 0:  
        raise ValueError("semver parts must be non-negative")  
  
    # Disallow leading plus/minus or whitespace variants via round-trip check  
    if f"{major}.{minor}.{patch}" != version.strip():  
        # version.strip() allows surrounding whitespace but keeps internal exactness  
        if f"{major}.{minor}.{patch}" != version:  
            raise ValueError("semver must be canonical digits separated by dots")  
  
    return SemVer(major=major, minor=minor, patch=patch)  
  
  
def is_valid_semver(version: str) -> bool:  
    try:  
        parse_semver(version)  
        return True  
    except ValueError:  
        return False  
  
  
def compare_semver(a: str | SemVer, b: str | SemVer) -> int:  
    """  
    Returns:  
      -1 if a < b  
       0 if a == b  
      +1 if a > b  
    """  
    av = parse_semver(a) if isinstance(a, str) else a  
    bv = parse_semver(b) if isinstance(b, str) else b  
    if av < bv:  
        return -1  
    if av > bv:  
        return 1  
    return 0  
  
  
_BumpPart = Literal["major", "minor", "patch"]  
  
  
def bump_semver(version: str | SemVer, part: _BumpPart) -> SemVer:  
    v = parse_semver(version) if isinstance(version, str) else version  
    if part == "major":  
        return SemVer(v.major + 1, 0, 0)  
    if part == "minor":  
        return SemVer(v.major, v.minor + 1, 0)  
    if part == "patch":  
        return SemVer(v.major, v.minor, v.patch + 1)  
    raise ValueError("part must be one of: major, minor, patch")  
  
  
def get_versioning_policy() -> VersioningPolicy:  
    """  
    Canonical versioning policy. Ordering is stable for reviewable diffs.  
    """  
    components = [  
        ComponentPolicy(  
            component_id="workflow",  
            scheme="semver",  
            production_rules=[  
                "Workflow versions MUST be strict SemVer: MAJOR.MINOR.PATCH.",  
                "Production releases MUST NOT use prerelease/build metadata in version strings.",  
                "A workflow version MUST be bumped whenever operator-visible behavior changes.",  
                "Workflows MUST remain limited to supported step/action types for the running framework.",  
            ],  
            bump_guidance={  
                "major": [  
                    "Breaking change to input contract (required fields renamed/removed).",  
                    "Breaking change to output/report contract consumed by downstream systems.",  
                    "Change in business semantics (e.g., different records acted on) that could surprise operators.",  
                ],  
                "minor": [  
                    "Backward-compatible feature additions (new optional inputs, new optional steps/paths).",  
                    "Support for additional pages/variants while preserving existing behavior.",  
                ],  
                "patch": [  
                    "Bug fixes that do not change the workflow’s external contract.",  
                    "Stability improvements (timing/selector robustness) with no semantic change.",  
                ],  
            },  
        ),  
        ComponentPolicy(  
            component_id="selectors",  
            scheme="semver",  
            production_rules=[  
                "Selectors bundle versions MUST be strict SemVer: MAJOR.MINOR.PATCH.",  
                "Selector reference names are part of the contract when workflows use selector_ref.",  
                "Production releases MUST NOT use prerelease/build metadata in version strings.",  
            ],  
            bump_guidance={  
                "major": [  
                    "Remove or rename a selector_ref used by released workflows.",  
                    "Change selector meaning (same ref points to a different element/behavior).",  
                ],  
                "minor": [  
                    "Add new selector_refs without modifying existing refs.",  
                    "Extend selector coverage for new pages/flows without breaking existing references.",  
                ],  
                "patch": [  
                    "Tighten/relax selector strategies while keeping the same selector_ref set and meaning.",  
                    "Fix selector typos or improve resilience without changing the referenced element semantics.",  
                ],  
            },  
        ),  
        ComponentPolicy(  
            component_id="framework",  
            scheme="semver",  
            production_rules=[  
                "Framework versions MUST be strict SemVer: MAJOR.MINOR.PATCH.",  
                "Production releases MUST NOT use prerelease/build metadata in version strings.",  
                "A framework MAJOR bump indicates breaking behavior/API changes for operators, workflows, or tooling.",  
            ],  
            bump_guidance={  
                "major": [  
                    "Breaking change to workflow execution semantics (runner/executor behavior).",  
                    "Change that requires updating existing workflows/selectors to keep working.",  
                    "Breaking change to artifact formats consumed operationally.",  
                ],  
                "minor": [  
                    "Backward-compatible capability additions (new optional features, performance improvements).",  
                    "New validations/gates that can be enabled without breaking existing releases by default.",  
                ],  
                "patch": [  
                    "Bug fixes and stability improvements with no breaking changes.",  
                    "Security hardening that does not change external contracts.",  
                ],  
            },  
        ),  
    ]  
  
    bundle_rules = [  
        "A production bundle SHOULD record versions for workflow + selectors + framework together.",  
        "A production promotion SHOULD be traceable via immutable artifacts and reviewable diffs.",  
        "If component MAJOR versions are mixed in a bundle, the release record MUST document compatibility rationale.",  
    ]  
  
    return VersioningPolicy(  
        policy_id="VP-12A",  
        title="Release Versioning Policy (Workflows / Selectors / Framework)",  
        components=components,  
        bundle_rules=bundle_rules,  
    )  
  
  
def check_release_versions(  
    versions: Mapping[str, str],  
    *,  
    require_same_major: bool = False,  
    required_components: Sequence[str] = ("workflow", "selectors", "framework"),  
) -> List[str]:  
    """  
    Governance helper: validate a set of component versions.  
  
    Returns a deterministic list of issues. Empty list means "passes policy checks".  
  
    versions keys are expected to include: workflow, selectors, framework (by default).  
    """  
    issues: List[str] = []  
  
    # Required components present  
    for c in required_components:  
        if c not in versions:  
            issues.append(f"Missing required component version: {c}")  
  
    # SemVer validation  
    parsed: Dict[str, SemVer] = {}  
    for k in sorted(versions.keys()):  
        v = versions[k]  
        try:  
            parsed[k] = parse_semver(v)  
        except ValueError as e:  
            issues.append(f"Invalid semver for {k}: {v!r} ({e})")  
  
    # Optional constraint: same major across required components  
    if require_same_major:  
        majors: List[Tuple[str, int]] = []  
        for c in required_components:  
            if c in parsed:  
                majors.append((c, parsed[c].major))  
        if majors:  
            first_major = majors[0][1]  
            mismatched = [(c, m) for (c, m) in majors if m != first_major]  
            if mismatched:  
                issues.append(  
                    "Major version mismatch across required components: "  
                    + ", ".join([f"{c}={m}" for (c, m) in majors])  
                )  
  
    return issues  
  
  
def _md(s: str) -> str:  
    return s.replace("\r\n", "\n").replace("\r", "\n")  
  
  
def render_versioning_policy_markdown(policy: VersioningPolicy) -> str:  
    lines: List[str] = []  
    lines.append(f"# { _md(policy.title) }")  
    lines.append("")  
    lines.append(f"**Policy ID:** { _md(policy.policy_id) }")  
    lines.append("")  
    lines.append("## Component Policies")  
    lines.append("")  
    for c in policy.components:  
        lines.append(f"### { _md(c.component_id) }")  
        lines.append("")  
        lines.append(f"- **Scheme:** { _md(c.scheme) }")  
        lines.append("- **Production rules:**")  
        for r in c.production_rules:  
            lines.append(f"  - { _md(r) }")  
        lines.append("")  
        lines.append("- **Bump guidance:**")  
        for part in ("major", "minor", "patch"):  
            lines.append(f"  - **{part}:**")  
            for item in c.bump_guidance.get(part, []):  
                lines.append(f"    - { _md(item) }")  
        lines.append("")  
    lines.append("## Bundle / Promotion Rules")  
    lines.append("")  
    for r in policy.bundle_rules:  
        lines.append(f"- { _md(r) }")  
    lines.append("")  
    return "\n".join(lines).rstrip() + "\n"  
  
  
def versioning_policy_to_json(policy: Optional[VersioningPolicy] = None) -> str:  
    p = policy or get_versioning_policy()  
    payload = {  
        "policy_id": p.policy_id,  
        "title": p.title,  
        "components": [  
            {  
                "component_id": c.component_id,  
                "scheme": c.scheme,  
                "production_rules": list(c.production_rules),  
                "bump_guidance": {k: list(v) for k, v in sorted(c.bump_guidance.items())},  
            }  
            for c in p.components  
        ],  
        "bundle_rules": list(p.bundle_rules),  
    }  
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"  
  
  
def write_text_file(path: str, content: str) -> None:  
    with open(path, "w", encoding="utf-8", newline="\n") as f:  
        f.write(content)  
  
  
def write_versioning_policy_markdown(path: str) -> None:  
    p = get_versioning_policy()  
    md = render_versioning_policy_markdown(p)  
    write_text_file(path, md)  