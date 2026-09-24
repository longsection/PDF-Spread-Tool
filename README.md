# PDF Spread Tool

A small Windows utility for batch-processing PDFs and images: merge consecutive PDF pages side by side with a true **0-gap** join, export PDF pages to JPG, or merge image files side by side.

## Features

- Merge PDF pages as `1+2, 3+4, 5+6...`
- Optional cover mode: keep item 1 single, then merge `2+3, 4+5, 6+7...`
- Batch processing and drag-and-drop
- PDF output modes:
  - Merge PDF only
  - Merge PDF and export merged pages as JPG
  - Export original PDF pages directly to JPG
- Image Spread supports JPG/JPEG, PNG, WEBP, BMP and TIFF/TIF
- Mixed image formats can be merged side by side with a 0-pixel gap
- Transparent image areas are composited onto white for JPG output
- Auto DPI is the default for PDF-to-JPG export
- Auto DPI checks each page independently and uses 150–300 DPI based on dominant embedded raster-image resolution
- Manual 150 / 200 / 300 DPI options remain available
- Multi-core PDF-to-JPG rendering
- Pause / resume during JPG export
- Existing output files are not overwritten
- PDF merging preserves original PDF page content instead of rasterizing the merge

## Download

For most Windows users, download `PDF-Spread-Tool.exe` from the latest GitHub Release. No Python installation is required for the standalone EXE.

## Run from source

Requirements:

- Windows
- Python 3
- PyMuPDF 1.28.2
- tkinterdnd2 0.6.3
- Pillow

1. Download or clone this repository.
2. Double-click `install_requirements.cmd`.
3. Double-click `pdf_spread_batch.pyw`.

Or install dependencies manually:

```powershell
py -3 -m pip install -r requirements.txt
```

## Usage

1. Add or drag PDFs and/or supported image files into the window.
2. Choose an output folder.
3. Choose an output mode.
4. Choose whether item 1 should be kept as a cover when merging.
5. For PDF-to-JPG export, leave DPI at **Auto** in most cases, or choose 150 / 200 / 300 manually.
6. Start processing.

When only image files are added, the tool switches to Image Spread mode. PDF modes process PDF files; Image Spread processes supported image files.

## License

This project uses PyMuPDF under its GNU Affero General Public License (AGPL) licensing option. PyMuPDF also offers a commercial licensing option.

See `LICENSE` and `THIRD_PARTY_NOTICES.txt` for licensing notes. If you redistribute this project, review and comply with the current licenses of all dependencies.

This repository's license notes are provided for practical distribution guidance and are not legal advice.
