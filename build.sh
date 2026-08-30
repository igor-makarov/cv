#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

name="Igor Makarov - CV"
rm -rf .build site
mkdir -p .build/cache site
export XDG_CACHE_HOME="$PWD/.build/cache"
reference_docx=".build/reference.docx"
python scripts/build_reference.py reference "$reference_docx"
pandoc cv.md \
  --from=markdown \
  --to=html5 \
  --standalone \
  --lua-filter=filters/cv.lua \
  --css=style.css \
  --metadata=pagetitle:"Igor Makarov — Staff Engineer" \
  --output=site/index.html
cp style.css site/style.css
cp -R fonts site/fonts

weasyprint --quiet site/index.html "site/$name.pdf"

pandoc cv.md \
  --from=markdown \
  --to=docx \
  --standalone \
  --lua-filter=filters/cv.lua \
  --reference-doc="$reference_docx" \
  --output="site/$name.docx"

python scripts/build_download_pages.py site "site/$name.pdf" "site/$name.docx"
python scripts/verify.py "site/$name.pdf" "site/$name.docx" site/index.html
printf 'Built:\n  site/index.html\n  site/pdf/index.html\n  site/docx/index.html\n  site/%s.pdf\n  site/%s.docx\n' \
  "$name" "$name"
