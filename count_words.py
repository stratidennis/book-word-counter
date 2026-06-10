import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import sys
import re
import os
import glob
import shutil
import subprocess
import tempfile

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ebooklib", "beautifulsoup4"])
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

try:
    import mobi
except ImportError:
    print("Installing mobi library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mobi"])
    import mobi

try:
    import docx
except ImportError:
    print("Installing python-docx library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    import docx

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber


def extract_text_from_epub(path):
    book = epub.read_epub(path)
    texts = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        texts.append(soup.get_text())
    return " ".join(texts)


def extract_text_from_mobi(path):
    temp_dir, _ = mobi.extract(path)
    texts = []
    try:
        html_files = (
            glob.glob(os.path.join(temp_dir, "**", "*.html"), recursive=True)
            + glob.glob(os.path.join(temp_dir, "**", "*.htm"), recursive=True)
        )
        for html_file in sorted(html_files):
            with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                texts.append(soup.get_text())
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return " ".join(texts)


def extract_text_from_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text_from_docx(path):
    doc = docx.Document(path)
    return " ".join(para.text for para in doc.paragraphs)


def extract_text_from_pdf(path):
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
    return " ".join(texts)


def extract_text_from_doc(path):
    """
    Try three strategies in order for legacy .doc files.
    Returns (text, method_used) so the caller can warn if only the
    fallback worked.
    """

    # Strategy 1: antiword (brew install antiword)
    try:
        result = subprocess.run(
            ["antiword", path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout, "antiword"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Strategy 2: LibreOffice headless conversion
    lo_candidates = [
        # macOS
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        # Windows (common install locations)
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        # Linux / in PATH
        "libreoffice",
        "soffice",
    ]
    for lo in lo_candidates:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = subprocess.run(
                    [lo, "--headless", "--convert-to", "txt:Text",
                     "--outdir", tmp, path],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    txt_files = glob.glob(os.path.join(tmp, "*.txt"))
                    if txt_files:
                        with open(txt_files[0], "r", encoding="utf-8", errors="ignore") as f:
                            return f.read(), "LibreOffice"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # Strategy 3: crude binary extraction (last resort — may be noisy)
    with open(path, "rb") as f:
        raw = f.read()
    # Word stores text as UTF-16-LE in the Word Document stream
    text = raw.decode("utf-16-le", errors="ignore")
    text = re.sub(r"[^\x20-\x7E\n\r\t]", " ", text)
    text = re.sub(r" {3,}", " ", text)
    return text.strip(), "binary fallback"


def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".epub":
        return extract_text_from_epub(path), None
    elif ext in (".mobi", ".azw3"):
        return extract_text_from_mobi(path), None
    elif ext == ".txt":
        return extract_text_from_txt(path), None
    elif ext == ".docx":
        return extract_text_from_docx(path), None
    elif ext == ".pdf":
        return extract_text_from_pdf(path), None
    elif ext == ".doc":
        return extract_text_from_doc(path)   # returns (text, method)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def start_at_phrase(text, start_phrase):
    """Return text from the start phrase onwards (case-insensitive)."""
    idx = text.lower().find(start_phrase.lower())
    if idx == -1:
        return text, False
    return text[idx:], True


def stop_at_phrase(text, stop_phrase):
    """Return only the portion of text before the stop phrase (case-insensitive)."""
    idx = text.lower().find(stop_phrase.lower())
    if idx == -1:
        return text, False
    return text[:idx], True


def count_words(text):
    words = re.findall(r"\b\w+(?:'\w+)*\b", text)
    return len(words)


def main():
    root = tk.Tk()
    root.withdraw()

    # Step 1: pick the file
    path = filedialog.askopenfilename(
        title="Select a file",
        filetypes=[
            ("All supported files", "*.epub *.mobi *.azw3 *.txt *.docx *.doc *.pdf"),
            ("eBook files", "*.epub *.mobi *.azw3"),
            ("EPUB files", "*.epub"),
            ("MOBI files", "*.mobi"),
            ("AZW3 files", "*.azw3"),
            ("Text files", "*.txt"),
            ("Word documents", "*.docx *.doc"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*"),
        ],
    )

    if not path:
        print("No file selected.")
        return

    # Step 2: ask for an optional start phrase
    start_phrase = simpledialog.askstring(
        "Start phrase (optional)",
        "Enter a phrase where the word count should START.\nLeave blank to start from the beginning of the book:",
        parent=root,
    )

    # Step 3: ask for an optional stop phrase
    stop_phrase = simpledialog.askstring(
        "Stop phrase (optional)",
        "Enter a phrase where the word count should STOP.\nLeave blank to count until the end of the book:",
        parent=root,
    )

    print(f"Reading: {path}")
    text, doc_method = extract_text(path)

    if doc_method == "binary fallback":
        messagebox.showwarning(
            ".doc extraction warning",
            "Neither antiword nor LibreOffice was found on your system.\n"
            "A basic binary extraction was used instead — the word count "
            "may be less accurate for this .doc file.\n\n"
            "For better results, install antiword:\n"
            "  brew install antiword\n"
            "or install LibreOffice (free at libreoffice.org).",
        )

    # Apply start phrase
    start_found = False
    if start_phrase and start_phrase.strip():
        text, start_found = start_at_phrase(text, start_phrase.strip())
        if not start_found:
            messagebox.showwarning(
                "Start phrase not found",
                f'The phrase "{start_phrase.strip()}" was not found in the book.\n'
                "Counting from the beginning instead.",
            )

    # Apply stop phrase (searched within the already-trimmed text)
    stop_found = False
    if stop_phrase and stop_phrase.strip():
        text, stop_found = stop_at_phrase(text, stop_phrase.strip())
        if not stop_found:
            messagebox.showwarning(
                "Stop phrase not found",
                f'The phrase "{stop_phrase.strip()}" was not found in the book.\n'
                "Counting until the end instead.",
            )

    total = count_words(text)

    # Build a summary note
    notes = []
    if start_phrase and start_phrase.strip():
        if start_found:
            notes.append(f'started at "{start_phrase.strip()}"')
        else:
            notes.append("start phrase not found — counted from beginning")
    if stop_phrase and stop_phrase.strip():
        if stop_found:
            notes.append(f'stopped at "{stop_phrase.strip()}"')
        else:
            notes.append("stop phrase not found — counted until end")

    note = f"\n({', '.join(notes)})" if notes else ""

    result = f"Word count: {total:,}{note}"
    print(result)
    messagebox.showinfo("Word Count", f"{result}\n\n{path}")


if __name__ == "__main__":
    main()
