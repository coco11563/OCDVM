import os
import time
import urllib.request

UA = os.environ.get("OCDVM_UA", "OCDVM research meng.xiao@nus.edu.sg")


def _cache_fresh(path: str, ttl_hours: float) -> bool:
    if not path or not os.path.exists(path):
        return False
    age_h = (time.time() - os.path.getmtime(path)) / 3600.0
    return age_h <= ttl_hours


def get(url: str, cache_path: str | None = None, ttl_hours: float = 24.0) -> bytes:
    if cache_path and _cache_fresh(cache_path, ttl_hours):
        with open(cache_path, "rb") as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(body)
    return body
