"""
Integration tests for complete DLI analysis workflow
"""

import pytest
from backend.ai.dli.keyword_detector import KeywordDetector
from backend.ai.dli.dli_analyzer import DLIAnalyzer
from backend.ai.dli.text_highlighter import TextHighlighter


class TestDLIIntegration:
    """Integration tests for complete DLI workflow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = DLIAnalyzer()
        self.highlighter = TextHighlighter()
    
    def test_complete_workflow_high_quality_rpp(self):
        """Test complete DLI analysis with high-quality RPP"""
        rpp_text = """
        RENCANA PELAKSANAAN PEMBELAJARAN
        
        KEGIATAN PEMBELAJARAN:
        
        1. Pendahuluan (10 menit)
           - Guru mengajak siswa untuk STOP sejenak dan merasakan nafas
           - Siswa merefleksikan pengalaman belajar sebelumnya
           - Guru memberikan pertanyaan pemantik: "Bagaimana kamu tahu bahwa kamu sudah memahami?"
        
        2. Kegiatan Inti (60 menit)
           - Siswa berdiskusi kelompok untuk memecahkan masalah nyata di lingkungan sekolah
           - Menggunakan simulasi PhET untuk eksplorasi konsep
           - Siswa menganalisis pola dan menghubungkan dengan materi sebelumnya
           - Guru sebagai fasilitator, memberikan tantangan yang sesuai
           - Siswa berkolaborasi dalam proyek berbasis masalah
        
        3. Penutup (20 menit)
           - Siswa melakukan refleksi diri tentang proses belajar
           - Penilaian sejawat untuk memberikan umpan balik
           - Siswa membuat mind map untuk mengorganisir konsep
        """
        
        # Analyze document
        result = self.analyzer.analyze_document(rpp_text)
        
        # Verify structure
        assert 'dli_score' in result
        assert 'scores' in result
        assert 'sub_scores' in result
        
        # Verify high DLI score (should be > 70%)
        assert result['dli_score'] > 70.0
        assert result['dli_category'] == 'Siap Implementasi'
        
        # Verify all aspects have scores
        assert len(result['scores']) == 5
        assert 'mindful' in result['scores']
        assert 'meaningful' in result['scores']
        assert 'joyful' in result['scores']
        assert 'pedagogis' in result['scores']
        assert 'digital' in result['scores']
        
        # Verify high aspect scores
        assert result['scores']['mindful'] > 60.0  # Has STOP, refleksi, metakognisi
        assert result['scores']['meaningful'] > 60.0  # Has memecahkan masalah, hubungan
        assert result['scores']['joyful'] > 60.0  # Has berdiskusi, kolaborasi
        assert result['scores']['digital'] > 50.0  # Has simulasi PhET
    
    def test_complete_workflow_with_highlighting(self):
        """Test complete workflow including text highlighting"""
        rpp_text = """
        Siswa berdiskusi kelompok untuk memecahkan masalah.
        Siswa mencatat poin penting.
        Menggunakan simulasi digital.
        Siswa melakukan refleksi.
        """
        
        # Analyze document
        result = self.analyzer.analyze_document(rpp_text)
        
        # Get keyword matches from analyzer
        detector = KeywordDetector()
        keyword_matches = detector.detect_keywords(rpp_text)
        
        # Highlight text
        highlighted = self.highlighter.highlight_text(rpp_text, keyword_matches)
        
        # Verify highlighting
        assert 'html' in highlighted
        assert 'keywords_found' in highlighted
        assert 'statistics' in highlighted
        
        # Verify green highlights (strong keywords)
        assert 'highlight-green' in highlighted['html']
        assert len(highlighted['keywords_found']['green']) > 0
        
        # Verify red highlights (surface learning)
        assert 'highlight-red' in highlighted['html']
        assert 'mencatat' in highlighted['keywords_found']['red']
        
        # Verify blue highlights (digital)
        assert 'highlight-blue' in highlighted['html']
        assert 'simulasi' in highlighted['keywords_found']['blue']
        
        # Verify yellow highlights (medium)
        assert 'highlight-yellow' in highlighted['html']
        assert 'refleksi' in highlighted['keywords_found']['yellow']
    
    def test_complete_workflow_poor_quality_rpp(self):
        """Test complete workflow with poor-quality RPP (surface learning)"""
        rpp_text = """
        RENCANA PELAKSANAAN PEMBELAJARAN
        
        KEGIATAN PEMBELAJARAN:
        
        1. Pendahuluan (5 menit)
           - Absensi dan berdoa
        
        2. Kegiatan Inti (70 menit)
           - Guru menjelaskan materi di papan tulis
           - Siswa mencatat penjelasan guru
           - Siswa menghafal rumus dan definisi
           - Siswa mengerjakan soal latihan secara individual
        
        3. Penutup (15 menit)
           - Guru memberikan PR
           - Siswa mengumpulkan tugas
        """
        
        # Analyze document
        result = self.analyzer.analyze_document(rpp_text)
        
        # Verify low DLI score (should be < 40%)
        assert result['dli_score'] < 40.0
        assert result['dli_category'] == 'Perlu Revisi Besar'
        
        # Verify low aspect scores
        assert result['scores']['mindful'] < 50.0  # Only has absensi (weak)
        assert result['scores']['meaningful'] < 50.0  # Has mencatat, menghafal (weak)
        assert result['scores']['joyful'] < 50.0  # No collaboration
        assert result['scores']['digital'] < 50.0  # No digital integration
    
    def test_complete_workflow_medium_quality_rpp(self):
        """Test complete workflow with medium-quality RPP"""
        rpp_text = """
        RENCANA PELAKSANAAN PEMBELAJARAN
        
        KEGIATAN PEMBELAJARAN:
        
        1. Pendahuluan (10 menit)
           - Berdoa dan fokus
           - Apersepsi dengan pertanyaan
        
        2. Kegiatan Inti (60 menit)
           - Siswa berdiskusi kelompok
           - Siswa presentasi hasil diskusi
           - Guru memberikan penjelasan tambahan
           - Siswa mengerjakan latihan
        
        3. Penutup (20 menit)
           - Refleksi pembelajaran
           - Evaluasi hasil belajar
        """
        
        # Analyze document
        result = self.analyzer.analyze_document(rpp_text)
        
        # Verify medium DLI score (should be 40-70%)
        assert 40.0 <= result['dli_score'] <= 70.0
        assert result['dli_category'] in ['Perlu Perbaikan', 'Siap Implementasi']
        
        # Verify mixed aspect scores
        assert result['scores']['joyful'] > 40.0  # Has berdiskusi
        assert result['scores']['mindful'] > 30.0  # Has fokus, refleksi
    
    def test_workflow_with_empty_text(self):
        """Test workflow with empty text"""
        rpp_text = ""
        
        # Analyze document
        result = self.analyzer.analyze_document(rpp_text)
        
        # Verify zero scores
        assert result['dli_score'] == 0.0
        assert all(score == 0.0 for score in result['scores'].values())
    
    def test_workflow_with_no_keywords(self):
        """Test workflow with text containing no keywords"""
        rpp_text = "Lorem ipsum dolor sit amet consectetur adipiscing elit"
        
        # Analyze document
        result = self.analyzer.analyze_document(rpp_text)
        
        # Verify zero scores
        assert result['dli_score'] == 0.0
        assert all(score == 0.0 for score in result['scores'].values())
    
    def test_workflow_performance(self):
        """Test that analysis completes within acceptable time"""
        import time
        
        # Large RPP text (simulate 10-page document)
        rpp_text = """
        Siswa berdiskusi kelompok untuk memecahkan masalah nyata.
        Guru memberikan pertanyaan pemantik untuk merangsang pemikiran.
        Siswa merefleksikan proses belajar dan menghubungkan dengan pengalaman.
        Menggunakan simulasi digital untuk eksplorasi konsep.
        Siswa berkolaborasi dalam proyek berbasis masalah.
        """ * 100  # Repeat 100 times
        
        start_time = time.time()
        result = self.analyzer.analyze_document(rpp_text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify analysis completes within 3 seconds
        assert processing_time < 3.0
        
        # Verify result is valid
        assert result['dli_score'] > 0.0
    
    def test_workflow_with_special_characters(self):
        """Test workflow with special characters in text"""
        rpp_text = """
        Siswa <berdiskusi> & memecahkan masalah.
        Guru bertanya: "Bagaimana kamu tahu?"
        Siswa merefleksikan (dengan tenang).
        """
        
        # Analyze document
        result = self.analyzer.analyze_document(rpp_text)
        
        # Verify analysis works despite special characters
        assert result['dli_score'] > 0.0
        assert result['scores']['joyful'] > 0.0  # berdiskusi detected
        assert result['scores']['mindful'] > 0.0  # merefleksikan detected
        
        # Highlight text
        detector = KeywordDetector()
        keyword_matches = detector.detect_keywords(rpp_text)
        highlighted = self.highlighter.highlight_text(rpp_text, keyword_matches)
        
        # Verify HTML entities are escaped
        assert '&lt;' in highlighted['html'] or '&amp;' in highlighted['html']
