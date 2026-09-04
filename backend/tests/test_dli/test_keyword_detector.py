"""
Unit tests for KeywordDetector module
"""

import pytest
from backend.ai.dli.keyword_detector import KeywordDetector


class TestKeywordDetector:
    """Test suite for KeywordDetector class"""
    
    @pytest.fixture
    def detector(self):
        """Create KeywordDetector instance for testing"""
        return KeywordDetector()
    
    def test_load_keywords(self, detector):
        """Test that keyword dictionaries are loaded correctly"""
        assert 'mindful' in detector.keywords
        assert 'meaningful' in detector.keywords
        assert 'joyful' in detector.keywords
        assert 'pedagogis' in detector.keywords
        assert 'digital' in detector.keywords
    
    def test_detect_keywords_case_insensitive(self, detector):
        """Test case-insensitive keyword detection"""
        # Test with mixed case
        text = "Siswa BERDISKUSI kelompok untuk MEMECAHKAN masalah"
        matches = detector.detect_keywords(text)
        
        # Should detect "berdiskusi kelompok" and "memecahkan masalah"
        joyful_matches = matches['joyful']['kolaborasi']['strong']
        pedagogis_matches = matches['pedagogis']['aktivator']['strong']
        
        assert any('berdiskusi kelompok' in kw.lower() for kw in joyful_matches)
        assert any('memecahkan masalah' in kw.lower() for kw in pedagogis_matches)
    
    def test_detect_strong_keywords(self, detector):
        """Test detection of strong deep learning keywords"""
        text = "Siswa merefleksikan pengalaman dan berdiskusi kelompok"
        matches = detector.detect_keywords(text)
        
        # Check mindful strong keywords
        mindful_strong = matches['mindful']['metakognisi']['strong']
        assert len(mindful_strong) > 0
        
        # Check joyful strong keywords
        joyful_strong = matches['joyful']['kolaborasi']['strong']
        assert len(joyful_strong) > 0
    
    def test_detect_weak_keywords(self, detector):
        """Test detection of weak surface learning keywords"""
        text = "Guru menjelaskan materi dan siswa mencatat"
        matches = detector.detect_keywords(text)
        
        # Check pedagogis weak keywords
        pedagogis_weak = matches['pedagogis']['aktivator']['weak']
        assert len(pedagogis_weak) > 0
    
    def test_calculate_aspect_score_positive(self, detector):
        """Test aspect score calculation with positive keywords"""
        # Simulate matches with only strong keywords
        aspect_matches = {
            'sub1': {
                'strong': ['keyword1', 'keyword2'],  # 2 * 4 = 8
                'medium': [],
                'weak': []
            }
        }
        
        score = detector.calculate_aspect_score(aspect_matches)
        assert score == 100.0  # All keywords are strong
    
    def test_calculate_aspect_score_mixed(self, detector):
        """Test aspect score calculation with mixed keywords — dominance penalty applies"""
        aspect_matches = {
            'sub1': {
                'strong': ['keyword1'],  # 1 * 4 = 4
                'medium': ['keyword2'],  # 1 * 3 = 3
                'weak': ['keyword3']     # 1 * -2 = -2, weak_ratio=1/3 > 30% → ×0.7
            }
        }

        # Raw score: 4 + 3 - 2 = 5, max: 7, normalized: 71.43
        # weak_ratio = 1/3 ≈ 0.33 > 0.30 → multiplier 0.7
        # final: 71.43 * 0.7 ≈ 50.0
        score = detector.calculate_aspect_score(aspect_matches)
        assert 48.0 < score < 52.0

    def test_dominance_penalty_high(self, detector):
        """Test heavy dominance penalty when weak ratio > 50%"""
        aspect_matches = {
            'sub1': {
                'strong': ['kw1'],
                'medium': [],
                'weak': ['kw2', 'kw3']  # weak_ratio = 2/3 > 50% → ×0.4
            }
        }
        score = detector.calculate_aspect_score(aspect_matches)
        # Without penalty: (4-4)/4 * 100 = 0 → clamped to 0
        # Even with penalty, score should be very low
        assert score <= 40.0

    def test_dominance_penalty_absolute_cap(self, detector):
        """Test absolute cap when weak count >= 5"""
        aspect_matches = {
            'sub1': {
                'strong': ['kw1', 'kw2', 'kw3', 'kw4', 'kw5', 'kw6'],
                'medium': ['kw7', 'kw8', 'kw9'],
                'weak': ['w1', 'w2', 'w3', 'w4', 'w5']  # 5 weak → cap at 40
            }
        }
        score = detector.calculate_aspect_score(aspect_matches)
        assert score <= 40.0
    
    def test_calculate_aspect_score_no_keywords(self, detector):
        """Test aspect score with no keywords found"""
        aspect_matches = {
            'sub1': {
                'strong': [],
                'medium': [],
                'weak': []
            }
        }
        
        score = detector.calculate_aspect_score(aspect_matches)
        assert score == 0.0
    
    def test_calculate_aspect_score_range(self, detector):
        """Test that aspect scores are clamped to 0-100 range"""
        # Test with many weak keywords (should not go below 0)
        aspect_matches = {
            'sub1': {
                'strong': [],
                'medium': [],
                'weak': ['kw1', 'kw2', 'kw3', 'kw4', 'kw5']
            }
        }
        
        score = detector.calculate_aspect_score(aspect_matches)
        assert score == 0.0  # Should be clamped to 0
    
    def test_get_all_keywords_flat(self, detector):
        """Test flattening of all keywords by strength"""
        flat = detector.get_all_keywords_flat()
        
        assert 'strong' in flat
        assert 'medium' in flat
        assert 'weak' in flat
        
        # Check that we have keywords in each category
        assert len(flat['strong']) > 0
        assert len(flat['medium']) > 0
        assert len(flat['weak']) > 0
        
        # Check no duplicates
        assert len(flat['strong']) == len(set(flat['strong']))
    
    def test_real_rpp_sample(self, detector):
        """Test with a realistic RPP sample"""
        rpp_text = """
        KEGIATAN PEMBELAJARAN:
        
        1. Pendahuluan (10 menit)
           - Guru memberikan apersepsi dengan pertanyaan pemantik
           - Siswa merefleksikan pengalaman sebelumnya
        
        2. Kegiatan Inti (60 menit)
           - Siswa berdiskusi kelompok untuk memecahkan masalah
           - Setiap kelompok menganalisis kasus yang berbeda
           - Siswa mempresentasikan hasil diskusi
           - Menggunakan simulasi PhET untuk eksperimen virtual
        
        3. Penutup (20 menit)
           - Siswa membuat refleksi tentang apa yang dipelajari
           - Penilaian sejawat untuk hasil presentasi
        """
        
        matches = detector.detect_keywords(rpp_text)
        
        # Should detect multiple aspects
        mindful_score = detector.calculate_aspect_score(matches['mindful'])
        meaningful_score = detector.calculate_aspect_score(matches['meaningful'])
        joyful_score = detector.calculate_aspect_score(matches['joyful'])
        pedagogis_score = detector.calculate_aspect_score(matches['pedagogis'])
        digital_score = detector.calculate_aspect_score(matches['digital'])
        
        # All scores should be > 0 for this good RPP
        assert mindful_score > 0
        assert meaningful_score > 0
        assert joyful_score > 0
        assert pedagogis_score > 0
        assert digital_score > 0
