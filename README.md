# Book Word Counter

A simple desktop tool that counts the words in an eBook or document file. Built with Python and Tkinter — just double-click to run.

## Features

- Pick a file from a native file dialog (works on macOS and Windows)
- Optional **start phrase** — counting begins from the first occurrence of a phrase you enter
- Optional **stop phrase** — counting stops when a phrase is reached (great for ignoring back-matter like acknowledgements or appendices)
- Both phrases are matched case-insensitively

## Supported formats

| Format | Extension |
|--------|-----------|
| EPUB | `.epub` |
| Kindle MOBI | `.mobi` |
| Kindle AZW3 | `.azw3` |
| Plain text | `.txt` |
| Word (modern) | `.docx` |
| Word (legacy) | `.doc` |
| PDF | `.pdf` |

> **Note on `.doc` files:** the tool tries `antiword` first, then LibreOffice, and falls back to a basic binary extraction if neither is installed. For best results with legacy `.doc` files, install [antiword](https://formulae.brew.sh/formula/antiword) (`brew install antiword`) or [LibreOffice](https://www.libreoffice.org).

## Requirements

- Python 3.8+
- Dependencies are installed automatically on first run, or manually:

```bash
pip install ebooklib beautifulsoup4 mobi python-docx pdfplumber
```

## Usage

### Double-click (macOS)
Double-click `start.command` in Finder. The first time, right-click → Open → Open to allow it.

### Double-click (Windows)
Double-click `Count Words.bat`. If Windows shows a security prompt, click **Run anyway**.

> Make sure [Python](https://www.python.org/downloads/) is installed and added to your PATH (tick the checkbox during the Python installer).

### Command line
```bash
python3 count_words.py
```

## License

MIT — see [LICENSE](LICENSE).
