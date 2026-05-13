"""生成多尺寸 assets/icon.ico，供 PyInstaller 和 Inno Setup 使用。"""
from pathlib import Path
from PIL import Image, ImageDraw


def _make(size: int) -> Image.Image:
    s = size / 64
    bg = (40, 40, 40, 255)
    fg = (80, 200, 80, 255)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    m = max(1, int(2 * s))
    d.ellipse([m, m, size - m - 1, size - m - 1], fill=bg)

    cx = size // 2
    mw = max(1, int(6 * s))
    d.rounded_rectangle([cx - mw, int(10*s), cx + mw, int(36*s)],
                        radius=max(1, int(6*s)), fill=fg)
    d.arc([int(20*s), int(26*s), int(44*s), int(46*s)],
          start=0, end=180, fill=fg, width=max(1, int(2*s)))
    d.line([cx, int(46*s), cx, int(52*s)], fill=fg, width=max(1, int(2*s)))
    d.line([int(24*s), int(52*s), int(40*s), int(52*s)], fill=fg, width=max(1, int(2*s)))

    return img


if __name__ == "__main__":
    Path("assets").mkdir(exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [_make(s) for s in sizes]
    images[0].save(
        "assets/icon.ico",
        format="ICO",
        append_images=images[1:],
        sizes=[(s, s) for s in sizes],
    )
    print(f"Generated assets/icon.ico  ({len(sizes)} sizes)")
