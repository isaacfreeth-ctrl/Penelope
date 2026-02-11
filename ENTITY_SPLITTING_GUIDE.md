# Handling Concatenated Entity Names

## The Problem

PDFs sometimes extract multiple entity names on a single line without clear delimiters:

```
Abundance Institute George W Bush Foundation Open Ran Policy Coalition
```

This should be **3 separate entities**, not one.

## Solutions in This Tool

### 1. **Automatic Detection** (Built into app.py)

The tool now automatically detects entity boundaries by looking for:
- Organizational endings: Institute, Foundation, Coalition, Council, etc.
- Corporate suffixes: Inc., LLC, AG, GmbH, etc.
- Pattern: `[Name] [Type]` followed by `[Name] [Type]`

**Example:**
```
Input:  "Abundance Institute George W Bush Foundation"
Output: ["Abundance Institute", "George W Bush Foundation"]
```

**Source**: Custom regex-based detection in `detect_entity_boundaries()` function

### 2. **Manual Review Interface**

After PDF extraction, the app shows an **editable dataframe** where you can:
- Review all extracted names
- Manually split concatenated names
- Add new rows
- Delete incorrect entries

**To use:**
1. Upload PDF
2. Click "Extract Names from PDF"
3. Review the extracted names table
4. Edit directly in the interface
5. Click "Looks Good - Match Names"

### 3. **Auto-detect More Splits Button**

If the initial extraction missed some concatenations:
1. Review the extracted names
2. Click "🔍 Auto-detect more splits"
3. The tool will re-analyze with additional patterns

### 4. **Test Before Processing**

Use `test_entity_detection.py` to test strings before uploading:

```bash
python test_entity_detection.py "Your concatenated string here"
```

**Example:**
```bash
$ python test_entity_detection.py "Abundance Institute George W Bush Foundation Open Ran Policy Coalition"

Detected 3 entities:
1. Abundance Institute
2. George W Bush Foundation
3. Open Ran Policy Coalition
```

## Customizing Detection Patterns

### Add Custom Organizational Types

Edit `app.py` line ~30, in the `detect_entity_boundaries()` function:

```python
org_endings = [
    r'\bInstitute(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
    r'\bFoundations?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
    # Add your custom patterns here:
    r'\bYourCustomType(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
]
```

### Common Patterns to Add

For European organizations:
```python
r'\bSociété(?:\s+(?:pour|de|d\'))?',  # French
r'\bStiftung',                         # German
r'\bFörening',                         # Swedish
```

For think tanks and advocacy:
```python
r'\bThink Tank',
r'\bPolicy Center',
r'\bAdvocacy Group',
r'\bAction Fund',
```

## Known Limitations

### Works Well With:
- ✓ Standard organizational types (Institute, Foundation, etc.)
- ✓ Corporate suffixes (Inc., LLC, AG, etc.)
- ✓ Clear naming patterns with capitals

### May Struggle With:
- ✗ All lowercase names: "abc foundation xyz institute"
- ✗ Unusual acronyms: "ABC123 XYZ456"
- ✗ Names without type indicators: "Abundance George Bush Open Ran"
- ✗ Mixed languages without clear patterns

### Workarounds:

**For problematic PDFs:**
1. Convert PDF to text first
2. Clean in a text editor
3. Use the "Paste Names" tab instead

**For specific document types:**
- If your PDFs have consistent formatting (e.g., bullet points, numbered lists), you can modify the extraction logic
- Consider using table extraction if names are in tabular format

## Best Practices

### 1. Always Review Before Matching
Don't click "Extract and Match" directly. Use the two-step process:
- Extract → Review → Match

### 2. Check First and Last Entries
Concatenation errors often appear at the start/end of pages.

### 3. Look for Orphaned Words
Single words like "Foundation" or "Institute" suggest a split error.

### 4. Test Problem Strings
Copy problematic concatenated strings into `test_entity_detection.py` to debug.

### 5. Build a Custom Suffix List
If working with specific document types (e.g., EU lobbying registers), build a custom suffix list:

```python
# In app.py or test_entity_detection.py
EU_SPECIFIC_SUFFIXES = [
    r'\bEEIG',  # European Economic Interest Grouping
    r'\bAISBL',  # International Non-Profit Association
    r'\bVZW',    # Belgian Non-Profit
]
```

## Advanced: Pre-processing PDFs

For very messy PDFs, consider pre-processing:

### Option 1: Use pdftotext with layout preservation
```bash
pdftotext -layout input.pdf output.txt
```

### Option 2: Use OCR if PDF is scanned
```bash
# Requires tesseract
tesseract input.pdf output
```

### Option 3: Python preprocessing script
```python
import pdfplumber

with pdfplumber.open('messy.pdf') as pdf:
    for page in pdf.pages:
        # Extract with explicit line spacing
        text = page.extract_text(x_tolerance=2, y_tolerance=2)
        print(text)
```

## Reporting Issues

If you find patterns that consistently fail:
1. Test with `test_entity_detection.py`
2. Note the pattern that's failing
3. Add a new regex pattern to `org_endings`

## References

- Regex patterns based on common organizational naming conventions
- Pattern matching inspired by NER (Named Entity Recognition) techniques
- Custom implementation - no external NER library used to keep dependencies minimal

**Related tools for more complex NER:**
- spaCy: https://spacy.io/usage/linguistic-features#named-entities
- Stanza: https://stanfordnlp.github.io/stanza/
- NLTK: https://www.nltk.org/
