"""Convert the study-guide markdown files in this folder to PDF.

Usage:  python docs/understanding/make_pdf.py            (all .md files)
        python docs/understanding/make_pdf.py day2_*.md  (selected files)

Markdown -> styled HTML (python-markdown) -> PDF via headless Edge/Chrome.
"""

import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]

CSS = """
@page { size: A4; margin: 16mm 15mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 18pt; color: #12355b; border-bottom: 2px solid #12355b;
     padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 13.5pt; color: #12355b; margin-top: 18px;
     page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #2c5d8a; margin-top: 14px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px;
        font-size: 9.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #b8c4d0; padding: 4px 6px; vertical-align: top;
         text-align: left; }
th { background: #e6edf4; }
blockquote { margin: 6px 0; padding: 6px 10px; background: #f3f6f9;
             border-left: 4px solid #2c5d8a; color: #333; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f1f1f1;
       padding: 0 3px; border-radius: 2px; }
hr { border: none; border-top: 1px solid #ccc; margin: 14px 0; }
p strong:first-child { color: #12355b; }
"""


def browser() -> str:
    for b in BROWSERS:
        if Path(b).exists():
            return b
    sys.exit("No Edge or Chrome found.")


def fix_lists(text: str) -> str:
    """Python-markdown needs a blank line before a list; add one if missing."""
    out, prev = [], ""
    for line in text.splitlines():
        is_item = re.match(r"\s*([-*]|\d+\.)\s", line) is not None
        prev_item = re.match(r"\s*([-*]|\d+\.)\s", prev) is not None
        if is_item and prev.strip() and not prev_item and not prev.startswith("|"):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def convert(md_path: Path, exe: str) -> Path:
    body = markdown.markdown(fix_lists(md_path.read_text(encoding="utf-8")),
                             extensions=["tables", "sane_lists"])
    html = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{md_path.stem}</title><style>{CSS}</style></head>"
            f"<body>{body}</body></html>")
    pdf_path = md_path.with_suffix(".pdf")
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / (md_path.stem + ".html")
        html_path.write_text(html, encoding="utf-8")
        # Print inside the temp dir, then copy: some setups block the browser
        # from writing into the project folder directly.
        tmp_pdf = Path(tmp) / pdf_path.name
        subprocess.run([exe, "--headless=new", "--disable-gpu",
                        "--no-pdf-header-footer",
                        f"--user-data-dir={Path(tmp) / 'profile'}",
                        f"--print-to-pdf={tmp_pdf}", html_path.as_uri()],
                       check=True, capture_output=True, timeout=120)
        # The browser may hand off to a background process and return early:
        # wait until the PDF appears and its size stops changing.
        last = -1
        for _ in range(120):
            size = tmp_pdf.stat().st_size if tmp_pdf.exists() else -1
            if size > 0 and size == last:
                break
            last = size
            time.sleep(0.5)
        if not tmp_pdf.exists():
            sys.exit(f"Browser did not write {tmp_pdf}; try setting TEMP to "
                     "a writable folder.")
        shutil.copyfile(tmp_pdf, pdf_path)
    return pdf_path


def main() -> None:
    names = sys.argv[1:]
    files = ([p for n in names for p in HERE.glob(n)] if names
             else sorted(HERE.glob("*.md")))
    exe = browser()
    for f in files:
        print("wrote", convert(f, exe))


if __name__ == "__main__":
    main()
