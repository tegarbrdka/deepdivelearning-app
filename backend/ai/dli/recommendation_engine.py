"""
Recommendation Engine Module for DLI Analysis

This module generates specific, actionable improvement suggestions for RPP documents
based on detected weaknesses and surface learning indicators.

Requirements:
    - Requirement 8.1: Generate specific improvement suggestions based on detected weaknesses
    - Requirement 8.2: Prioritize recommendations (high, medium, low)
    - Requirement 8.3: Suggest alternatives for surface learning activities
    - Requirement 8.4: Provide concrete examples for low-scoring aspects
    - Requirement 8.5: Generate 3-10 recommendations per RPP
    - Requirement 8.6: Display recommendations in priority order
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Recommendation:
    """Recommendation data structure"""
    priority: str  # 'high', 'medium', 'low'
    category: str
    issue: str
    suggestion: str


class RecommendationEngine:
    """
    Generates prioritized, actionable recommendations for RPP improvement
    
    Priority levels:
        - High: Surface learning detected OR aspect score < 40%
        - Medium: Aspect score 40-60%
        - Low: Missing sub-aspects OR general improvements
    """
    
    # Score thresholds for recommendations
    CRITICAL_THRESHOLD = 40.0
    WARNING_THRESHOLD = 60.0
    
    # Surface learning keywords that trigger high-priority replacements
    SURFACE_LEARNING_KEYWORDS = {
        'mencatat': 'membuat mind map kolaboratif untuk mengorganisir konsep',
        'menghafal': 'menganalisis pola dan menjelaskan mengapa konsep tersebut berlaku',
        'menyalin': 'merekonstruksi dengan kata-kata sendiri dan menghubungkan dengan pengalaman',
        'mendengarkan ceramah': 'berdiskusi aktif dan mengajukan pertanyaan kritis',
        'mengerjakan soal rutin': 'memecahkan masalah kompleks yang memerlukan analisis mendalam',
        'absensi': 'aktivasi fokus dengan STOP atau mindful breathing',
        'presensi': 'check-in emosional atau refleksi singkat',
        'guru menjelaskan': 'siswa mengeksplorasi dan menemukan konsep melalui inquiry',
        'siswa mendengarkan': 'siswa berdiskusi dan berkolaborasi',
        'mengisi lembar kerja': 'membuat produk kreatif yang menunjukkan pemahaman'
    }
    
    # Aspect-specific improvement tips
    ASPECT_TIPS = {
        'mindful': {
            'title': 'Meningkatkan Aspek Mindful',
            'tips': [
                'Aktivasi Fokus: Mulai pembelajaran dengan aktivitas STOP (Stop, Take a breath, Observe, Proceed) atau mindful breathing selama 1-2 menit',
                'Metakognisi: Ajukan pertanyaan reflektif seperti "Bagaimana kamu tahu jawabanmu benar?" atau "Strategi apa yang kamu gunakan?"',
                'Kesadaran Fisik: Integrasikan gerakan atau kesadaran sensori, misalnya "Perhatikan detak jantung kalian setelah aktivitas ini"',
                'Refleksi Proses: Minta siswa merefleksikan proses berpikir mereka, bukan hanya hasil akhir'
            ]
        },
        'meaningful': {
            'title': 'Meningkatkan Aspek Meaningful',
            'tips': [
                'Linking: Hubungkan materi baru dengan pengetahuan atau pengalaman siswa sebelumnya melalui pertanyaan pemantik',
                'Real World Connection: Gunakan konteks dunia nyata yang relevan dengan kehidupan siswa',
                'Asesmen Autentik: Ganti tes tertulis dengan proyek, presentasi, atau portfolio yang menunjukkan pemahaman mendalam',
                'Transfer Learning: Minta siswa menerapkan konsep ke situasi baru atau berbeda'
            ]
        },
        'joyful': {
            'title': 'Meningkatkan Aspek Joyful',
            'tips': [
                'Flow State: Rancang aktivitas yang menantang namun achievable, sesuai dengan zona perkembangan proksimal siswa',
                'Kolaborasi Bermakna: Gunakan diskusi kelompok, peer teaching, atau proyek kolaboratif',
                'Gamifikasi: Integrasikan elemen permainan seperti poin, level, atau kompetisi sehat',
                'Pilihan dan Otonomi: Berikan siswa pilihan dalam topik, metode, atau produk akhir'
            ]
        },
        'pedagogis': {
            'title': 'Meningkatkan Aspek Pedagogis',
            'tips': [
                'Student-Centered: Ubah dari teacher-centered ke student-centered learning',
                'Active Learning: Gunakan diskusi, problem-based learning, atau hands-on activities',
                'Higher-Order Thinking: Fokus pada analisis, evaluasi, dan kreasi, bukan hanya mengingat',
                'Scaffolding: Berikan dukungan bertahap yang dikurangi seiring siswa lebih mandiri'
            ]
        },
        'digital': {
            'title': 'Meningkatkan Aspek Akselerasi Digital',
            'tips': [
                'Simulasi: Gunakan PhET, Labster, atau simulasi lain untuk eksperimen virtual',
                'Gamifikasi Digital: Integrasikan Kahoot, Quizizz, atau Blooket untuk review interaktif',
                'Kolaborasi Digital: Gunakan Padlet, Jamboard, atau Miro untuk brainstorming kolaboratif',
                'Kreasi Digital: Minta siswa membuat video, podcast, atau infografis digital',
                'Augmented Reality: Eksplorasi AR apps untuk visualisasi konsep abstrak'
            ]
        }
    }
    
    def generate_recommendations(
        self,
        aspect_scores: Dict[str, float],
        keyword_matches: Dict[str, Dict[str, List[str]]]
    ) -> List[Recommendation]:
        """
        Generate prioritized recommendations based on scores and detected keywords
        
        Args:
            aspect_scores: Dictionary with aspect scores (0-100)
            keyword_matches: Dictionary with detected keywords by aspect and strength
                            Example: {'mindful': {'strong': [...], 'weak': [...]}, ...}
        
        Returns:
            List of Recommendation objects sorted by priority (high, medium, low)
            Minimum 3, maximum 10 recommendations
        
        Examples:
            >>> engine = RecommendationEngine()
            >>> scores = {'mindful': 85, 'meaningful': 90, 'joyful': 35, 'pedagogis': 55, 'digital': 70}
            >>> matches = {'joyful': {'weak': ['mencatat', 'menghafal']}}
            >>> recs = engine.generate_recommendations(scores, matches)
            >>> len(recs) >= 3 and len(recs) <= 10
            True
            >>> recs[0].priority
            'high'
        """
        recommendations = []
        
        # 1. Generate surface learning replacement recommendations (HIGH priority)
        surface_recs = self._generate_surface_replacements(keyword_matches)
        recommendations.extend(surface_recs)
        
        # 2. Generate critical aspect recommendations (HIGH priority)
        critical_recs = self._generate_critical_aspect_tips(aspect_scores)
        recommendations.extend(critical_recs)
        
        # 3. Generate warning aspect recommendations (MEDIUM priority)
        warning_recs = self._generate_warning_aspect_tips(aspect_scores)
        recommendations.extend(warning_recs)
        
        # 4. Generate general improvement tips (LOW priority) if needed
        if len(recommendations) < 3:
            general_recs = self._generate_general_tips(aspect_scores)
            recommendations.extend(general_recs)
        
        # Sort by priority: high, medium, low
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        # Limit to 3-10 recommendations
        if len(recommendations) < 3:
            # Pad with general tips if needed
            while len(recommendations) < 3:
                recommendations.append(Recommendation(
                    priority='low',
                    category='Peningkatan Umum',
                    issue='RPP sudah cukup baik',
                    suggestion='Pertahankan praktik baik yang sudah ada dan terus eksplorasi metode pembelajaran inovatif.'
                ))
        
        return recommendations[:10]  # Maximum 10
    
    def _generate_surface_replacements(
        self,
        keyword_matches: Dict[str, Dict[str, List[str]]]
    ) -> List[Recommendation]:
        """
        Generate high-priority recommendations for surface learning replacements
        
        Args:
            keyword_matches: Dictionary with detected keywords
        
        Returns:
            List of high-priority recommendations
        """
        recommendations = []
        detected_surface = set()
        
        # Collect all weak (surface learning) keywords
        for aspect, matches in keyword_matches.items():
            if 'weak' in matches:
                detected_surface.update(matches['weak'])
        
        # Generate replacements for detected surface learning keywords
        for keyword in detected_surface:
            # Find matching surface learning keyword (case-insensitive)
            for surface_key, replacement in self.SURFACE_LEARNING_KEYWORDS.items():
                if surface_key.lower() in keyword.lower():
                    rec = Recommendation(
                        priority='high',
                        category='Surface Learning Terdeteksi',
                        issue=f'Ditemukan indikator Surface Learning: "{keyword}"',
                        suggestion=f'❌ Ganti "{keyword}"\n✅ Dengan "{replacement}"'
                    )
                    recommendations.append(rec)
                    break
        
        # If surface learning detected but no specific match, give general advice
        if detected_surface and len(recommendations) == 0:
            rec = Recommendation(
                priority='high',
                category='Surface Learning Terdeteksi',
                issue='Ditemukan indikator pembelajaran pasif',
                suggestion='Ubah aktivitas pasif (mencatat, menghafal, mendengarkan) menjadi aktivitas aktif (menganalisis, berdiskusi, memecahkan masalah, merefleksikan).'
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_critical_aspect_tips(
        self,
        aspect_scores: Dict[str, float]
    ) -> List[Recommendation]:
        """
        Generate high-priority recommendations for critical aspects (score < 40%)
        
        Args:
            aspect_scores: Dictionary with aspect scores
        
        Returns:
            List of high-priority recommendations
        """
        recommendations = []
        
        for aspect, score in aspect_scores.items():
            if score < self.CRITICAL_THRESHOLD:
                tips = self.ASPECT_TIPS.get(aspect, {}).get('tips', [])
                if tips:
                    # Pick top 2 tips for critical aspects
                    selected_tips = tips[:2]
                    suggestion = '\n'.join([f'• {tip}' for tip in selected_tips])
                    
                    rec = Recommendation(
                        priority='high',
                        category=self.ASPECT_TIPS[aspect]['title'],
                        issue=f'Aspek {aspect.capitalize()} sangat kurang ({score:.0f}%)',
                        suggestion=suggestion
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    def _generate_warning_aspect_tips(
        self,
        aspect_scores: Dict[str, float]
    ) -> List[Recommendation]:
        """
        Generate medium-priority recommendations for warning aspects (40% <= score < 60%)
        
        Args:
            aspect_scores: Dictionary with aspect scores
        
        Returns:
            List of medium-priority recommendations
        """
        recommendations = []
        
        for aspect, score in aspect_scores.items():
            if self.CRITICAL_THRESHOLD <= score < self.WARNING_THRESHOLD:
                tips = self.ASPECT_TIPS.get(aspect, {}).get('tips', [])
                if tips:
                    # Pick top 2 tips for warning aspects
                    selected_tips = tips[:2]
                    suggestion = '\n'.join([f'• {tip}' for tip in selected_tips])
                    
                    rec = Recommendation(
                        priority='medium',
                        category=self.ASPECT_TIPS[aspect]['title'],
                        issue=f'Aspek {aspect.capitalize()} perlu ditingkatkan ({score:.0f}%)',
                        suggestion=suggestion
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    def _generate_general_tips(
        self,
        aspect_scores: Dict[str, float]
    ) -> List[Recommendation]:
        """
        Generate low-priority general improvement tips
        
        Args:
            aspect_scores: Dictionary with aspect scores
        
        Returns:
            List of low-priority recommendations
        """
        recommendations = []
        
        # Find lowest scoring aspect (even if above 60%)
        if aspect_scores:
            lowest_aspect = min(aspect_scores.items(), key=lambda x: x[1])
            aspect, score = lowest_aspect
            
            if score >= self.WARNING_THRESHOLD:
                tips = self.ASPECT_TIPS.get(aspect, {}).get('tips', [])
                if tips:
                    # Pick 1 tip for general improvement
                    suggestion = f'• {tips[0]}'
                    
                    rec = Recommendation(
                        priority='low',
                        category='Peningkatan Lebih Lanjut',
                        issue=f'Aspek {aspect.capitalize()} dapat ditingkatkan lebih lanjut ({score:.0f}%)',
                        suggestion=suggestion
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    def to_dict(self, recommendation: Recommendation) -> dict:
        """
        Convert Recommendation object to dictionary for JSON serialization
        
        Args:
            recommendation: Recommendation object
        
        Returns:
            Dictionary representation
        """
        return {
            'priority': recommendation.priority,
            'category': recommendation.category,
            'issue': recommendation.issue,
            'suggestion': recommendation.suggestion
        }
    
    def recommendations_to_dict_list(self, recommendations: List[Recommendation]) -> List[dict]:
        """
        Convert list of Recommendation objects to list of dictionaries
        
        Args:
            recommendations: List of Recommendation objects
        
        Returns:
            List of dictionaries
        """
        return [self.to_dict(rec) for rec in recommendations]


# Example usage
if __name__ == "__main__":
    engine = RecommendationEngine()
    
    # Test with sample data
    test_scores = {
        'mindful': 85.0,
        'meaningful': 90.0,
        'joyful': 35.0,  # Critical
        'pedagogis': 55.0,  # Warning
        'digital': 70.0
    }
    
    test_matches = {
        'joyful': {
            'weak': ['mencatat', 'menghafal']
        },
        'pedagogis': {
            'weak': ['guru menjelaskan']
        }
    }
    
    recommendations = engine.generate_recommendations(test_scores, test_matches)
    
    print("Generated Recommendations:")
    print("=" * 80)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec.priority.upper()}] {rec.category}")
        print(f"   Issue: {rec.issue}")
        print(f"   Suggestion:\n   {rec.suggestion}")
    
    print("\n" + "=" * 80)
    print(f"Total recommendations: {len(recommendations)}")
