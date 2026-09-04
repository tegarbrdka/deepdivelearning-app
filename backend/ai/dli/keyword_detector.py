"""
Keyword Detector Module

Detects pedagogical keywords in RPP text and classifies by strength.
Uses case-insensitive matching with keyword dictionaries.
"""

import json
import os
import re
from typing import Dict, List, Tuple
from pathlib import Path


class KeywordDetector:
    """
    Detects keywords in text based on predefined dictionaries.
    
    Supports three strength levels:
    - strong: +4 points (deep learning indicators)
    - medium: +3 points (neutral/moderate indicators)
    - weak: -2 points (surface learning indicators)
    """
    
    def __init__(self, keywords_dir: str = None):
        """
        Initialize KeywordDetector with keyword dictionaries.
        
        Args:
            keywords_dir: Path to directory containing keyword JSON files.
                         Defaults to backend/ai/dli/keywords/
        """
        if keywords_dir is None:
            # Default to keywords directory relative to this file
            current_dir = Path(__file__).parent
            keywords_dir = current_dir / "keywords"
        
        self.keywords_dir = Path(keywords_dir)
        self.keywords = self._load_keywords()
    
    def _load_keywords(self) -> Dict:
        """
        Load all keyword dictionaries from JSON files.
        
        Returns:
            Dict with structure: {
                'mindful': {'aktivasi_fokus': {'strong': [...], 'medium': [...], 'weak': [...]}, ...},
                'meaningful': {...},
                ...
            }
        """
        keywords = {}
        
        # Load each aspect's keyword file
        aspects = ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']
        
        for aspect in aspects:
            file_path = self.keywords_dir / f"{aspect}.json"
            
            if not file_path.exists():
                raise FileNotFoundError(f"Keyword file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                keywords[aspect] = json.load(f)
        
        return keywords
    
    def detect_keywords(self, text: str) -> Dict:
        """
        Detect all keywords in text across all aspects.
        
        Args:
            text: RPP text content to analyze
        
        Returns:
            Dict with structure: {
                'mindful': {
                    'aktivasi_fokus': {'strong': [...], 'medium': [...], 'weak': [...]},
                    'metakognisi': {...},
                    ...
                },
                'meaningful': {...},
                ...
            }
        """
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        matches = {}
        
        for aspect, sub_aspects in self.keywords.items():
            matches[aspect] = {}
            
            for sub_aspect, strength_keywords in sub_aspects.items():
                matches[aspect][sub_aspect] = {
                    'strong': [],
                    'medium': [],
                    'weak': []
                }
                
                # Check each strength level
                for strength in ['strong', 'medium', 'weak']:
                    if strength not in strength_keywords:
                        continue
                    
                    for keyword in strength_keywords[strength]:
                        # Case-insensitive search
                        if keyword.lower() in text_lower:
                            matches[aspect][sub_aspect][strength].append(keyword)
        
        return matches
    
    # Dominance penalty thresholds
    # If weak keywords dominate, apply a multiplier to penalize the score
    DOMINANCE_PENALTY_HIGH = 0.5   # weak ratio > 50% → multiply score by 0.4
    DOMINANCE_PENALTY_MED  = 0.3   # weak ratio > 30% → multiply score by 0.7
    DOMINANCE_MULTIPLIER_HIGH = 0.4
    DOMINANCE_MULTIPLIER_MED  = 0.7
    # Absolute cap: if weak count alone exceeds this, score cannot exceed 40
    WEAK_ABSOLUTE_CAP_COUNT = 5
    WEAK_ABSOLUTE_CAP_SCORE = 40.0

    def calculate_aspect_score(self, aspect_matches: Dict) -> float:
        """
        Calculate score for one aspect based on keyword matches.

        Scoring:
        - Strong keywords: +4 points each
        - Medium keywords: +3 points each
        - Weak keywords:   -2 points each (surface learning / KKO Level 1)

        Dominance Penalty (Negative Constraints):
        - If weak_ratio > 50%: score × 0.4  (heavy surface learning dominance)
        - If weak_ratio > 30%: score × 0.7  (moderate surface learning dominance)
        - If total weak count > 5: score capped at 40 (absolute cap)

        Score is normalized to 0-100 range.

        Args:
            aspect_matches: Matches for one aspect with structure:
                {
                    'sub_aspect1': {'strong': [...], 'medium': [...], 'weak': [...]},
                    'sub_aspect2': {...},
                    ...
                }

        Returns:
            Score between 0 and 100
        """
        total_score = 0
        max_possible_score = 0
        total_strong = 0
        total_medium = 0
        total_weak = 0

        for sub_aspect, strength_matches in aspect_matches.items():
            strong_count = len(strength_matches.get('strong', []))
            medium_count = len(strength_matches.get('medium', []))
            weak_count   = len(strength_matches.get('weak', []))

            total_strong += strong_count
            total_medium += medium_count
            total_weak   += weak_count

            sub_score     = (strong_count * 4) + (medium_count * 3) - (weak_count * 2)
            max_sub_score = (strong_count * 4) + (medium_count * 3)

            total_score       += sub_score
            max_possible_score += max_sub_score

        # Normalize to 0-100
        if max_possible_score == 0:
            return 0.0

        normalized_score = (total_score / max_possible_score) * 100
        normalized_score = max(0.0, min(100.0, normalized_score))

        # --- Dominance Penalty ---
        total_keywords = total_strong + total_medium + total_weak
        if total_keywords > 0:
            weak_ratio = total_weak / total_keywords

            if weak_ratio > self.DOMINANCE_PENALTY_HIGH:
                normalized_score *= self.DOMINANCE_MULTIPLIER_HIGH
            elif weak_ratio > self.DOMINANCE_PENALTY_MED:
                normalized_score *= self.DOMINANCE_MULTIPLIER_MED

        # Absolute cap: too many surface learning keywords → cannot exceed 40
        if total_weak >= self.WEAK_ABSOLUTE_CAP_COUNT:
            normalized_score = min(normalized_score, self.WEAK_ABSOLUTE_CAP_SCORE)

        return round(max(0.0, min(100.0, normalized_score)), 2)
    
    def calculate_sub_aspect_score(self, sub_aspect_matches: Dict) -> float:
        """
        Calculate score for one sub-aspect with dominance penalty.

        Args:
            sub_aspect_matches: {'strong': [...], 'medium': [...], 'weak': [...]}

        Returns:
            Score between 0 and 100
        """
        strong_count = len(sub_aspect_matches.get('strong', []))
        medium_count = len(sub_aspect_matches.get('medium', []))
        weak_count   = len(sub_aspect_matches.get('weak', []))

        raw_score = (strong_count * 4) + (medium_count * 3) - (weak_count * 2)
        max_score = (strong_count * 4) + (medium_count * 3)

        if max_score == 0:
            return 0.0

        normalized_score = (raw_score / max_score) * 100
        normalized_score = max(0.0, min(100.0, normalized_score))

        # Dominance penalty
        total_keywords = strong_count + medium_count + weak_count
        if total_keywords > 0:
            weak_ratio = weak_count / total_keywords
            if weak_ratio > self.DOMINANCE_PENALTY_HIGH:
                normalized_score *= self.DOMINANCE_MULTIPLIER_HIGH
            elif weak_ratio > self.DOMINANCE_PENALTY_MED:
                normalized_score *= self.DOMINANCE_MULTIPLIER_MED

        if weak_count >= self.WEAK_ABSOLUTE_CAP_COUNT:
            normalized_score = min(normalized_score, self.WEAK_ABSOLUTE_CAP_SCORE)

        return round(max(0.0, min(100.0, normalized_score)), 2)
    
    def get_all_keywords_flat(self) -> Dict[str, List[str]]:
        """
        Get all keywords flattened by strength across all aspects.
        
        Useful for text highlighting.
        
        Returns:
            Dict with structure: {
                'strong': [all strong keywords],
                'medium': [all medium keywords],
                'weak': [all weak keywords]
            }
        """
        flat_keywords = {
            'strong': [],
            'medium': [],
            'weak': []
        }
        
        for aspect, sub_aspects in self.keywords.items():
            for sub_aspect, strength_keywords in sub_aspects.items():
                for strength in ['strong', 'medium', 'weak']:
                    if strength in strength_keywords:
                        flat_keywords[strength].extend(strength_keywords[strength])
        
        # Remove duplicates while preserving order
        for strength in flat_keywords:
            flat_keywords[strength] = list(dict.fromkeys(flat_keywords[strength]))
        
        return flat_keywords
