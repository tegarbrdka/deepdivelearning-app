"""
Unit tests for DLIAnalyzer module
"""

import pytest
from backend.ai.dli.dli_analyzer import DLIAnalyzer


class TestDLIAnalyzer:
    """Test suite for DLIAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create DLIAnalyzer instance for testing"""
        return DLIAnalyzer()
    
    def test_analyze_document_structure(self, analyzer):
        """Test that analyze_document returns correct structure"""
        text = "Siswa berdiskusi kelompok dan merefleksikan pembelajaran"
        result = analyzer.analyze_document(text)
        
        # Check required keys
        assert 'dli_score' in result
        assert 'dli_category' in result
        assert 'scores' in result
        assert 'sub_scores' in result
        assert 'processing_time' in result
        
        # Check scores structure
        assert 'mindful' in result['scores']
        assert 'meaningful' in result['scores']
        assert 'joyful' in result['scores']
        assert 'pedagogis' in result['scores']
        assert 'digital' in result['scores']
    
    def test_dli_score_range(self, analyzer):
        """Test that DLI score is in valid range"""
        text = "Siswa menganalisis masalah dan berdiskusi kelompok"
        result = analyzer.analyze_document(text)
        
        assert 0 <= result['dli_score'] <= 100
    
    def test_aspect_scores_range(self, analyzer):
        """Test that all aspect scores are in valid range"""
        text = "Siswa berdiskusi dan menggunakan simulasi digital"
        result = analyzer.analyze_document(text)
        
        for aspect, score in result['scores'].items():
            assert 0 <= score <= 100, f"{aspect} score out of range: {score}"
    
    def test_weighted_calculation(self, analyzer):
        """Test weighted DLI calculation"""
        # Create mock aspect scores
        aspect_scores = {
            'mindful': 80.0,
            'meaningful': 90.0,
            'joyful': 70.0,
            'pedagogis': 60.0,
            'digital': 50.0
        }
        
        # Calculate expected DLI
        expected = (80 * 0.25) + (90 * 0.25) + (70 * 0.20) + (60 * 0.15) + (50 * 0.15)
        # = 20 + 22.5 + 14 + 9 + 7.5 = 73.0
        
        calculated = analyzer._calculate_dli_score(aspect_scores)
        
        assert abs(calculated - expected) < 0.01
    
    def test_dli_category_siap(self, analyzer):
        """Test DLI category for high scores"""
        category = analyzer._get_dli_category(75.0)
        assert category == "Siap Implementasi"
    
    def test_dli_category_perbaikan(self, analyzer):
        """Test DLI category for medium scores"""
        category = analyzer._get_dli_category(55.0)
        assert category == "Perlu Perbaikan"
    
    def test_dli_category_revisi(self, analyzer):
        """Test DLI category for low scores"""
        category = analyzer._get_dli_category(30.0)
        assert category == "Perlu Revisi Besar"
    
    def test_sub_scores_structure(self, analyzer):
        """Test sub-scores structure"""
        text = "Siswa merefleksikan dan berdiskusi kelompok"
        result = analyzer.analyze_document(text)
        
        # Check mindful sub-scores
        assert 'mindful' in result['sub_scores']
        assert 'aktivasi_fokus' in result['sub_scores']['mindful']
        assert 'metakognisi' in result['sub_scores']['mindful']
        assert 'kesadaran_fisik' in result['sub_scores']['mindful']
        
        # Check meaningful sub-scores
        assert 'meaningful' in result['sub_scores']
        assert 'linking' in result['sub_scores']['meaningful']
        assert 'realworld' in result['sub_scores']['meaningful']
        assert 'asesmen' in result['sub_scores']['meaningful']
        
        # Check joyful sub-scores
        assert 'joyful' in result['sub_scores']
        assert 'flow' in result['sub_scores']['joyful']
        assert 'kolaborasi' in result['sub_scores']['joyful']
    
    def test_processing_time(self, analyzer):
        """Test that processing time is recorded"""
        text = "Siswa berdiskusi kelompok"
        result = analyzer.analyze_document(text)
        
        assert result['processing_time'] >= 0  # Should be non-negative
        assert result['processing_time'] < 5  # Should be fast
    
    def test_real_rpp_comprehensive(self, analyzer):
        """Test with comprehensive RPP sample"""
        rpp_text = """
        RENCANA PELAKSANAAN PEMBELAJARAN
        
        A. PENDAHULUAN (15 menit)
        1. Guru memulai dengan hening sejenak untuk fokus
        2. Siswa merefleksikan pengalaman belajar sebelumnya
        3. Guru memberikan pertanyaan pemantik: "Bagaimana jika kita bisa mengubah dunia?"
        
        B. KEGIATAN INTI (60 menit)
        1. Siswa berdiskusi kelompok untuk memecahkan masalah nyata di lingkungan
        2. Setiap kelompok menganalisis kasus yang berbeda
        3. Siswa menggunakan simulasi PhET untuk eksperimen virtual
        4. Siswa mempresentasikan hasil dengan kreasi konten digital
        5. Teman sejawat memberikan umpan balik konstruktif
        
        C. PENUTUP (15 menit)
        1. Siswa membuat refleksi: "Apa yang saya pelajari? Bagaimana saya belajar?"
        2. Penilaian sejawat untuk hasil presentasi
        3. Siswa menghubungkan dengan materi sebelumnya
        """
        
        result = analyzer.analyze_document(rpp_text)
        
        # Should have high scores for this good RPP
        assert result['dli_score'] > 50, f"DLI score too low: {result['dli_score']}"
        
        # Check individual aspects
        assert result['scores']['mindful'] > 0, "Mindful should be detected"
        assert result['scores']['meaningful'] > 0, "Meaningful should be detected"
        assert result['scores']['joyful'] > 0, "Joyful should be detected"
        assert result['scores']['pedagogis'] > 0, "Pedagogis should be detected"
        assert result['scores']['digital'] > 0, "Digital should be detected"
        
        # Category should be at least "Perlu Perbaikan"
        assert result['dli_category'] in ["Siap Implementasi", "Perlu Perbaikan"]
    
    def test_poor_rpp_sample(self, analyzer):
        """Test with poor quality RPP"""
        poor_rpp = """
        KEGIATAN PEMBELAJARAN:
        
        1. Guru menjelaskan materi di depan kelas
        2. Siswa mendengarkan penjelasan guru
        3. Siswa mencatat poin-poin penting
        4. Siswa menghafal rumus
        5. Guru memberikan ujian pilihan ganda
        """
        
        result = analyzer.analyze_document(poor_rpp)
        
        # Should have lower scores due to surface learning indicators
        # Note: Score might not be 0 because some neutral words might match
        assert result['dli_score'] < 70, "Poor RPP should have lower DLI score"
        
        # Pedagogis should be low due to teacher-centered approach
        assert result['scores']['pedagogis'] < 80, "Pedagogis should be low for teacher-centered"
