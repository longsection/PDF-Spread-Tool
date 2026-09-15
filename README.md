# PDF Spread Tool

A small Windows utility for batch-processing PDFs: merge consecutive pages side by side with a true **0-gap** join, or export original PDF pages directly to JPG.

## Features

- Merge pages as `1+2, 3+4, 5+6...`
- Optional cover mode: keep page 1 single, then merge `2+3, 4+5, 6+7...`
- Batch processing for multiple PDF files
- Drag and drop support
- Three output modes:
  - Merge PDF only
  - Merge PDF and export merged pages as JPG
  - Export original PDF pages directly to JPG without merging or creating a new PDF
- JPG export at 150 / 200 / 300 DPI
- Multi-core JPG rendering for faster export
- Pause / resume during JPG export
- Conflict-safe output naming: existing files and JPG folders are never overwritten
- Original PDF page content is placed directly into merged PDFs; the merge step does not rasterize the pages

## Download

For most Windows users, the easiest option is to download `PDF-Spread-Tool.exe` from the latest GitHub Release. No Python installation is required for the standalone EXE.

## Run from source

Requirements:

- Windows
- Python 3
- PyMuPDF 1.28.2
- tkinterdnd2 0.6.3

1. Download or clone this repository.
2. Double-click `install_requirements.cmd`.
3. Double-click `pdf_spread_batch.pyw`.

Or install dependencies manually:

```powershell
py -3 -m pip install -r requirements.txt
```

## Usage

1. Add or drag one or more PDF files into the window.
2. Choose an output folder.
3. Choose an output mode.
4. If merging pages, choose whether page 1 should be kept as a cover.
5. If exporting JPG files, choose 150 / 200 / 300 DPI.
6. Start processing.

JPG rendering automatically uses multiple CPU cores for faster export.

If an output already exists, the program automatically chooses a conflict-safe name instead of overwriting it.

## License

This project uses PyMuPDF under its GNU Affero General Public License (AGPL) licensing option. PyMuPDF also offers a commercial licensing option.

See `LICENSE` and `THIRD_PARTY_NOTICES.txt` for licensing notes. If you redistribute this project, review and comply with the current licenses of all dependencies.

This repository's license notes are provided for practical distribution guidance and are not legal advice.
