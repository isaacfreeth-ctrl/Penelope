"""
Advanced Entity Splitting with Multiple Strategies

This provides a more sophisticated approach that combines:
1. Pattern-based detection (existing)
2. Comma/punctuation detection
3. Capitalization pattern analysis
4. Manual override capabilities

Use this when standard detection fails on complex strings.
"""

import re
from typing import List

def split_on_commas_and_patterns(text: str) -> List[str]:
    """
    First split on commas, then apply pattern detection to each segment.
    This handles cases like: "Entity A, Entity B Entity C"
    """
    # Split on commas first
    comma_segments = [s.strip() for s in text.split(',') if s.strip()]
    
    all_entities = []
    for segment in comma_segments:
        # Apply pattern detection to each comma-separated segment
        entities = detect_by_patterns(segment)
        all_entities.extend(entities)
    
    return all_entities

def detect_by_patterns(text: str) -> List[str]:
    """Pattern-based detection (same as app.py)"""
    org_endings = [
        r'\bChamber\s+[Oo]f\s+Commerce',
        r'\bChurch\s+[Oo]f\s+Christ',
        r'\bInaugural\s+Committee',
        r'\bBuilding\s+Congress',
        r'\bCommittee',
        r'\bInstitutes?',
        r'\bFoundations?',
        r'\bCoalitions?',
        r'\bCongress(?:es)?',
    ]
    
    entity_ends = []
    for pattern in org_endings:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            full_match_end = match.end()
            if full_match_end < len(text):
                remaining = text[full_match_end:].lstrip()
                if remaining and remaining[0].isupper():
                    entity_ends.append(full_match_end)
            else:
                entity_ends.append(full_match_end)
    
    if not entity_ends:
        return [text]
    
    entity_ends = sorted(set(entity_ends))
    
    entities = []
    start = 0
    for end_pos in entity_ends:
        entity = text[start:end_pos].strip()
        if entity and len(entity) > 3:
            entities.append(entity)
        start = end_pos
    
    remaining = text[start:].strip()
    if remaining and len(remaining) > 3:
        entities.append(remaining)
    
    return entities if entities else [text]

def detect_by_capitalization(text: str, min_entity_length: int = 10) -> List[str]:
    """
    Split when we see: lowercase word, space, Uppercase Word pattern.
    This catches entities without clear type endings.
    
    Example: "Dallas Regional Chamber Netchoice United"
              Split between "Chamber" and "Netchoice"
    """
    # Find positions where lowercase followed by space then uppercase
    split_points = []
    
    # Pattern: word ending in lowercase, space, word starting with uppercase
    for match in re.finditer(r'([a-z])\s+([A-Z][a-z]*(?:[A-Z][a-z]*)*)', text):
        # Check if this looks like a new entity (not just a proper noun in same entity)
        pos = match.start(2)  # Start of the capitalized word
        
        # Don't split if the capitalized word is very short (likely part of name)
        if len(match.group(2)) >= 3:
            split_points.append(pos)
    
    if not split_points:
        return [text]
    
    entities = []
    start = 0
    for pos in split_points:
        entity = text[start:pos].strip()
        if entity and len(entity) >= min_entity_length:
            entities.append(entity)
        start = pos
    
    # Add remaining
    remaining = text[start:].strip()
    if remaining and len(remaining) >= min_entity_length:
        entities.append(remaining)
    
    return entities if entities else [text]

def smart_split(text: str, aggressive: bool = False) -> List[str]:
    """
    Combine multiple strategies for best results.
    
    Args:
        text: Concatenated entity string
        aggressive: If True, use capitalization-based splitting as well
    
    Returns:
        List of individual entities
    """
    # Strategy 1: Split on commas first
    entities = split_on_commas_and_patterns(text)
    
    # Strategy 2: If aggressive mode, further split by capitalization
    if aggressive:
        final_entities = []
        for entity in entities:
            cap_split = detect_by_capitalization(entity, min_entity_length=8)
            final_entities.extend(cap_split)
        return final_entities
    
    return entities

# Testing
if __name__ == "__main__":
    test_cases = [
        "Delaware State Chamber Of United States Pan Asian American Commerce, New York Building Congress Chamber Of Commerce Education",
        "Dallas Regional Chamber Netchoice United Church of Christ",
        "Bluffs Area Chamber Of Commerce Nebraska Chamber Of Commerce Trump Vance Inaugural Committee",
    ]
    
    print("=" * 80)
    print("STANDARD SPLITTING (Pattern-based)")
    print("=" * 80)
    for test in test_cases:
        print(f"\nInput: {test[:70]}...")
        result = smart_split(test, aggressive=False)
        print(f"Found {len(result)} entities:")
        for i, e in enumerate(result, 1):
            print(f"  {i}. {e}")
    
    print("\n" + "=" * 80)
    print("AGGRESSIVE SPLITTING (Pattern + Capitalization)")
    print("=" * 80)
    for test in test_cases:
        print(f"\nInput: {test[:70]}...")
        result = smart_split(test, aggressive=True)
        print(f"Found {len(result)} entities:")
        for i, e in enumerate(result, 1):
            print(f"  {i}. {e}")
