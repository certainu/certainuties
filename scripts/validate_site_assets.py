#!/usr/bin/env python3
"""Check local HTML file references without downloading remote resources."""
import re
from pathlib import Path
from urllib.parse import urlsplit
root=Path(__file__).resolve().parents[1]
html=(root/"index.html").read_text(encoding="utf-8")
missing=[]
for ref in re.findall(r'(?:src|href)\s*=\s*["\']([^"\']+)["\']',html):
    if ref.startswith(("http:","https:","//","data:","mailto:","#")): continue
    path=urlsplit(ref).path.lstrip("/")
    if path and not (root/path).is_file(): missing.append(ref)
if missing: raise SystemExit("Missing local references: "+", ".join(missing))
print("Local asset references valid")
