import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Set, Tuple

# NOTE: Pricing varies by region; keep as inputs/env if you want.
PRICING = {
    "standard": 0.30,   # $/GB-month
    "ia": 0.025,
    "archive": 0.016,
}

GB = 1024 * 1024 * 1024

CATEGORIES = (
    ("0-7_days", 7),
    ("8-14_days", 14),
    ("15-30_days", 30),
    ("31-60_days", 60),
    ("61-90_days", 90),
    ("91-365_days", 365),
    ("1-2_years", 730),
    ("2+_years", 10**9),
)

DEFAULT_SKIP_PREFIXES = (
    "/proc", "/sys", "/dev", "/run", "/var/run",
)

@dataclass
class FileStats:
    categories: Dict[str, int] = field(default_factory=lambda: {k: 0 for k, _ in CATEGORIES})
    total_size: int = 0
    total_files: int = 0
    errors: int = 0
    skipped: int = 0

    def add_file(self, size: int, last_access_days: int) -> None:
        self.total_size += size
        self.total_files += 1
        for name, max_days in CATEGORIES:
            if last_access_days <= max_days:
                self.categories[name] += size
                return

def _should_skip_path(path: str, extra_excludes: Set[str], skip_prefixes=DEFAULT_SKIP_PREFIXES) -> bool:
    # Skip exact directory names anywhere in the path
    # (E.g. "node_modules", ".git", "cache")
    parts = path.strip("/").split("/")
    if any(p in extra_excludes for p in parts):
        return True

    # Skip known virtual/system paths by absolute prefix only (safe + predictable)
    return any(path == pref or path.startswith(pref + "/") for pref in skip_prefixes)

def _last_access_days_from_stat(st: os.stat_result, now_ts: float) -> int:
    # EFS atime may be unreliable; use max(atime, mtime) as you did.
    last_ts = st.st_atime if st.st_atime >= st.st_mtime else st.st_mtime
    days = int((now_ts - last_ts) // 86400)
    return 0 if days < 0 else days

def scan_efs(
    root: str,
    *,
    excludes: Set[str],
    follow_symlinks: bool,
    max_depth: int,
    max_files: int,
    max_seconds: float,
) -> Tuple[FileStats, Dict[str, int]]:
    """
    Iterative scandir walk. Stops when max_files or max_seconds reached.
    Returns (stats, meta) where meta includes stop reason and counters.
    """
    stats = FileStats()
    start = time.time()
    now_ts = start

    # Stack holds (path, depth)
    stack = [(root, 0)]

    # If following symlinks, avoid inode loops (dir inode+dev tuple)
    visited_dirs: Set[Tuple[int, int]] = set()

    stop_reason = "completed"

    while stack:
        if (time.time() - start) > max_seconds:
            stop_reason = "time_limit_reached"
            break
        if stats.total_files >= max_files:
            stop_reason = "file_limit_reached"
            break

        current, depth = stack.pop()
        if depth > max_depth:
            continue

        if _should_skip_path(current, excludes):
            stats.skipped += 1
            continue

        try:
            with os.scandir(current) as it:
                for entry in it:
                    # Check limits frequently
                    if (time.time() - start) > max_seconds:
                        stop_reason = "time_limit_reached"
                        stack.clear()
                        break
                    if stats.total_files >= max_files:
                        stop_reason = "file_limit_reached"
                        stack.clear()
                        break

                    try:
                        # Fast path: directory vs file without extra stats unless needed
                        if entry.is_dir(follow_symlinks=follow_symlinks):
                            p = entry.path
                            if _should_skip_path(p, excludes):
                                stats.skipped += 1
                                continue

                            if follow_symlinks:
                                try:
                                    st = entry.stat(follow_symlinks=True)
                                    key = (st.st_dev, st.st_ino)
                                    if key in visited_dirs:
                                        stats.skipped += 1
                                        continue
                                    visited_dirs.add(key)
                                except OSError:
                                    stats.errors += 1
                                    continue

                            stack.append((p, depth + 1))

                        elif entry.is_file(follow_symlinks=follow_symlinks):
                            try:
                                st = entry.stat(follow_symlinks=follow_symlinks)
                                days = _last_access_days_from_stat(st, now_ts)
                                stats.add_file(st.st_size, days)
                            except OSError:
                                stats.errors += 1

                        else:
                            # sockets, fifos, etc.
                            stats.skipped += 1

                    except OSError:
                        stats.errors += 1

        except OSError:
            stats.errors += 1

    meta = {
        "stop_reason": stop_reason,
        "elapsed_seconds": round(time.time() - start, 3),
        "root": root,
    }
    return stats, meta

def calculate_costs(stats: FileStats) -> Dict:
    total_gb = stats.total_size / GB
    current_cost = total_gb * PRICING["standard"]

    standard_gb = stats.categories["0-7_days"] / GB
    ia_gb = (stats.categories["8-14_days"] + stats.categories["15-30_days"]) / GB
    archive_gb = (
        stats.categories["31-60_days"]
        + stats.categories["61-90_days"]
        + stats.categories["91-365_days"]
        + stats.categories["1-2_years"]
        + stats.categories["2+_years"]
    ) / GB

    optimized_cost = (
        standard_gb * PRICING["standard"]
        + ia_gb * PRICING["ia"]
        + archive_gb * PRICING["archive"]
    )

    savings = current_cost - optimized_cost
    savings_pct = (savings / current_cost * 100) if current_cost > 0 else 0.0

    return {
        "total_gb": total_gb,
        "current_cost": current_cost,
        "optimized_cost": optimized_cost,
        "monthly_savings": savings,
        "savings_percentage": savings_pct,
        "tier_distribution_gb": {
            "standard": standard_gb,
            "ia": ia_gb,
            "archive": archive_gb,
        },
    }

def lambda_handler(event, context):
    """
    event example:
    {
      "path": "/mnt/efs",
      "exclude": ["node_modules", ".git", "cache"],
      "follow_symlinks": false,
      "max_depth": 50,
      "max_files": 500000,
      "max_seconds": 840
    }
    """
    root = event.get("path", "/mnt/efs")
    excludes = set(event.get("exclude", []))

    # IMPORTANT: Do NOT treat /mnt as system in Lambda EFS use-cases.
    # We only skip truly virtual FS prefixes by default.
    follow = bool(event.get("follow_symlinks", False))
    max_depth = int(event.get("max_depth", 50))
    max_files = int(event.get("max_files", 300000))

    # Leave a safety buffer before Lambda timeout
    requested = float(event.get("max_seconds", 0))
    if requested <= 0:
        # context.get_remaining_time_in_millis() exists in Lambda
        remaining = getattr(context, "get_remaining_time_in_millis", lambda: 900000)()
        max_seconds = max(1.0, (remaining / 1000.0) - 2.0)
    else:
        max_seconds = requested

    if not os.path.exists(root):
        return {"ok": False, "error": f"path_not_found: {root}"}

    stats, meta = scan_efs(
        root,
        excludes=excludes,
        follow_symlinks=follow,
        max_depth=max_depth,
        max_files=max_files,
        max_seconds=max_seconds,
    )

    costs = calculate_costs(stats)

    return {
        "ok": True,
        "meta": meta,
        "summary": {
            "total_files": stats.total_files,
            "total_size_bytes": stats.total_size,
            "errors": stats.errors,
            "skipped": stats.skipped,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
        "by_access_bucket_bytes": stats.categories,
        "cost_analysis": costs,
        "notes": [
            "Uses max(atime, mtime) for last-access approximation.",
            "EFS lifecycle policies have minimum storage durations and other nuances; treat savings as directional.",
        ],
    }
