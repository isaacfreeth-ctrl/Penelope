# Company Name Matching Tool

A Streamlit web application that extracts company names from PDFs or text input and matches them against company databases using fuzzy string matching.

## Features

- **PDF Upload**: Extract company names from PDF documents with intelligent handling of multi-line name splits
- **Text Input**: Paste company names directly (comma, semicolon, or newline separated)
- **Multiple APIs**: 
  - OpenCorporates (free tier) - [Documentation](https://api.opencorporates.com/documentation/API-Reference)
  - Refinitiv Data Platform API (requires key) - [Documentation](https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis)
  - Mock data for testing
- **Fuzzy Matching**: Uses multiple string similarity algorithms to find best matches
- **Export Results**: Download matched data as CSV or Excel

## Methodology

Based on the approach described in corporate research workflows:

### 1. PDF Text Extraction
- Uses [pdfplumber](https://github.com/jsvine/pdfplumber) to extract text from PDFs
- Tracks page numbers for each extracted name
- Reference: https://github.com/jsvine/pdfplumber

### 2. Multi-line Name Detection
- Maintains a list of common corporate suffixes (Limited, LLC, GmbH, S.A., etc.)
- Detects when company names are split across lines
- Automatically recombines split names based on suffix patterns
- Handles international naming conventions (Deutschland, UK, US variations)

### 3. Company Matching
- Sends each unique name (case-insensitive) to selected API
- Takes highest-ranked result from API responses
- Calculates string similarity scores using multiple algorithms:
  - Basic ratio comparison
  - Partial ratio matching
  - Token sort ratio
- Reference: [FuzzyWuzzy Documentation](https://github.com/seatgeek/fuzzywuzzy)

### 4. String Distance Calculation
- Uses weighted combination of similarity metrics
- Optimal String Alignment algorithm via rapidfuzz
- Surfaces major differences between original and matched names
- Configurable minimum similarity threshold

### 5. Results Export
- Joins API results back to original name list
- Includes canonical names, metadata, and similarity scores
- Exports to CSV or Excel for further analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/company-name-matcher.git
cd company-name-matcher

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Usage

### Running Locally

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### PDF Upload Mode

1. Select "Upload PDF" tab
2. Upload a PDF containing company names
3. Configure matching settings in sidebar
4. Click "Extract and Match Names"
5. Review results and export

### Text Input Mode

1. Select "Paste Names" tab
2. Enter company names (one per line or separated by commas/semicolons)
3. Configure matching settings in sidebar
4. Click "Match Names"
5. Review results and export

## Configuration

### API Selection

- **OpenCorporates (Free)**: No API key required, rate-limited to 2 requests/second
  - Source: https://api.opencorporates.com/documentation/API-Reference
- **Refinitiv**: Requires API key and proper authentication setup
  - Source: https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis
- **Mock Data**: For testing without API calls

### Matching Settings

- **Minimum Match Score**: Threshold for accepting matches (0-100)
- **Max Results per Name**: Number of top matches to return per company name

## Output Fields

Each matched company includes:

- `original_name`: Name as extracted from PDF or input
- `page`: Page number (PDF only)
- `matched_name`: Canonical company name from database
- `similarity_score`: String similarity percentage (0-100)
- `jurisdiction`: Company jurisdiction/country code
- `company_number`: Official registration number
- `status`: Current company status (Active, Dissolved, etc.)
- `incorporation_date`: Date of incorporation
- `company_type`: Legal structure type
- `source`: Which API provided the match
- `url`: Link to company profile (when available)

## Technical Stack

- **Streamlit**: Web application framework - https://streamlit.io/
- **pdfplumber**: PDF text extraction - https://github.com/jsvine/pdfplumber
- **pandas**: Data manipulation - https://pandas.pydata.org/
- **fuzzywuzzy**: String matching - https://github.com/seatgeek/fuzzywuzzy
- **rapidfuzz**: Fast string matching - https://github.com/maxbachmann/RapidFuzz
- **requests**: HTTP API calls - https://docs.python-requests.org/

## Adapting for Refinitiv

To use the Refinitiv Data Platform API:

1. Obtain API credentials from Refinitiv
2. Implement OAuth2 authentication flow
3. Update the `search_refinitiv()` function with proper endpoints
4. Reference: https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis/documentation

Example authentication structure:

```python
def get_refinitiv_token(api_key, api_secret):
    """Get OAuth2 token from Refinitiv"""
    url = "https://api.refinitiv.com/auth/oauth2/v1/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': api_key,
        'client_secret': api_secret,
        'scope': 'search'
    }
    response = requests.post(url, data=data)
    return response.json()['access_token']
```

## Known Limitations

- OpenCorporates free tier has rate limits (2 requests/second)
- Some PDF layouts may not extract cleanly
- Fuzzy matching may produce false positives for very similar company names
- Refinitiv integration requires additional setup and credentials

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description

## License

MIT License - see LICENSE file for details

## References

- OpenCorporates API: https://api.opencorporates.com/documentation/API-Reference
- Refinitiv Data Platform: https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis
- pdfplumber: https://github.com/jsvine/pdfplumber
- FuzzyWuzzy: https://github.com/seatgeek/fuzzywuzzy
- Streamlit: https://docs.streamlit.io/

## Contact

For questions about monopoly research methodology or investigative tool development, please open an issue on GitHub.
