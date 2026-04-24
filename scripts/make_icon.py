#!/usr/bin/env python3
"""Generate ChatMate app icons for macOS (.icns) and Windows (.ico)."""
import math
import os
import struct
import subprocess
import zlib
from pathlib import Path


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(4))


def draw_icon(size: int) -> list[list[tuple[int, int, int, int]]]:
    """Render the icon at `size` x `size`, returns RGBA pixel grid."""
    pixels = [[(0, 0, 0, 0)] * size for _ in range(size)]

    cx = size / 2
    cy = size / 2
    r = size * 0.46   # outer circle radius
    cr = size * 0.14  # corner radius for bubble

    # Gradient: top-left indigo → bottom-right violet
    top_col    = (79, 70, 229, 255)   # indigo-600
    bottom_col = (124, 58, 237, 255)  # violet-600

    # --- background circle with gradient ---
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy <= r * r:
                t = (x + y) / (size * 2)
                pixels[y][x] = lerp_color(top_col, bottom_col, t)

    # --- chat bubble (rounded rect, white, slight transparency) ---
    bw = size * 0.58   # bubble width
    bh = size * 0.42   # bubble height
    bx = cx - bw / 2   # bubble left
    by = cy - bh / 2 - size * 0.04  # bubble top (offset up a little)

    bubble_col = (255, 255, 255, 245)

    def in_bubble(px, py):
        # Rounded rectangle test
        ix = max(bx + cr, min(bx + bw - cr, px))
        iy = max(by + cr, min(by + bh - cr, py))
        return (px - ix) ** 2 + (py - iy) ** 2 <= cr * cr

    # Tail triangle vertices (bottom-left of bubble)
    tail_x1 = bx + cr * 1.5
    tail_y1 = by + bh
    tail_x2 = bx + cr * 2.8
    tail_y2 = by + bh
    tail_x3 = bx + cr * 1.0
    tail_y3 = by + bh + size * 0.13

    def in_tail(px, py):
        # Barycentric test for triangle
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        d1 = sign((px, py), (tail_x1, tail_y1), (tail_x2, tail_y2))
        d2 = sign((px, py), (tail_x2, tail_y2), (tail_x3, tail_y3))
        d3 = sign((px, py), (tail_x3, tail_y3), (tail_x1, tail_y1))
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    for y in range(size):
        for x in range(size):
            if pixels[y][x][3] == 0:
                continue
            if in_bubble(x, y) or in_tail(x, y):
                pixels[y][x] = bubble_col

    # --- three dots inside bubble (indigo) ---
    dot_r   = size * 0.042
    dot_gap = size * 0.115
    dot_y   = by + bh * 0.5
    dot_col = (99, 102, 241, 255)  # indigo-500

    for i, dot_x in enumerate([cx - dot_gap, cx, cx + dot_gap]):
        for y in range(size):
            for x in range(size):
                if pixels[y][x][3] == 0:
                    continue
                if (x - dot_x) ** 2 + (y - dot_y) ** 2 <= dot_r ** 2:
                    pixels[y][x] = dot_col

    return pixels


def make_png_bytes(pixels: list[list[tuple]], size: int) -> bytes:
    """Encode pixel grid as a minimal PNG (no external library needed)."""
    def png_chunk(name: bytes, data: bytes) -> bytes:
        c = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", c)

    raw = b""
    for row in pixels:
        raw += b"\x00"  # filter type None
        for r, g, b, a in row:
            raw += bytes([r, g, b, a])

    compressed = zlib.compress(raw, 9)
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2 | 4, 0, 0, 0)  # 8-bit RGBA
    # Rebuild IHDR: width, height, bit_depth=8, colortype=6 (RGBA)
    ihdr = struct.pack(">II", size, size) + bytes([8, 6, 0, 0, 0])

    header = b"\x89PNG\r\n\x1a\n"
    return (
        header
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )


def save_png(pixels, size, path):
    path.write_bytes(make_png_bytes(pixels, size))


def make_icns(out_path: Path, png_sizes: dict[int, Path]):
    """Build a minimal .icns from pre-rendered PNG files."""
    # icns type codes for each size
    type_map = {
        16:   b"icp4",
        32:   b"icp5",
        64:   b"icp6",
        128:  b"ic07",
        256:  b"ic08",
        512:  b"ic09",
        1024: b"ic10",
    }
    body = b""
    for size, png_path in png_sizes.items():
        if size not in type_map:
            continue
        data = png_path.read_bytes()
        code = type_map[size]
        chunk_len = 8 + len(data)
        body += code + struct.pack(">I", chunk_len) + data

    total = 8 + len(body)
    out_path.write_bytes(b"icns" + struct.pack(">I", total) + body)


def make_ico(out_path: Path, png_sizes: dict[int, Path]):
    """Build a .ico containing multiple PNG-compressed images."""
    sizes = sorted(png_sizes.keys())
    entries = []
    for s in sizes:
        data = png_sizes[s].read_bytes()
        entries.append((s, data))

    # ICO header: reserved=0, type=1 (icon), count
    header = struct.pack("<HHH", 0, 1, len(entries))
    # Each directory entry is 16 bytes
    offset = 6 + 16 * len(entries)
    directory = b""
    images = b""
    for s, data in entries:
        w = h = s if s < 256 else 0  # 0 means 256 in ICO spec
        directory += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
        images += data
    out_path.write_bytes(header + directory + images)


def main():
    root = Path(__file__).parent.parent
    assets = root / "assets"
    assets.mkdir(exist_ok=True)

    print("Rendering icon at multiple sizes...")
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    png_files: dict[int, Path] = {}

    for s in sizes:
        p = assets / f"icon_{s}.png"
        pixels = draw_icon(s)
        save_png(pixels, s, p)
        png_files[s] = p
        print(f"  {s}x{s} OK")

    icns_path = assets / "ChatMate.icns"
    make_icns(icns_path, png_files)
    print(f"Created {icns_path}")

    ico_path = assets / "ChatMate.ico"
    make_ico(ico_path, {s: p for s, p in png_files.items() if s <= 256})
    print(f"Created {ico_path}")

    # Clean up per-size PNGs
    for p in png_files.values():
        p.unlink()

    print("Done.")


if __name__ == "__main__":
    main()
