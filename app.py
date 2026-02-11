import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO
import requests
from fuzzywuzzy import fuzz
from rapidfuzz import process, fuzz as rapidfuzz
import time

st.set_page_config(page_title="Company Name Matcher", layout="wide")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

st.title("📊 Company Name Matching Tool")
st.markdown("""
Upload a PDF or paste company names to match them against company databases.
Handles multi-line name splits and fuzzy matching.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    st.subheader("API Settings")
    api_choice = st.selectbox(
        "Select API",
        ["OpenCorporates (Free)", "Refinitiv (Requires Key)", "Mock Data (Testing)"]
    )
    
    if api_choice == "Refinitiv (Requires Key)":
        refinitiv_key = st.text_input("Refinitiv API Key", type="password")
    else:
        refinitiv_key = None
    
    st.subheader("Matching Settings")
    min_similarity = st.slider("Minimum Match Score", 0, 100, 80)
    max_results = st.number_input("Max Results per Name", 1, 10, 1)

# Common suffixes that indicate line splits
COMMON_SUFFIXES = [
    "Limited", "Ltd", "Ltd.", "LLC", "L.L.C.", "Inc", "Inc.", "Incorporated",
    "Corp", "Corp.", "Corporation", "Co.", "Co", "Company", "GmbH", "AG", 
    "S.A.", "S.A", "SA", "S.p.A.", "SpA", "N.V.", "NV", "B.V.", "BV",
    "Pty", "Pty.", "PLC", "P.L.C.", "(Deutschland)", "(UK)", "(US)",
    "Co.,Ltd.", "Co., Ltd.", "Pte", "Pte.", "Sdn Bhd", "Sdn. Bhd.",
    "A.S.", "AS", "AB", "Oyj", "S.r.l.", "Srl", "KG", "mbH"
]

def detect_entity_boundaries(text):
    """
    Detect where one entity name ends and another begins on the same line.
    Uses organizational keywords and capitalization patterns to identify entity boundaries.
    """
    
    # Common organizational endings that mark entity boundaries
    org_endings = [
        r'\bInstitute(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bFoundations?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bCoalitions?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bAlliances?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bAssociations?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bCouncils?(?:\s+on\s+[A-Za-z\s&]+)?',
        r'\bCentres?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bNetworks?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bGroups?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bSociet(?:y|ies)(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bTrusts?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bFunds?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bOrganizations?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bOrganisations?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bInitiatives?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bProjects?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bPrograms?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        r'\bProgrammes?(?:\s+(?:for|of|on)\s+[A-Za-z\s&]+)?',
        # Special: "Relations" often ends an entity name
        r'\bRelations',
        # Corporate suffixes
        r'\bCorporations?',
        r'\bInc\.?',
        r'\bLLC',
        r'\bLtd\.?',
        r'\bPLC',
        r'\bAG',
        r'\bGmbH',
        r'\bS\.A\.',
        r'\bN\.V\.',
    ]
    
    # Find all entity ending positions
    entity_ends = []
    
    for pattern in org_endings:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Avoid matching "Foundations" when it's part of "Foundations Bill"
            # by checking if next character is a space followed by capital letter
            full_match_end = match.end()
            
            # Check if there's more text after this match
            if full_match_end < len(text):
                remaining = text[full_match_end:].lstrip()
                # If next word starts with capital, this is a boundary
                if remaining and remaining[0].isupper():
                    entity_ends.append((full_match_end, match.group()))
            else:
                # End of string, definitely a boundary
                entity_ends.append((full_match_end, match.group()))
    
    # Sort by position and remove duplicates
    entity_ends = sorted(set(entity_ends))
    
    if not entity_ends:
        return [text]
    
    # Split at entity boundaries
    entities = []
    start = 0
    
    for end_pos, matched_ending in entity_ends:
        # Extract from start to this entity's end
        entity = text[start:end_pos].strip()
        if entity:
            entities.append(entity)
        start = end_pos
    
    # Add any remaining text
    remaining = text[start:].strip()
    if remaining:
        # Only add if it looks like an entity (contains uppercase letter)
        if any(c.isupper() for c in remaining):
            entities.append(remaining)
    
    # Filter out very short entities (likely false positives)
    entities = [e for e in entities if len(e) > 3]
    
    return entities if entities else [text]

def extract_names_from_pdf(pdf_file):
    """Extract company names from PDF, handling multi-line splits and multi-entity lines"""
    names = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                
                # Process lines to detect and merge split names
                i = 0
                while i < len(lines):
                    current_line = lines[i].strip()
                    
                    if current_line:
                        # Check if next line is a suffix
                        merged = False
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            
                            # Check if next line is a common suffix
                            if any(next_line.startswith(suffix) for suffix in COMMON_SUFFIXES):
                                current_line = f"{current_line} {next_line}"
                                merged = True
                                i += 1  # Skip next line
                        
                        # Try to detect multiple entities on the same line
                        entities = detect_entity_boundaries(current_line)
                        
                        for entity in entities:
                            if entity:
                                names.append({
                                    'name': entity,
                                    'page': page_num,
                                    'original_name': entity
                                })
                    
                    i += 1
    
    return pd.DataFrame(names)

def parse_text_input(text):
    """Parse text input into individual company names"""
    # Split by newlines or common delimiters
    names = []
    lines = text.split('\n')
    
    for line in lines:
        # Also split by commas, semicolons, or pipes
        subnames = re.split(r'[,;|]', line)
        for name in subnames:
            name = name.strip()
            if name:
                names.append({
                    'name': name,
                    'page': None,
                    'original_name': name
                })
    
    return pd.DataFrame(names)

def search_opencorporates(company_name):
    """Search OpenCorporates API (free tier)"""
    try:
        url = "https://api.opencorporates.com/v0.4/companies/search"
        params = {
            'q': company_name,
            'per_page': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results', {}).get('companies'):
                company = data['results']['companies'][0]['company']
                return {
                    'matched_name': company.get('name'),
                    'jurisdiction': company.get('jurisdiction_code'),
                    'company_number': company.get('company_number'),
                    'status': company.get('current_status'),
                    'incorporation_date': company.get('incorporation_date'),
                    'company_type': company.get('company_type'),
                    'source': 'OpenCorporates',
                    'opencorporates_url': company.get('opencorporates_url')
                }
        
        return None
    
    except Exception as e:
        st.warning(f"Error searching for '{company_name}': {str(e)}")
        return None

def search_refinitiv(company_name, api_key):
    """Search Refinitiv Data Platform API"""
    # Note: This is a placeholder - actual implementation requires proper authentication
    # Reference: https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis
    
    if not api_key:
        return None
    
    try:
        # Placeholder for Refinitiv API call
        # Actual implementation would use OAuth2 authentication
        st.warning("Refinitiv integration requires proper authentication setup")
        return None
    
    except Exception as e:
        st.warning(f"Error searching Refinitiv for '{company_name}': {str(e)}")
        return None

def generate_mock_data(company_name):
    """Generate mock data for testing"""
    return {
        'matched_name': f"{company_name} Limited",
        'jurisdiction': 'GB',
        'company_number': 'MOCK123456',
        'status': 'Active',
        'incorporation_date': '2020-01-01',
        'company_type': 'Private Limited Company',
        'source': 'Mock Data',
        'opencorporates_url': None
    }

def calculate_string_distance(str1, str2):
    """Calculate string distance using multiple algorithms"""
    if not str1 or not str2:
        return 0
    
    # Normalize strings
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()
    
    # Calculate multiple similarity scores
    ratio = fuzz.ratio(s1, s2)
    partial_ratio = fuzz.partial_ratio(s1, s2)
    token_sort = fuzz.token_sort_ratio(s1, s2)
    
    # Return weighted average
    return (ratio * 0.4 + partial_ratio * 0.3 + token_sort * 0.3)

def match_names(df, api_choice, refinitiv_key=None, min_similarity=80, max_results=1):
    """Match company names using selected API"""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Get unique names (case-insensitive)
    unique_names = df['name'].str.lower().unique()
    total_names = len(unique_names)
    
    for idx, name in enumerate(unique_names):
        status_text.text(f"Processing {idx + 1}/{total_names}: {name}")
        progress_bar.progress((idx + 1) / total_names)
        
        # Search using selected API
        if api_choice == "OpenCorporates (Free)":
            match = search_opencorporates(name)
        elif api_choice == "Refinitiv (Requires Key)":
            match = search_refinitiv(name, refinitiv_key)
        else:  # Mock Data
            match = generate_mock_data(name)
        
        if match:
            # Calculate string distance
            similarity = calculate_string_distance(name, match.get('matched_name', ''))
            
            if similarity >= min_similarity:
                # Join back to original dataframe
                original_rows = df[df['name'].str.lower() == name]
                
                for _, row in original_rows.iterrows():
                    result = {
                        'original_name': row['original_name'],
                        'page': row['page'],
                        'matched_name': match.get('matched_name'),
                        'similarity_score': round(similarity, 2),
                        'jurisdiction': match.get('jurisdiction'),
                        'company_number': match.get('company_number'),
                        'status': match.get('status'),
                        'incorporation_date': match.get('incorporation_date'),
                        'company_type': match.get('company_type'),
                        'source': match.get('source'),
                        'url': match.get('opencorporates_url')
                    }
                    results.append(result)
        else:
            # No match found
            original_rows = df[df['name'].str.lower() == name]
            for _, row in original_rows.iterrows():
                results.append({
                    'original_name': row['original_name'],
                    'page': row['page'],
                    'matched_name': None,
                    'similarity_score': None,
                    'jurisdiction': None,
                    'company_number': None,
                    'status': None,
                    'incorporation_date': None,
                    'company_type': None,
                    'source': None,
                    'url': None
                })
        
        # Rate limiting for OpenCorporates (free tier)
        if api_choice == "OpenCorporates (Free)":
            time.sleep(0.5)  # 2 requests per second limit
    
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(results)

# Main interface
tab1, tab2 = st.tabs(["📄 Upload PDF", "✏️ Paste Names"])

with tab1:
    st.header("Upload PDF with Company Names")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # Step 1: Extract names
        if 'extracted_names' not in st.session_state:
            st.session_state.extracted_names = None
        
        if st.button("Extract Names from PDF", key="extract_button"):
            with st.spinner("Extracting names from PDF..."):
                df_names = extract_names_from_pdf(uploaded_file)
                st.session_state.extracted_names = df_names
                st.success(f"Extracted {len(df_names)} entries")
        
        # Step 2: Review and edit
        if st.session_state.extracted_names is not None:
            st.subheader("Review Extracted Names")
            st.markdown("**Review the extracted names below. You can edit the CSV directly before matching.**")
            
            # Editable dataframe
            edited_df = st.data_editor(
                st.session_state.extracted_names,
                num_rows="dynamic",
                use_container_width=True,
                height=400
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Option to manually split concatenated names
                if st.button("🔍 Auto-detect more splits", help="Run additional detection for concatenated names"):
                    with st.spinner("Detecting more entity boundaries..."):
                        expanded_names = []
                        for _, row in edited_df.iterrows():
                            entities = detect_entity_boundaries(row['name'])
                            if len(entities) > 1:
                                for entity in entities:
                                    expanded_names.append({
                                        'name': entity,
                                        'page': row['page'],
                                        'original_name': entity
                                    })
                            else:
                                expanded_names.append(row.to_dict())
                        
                        st.session_state.extracted_names = pd.DataFrame(expanded_names)
                        st.rerun()
            
            with col2:
                # Proceed to matching
                if st.button("✓ Looks Good - Match Names", key="pdf_match_button", type="primary"):
                    with st.spinner("Matching names against company database..."):
                        results_df = match_names(edited_df, api_choice, refinitiv_key, min_similarity, max_results)
                        st.session_state.results = results_df
                        st.session_state.extracted_names = None  # Clear for next upload

with tab2:
    st.header("Paste Company Names")
    st.markdown("Enter company names (one per line, or separated by commas/semicolons)")
    
    text_input = st.text_area("Company Names", height=200, 
                              placeholder="Company Name 1\nCompany Name 2\nCompany Name 3...")
    
    if text_input:
        if st.button("Match Names", key="text_button"):
            with st.spinner("Parsing names..."):
                df_names = parse_text_input(text_input)
                st.info(f"Parsed {len(df_names)} company names")
                
                with st.expander("Preview Parsed Names"):
                    st.dataframe(df_names)
            
            with st.spinner("Matching names against company database..."):
                results_df = match_names(df_names, api_choice, refinitiv_key, min_similarity, max_results)
                st.session_state.results = results_df

# Display results
if st.session_state.results is not None:
    st.header("📊 Results")
    
    results_df = st.session_state.results
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Names", len(results_df))
    with col2:
        matched = results_df['matched_name'].notna().sum()
        st.metric("Matched", matched)
    with col3:
        unmatched = results_df['matched_name'].isna().sum()
        st.metric("Unmatched", unmatched)
    
    # Filter options
    st.subheader("Filter Results")
    col1, col2 = st.columns(2)
    
    with col1:
        show_matched = st.checkbox("Show Matched", value=True)
    with col2:
        show_unmatched = st.checkbox("Show Unmatched", value=True)
    
    # Apply filters
    filtered_df = results_df.copy()
    if not show_matched:
        filtered_df = filtered_df[filtered_df['matched_name'].isna()]
    if not show_unmatched:
        filtered_df = filtered_df[filtered_df['matched_name'].notna()]
    
    # Display results
    st.dataframe(filtered_df, use_container_width=True)
    
    # Export options
    st.subheader("Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="company_matches.csv",
            mime="text/csv"
        )
    
    with col2:
        # Excel export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Matches')
        
        st.download_button(
            label="📥 Download Excel",
            data=buffer.getvalue(),
            file_name="company_matches.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Footer
st.markdown("---")
st.markdown("""
**Sources:**
- [OpenCorporates API Documentation](https://api.opencorporates.com/documentation/API-Reference)
- [Refinitiv Data Platform API](https://developers.refinitiv.com/en/api-catalog/refinitiv-data-platform/refinitiv-data-platform-apis)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)
- [FuzzyWuzzy String Matching](https://github.com/seatgeek/fuzzywuzzy)
""")
