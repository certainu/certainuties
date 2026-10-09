#!/usr/bin/env python3
"""One-time lossless-layout image optimization for the CERTAINU hero artwork."""
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
src=root/"assets/certainu-08.png"
dst=root/"assets/certainu-08.webp"
html=root/"index.html"
if not src.exists():
    assert dst.exists(), "Neither original nor optimized image exists"
    print("Image already optimized")
else:
    with Image.open(src) as image:
        image.save(dst, "WEBP", quality=85, method=6)
    old=src.stat().st_size
    new=dst.stat().st_size
    assert new < old * 0.6, f"Optimization too small: {new} vs {old}"
    content=html.read_text()
    assert "assets/certainu-08.png" in content, "Expected image reference missing"
    html.write_text(content.replace("assets/certainu-08.png","assets/certainu-08.webp"))
    src.unlink()
    print(f"Optimized artwork: {old} -> {new} bytes ({100*(1-new/old):.1f}% smaller)")
