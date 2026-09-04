"""
DLI Analyzer Module

Orchestrates the complete Deep Learning Index analysis workflow.
Calculates scores across 5 pedagogical aspects with weighted scoring.
"""

import time
from typing import Dict, List, Optional
from .keyword_detector import KeywordDetector


class DLIAnalyzer:
    """
    Main orchestrator for Deep Learning Index analysis.
    
    Analyzes RPP documents across 5 aspects:
    - Mindful (25% weight)
    - Meaningful (25% weight)
    - Joyful (20% weight)
    - Pedagogis (15% weight)
    - Digital (15% weight)
    """
    
    # Aspect weights for DLI calculation
    ASPECT_WEIGHTS = {
        'mindful': 0.25,
        'meaningful': 0.25,
        'joyful': 0.20,
        'pedagogis': 0.15,
        'digital': 0.15
    }
    
    def __init__(self, keywords_dir: str = None):
        """
        Initialize DLIAnalyzer with KeywordDetector.
        
        Args:
            keywords_dir: Path to keyword dictionaries directory
        """
        self.keyword_detector = KeywordDetector(keywords_dir)
    
    def analyze_document(self, text: str) -> Dict:
        """
        Perform complete DLI analysis on RPP text.
        
        Args:
            text: Extracted RPP text content
        
        Returns:
            Dict containing:
                - dli_score: Overall DLI score (0-100)
                - dli_category: Category based on score
                - scores: Dict of 5 aspect scores
                - sub_scores: Dict of sub-aspect scores
                - processing_time: Time taken for analysis
        """
        start_time = time.time()
        
        # Step 1: Detect keywords across all aspects
        keyword_matches = self.keyword_detector.detect_keywords(text)
        
        # Step 2: Calculate aspect scores
        aspect_scores = self._calculate_aspect_scores(keyword_matches)
        
        # Step 3: Calculate sub-aspect scores
        sub_scores = self._calculate_sub_aspect_scores(keyword_matches)
        
        # Step 4: Calculate weighted DLI score
        dli_score = self._calculate_dli_score(aspect_scores)
        
        # Step 5: Determine DLI category
        dli_category = self._get_dli_category(dli_score)
        
        processing_time = time.time() - start_time
        
        return {
            'dli_score': round(dli_score, 2),
            'dli_category': dli_category,
            'scores': {k: round(v, 2) for k, v in aspect_scores.items()},
            'sub_scores': sub_scores,
            'keyword_matches': keyword_matches,
            'processing_time': round(processing_time, 3)
        }
    
    def _calculate_aspect_scores(self, keyword_matches: Dict) -> Dict[str, float]:
        """
        Calculate scores for all 5 main aspects.
        
        Args:
            keyword_matches: Keyword matches from KeywordDetector
        
        Returns:
            Dict with aspect names as keys and scores (0-100) as values
        """
        aspect_scores = {}
        
        for aspect in ['mindful', 'meaningful', 'joyful', 'pedagogis', 'digital']:
            aspect_matches = keyword_matches.get(aspect, {})
            score = self.keyword_detector.calculate_aspect_score(aspect_matches)
            aspect_scores[aspect] = score
        
        return aspect_scores
    
    def _calculate_sub_aspect_scores(self, keyword_matches: Dict) -> Dict:
        """
        Calculate scores for all sub-aspects.
        
        Args:
            keyword_matches: Keyword matches from KeywordDetector
        
        Returns:
            Dict with structure:
                {
                    'mindful': {'aktivasi_fokus': 80, 'metakognisi': 90, ...},
                    'meaningful': {...},
                    ...
                }
        """
        sub_scores = {}
        
        # Mindful sub-aspects
        mindful_matches = keyword_matches.get('mindful', {})
        sub_scores['mindful'] = {
            'aktivasi_fokus': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    mindful_matches.get('aktivasi_fokus', {})
                ), 2
            ),
            'metakognisi': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    mindful_matches.get('metakognisi', {})
                ), 2
            ),
            'kesadaran_fisik': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    mindful_matches.get('kesadaran_fisik', {})
                ), 2
            )
        }
        
        # Meaningful sub-aspects
        meaningful_matches = keyword_matches.get('meaningful', {})
        sub_scores['meaningful'] = {
            'linking': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    meaningful_matches.get('linking', {})
                ), 2
            ),
            'realworld': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    meaningful_matches.get('realworld', {})
                ), 2
            ),
            'asesmen': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    meaningful_matches.get('asesmen', {})
                ), 2
            )
        }
        
        # Joyful sub-aspects
        joyful_matches = keyword_matches.get('joyful', {})
        sub_scores['joyful'] = {
            'flow': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    joyful_matches.get('flow', {})
                ), 2
            ),
            'kolaborasi': round(
                self.keyword_detector.calculate_sub_aspect_score(
                    joyful_matches.get('kolaborasi', {})
                ), 2
            )
        }
        
        return sub_scores
    
    def _calculate_dli_score(self, aspect_scores: Dict[str, float]) -> float:
        """
        Calculate weighted overall DLI score.
        
        Formula:
        DLI = (Mindful × 0.25) + (Meaningful × 0.25) + (Joyful × 0.20) +
              (Pedagogis × 0.15) + (Digital × 0.15)
        
        Args:
            aspect_scores: Dict of aspect scores
        
        Returns:
            Weighted DLI score (0-100)
        """
        dli_score = 0.0
        
        for aspect, weight in self.ASPECT_WEIGHTS.items():
            score = aspect_scores.get(aspect, 0.0)
            dli_score += score * weight
        
        return dli_score
    
    def _get_dli_category(self, dli_score: float) -> str:
        """
        Determine DLI category based on score.
        
        Categories:
        - Siap Implementasi: >= 70%
        - Perlu Perbaikan: 40-70%
        - Perlu Revisi Besar: < 40%
        
        Args:
            dli_score: Overall DLI score
        
        Returns:
            Category string
        """
        if dli_score >= 70:
            return "Siap Implementasi"
        elif dli_score >= 40:
            return "Perlu Perbaikan"
        else:
            return "Perlu Revisi Besar"
