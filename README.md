# OCR Machine

A Python tool that batch-processes scanned PDFs with OCR (Optical Character Recognition) and identifies pages where OCR failed or no text was detected. Includes a built-in string search function that searches across all processed PDFs and generates a CSV report.

## Features

- Batch OCR processing of all PDFs in a folder using Tesseract via OCRmyPDF
- Automatic detection of pages with no text layer (failed OCR or blank pages)
- String search across multiple PDFs with per-page instance counts
- CSV reports for both OCR results and search results
- Skips pages that already have a text layer to avoid redundant processing
- Automatic page deskewing for better OCR accuracy

## Prerequisites

### 1. Python 3.8+

Download from [python.org](https://www.python.org/downloads/).

### 2. Tesseract OCR Engine

Tesseract must be installed separately. It is the OCR engine that runs under the hood.

- **Windows**: Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Note your install path (default: `C:\Program Files\Tesseract-OCR`).
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`

### 3. Python Packages

```bash
pip install ocrmypdf PyMuPDF
```

> **Note**: If you encounter an import error related to `fitz` referencing `frontend` or `clipboard`, you may have the wrong `fitz` package installed. Run the following to fix it:
> ```bash
> pip uninstall fitz frontend
> pip install --force-reinstall PyMuPDF
> ```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ocr-machine.git
   cd ocr-machine
   ```

2. Install dependencies:
   ```bash
   pip install ocrmypdf PyMuPDF
   ```

3. Open `ocr-machine.py` and update the `TESSERACT_PATH` variable at the top of the script to match your Tesseract install location:
   ```python
   TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR"  # Update this
   ```

4. Create the input folder (or it will be referenced from the script's directory):
   ```bash
   mkdir input_folder
   ```

5. Place your scanned PDFs into the `input_folder` directory.

## Usage

Run the script:

```bash
python ocr-machine.py
```

You will be prompted to select a mode:

```
Select a mode:
  1 = Scan + OCR only
  2 = Search only (searches the ocr_output folder)
  3 = Scan + OCR, then Search
Enter 1, 2, or 3:
```

### Mode 1: Scan + OCR Only

- Processes all PDFs in `input_folder`.
- Outputs OCR'd PDFs to `ocr_output`.
- Generates `ocr_report.csv` listing each file, total pages, number of failed pages, and the specific page numbers with no detected text.

### Mode 2: Search Only

- Prompts for a search term.
- Searches all PDFs in `ocr_output` (or `input_folder` if no output exists).
- Generates `search_report.csv` with instance counts per file and per page.

### Mode 3: Scan + OCR, then Search

- Runs OCR first (Mode 1), then prompts for a search term (Mode 2).

## Output

### OCR Report (`ocr_report.csv`)

| Column | Description |
|---|---|
| File | PDF filename |
| Total Pages | Number of pages in the PDF |
| Failed Pages Count | Number of pages with no detected text |
| Failed Page Numbers | Comma-separated list of page numbers with no text |
| OCR Result | Return code from OCRmyPDF |
| Status | OK or REVIEW NEEDED |

### Search Report (`search_report.csv`)

| Column | Description |
|---|---|
| File | PDF filename |
| Search Term | The string that was searched |
| Total Instances | Total number of matches in the file |
| Pages with Matches | Number of distinct pages containing the term |
| Detail (page and count) | Breakdown by page, e.g., `p.3 (2); p.15 (1)` |

## Configuration

The following settings can be adjusted in the script:

| Setting | Default | Description |
|---|---|---|
| `TESSERACT_PATH` | `C:\Program Files\Tesseract-OCR` | Path to your Tesseract installation |
| `INPUT_FOLDER` | `./input_folder` | Folder containing PDFs to process |
| `OUTPUT_FOLDER` | `./ocr_output` | Folder where OCR'd PDFs are saved |
| `language` | `eng` | OCR language. Use `eng+spa` for multi-language. |
| `deskew` | `True` | Straighten crooked pages before OCR |
| `skip_text` | `True` | Skip pages that already have a text layer |
| `optimize` | `0` | File size optimization (0 = none, 1-3 = increasing) |

## Troubleshooting

### "Could not find program 'tesseract' on the PATH"

Tesseract is not installed or the `TESSERACT_PATH` variable does not match your install location. Verify the path and update the variable in the script.

### "[WinError 2] The system cannot find the file specified"

These warnings are non-critical. They occur because optional optimization tools (`jbig2enc`, `pngquant`) are not installed. OCR still completes successfully. Set `optimize=0` to suppress them.

### Import error: `fitz` references `frontend` or `clipboard`

You have the wrong `fitz` package installed. Run:
```bash
pip uninstall fitz frontend
pip install --force-reinstall PyMuPDF
```

### Pages flagged as "no text" that are actually blank

Blank backs from double-sided scanning will be flagged. This is expected behavior. Review the flagged pages in a PDF viewer to confirm.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

Ly-Bach Truong
