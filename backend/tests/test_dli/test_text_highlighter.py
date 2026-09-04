"""
Unit tests for TextHighlighter module
"""

import pytest
from backend.ai.dli.text_highlighter import TextHighlighter


class TestTextHighlighter:
    """Test suite for TextHighlighter class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.highlighter = TextHighlighter()
    
    def test_highlight_text_with_strong_keywords(self):
        """Test highlighting with strong deep learning keywords"""
        text = "Siswa berdiskusi kelompok untuk memecahkan masalah"
        keyword_matches = {
            'joyful': {
                'kolaborasi': {
                    'strong': ['berdiskusi kelompok'],
                    'medium': [],
                    'weak': []
                }
            },
            'meaningful': {
                'linking': {
                    'strong': ['memecahkan masalah'],
                    'medium': [],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check HTML contains highlights
        assert '<span class="highlight-green">berdiskusi kelompok</span>' in result['html']
        assert '<span class="highlight-green">memecahkan masalah</span>' in result['html']
        
        # Check keywords_found
        assert 'berdiskusi kelompok' in result['keywords_found']['green']
        assert 'memecahkan masalah' in result['keywords_found']['green']
        
        # Check statistics
        assert result['statistics']['green'] == 2
        assert result['statistics']['red'] == 0
    
    def test_highlight_text_with_surface_learning(self):
        """Test highlighting with surface learning keywords (red)"""
        text = "Siswa mencatat dan menghafal rumus"
        keyword_matches = {
            'meaningful': {
                'linking': {
                    'strong': [],
                    'medium': [],
                    'weak': ['mencatat', 'menghafal']
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check HTML contains red highlights
        assert '<span class="highlight-red">mencatat</span>' in result['html']
        assert '<span class="highlight-red">menghafal</span>' in result['html']
        
        # Check keywords_found
        assert 'mencatat' in result['keywords_found']['red']
        assert 'menghafal' in result['keywords_found']['red']
        
        # Check statistics
        assert result['statistics']['red'] == 2
        assert result['statistics']['green'] == 0
    
    def test_highlight_text_with_digital_keywords(self):
        """Test highlighting with digital keywords (blue)"""
        text = "Menggunakan simulasi dan kahoot untuk pembelajaran"
        keyword_matches = {
            'digital': {
                'akselerasi': {
                    'strong': ['simulasi', 'kahoot'],
                    'medium': [],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check HTML contains blue highlights
        assert '<span class="highlight-blue">simulasi</span>' in result['html']
        assert '<span class="highlight-blue">kahoot</span>' in result['html']
        
        # Check keywords_found
        assert 'simulasi' in result['keywords_found']['blue']
        assert 'kahoot' in result['keywords_found']['blue']
        
        # Check statistics
        assert result['statistics']['blue'] == 2
    
    def test_highlight_text_with_medium_keywords(self):
        """Test highlighting with medium-strength keywords (yellow)"""
        text = "Siswa melakukan refleksi dan evaluasi"
        keyword_matches = {
            'mindful': {
                'metakognisi': {
                    'strong': [],
                    'medium': ['refleksi', 'evaluasi'],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check HTML contains yellow highlights
        assert '<span class="highlight-yellow">refleksi</span>' in result['html']
        assert '<span class="highlight-yellow">evaluasi</span>' in result['html']
        
        # Check keywords_found
        assert 'refleksi' in result['keywords_found']['yellow']
        assert 'evaluasi' in result['keywords_found']['yellow']
        
        # Check statistics
        assert result['statistics']['yellow'] == 2
    
    def test_highlight_text_case_insensitive(self):
        """Test case-insensitive keyword matching"""
        text = "Siswa BERDISKUSI dan Memecahkan masalah"
        keyword_matches = {
            'joyful': {
                'kolaborasi': {
                    'strong': ['berdiskusi'],
                    'medium': [],
                    'weak': []
                }
            },
            'meaningful': {
                'linking': {
                    'strong': ['memecahkan masalah'],
                    'medium': [],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check case-insensitive matching
        assert '<span class="highlight-green">BERDISKUSI</span>' in result['html']
        assert '<span class="highlight-green">Memecahkan masalah</span>' in result['html']
        
        # Check statistics
        assert result['statistics']['green'] == 2
    
    def test_highlight_text_with_overlapping_keywords(self):
        """Test handling of overlapping keywords (longest first)"""
        text = "Siswa merefleksikan pengalaman"
        keyword_matches = {
            'mindful': {
                'metakognisi': {
                    'strong': ['merefleksikan'],
                    'medium': ['refleksi'],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Longer keyword should be matched first
        assert '<span class="highlight-green">merefleksikan</span>' in result['html']
        
        # Check statistics (only one match, not two)
        assert result['statistics']['green'] == 1
        assert result['statistics']['yellow'] == 0
    
    def test_highlight_text_preserves_original_content(self):
        """Test that original text content is preserved"""
        text = "Siswa berdiskusi kelompok"
        keyword_matches = {
            'joyful': {
                'kolaborasi': {
                    'strong': ['berdiskusi'],
                    'medium': [],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Remove HTML tags and check content
        import re
        clean_text = re.sub(r'<[^>]+>', '', result['html'])
        assert clean_text == text
    
    def test_highlight_text_with_special_characters(self):
        """Test handling of special HTML characters"""
        text = "Siswa <berdiskusi> & memecahkan masalah"
        keyword_matches = {
            'joyful': {
                'kolaborasi': {
                    'strong': ['berdiskusi'],
                    'medium': [],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check HTML entities are escaped
        assert '&lt;' in result['html']  # < escaped
        assert '&amp;' in result['html']  # & escaped
        assert '<span class="highlight-green">berdiskusi</span>' in result['html']
    
    def test_highlight_text_with_no_matches(self):
        """Test highlighting when no keywords are found"""
        text = "Ini adalah teks tanpa kata kunci"
        keyword_matches = {
            'mindful': {
                'aktivasi_fokus': {
                    'strong': ['STOP', 'hening'],
                    'medium': [],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check no highlights
        assert '<span' not in result['html']
        
        # Check empty keywords_found
        assert len(result['keywords_found']['green']) == 0
        assert len(result['keywords_found']['red']) == 0
        assert len(result['keywords_found']['blue']) == 0
        assert len(result['keywords_found']['yellow']) == 0
        
        # Check zero statistics
        assert result['statistics']['green'] == 0
        assert result['statistics']['red'] == 0
        assert result['statistics']['blue'] == 0
        assert result['statistics']['yellow'] == 0
    
    def test_highlight_text_with_empty_text(self):
        """Test highlighting with empty text"""
        text = ""
        keyword_matches = {
            'mindful': {
                'aktivasi_fokus': {
                    'strong': ['STOP'],
                    'medium': [],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check empty result
        assert result['html'] == ""
        assert result['statistics']['green'] == 0
    
    def test_categorize_keywords_by_color(self):
        """Test keyword categorization by color"""
        keyword_matches = {
            'mindful': {
                'aktivasi_fokus': {
                    'strong': ['STOP', 'hening'],
                    'medium': ['fokus'],
                    'weak': ['absensi']
                }
            },
            'digital': {
                'akselerasi': {
                    'strong': ['simulasi'],
                    'medium': ['kahoot'],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter._categorize_keywords_by_color(keyword_matches)
        
        # Check green (strong non-digital)
        assert 'STOP' in result['green']
        assert 'hening' in result['green']
        
        # Check yellow (medium non-digital)
        assert 'fokus' in result['yellow']
        
        # Check red (weak)
        assert 'absensi' in result['red']
        
        # Check blue (all digital)
        assert 'simulasi' in result['blue']
        assert 'kahoot' in result['blue']
    
    def test_highlight_text_with_mixed_keywords(self):
        """Test highlighting with all color categories"""
        text = "Siswa berdiskusi kelompok, mencatat, menggunakan simulasi, dan melakukan refleksi"
        keyword_matches = {
            'joyful': {
                'kolaborasi': {
                    'strong': ['berdiskusi kelompok'],
                    'medium': [],
                    'weak': []
                }
            },
            'meaningful': {
                'linking': {
                    'strong': [],
                    'medium': [],
                    'weak': ['mencatat']
                }
            },
            'digital': {
                'akselerasi': {
                    'strong': ['simulasi'],
                    'medium': [],
                    'weak': []
                }
            },
            'mindful': {
                'metakognisi': {
                    'strong': [],
                    'medium': ['refleksi'],
                    'weak': []
                }
            }
        }
        
        result = self.highlighter.highlight_text(text, keyword_matches)
        
        # Check all colors present
        assert result['statistics']['green'] == 1  # berdiskusi kelompok
        assert result['statistics']['red'] == 1    # mencatat
        assert result['statistics']['blue'] == 1   # simulasi
        assert result['statistics']['yellow'] == 1 # refleksi
        
        # Check HTML contains all highlights
        assert 'highlight-green' in result['html']
        assert 'highlight-red' in result['html']
        assert 'highlight-blue' in result['html']
        assert 'highlight-yellow' in result['html']
