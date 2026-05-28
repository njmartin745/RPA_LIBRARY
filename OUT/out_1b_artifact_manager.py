"""  
OUT-1B — Artifact Normalization (rename/move/archive, collision-safe).  
  
Filesystem-only helpers to normalize detected downloads (OUT-1A) into a predictable  
structure with stable names, per-run/per-item metadata, collision-safe policies,  
and optional archiving of prior outputs.  
  
Windows-safe, deterministic naming:  
- safe_slug() only uses [a-z0-9._-] and collapses runs.  
- build_artifact_name() composes base/run_id/item_id + extension.  
- move_artifact() handles overwrite policy, collision suffixing, and optional archive.  
"""  
  
from __future__ import annotations  
  
import shutil  
from datetime import datetime, timezone  
from pathlib import Path  
from typing import Optional  
  
__all__ = [  
    "ensure_dir",  
    "safe_slug",  
    "build_artifact_name",  
    "move_artifact",  
    "normalize_download",  
]  
  
  
def ensure_dir(path: Path) -> Path:  
    p = Path(path)  
    p.mkdir(parents=True, exist_ok=True)  
    return p  
  
  
def safe_slug(text: str) -> str:  
    """  
    Create a filesystem-safe slug:  
    - lowercase  
    - keep only [a-z0-9._-]  
    - convert whitespace to "-"  
    - collapse repeated separators  
    - strip leading/trailing separators/dots  
  
    Never returns empty string: falls back to "item".  
    """  
    s = (text or "").strip().lower()  
    if not s:  
        return "item"  
  
    out = []  
    prev_sep = False  
  
    for ch in s:  
        if ch.isalnum():  
            out.append(ch)  
            prev_sep = False  
            continue  
        if ch in {".", "_", "-"}:  
            if not prev_sep:  
                out.append(ch)  
            prev_sep = True  
            continue  
        if ch.isspace():  
            if not prev_sep:  
                out.append("-")  
            prev_sep = True  
            continue  
        # drop all other characters  
  
    slug = "".join(out).strip("._-")  
    if not slug:  
        return "item"  
  
    # collapse any accidental repeats after strip  
    while "__" in slug:  
        slug = slug.replace("__", "_")  
    while "--" in slug:  
        slug = slug.replace("--", "-")  
    while ".." in slug:  
        slug = slug.replace("..", ".")  
    return slug  
  
  
def build_artifact_name(*, base: str, run_id: str | None, item_id: str | None, ext: str | None) -> str:  
    """  
    Build a deterministic artifact file name:  
      <base>__run-<run_id>__item-<item_id><.ext>  
  
    - base/run_id/item_id are slugged  
    - ext may be provided with or without leading dot  
    """  
    base_s = safe_slug(base)  
    parts = [base_s]  
  
    if run_id:  
        parts.append(f"run-{safe_slug(str(run_id))}")  
    if item_id:  
        parts.append(f"item-{safe_slug(str(item_id))}")  
  
    name = "__".join(parts)  
  
    if ext:  
        e = str(ext).strip()  
        if e and not e.startswith("."):  
            e = "." + e  
        if e and e != ".":  
            name += e  
  
    return name  
  
  
def _next_versioned_name(dst_dir: Path, dst_name: str) -> str:  
    """  
    If dst_name exists in dst_dir, returns a versioned name:  
      foo.ext -> foo__v2.ext, foo__v3.ext, ...  
    """  
    dst_dir = Path(dst_dir)  
    base = Path(dst_name).name  
  
    stem = Path(base).stem  
    suffix = Path(base).suffix  # includes dot  
  
    candidate = base  
    v = 2  
    while (dst_dir / candidate).exists():  
        candidate = f"{stem}__v{v}{suffix}"  
        v += 1  
    return candidate  
  
  
def _archive_existing(dst: Path, archive_dir: Path) -> Path:  
    """  
    Move existing dst into archive_dir with a UTC timestamp suffix.  
    """  
    ensure_dir(archive_dir)  
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  
    stem = dst.stem  
    suffix = dst.suffix  
    archived_name = f"{stem}__arch_{ts}{suffix}"  
    archived_path = archive_dir / archived_name  
  
    # Collision-safe within archive as well  
    if archived_path.exists():  
        archived_name = _next_versioned_name(archive_dir, archived_name)  
        archived_path = archive_dir / archived_name  
  
    shutil.move(str(dst), str(archived_path))  
    return archived_path  
  
  
def move_artifact(  
    src: Path,  
    dst_dir: Path,  
    *,  
    dst_name: str,  
    overwrite: bool = False,  
    archive_dir: Path | None = None,  
) -> Path:  
    """  
    Move src into dst_dir with dst_name.  
  
    Policies:  
    - If overwrite=False and dst exists: append suffix __v2, __v3...  
    - If archive_dir is provided and dst exists: move existing dst into archive_dir first  
      (timestamped) before placing the new artifact.  
      - If overwrite=False, versioning still applies (archive affects only the specific  
        chosen dst path if it exists).  
    - If overwrite=True: place artifact at dst_name (after archiving existing if requested).  
  
    Returns final destination Path.  
    """  
    src = Path(src)  
    dst_dir = ensure_dir(Path(dst_dir))  
    if not src.exists() or not src.is_file():  
        raise FileNotFoundError(str(src))  
  
    dst_name = Path(dst_name).name  
    if not dst_name:  
        raise ValueError("dst_name must be a non-empty file name")  
  
    desired = dst_dir / dst_name  
  
    if overwrite:  
        if desired.exists():  
            if archive_dir is not None:  
                _archive_existing(desired, Path(archive_dir))  
            else:  
                desired.unlink()  
        final_dst = desired  
    else:  
        # no overwrite: choose a free name; if initial exists and archive_dir set,  
        # we still version rather than overwriting deterministically.  
        final_name = dst_name if not desired.exists() else _next_versioned_name(dst_dir, dst_name)  
        final_dst = dst_dir / final_name  
  
    # If final_dst exists and archive_dir set, archive it (should happen rarely, but safe)  
    if final_dst.exists():  
        if archive_dir is not None:  
            _archive_existing(final_dst, Path(archive_dir))  
        elif overwrite:  
            final_dst.unlink()  
        else:  
            # last-resort version bump  
            final_dst = dst_dir / _next_versioned_name(dst_dir, final_dst.name)  
  
    shutil.move(str(src), str(final_dst))  
    return final_dst  
  
  
def normalize_download(  
    download_path: Path,  
    *,  
    out_dir: Path,  
    run_id: str | None,  
    item_id: str | None,  
    base_name: str,  
    overwrite: bool = False,  
    archive_dir: Path | None = None,  
) -> Path:  
    """  
    Normalize a detected download into out_dir using a canonical naming scheme.  
  
    - Uses download_path suffix as extension.  
    - Returns final artifact Path.  
    """  
    download_path = Path(download_path)  
    ext = download_path.suffix[1:] if download_path.suffix.startswith(".") else download_path.suffix  
    dst_name = build_artifact_name(base=base_name, run_id=run_id, item_id=item_id, ext=ext or None)  
  
    return move_artifact(  
        download_path,  
        Path(out_dir),  
        dst_name=dst_name,  
        overwrite=overwrite,  
        archive_dir=Path(archive_dir) if archive_dir is not None else None,  
    )  