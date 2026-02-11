"""
Entity Boundary Detection Tester

Test and refine the entity splitting logic with your actual data.
Use this to improve detection patterns before running the main app.

Usage:
    python test_entity_detection.py "Your concatenated entity string"
    
Reference: Custom implementation for handling poorly formatted PDF extractions
"""

import re

def detect_entity_boundaries(text):
    """
    Detect where one entity name ends and another begins on the same line.
    Uses organizational keywords and capitalization patterns to identify entity boundaries.
    """
    
    # Common organizational endings that mark entity boundaries
    org_endings = [
        r'\bInstitute(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bFoundation(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bCoalition(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bAlliance(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bAssociation(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bCouncil(?:\s+on\s+[A-Za-z\s]+)?',
        r'\bCentre?(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bNetwork(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bGroup(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bSociety(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bTrust(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bFund(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bOrganizations?(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bInitiative(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bProject(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        r'\bPrograms?(?:\s+(?:for|of|on)\s+[A-Za-z\s]+)?',
        # Corporate suffixes
        r'\bCorporation',
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
            entity_ends.append((match.end(), match.group()))
    
    # Sort by position
    entity_ends.sort()
    
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
        entities.append(remaining)
    
    # Filter out very short entities (likely false positives)
    entities = [e for e in entities if len(e) > 3]
    
    return entities if entities else [text]

def test_detection(text):
    """Test entity detection and show results"""
    print(f"Input text: {text}")
    print(f"Length: {len(text)} characters")
    print("-" * 80)
    
    entities = detect_entity_boundaries(text)
    
    print(f"Detected {len(entities)} entities:")
    print("-" * 80)
    
    for i, entity in enumerate(entities, 1):
        print(f"{i}. {entity}")
    
    print("-" * 80)

if __name__ == "__main__":
    import sys
    
    # Test cases
    test_cases = [
        "Abundance Institute George W Bush Foundation Open Ran Policy Coalition",
        "Microsoft Corporation Apple Inc Google LLC",
        "The Climate Action Network European Policy Centre Tech Alliance",
        "Amazon.com, Inc. Meta Platforms, Inc. Tesla, Inc.",
        "Deutsche Bank AG Volkswagen AG Siemens AG",
        "Council on Foreign Relations Brookings Institution Atlantic Council",
        "American Enterprise Institute Heritage Foundation Cato Institute",
        "Open Society Foundations Bill & Melinda Gates Foundation Ford Foundation"
    ]
    
    if len(sys.argv) > 1:
        # Test with command line argument
        input_text = " ".join(sys.argv[1:])
        test_detection(input_text)
    else:
        # Run all test cases
        print("ENTITY BOUNDARY DETECTION TESTS")
        print("=" * 80)
        print()
        
        for test in test_cases:
            test_detection(test)
            print()
            print("=" * 80)
            print()

"""
Example output:

Input text: Abundance Institute George W Bush Foundation Open Ran Policy Coalition
Length: 70 characters
--------------------------------------------------------------------------------
Detected 3 entities:
--------------------------------------------------------------------------------
1. Abundance Institute
2. George W Bush Foundation
3. Open Ran Policy Coalition
--------------------------------------------------------------------------------

To add custom patterns, modify the entity_starters list in detect_entity_boundaries()
"""
