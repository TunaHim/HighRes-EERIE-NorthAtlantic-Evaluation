"""Render the two A0 landscape posters in posters/ to print-ready PDF (and a PNG preview).

    python scripts/build_posters.py

Uses a Chromium-based browser in headless mode (Microsoft Edge or Google Chrome); the page size,
1189 x 841 mm, comes from posters/poster.css. Run scripts/build_poster_figures.py first for the
vector figures. The QR codes are drawn by a small JavaScript library from cdnjs, so an internet
connection is needed while rendering.
"""
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTERS = ["poster_science", "poster_engineering"]
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "msedge", "google-chrome", "chromium", "chromium-browser",
]


def browser() -> str:
    for candidate in BROWSERS:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    sys.exit("No Chromium-based browser found (Edge or Chrome).")


def wait_for(path: Path, timeout: float = 120.0):
    """The browser launcher can return before the file is written: wait until it exists and stops growing."""
    start, last = time.time(), -1
    while time.time() - start < timeout:
        if path.exists():
            size = path.stat().st_size
            if size > 0 and size == last:
                return
            last = size
        time.sleep(1.0)
    sys.exit(f"{path.name} was not written")


def render(name: str, exe: str, preview: bool = True):
    page = (ROOT / "posters" / f"{name}.html").as_uri()
    pdf = ROOT / "posters" / f"{name}.pdf"
    # a separate profile, so the call does not hand over to an already running browser and return early
    def common():
        return [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=20000",
                f"--user-data-dir={tempfile.mkdtemp(prefix='poster-render-')}", "--no-first-run"]

    pdf.unlink(missing_ok=True)
    subprocess.run(common() + ["--no-pdf-header-footer", f"--print-to-pdf={pdf}", page], check=True, capture_output=True)
    wait_for(pdf)
    print(f"{pdf.name}: {pdf.stat().st_size / 1e6:.1f} MB")
    if preview:
        png = ROOT / "posters" / f"{name}_preview.png"
        # the page is 1189 x 841 mm = 4494 x 3179 CSS pixels; the preview is shrunk to 1800 px wide
        png.unlink(missing_ok=True)
        subprocess.run(common() + ["--window-size=4494,3179", f"--screenshot={png}", page], check=True, capture_output=True)
        wait_for(png)
        from PIL import Image

        with Image.open(png) as im:
            small = im.convert("RGB").resize((1800, round(1800 * im.height / im.width)), Image.LANCZOS)
        small.save(png, optimize=True)


def main():
    exe = browser()
    for name in sys.argv[1:] or POSTERS:
        render(name, exe)


if __name__ == "__main__":
    main()
