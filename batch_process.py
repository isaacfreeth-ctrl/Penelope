#!/usr/bin/env python3
"""
Command-line batch processor for company name matching

Usage:
    python batch_process.py input.txt --output results.csv --api opencorporates
    python batch_process.py input.pdf --output results.xlsx --min-score 85

References:
- OpenCorporates API: https://api.opencorporates.com/documentation/API-Reference
- FuzzyWuzzy: https://github.com/seatgeek/fuzzywuzzy
"""

import argparse
import sys
import pandas as pd
import pdfplumber
import requests
import time
from pathlib import Path
from fuzzywuzzy import fuzz
from name_cleaner import NameCleaner

def search_opencorporates(company_name, max_results=1):
    """
    Search OpenCorporates API for company matches
    
    Args:
        company_name: Company name to search
        max_results: Maximum number of results to return
        
    Returns:
        List of matched companies or None
        
    Reference: https://api.opencorporates.com/documentation/API-Reference
    """
    try:
        url = "https://api.opencorporates.com/v0.4/companies/search"
        params = {
            'q': company_name,
            'per_page': max_results
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            companies = data.get('results', {}).get('companies', [])
            return [item['company'] for item in companies]
        
        return None
    
    except Exception as e:
        print(f"Error searching for '{company_name}': {str(e)}", file=sys.stderr)
        return None

def extract_names_from_pdf(pdf_path):
    """
    Extract company names from PDF file
    
    Reference: https://github.com/jsvine/pdfplumber
    """
    names = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        names.append({
                            'name': line.strip(),
                            'page': page_num,
                            'source': str(pdf_path)
                        })
    
    return pd.DataFrame(names)

def extract_names_from_text(text_path):
    """Extract company names from text file"""
    with open(text_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaner = NameCleaner()
    names = cleaner.split_on_delimiters(content)
    
    return pd.DataFrame([
        {'name': name, 'page': None, 'source': str(text_path)}
        for name in names
    ])

def calculate_similarity(str1, str2):
    """
    Calculate weighted string similarity score
    
    Reference: https://github.com/seatgeek/fuzzywuzzy
    """
    if not str1 or not str2:
        return 0
    
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()
    
    ratio = fuzz.ratio(s1, s2)
    partial_ratio = fuzz.partial_ratio(s1, s2)
    token_sort = fuzz.token_sort_ratio(s1, s2)
    
    return round(ratio * 0.4 + partial_ratio * 0.3 + token_sort * 0.3, 2)

def process_names(df, api='opencorporates', min_similarity=80, delay=0.5):
    """Process names and match against API"""
    results = []
    
    # Get unique names
    unique_names = df['name'].str.lower().unique()
    total = len(unique_names)
    
    print(f"Processing {total} unique company names...")
    
    for idx, name in enumerate(unique_names, 1):
        print(f"[{idx}/{total}] Searching: {name}")
        
        # Search API
        if api == 'opencorporates':
            matches = search_opencorporates(name)
        else:
            print(f"Unsupported API: {api}", file=sys.stderr)
            matches = None
        
        if matches:
            match = matches[0]
            similarity = calculate_similarity(name, match.get('name', ''))
            
            if similarity >= min_similarity:
                # Join back to original dataframe
                original_rows = df[df['name'].str.lower() == name]
                
                for _, row in original_rows.iterrows():
                    results.append({
                        'original_name': row['name'],
                        'page': row.get('page'),
                        'source': row.get('source'),
                        'matched_name': match.get('name'),
                        'similarity_score': similarity,
                        'jurisdiction': match.get('jurisdiction_code'),
                        'company_number': match.get('company_number'),
                        'status': match.get('current_status'),
                        'incorporation_date': match.get('incorporation_date'),
                        'company_type': match.get('company_type'),
                        'opencorporates_url': match.get('opencorporates_url')
                    })
            else:
                # Low similarity match
                original_rows = df[df['name'].str.lower() == name]
                for _, row in original_rows.iterrows():
                    results.append({
                        'original_name': row['name'],
                        'page': row.get('page'),
                        'source': row.get('source'),
                        'matched_name': match.get('name'),
                        'similarity_score': similarity,
                        'jurisdiction': None,
                        'company_number': None,
                        'status': None,
                        'incorporation_date': None,
                        'company_type': None,
                        'opencorporates_url': None
                    })
        else:
            # No match found
            original_rows = df[df['name'].str.lower() == name]
            for _, row in original_rows.iterrows():
                results.append({
                    'original_name': row['name'],
                    'page': row.get('page'),
                    'source': row.get('source'),
                    'matched_name': None,
                    'similarity_score': None,
                    'jurisdiction': None,
                    'company_number': None,
                    'status': None,
                    'incorporation_date': None,
                    'company_type': None,
                    'opencorporates_url': None
                })
        
        # Rate limiting
        time.sleep(delay)
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(
        description='Batch process company name matching',
        epilog='For more information, see: https://api.opencorporates.com/documentation/API-Reference'
    )
    parser.add_argument('input', type=str, help='Input file (PDF or TXT)')
    parser.add_argument('--output', '-o', type=str, required=True, 
                       help='Output file (CSV or XLSX)')
    parser.add_argument('--api', type=str, default='opencorporates',
                       choices=['opencorporates'],
                       help='API to use for matching (default: opencorporates)')
    parser.add_argument('--min-score', type=int, default=80,
                       help='Minimum similarity score (0-100, default: 80)')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between API calls in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Extract names based on file type
    print(f"Reading input from: {args.input}")
    
    if input_path.suffix.lower() == '.pdf':
        df_names = extract_names_from_pdf(input_path)
    elif input_path.suffix.lower() in ['.txt', '.text']:
        df_names = extract_names_from_text(input_path)
    else:
        print(f"Error: Unsupported file type: {input_path.suffix}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Extracted {len(df_names)} company names")
    
    # Process names
    results = process_names(
        df_names,
        api=args.api,
        min_similarity=args.min_score,
        delay=args.delay
    )
    
    # Export results
    output_path = Path(args.output)
    
    print(f"\nWriting results to: {args.output}")
    
    if output_path.suffix.lower() == '.csv':
        results.to_csv(output_path, index=False)
    elif output_path.suffix.lower() in ['.xlsx', '.xls']:
        results.to_excel(output_path, index=False, sheet_name='Matches')
    else:
        print(f"Error: Unsupported output format: {output_path.suffix}", file=sys.stderr)
        sys.exit(1)
    
    # Summary statistics
    matched = results['matched_name'].notna().sum()
    unmatched = results['matched_name'].isna().sum()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total names processed: {len(results)}")
    print(f"Matched: {matched}")
    print(f"Unmatched: {unmatched}")
    print(f"Match rate: {matched/len(results)*100:.1f}%")
    print("="*60)

if __name__ == '__main__':
    main()
