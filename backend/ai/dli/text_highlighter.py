"""
Text Highlighter Module

Applies color coding to RPP text based on detected keywords.
Generates HTML with color-coded spans and keyword statistics.
"""

import re
from typing import Dict, List, Tuple
from html import escape


class TextHighlighter:
    """
    Highlights keywords in text with color-coded HTML spans.
    
    Color scheme:
    - Green: Strong deep learning keywords (high pedagogical value)
    - Red: Surface learning indicators (negative pedagogical value)
    - Blue: Digital integration keywords
    - Yellow: Medium-strength keywords
    """
    
    def __init__(self):
        """Initialize TextHighlighter."""
        pass
    
    def highlight_text(self, text: str, keyword_matches: Dict) -> Dict:
        """
        Apply HTML spans with color classes to keywords.
        
        Args:
            text: Original RPP text content
            keyword_matches: Detected keywords by aspect and strength
                Structure: {
                    'mindful': {
                        'aktivasi_fokus': {'strong': [...], 'medium': [...], 'weak': [...]},
                        ...
                    },
                    'meaningful': {...},
                    ...
                }
        
        Returns:
            Dict with structure: {
                'html': '<p>Siswa <span class="highlight-green">berdiskusi</span>...</p>',
                'keywords_found': {
                    'green': [...],
                    'red': [...],
                    'blue': [...],
                    'yellow': [...]
                },
                'statistics': {'green': 15, 'red': 3, 'blue': 5, 'yellow': 8}
            }
        """
        # Flatten keywords by color category
        keywords_by_color = self._categorize_keywords_by_color(keyword_matches)
        
        # Sort keywords by length (longest first) to avoid partial matches
        all_keywords = []
        for color, keywords in keywords_by_color.items():
            for keyword in keywords:
                all_keywords.append((keyword, color))
        
        # Sort by length descending
        all_keywords.sort(key=lambda x: len(x[0]), reverse=True)
        
        # Escape HTML in original text
        escaped_text = escape(text)
        
        # Track which keywords were actually found in text
        found_keywords = {
            'green': [],
            'red': [],
            'blue': [],
            'yellow': []
        }
        
        # Apply highlights
        # Use a different approach: mark positions first, then apply highlights
        # This prevents nested highlights
        highlighted_text = escaped_text
        
        # Track already highlighted positions to avoid overlaps
        highlighted_positions = set()
        
        # Collect all matches with positions
        matches_with_positions = []
        for keyword, color in all_keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            for match in pattern.finditer(highlighted_text):
                start, end = match.span()
                # Check if this position overlaps with already highlighted text
                if not any(pos in highlighted_positions for pos in range(start, end)):
                    matches_with_positions.append((start, end, match.group(), color, keyword))
                    # Mark these positions as highlighted
                    highlighted_positions.update(range(start, end))
        
        # Sort matches by start position (descending) to replace from end to start
        matches_with_positions.sort(key=lambda x: x[0], reverse=True)
        
        # Apply highlights from end to start to preserve positions
        for start, end, matched_text, color, keyword in matches_with_positions:
            # Track found keyword
            if keyword not in found_keywords[color]:
                found_keywords[color].append(keyword)
            
            # Replace with highlighted version
            highlighted_text = (
                highlighted_text[:start] +
                f'<span class="highlight-{color}">{matched_text}</span>' +
                highlighted_text[end:]
            )
        
        # Calculate statistics
        statistics = {
            'green': len(found_keywords['green']),
            'red': len(found_keywords['red']),
            'blue': len(found_keywords['blue']),
            'yellow': len(found_keywords['yellow'])
        }
        
        return {
            'html': highlighted_text,
            'keywords_found': found_keywords,
            'statistics': statistics
        }
    
    def _categorize_keywords_by_color(self, keyword_matches: Dict) -> Dict[str, List[str]]:
        """
        Categorize keywords by color based on aspect and strength.
        
        Color mapping:
        - Green: Strong keywords from all aspects (except digital)
        - Red: Weak keywords (surface learning)
        - Blue: All keywords from digital aspect
        - Yellow: Medium keywords from all aspects (except digital)
        
        Args:
            keyword_matches: Detected keywords by aspect and strength
        
        Returns:
            Dict with structure: {
                'green': [all strong keywords],
                'red': [all weak keywords],
                'blue': [all digital keywords],
                'yellow': [all medium keywords]
            }
        """
        keywords_by_color = {
            'green': [],
            'red': [],
            'blue': [],
            'yellow': []
        }
        
        for aspect, sub_aspects in keyword_matches.items():
            for sub_aspect, strength_keywords in sub_aspects.items():
                # Digital aspect: all keywords are blue
                if aspect == 'digital':
                    for strength in ['strong', 'medium', 'weak']:
                        if strength in strength_keywords:
                            keywords_by_color['blue'].extend(strength_keywords[strength])
                else:
                    # Other aspects: color by strength
                    if 'strong' in strength_keywords:
                        keywords_by_color['green'].extend(strength_keywords['strong'])
                    
                    if 'medium' in strength_keywords:
                        keywords_by_color['yellow'].extend(strength_keywords['medium'])
                    
                    if 'weak' in strength_keywords:
                        keywords_by_color['red'].extend(strength_keywords['weak'])
        
        # Remove duplicates while preserving order
        for color in keywords_by_color:
            keywords_by_color[color] = list(dict.fromkeys(keywords_by_color[color]))
        
        return keywords_by_color
