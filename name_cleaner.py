"""
Enhanced name cleaning utilities for the company matching tool

Additional preprocessing functions to improve match quality
"""

import re
from typing import List, Tuple

class NameCleaner:
    """Advanced company name cleaning and normalization"""
    
    # Extended suffix list with variations
    LEGAL_SUFFIXES = [
        # English
        r'\bLimited\b', r'\bLtd\.?\b', r'\bLLC\b', r'\bL\.L\.C\.?\b',
        r'\bInc\.?\b', r'\bIncorporated\b', r'\bCorp\.?\b', r'\bCorporation\b',
        r'\bCo\.?\b', r'\bCompany\b', r'\bPLC\b', r'\bP\.L\.C\.?\b',
        
        # German
        r'\bGmbH\b', r'\bAG\b', r'\bKG\b', r'\bmbH\b', r'\be\.V\.?\b',
        
        # French
        r'\bS\.A\.?\b', r'\bSA\b', r'\bS\.A\.R\.L\.?\b', r'\bSARL\b',
        r'\bSociété Anonyme\b', r'\bS\.A\.S\.?\b',
        
        # Italian
        r'\bS\.p\.A\.?\b', r'\bSpA\b', r'\bS\.r\.l\.?\b', r'\bSrl\b',
        
        # Dutch
        r'\bN\.V\.?\b', r'\bNV\b', r'\bB\.V\.?\b', r'\bBV\b',
        
        # Nordic
        r'\bAB\b', r'\bA/S\b', r'\bA\.S\.?\b', r'\bOyj\b', r'\bAS\b',
        
        # Asian
        r'\bPte\.?\b', r'\bLtd\.?\b', r'\bCo\.,\s*Ltd\.?\b',
        r'\bSdn\.?\s+Bhd\.?\b', r'\bK\.K\.?\b', r'\bCo\., Ltd\.?\b',
        
        # Other
        r'\bPty\.?\b', r'\bS\.C\.?\b', r'\bLtda\.?\b',
        
        # Geographic indicators
        r'\([A-Z]{2,}\)', r'\(Deutschland\)', r'\(UK\)', r'\(US\)',
        r'\(Europe\)', r'\(Asia\)', r'\(International\)'
    ]
    
    # Common words to remove for matching
    NOISE_WORDS = [
        r'\bThe\b', r'\bGroup\b', r'\bHoldings?\b', r'\bInternational\b',
        r'\bGlobal\b', r'\bWorldwide\b', r'\b&\s*Co\.?\b'
    ]
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize company name for better matching"""
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove punctuation except ampersands
        normalized = re.sub(r'[^\w\s&-]', ' ', normalized)
        
        # Standardize ampersands
        normalized = re.sub(r'\s+&\s+', ' and ', normalized)
        
        return normalized.strip()
    
    @classmethod
    def remove_legal_suffixes(cls, name: str) -> str:
        """Remove legal entity suffixes"""
        cleaned = name
        
        for suffix in cls.LEGAL_SUFFIXES:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    @classmethod
    def remove_noise_words(cls, name: str) -> str:
        """Remove common noise words"""
        cleaned = name
        
        for noise in cls.NOISE_WORDS:
            cleaned = re.sub(noise, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    @classmethod
    def extract_core_name(cls, name: str) -> str:
        """Extract core business name for matching"""
        # Normalize
        core = cls.normalize_name(name)
        
        # Remove suffixes
        core = cls.remove_legal_suffixes(core)
        
        # Remove noise words
        core = cls.remove_noise_words(core)
        
        # Clean up any remaining artifacts
        core = re.sub(r'\s+', ' ', core).strip()
        
        return core
    
    @staticmethod
    def detect_parent_subsidiary(names: List[str]) -> List[Tuple[str, str]]:
        """Detect potential parent-subsidiary relationships"""
        relationships = []
        
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                # Check if one name contains the other
                if name1.lower() in name2.lower():
                    relationships.append((name1, name2))
                elif name2.lower() in name1.lower():
                    relationships.append((name2, name1))
        
        return relationships
    
    @staticmethod
    def split_on_delimiters(text: str) -> List[str]:
        """Split text on multiple delimiters"""
        # Split on newlines, commas, semicolons, pipes
        names = re.split(r'[\n,;|]', text)
        
        # Clean and filter
        return [name.strip() for name in names if name.strip()]
    
    @staticmethod
    def detect_address_contamination(name: str) -> bool:
        """Detect if name contains address information"""
        address_patterns = [
            r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)',
            r'\d{5}(-\d{4})?',  # US ZIP codes
            r'[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}',  # UK postcodes
            r'Suite\s+\d+',
            r'Floor\s+\d+',
            r'P\.?O\.?\s+Box'
        ]
        
        for pattern in address_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def preprocess_for_api(cls, name: str) -> str:
        """Prepare name for API search"""
        # Keep original name but remove obvious garbage
        processed = name.strip()
        
        # Remove leading/trailing punctuation
        processed = re.sub(r'^[^\w]+|[^\w]+$', '', processed)
        
        # Collapse multiple spaces
        processed = re.sub(r'\s+', ' ', processed)
        
        return processed

# Example usage and tests
if __name__ == "__main__":
    cleaner = NameCleaner()
    
    test_names = [
        "Amazon.com, Inc.",
        "Volkswagen AG (Deutschland)",
        "Société Générale S.A.",
        "HSBC Holdings plc",
        "Samsung Electronics Co., Ltd.",
        "Microsoft Corporation",
        "The ABC Group Holdings Limited"
    ]
    
    print("Testing name cleaning utilities:\n")
    
    for name in test_names:
        normalized = cleaner.normalize_name(name)
        core = cleaner.extract_core_name(name)
        
        print(f"Original:    {name}")
        print(f"Normalized:  {normalized}")
        print(f"Core:        {core}")
        print("-" * 60)
