# PDF Spread Tool

A small Windows utility for batch-processing PDFs by placing two consecutive pages side by side with a true **0-gap** join.

## Features

- Merge pages as `1+2, 3+4, 5+6...`
- Optional cover mode: keep page 1 single, then merge `2+3, 4+5, 6+7...`
- Batch processing for multiple PDF files
- Drag and drop support
- Optional JPG export at 150 / 200 / 300 DPI
- Pause / resume during JPG export
- Conflict-safe output naming: existing files are never overwritten
- Original PDF page content is placed directly into the new PDF; the merge step does not rasterize the pages

## Requirements

- Windows
- Python 3
- PyMuPDF 1.28.2
- tkinterdnd2 0.6.3

## Installation

1. Install Python 3 if it is not already installed.
2. Download or clone this repository.
3. Double-click `install_requirements.cmd`.
4. Double-click `pdf_spread_batch.pyw`.

Or install dependencies manually:

```powershell
py -3 -m pip install -r requirements.txt
```

## Usage

1. Add or drag one or more PDF files into the window.
2. Choose whether page 1 should be kept as a cover.
3. Choose an output folder.
4. Optionally enable JPG export and select DPI.
5. Click **Merge All**.

If an output file already exists, the program automatically uses names such as `name (1).pdf`, `name (2).pdf`, and matching JPG folders.

## License

This project uses PyMuPDF under its GNU Affero General Public License (AGPL) licensing option. PyMuPDF also offers a commercial licensing option.

See `LICENSE` and `THIRD_PARTY_NOTICES.txt` for licensing notes. If you redistribute this project, review and comply with the current licenses of all dependencies.

This repository's license notes are provided for practical distribution guidance and are not legal advice.
