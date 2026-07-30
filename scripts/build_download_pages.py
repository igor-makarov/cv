from html import escape
from pathlib import Path
import shutil
import sys
from urllib.parse import quote

site_dir = Path(sys.argv[1])
source_files = [Path(path) for path in sys.argv[2:]]

for source in source_files:
    if not source.is_file():
        raise SystemExit(f"Download source is missing: {source}")

    filename = source.name
    route = source.suffix.removeprefix(".").lower()
    destination = site_dir / filename
    page_dir = site_dir / route
    page_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)

    label = route.upper()
    href = "../" + quote(filename)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Download Igor Makarov’s CV ({label})</title>
  <style>
    html {{ color: #18212b; background: #fff; font: 16px/1.5 system-ui, sans-serif; }}
    body {{ display: grid; min-height: 100vh; margin: 0; place-items: center; }}
    main {{ max-width: 32rem; padding: 2rem; text-align: center; }}
    a {{ color: #005ea8; }}
  </style>
</head>
<body>
  <main>
    <p>Your download should start automatically.</p>
    <p>If it doesn’t, <a id="download" href="{escape(href)}" download="{escape(filename)}">download the {label} CV</a>.</p>
  </main>
  <script>document.getElementById("download").click();</script>
</body>
</html>
"""
    (page_dir / "index.html").write_text(page)
