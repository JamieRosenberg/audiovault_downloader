# Audiovault Downloader

Audiovault Downloader is a Python script designed to fetch, review, and download audio and video files from Audiovault. The script uses search terms to locate items, allows you to filter results, and downloads selected files while keeping track of their statuses.

---

## Features

- Search for items using keywords.
- Review results with options to include/exclude items by ID or keywords.
- Automatically fetch metadata such as file size and name.
- Organize downloads into subdirectories based on search terms.
- Tracks download status (`success`, `fail`, `incomplete`, `skipped`) in a CSV file.

---

## Prerequisites

1. **Python 3.7 or higher**:
   - Install Python: [Download Python](https://www.python.org/downloads/)
2. **Pip (Python package manager)**:
   - Comes bundled with Python installations.

---

## Setup

### 1. Clone the Repository

    git clone https://github.com/your-username/audiovault_downloader.git
    cd audiovault_downloader

### 2. Create and Activate a Virtual Environment

A virtual environment is used to isolate project dependencies.

#### On macOS/Linux:

    python3 -m venv venv
    source venv/bin/activate

#### On Windows:

    python -m venv venv
    venv\Scripts\activate

### 3. Install Dependencies

Install the required Python packages:

    pip install -r requirements.txt

If `requirements.txt` is missing, you can generate it after installing the necessary packages:

    pip install pandas requests beautifulsoup4
    pip freeze > requirements.txt

---

## Prepare `cookies.txt`

To authenticate the script with Audiovault:

1. **Log in to Audiovault** using your browser.
2. Open the browser's developer tools (usually `F12` or right-click > Inspect).
3. Go to the **Network** tab and refresh the page.
4. Find a network request to `audiovault.net` and inspect its cookies.
5. Use an extension like [EditThisCookie](https://editthiscookie.com/) or [Get Cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/) to export cookies as `cookies.txt`.
6. Save the exported cookies file to the root of the project.

---

## Running the Script

Run the downloader script with:

    python audiovault_downloader.py

---

## Outputs

- **Metadata CSV**: `search_results_with_metadata.csv`:
  - Contains details like file name, size, download status, etc.
- **Downloaded Files**:
  - Saved in subdirectories named after your search terms.

---

## Troubleshooting

### Progress Bar Not Showing
If the `curl` progress bar doesn’t appear, ensure you’re not redirecting stdout to a file or piping the output.

### Missing Dependencies
If you encounter missing dependency errors, ensure all packages are installed:

    pip install -r requirements.txt

### Updating Dependencies
After installing new dependencies, regenerate the `requirements.txt` file:

    pip freeze > requirements.txt

---

## License

MIT License
