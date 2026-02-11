# Quick Start Guide

## Immediate Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Source**: All dependencies listed in `requirements.txt` with documentation links in README.md

### 2. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

**Reference**: [Streamlit Documentation](https://docs.streamlit.io/)

### 3. Test with Sample Data

Use the included `test_names.txt` file to test the text input functionality:

1. Open the app
2. Go to "Paste Names" tab
3. Copy contents of `test_names.txt` and paste
4. Click "Match Names"

## Features at a Glance

### PDF Processing
- Upload PDF with company names
- Automatic detection of multi-line name splits
- Handles international corporate suffixes
- **Source**: Built with [pdfplumber](https://github.com/jsvine/pdfplumber)

### Text Input
- Paste company names directly
- Supports multiple delimiters (newlines, commas, semicolons)
- Batch processing of hundreds of names

### Company Matching
- **OpenCorporates API** (free, no key required)
  - Documentation: https://api.opencorporates.com/documentation/API-Reference
  - Rate limit: 2 requests/second
- **Refinitiv API** (requires key)
  - Documentation: https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis
- Mock data for testing

### Fuzzy Matching
- Multiple similarity algorithms (ratio, partial, token sort)
- Configurable similarity threshold (0-100%)
- **Source**: [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy)

### Export Options
- CSV download
- Excel (.xlsx) download with formatting

## Command-Line Usage

For batch processing without the web interface:

```bash
python batch_process.py input.txt --output results.csv --min-score 85
```

Or with PDF:

```bash
python batch_process.py companies.pdf --output results.xlsx --min-score 80
```

**Options:**
- `--api`: Choose API (default: opencorporates)
- `--min-score`: Minimum similarity score 0-100 (default: 80)
- `--delay`: Delay between API calls in seconds (default: 0.5)

## Customization

### Adding Corporate Suffixes

Edit the `COMMON_SUFFIXES` list in `app.py` (line ~50) to add more variations:

```python
COMMON_SUFFIXES = [
    "Limited", "Ltd", "LLC", 
    # Add your custom suffixes here
    "Your Custom Suffix"
]
```

### Adjusting Similarity Calculation

Modify the `calculate_string_distance()` function in `app.py` (line ~140) to adjust weights:

```python
# Current weights: 40% ratio, 30% partial, 30% token_sort
return (ratio * 0.4 + partial_ratio * 0.3 + token_sort * 0.3)
```

### Advanced Name Cleaning

Use the `NameCleaner` class from `name_cleaner.py` for preprocessing:

```python
from name_cleaner import NameCleaner

cleaner = NameCleaner()
core_name = cleaner.extract_core_name("Amazon.com, Inc.")
# Returns: "amazon"
```

**Reference**: Full documentation in `name_cleaner.py`

## Troubleshooting

### OpenCorporates Rate Limits

If you hit rate limits, increase delay in sidebar or use:

```python
time.sleep(0.5)  # Adjust this value
```

**Source**: [OpenCorporates API Reference](https://api.opencorporates.com/documentation/API-Reference)

### PDF Extraction Issues

Some PDFs have complex layouts. Try:

1. Converting PDF to text externally first
2. Using "Paste Names" tab instead
3. Adjusting extraction logic in `extract_names_from_pdf()` function

### Low Match Rates

- Lower the minimum similarity threshold
- Check if company names include typos
- Verify jurisdiction (some companies only in specific registries)
- Use the `NameCleaner` class to normalize names first

## Next Steps

### Deploy to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Company name matching tool"
git remote add origin https://github.com/yourusername/company-name-matcher.git
git push -u origin main
```

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Connect your repository
4. Deploy!

**Reference**: [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)

### Integrate Refinitiv

1. Obtain API credentials from Refinitiv
2. Implement OAuth2 in `search_refinitiv()` function
3. See README.md for authentication example
4. **Source**: [Refinitiv API Docs](https://developers.refinitiv.com/)

## Advanced Usage Examples

### Development Notebook

Open `development_notebook.ipynb` in Jupyter:

```bash
jupyter notebook development_notebook.ipynb
```

Test individual functions and API calls interactively.

### Custom Name Cleaning Pipeline

```python
from name_cleaner import NameCleaner
import pandas as pd

cleaner = NameCleaner()

names = ["Amazon.com, Inc.", "Microsoft Corporation"]
cleaned = [cleaner.extract_core_name(n) for n in names]

df = pd.DataFrame({'original': names, 'cleaned': cleaned})
```

### Batch Processing with Progress Tracking

```python
import pandas as pd
from tqdm import tqdm

for name in tqdm(df['name'].unique()):
    # Your matching logic here
    pass
```

## Support & Resources

- **OpenCorporates**: https://api.opencorporates.com/documentation/API-Reference
- **Refinitiv**: https://developers.refinitiv.com/
- **pdfplumber**: https://github.com/jsvine/pdfplumber
- **FuzzyWuzzy**: https://github.com/seatgeek/fuzzywuzzy
- **Streamlit**: https://docs.streamlit.io/

For issues with this tool, open an issue on GitHub.
