"""
Alert Generator Module for DLI Analysis

This module generates alerts for low-scoring aspects in RPP documents.
Alerts are categorized by severity (critical, warning) based on score thresholds.

Requirements:
    - Requirement 5.1: Generate warning-level alert when aspect score < 60%
    - Requirement 5.2: Generate critical-level alert when aspect score < 40%
    - Requirement 5.3: Display alerts prominently with severity indicators
    - Requirement 5.4: Include aspect name, score, and brief recommendation
    - Requirement 5.5: Sort alerts by severity (critical first, then warnings)
"""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Alert:
    """Alert data structure"""
    aspect: str
    score: float
    level: str  # 'critical' or 'warning'
    message: str


class AlertGenerator:
    """
    Generates alerts for low-scoring aspects in DLI analysis
    
    Thresholds:
        - Critical (red): score < 40%
        - Warning (yellow): score < 60%
        - No alert: score >= 60%
    """
    
    # Alert thresholds
    CRITICAL_THRESHOLD = 40.0
    WARNING_THRESHOLD = 60.0
    
    # Aspect names in Indonesian
    ASPECT_NAMES = {
        'mindful': 'Mindful',
        'meaningful': 'Meaningful',
        'joyful': 'Joyful',
        'pedagogis': 'Pedagogis',
        'digital': 'Akselerasi Digital'
    }
    
    # Alert messages for each aspect
    ALERT_MESSAGES = {
        'mindful': {
            'critical': 'Aspek Mindful sangat kurang. RPP perlu menambahkan aktivitas untuk meningkatkan fokus, metakognisi, dan kesadaran fisik siswa.',
            'warning': 'Aspek Mindful perlu ditingkatkan. Pertimbangkan menambahkan aktivitas STOP, refleksi proses berpikir, atau kesadaran sensori.'
        },
        'meaningful': {
            'critical': 'Aspek Meaningful sangat kurang. RPP perlu menghubungkan materi dengan pengetahuan sebelumnya, dunia nyata, dan asesmen autentik.',
            'warning': 'Aspek Meaningful perlu ditingkatkan. Pertimbangkan menambahkan linking ke pengalaman siswa, konteks dunia nyata, atau asesmen berbasis proyek.'
        },
        'joyful': {
            'critical': 'Aspek Joyful sangat kurang. RPP perlu menambahkan aktivitas yang menciptakan flow dan kolaborasi untuk meningkatkan kegembiraan belajar.',
            'warning': 'Aspek Joyful perlu ditingkatkan. Pertimbangkan menambahkan aktivitas yang menantang namun achievable, atau kolaborasi kelompok yang bermakna.'
        },
        'pedagogis': {
            'critical': 'Aspek Pedagogis sangat kurang. RPP perlu menerapkan metode pembelajaran aktif seperti diskusi, problem solving, dan hands-on activities.',
            'warning': 'Aspek Pedagogis perlu ditingkatkan. Pertimbangkan menambahkan lebih banyak aktivitas student-centered dan mengurangi metode teacher-centered.'
        },
        'digital': {
            'critical': 'Aspek Akselerasi Digital sangat kurang. RPP perlu mengintegrasikan teknologi untuk memperdalam pemahaman, bukan hanya sebagai alat presentasi.',
            'warning': 'Aspek Akselerasi Digital perlu ditingkatkan. Pertimbangkan menambahkan simulasi, gamifikasi, atau tools kolaborasi digital.'
        }
    }
    
    def generate_alerts(self, aspect_scores: Dict[str, float]) -> List[Alert]:
        """
        Generate alerts based on aspect scores
        
        Args:
            aspect_scores: Dictionary with aspect names as keys and scores (0-100) as values
                          Example: {'mindful': 85.0, 'meaningful': 90.0, 'joyful': 35.0, ...}
        
        Returns:
            List of Alert objects sorted by severity (critical first) and score (lowest first)
        
        Examples:
            >>> generator = AlertGenerator()
            >>> scores = {'mindful': 85, 'meaningful': 90, 'joyful': 35, 'pedagogis': 55, 'digital': 70}
            >>> alerts = generator.generate_alerts(scores)
            >>> len(alerts)
            2
            >>> alerts[0].level
            'critical'
            >>> alerts[0].aspect
            'joyful'
        """
        alerts = []
        
        for aspect, score in aspect_scores.items():
            if score < self.CRITICAL_THRESHOLD:
                # Critical alert
                alert = Alert(
                    aspect=aspect,
                    score=score,
                    level='critical',
                    message=self._get_alert_message(aspect, 'critical')
                )
                alerts.append(alert)
                
            elif score < self.WARNING_THRESHOLD:
                # Warning alert
                alert = Alert(
                    aspect=aspect,
                    score=score,
                    level='warning',
                    message=self._get_alert_message(aspect, 'warning')
                )
                alerts.append(alert)
        
        # Sort alerts: critical first, then by lowest score
        alerts.sort(key=lambda x: (0 if x.level == 'critical' else 1, x.score))
        
        return alerts
    
    def _get_alert_message(self, aspect: str, level: str) -> str:
        """
        Get alert message for a specific aspect and severity level
        
        Args:
            aspect: Aspect name (mindful, meaningful, joyful, pedagogis, digital)
            level: Alert level ('critical' or 'warning')
        
        Returns:
            Alert message in Indonesian
        """
        if aspect in self.ALERT_MESSAGES and level in self.ALERT_MESSAGES[aspect]:
            return self.ALERT_MESSAGES[aspect][level]
        
        # Fallback message
        aspect_name = self.ASPECT_NAMES.get(aspect, aspect.capitalize())
        if level == 'critical':
            return f"Aspek {aspect_name} sangat kurang dan perlu perbaikan segera."
        else:
            return f"Aspek {aspect_name} perlu ditingkatkan."
    
    def get_aspect_name(self, aspect: str) -> str:
        """
        Get Indonesian name for an aspect
        
        Args:
            aspect: Aspect key (mindful, meaningful, joyful, pedagogis, digital)
        
        Returns:
            Indonesian aspect name
        """
        return self.ASPECT_NAMES.get(aspect, aspect.capitalize())
    
    def to_dict(self, alert: Alert) -> dict:
        """
        Convert Alert object to dictionary for JSON serialization
        
        Args:
            alert: Alert object
        
        Returns:
            Dictionary representation of the alert
        """
        return {
            'aspect': alert.aspect,
            'score': alert.score,
            'level': alert.level,
            'message': alert.message
        }
    
    def alerts_to_dict_list(self, alerts: List[Alert]) -> List[dict]:
        """
        Convert list of Alert objects to list of dictionaries
        
        Args:
            alerts: List of Alert objects
        
        Returns:
            List of dictionaries
        """
        return [self.to_dict(alert) for alert in alerts]


# Example usage
if __name__ == "__main__":
    generator = AlertGenerator()
    
    # Test with sample scores
    test_scores = {
        'mindful': 85.0,
        'meaningful': 90.0,
        'joyful': 35.0,  # Critical
        'pedagogis': 55.0,  # Warning
        'digital': 70.0
    }
    
    alerts = generator.generate_alerts(test_scores)
    
    print("Generated Alerts:")
    print("=" * 80)
    for alert in alerts:
        print(f"\n{alert.level.upper()}: {generator.get_aspect_name(alert.aspect)} ({alert.score}%)")
        print(f"Message: {alert.message}")
    
    print("\n" + "=" * 80)
    print(f"Total alerts: {len(alerts)}")
