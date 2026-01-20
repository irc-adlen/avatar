# 🛠️ LLM Dataset Creator - User Guide

This toolkit contains three specialized scripts to extract high-quality text from different sources:

1. **PDF Extractor:** Converts local PDF files into clean text.
2. **Wikipedia Extractor:** Downloads articles in both raw text and structured Markdown.
3. **Web Extractor (Trafilatura):** Scrapes blog posts and news articles while removing ads and menus.

---

## 1. Environment Setup

Using a virtual environment (`venv`) is essential to keep your dependencies organized and avoid conflicts with your system's Python.

### On Windows

Open your terminal (PowerShell or Command Prompt) in your project folder:

```powershell
# Create the virtual environment
python -m venv venv

# Activate the environment
.\venv\Scripts\activate

```

### On Linux / macOS

Open your terminal in your project folder:

```bash
# Create the virtual environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate

```

### Installing Dependencies

Once the environment is activated, install the required libraries:

```bash
pip install pymupdf wikipedia-api trafilatura

```

---

## 2. Project Structure

To ensure the scripts run correctly, organize your folders as follows:

```text
PROJECT_FOLDER/
├── venv/                 # Virtual environment (created above)
├── pdf/          # Drop your .pdf files here
├── helpers/        # Extraction scripts


```

---

## 3. How to Use the Scripts

### A. Extracting from PDFs

1. Place your PDF files in the `source_pdfs/` folder.
2. Run the script:

```bash
python extract_pdf.py

```

* **Output:** Cleaned `.txt` files will be generated in a `dataset_txt` folder.

### B. Extracting from Wikipedia

1. Open `extract_wiki.py` to edit the list of topics (e.g., `topics = ["Quantum Physics", "History of France"]`).
2. Run the script:

```bash
python extract_wiki.py

```

* **Output:** You will get both `.txt` (raw) and `.md` (structured) files in the `dataset_wiki` folder.

### C. Extracting from the Web (URLs)

1. Open `extract_web.py` and add the URLs you want to scrape to the list.
2. Run the script:

```bash
python extract_web.py

```

* **Output:** A `web_dataset.md` file containing only the main text body of the pages.

---

## 4. Cross-Platform Compatibility (Windows & Linux)

This suite is designed to work on both operating systems by following these rules:

* **Path Management:** The scripts use `os.path` or `pathlib` to handle slashes correctly (`/` vs `\`).
* **Character Encoding:** All files are saved using `utf-8` encoding. This prevents "Mojibake" (broken characters) which often happens on Windows with French or special characters.
* **Python Command:** Remember that on Linux/macOS you might need to use `python3`, while Windows usually uses `python`.

---

## 5. Next Steps

Your data is currently stored as individual files. For professional LLM training, you usually need to merge these into a single "shuffled" file.
