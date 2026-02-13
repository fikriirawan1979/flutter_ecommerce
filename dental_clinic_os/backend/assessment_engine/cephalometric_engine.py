"""
Dental Assessment Rule Engine

This module implements a rule-based diagnostic engine for cephalometric analysis.
It uses established orthodontic norms and thresholds to classify skeletal patterns
and suggest treatment approaches.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SkeletalClass(str, Enum):
    CLASS_I = "Class I"
    CLASS_II = "Class II"
    CLASS_III = "Class III"

class Severity(str, Enum):
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

@dataclass
class CephalometricMeasurements:
    """Standard cephalometric measurements"""
    sna: Optional[float] = None  # Sella-Nasion-A point (normal: 82° ± 2)
    snb: Optional[float] = None  # Sella-Nasion-B point (normal: 80° ± 2)
    anb: Optional[float] = None  # A point-Nasion-B point (normal: 2° ± 2)
    overjet: Optional[float] = None  # mm
    overbite: Optional[float] = None  # mm

@dataclass
class AssessmentResult:
    """Result of the assessment engine"""
    skeletal_class: SkeletalClass
    severity: Severity
    treatment_suggestion: str
    confidence_score: float
    detailed_analysis: Dict[str, Any]

class CephalometricRuleEngine:
    """
    Rule-based cephalometric assessment engine.
    
    Based on orthodontic standards:
    - ANB: 0-4° = Class I, >4° = Class II, <0° = Class III
    - SNA: 80-84° is normal range
    - SNB: 78-82° is normal range
    """
    
    # Normal ranges
    NORMAL_SNA = (80, 84)
    NORMAL_SNB = (78, 82)
    NORMAL_ANB = (0, 4)
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize diagnostic rules"""
        return {
            'anb_classification': {
                'class_i': {'min': 0, 'max': 4},
                'class_ii': {'min': 4, 'max': float('inf')},
                'class_iii': {'min': float('-inf'), 'max': 0},
            },
            'severity_thresholds': {
                'class_ii': {'mild': 4, 'moderate': 7, 'severe': 10},
                'class_iii': {'mild': -2, 'moderate': -5, 'severe': -8},
            }
        }
    
    def assess(self, measurements: Dict[str, Any]) -> AssessmentResult:
        """
        Perform assessment based on cephalometric measurements.
        
        Args:
            measurements: Dictionary containing SNA, SNB, ANB, Overjet, Overbite
            
        Returns:
            AssessmentResult with classification and treatment suggestions
        """
        # Extract measurements
        sna = measurements.get('SNA')
        snb = measurements.get('SNB')
        anb = measurements.get('ANB')
        overjet = measurements.get('Overjet')
        overbite = measurements.get('Overbite')
        
        # Determine skeletal class
        skeletal_class = self._classify_skeletal_class(anb)
        
        # Determine severity
        severity = self._classify_severity(anb, skeletal_class)
        
        # Generate treatment suggestion
        treatment = self._generate_treatment_suggestion(
            skeletal_class, severity, measurements
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(measurements)
        
        # Build detailed analysis
        detailed_analysis = self._build_detailed_analysis(
            sna, snb, anb, overjet, overbite, skeletal_class
        )
        
        return AssessmentResult(
            skeletal_class=skeletal_class,
            severity=severity,
            treatment_suggestion=treatment,
            confidence_score=confidence,
            detailed_analysis=detailed_analysis
        )
    
    def _classify_skeletal_class(self, anb: Optional[float]) -> SkeletalClass:
        """Classify skeletal pattern based on ANB angle"""
        if anb is None:
            return SkeletalClass.CLASS_I
        
        if anb < 0:
            return SkeletalClass.CLASS_III
        elif anb > 4:
            return SkeletalClass.CLASS_II
        else:
            return SkeletalClass.CLASS_I
    
    def _classify_severity(self, anb: Optional[float], 
                          skeletal_class: SkeletalClass) -> Severity:
        """Determine severity of skeletal discrepancy"""
        if anb is None:
            return Severity.MILD
        
        anb_abs = abs(anb)
        
        if skeletal_class == SkeletalClass.CLASS_II:
            if anb >= 10:
                return Severity.SEVERE
            elif anb >= 7:
                return Severity.MODERATE
            else:
                return Severity.MILD
        elif skeletal_class == SkeletalClass.CLASS_III:
            if anb_abs >= 8:
                return Severity.SEVERE
            elif anb_abs >= 5:
                return Severity.MODERATE
            else:
                return Severity.MILD
        else:
            # Class I
            if anb_abs >= 3:
                return Severity.MODERATE
            return Severity.MILD
    
    def _generate_treatment_suggestion(self, skeletal_class: SkeletalClass,
                                     severity: Severity,
                                     measurements: Dict[str, Any]) -> str:
        """Generate treatment recommendation based on assessment"""
        
        suggestions = {
            (SkeletalClass.CLASS_I, Severity.MILD): 
                "Maintain current occlusion. Regular monitoring recommended. Consider minor adjustments if aesthetic concerns exist.",
            (SkeletalClass.CLASS_I, Severity.MODERATE):
                "Possible dental compensation. Evaluate for camouflage treatment or mild skeletal correction.",
            
            (SkeletalClass.CLASS_II, Severity.MILD):
                "Dental correction with possible distalization or extraction if crowding present.",
            (SkeletalClass.CLASS_II, Severity.MODERATE):
                "Non-extraction with growth modification if patient is growing. Consider functional appliances or headgear.",
            (SkeletalClass.CLASS_II, Severity.SEVERE):
                "Comprehensive orthodontic treatment likely requires extraction or surgical intervention. Refer for orthognathic surgery evaluation if growth complete.",
            
            (SkeletalClass.CLASS_III, Severity.MILD):
                "Dental compensation with possible proclination of upper incisors and retroclination of lower incisors.",
            (SkeletalClass.CLASS_III, Severity.MODERATE):
                "Early intervention recommended if growing. Consider reverse pull headgear or face mask therapy.",
            (SkeletalClass.CLASS_III, Severity.SEVERE):
                "Orthognathic surgery likely required. Coordinate with oral surgeon for combined orthodontic-surgical approach.",
        }
        
        return suggestions.get((skeletal_class, severity), 
                             "Further evaluation required. Consult with specialist.")
    
    def _calculate_confidence(self, measurements: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness"""
        required_fields = ['SNA', 'SNB', 'ANB', 'Overjet', 'Overbite']
        available = sum(1 for field in required_fields 
                       if measurements.get(field) is not None)
        
        base_confidence = available / len(required_fields)
        
        # Adjust confidence based on measurement validity
        confidence = base_confidence * 0.9 + 0.1  # Base 10% confidence
        
        return round(min(confidence, 1.0), 2)
    
    def _build_detailed_analysis(self, sna: Optional[float], 
                                snb: Optional[float], 
                                anb: Optional[float],
                                overjet: Optional[float],
                                overbite: Optional[float],
                                skeletal_class: SkeletalClass) -> Dict[str, Any]:
        """Build detailed analysis of measurements"""
        analysis = {
            'measurements': {
                'sna': {'value': sna, 'normal_range': self.NORMAL_SNA, 
                       'status': self._get_status(sna, self.NORMAL_SNA)},
                'snb': {'value': snb, 'normal_range': self.NORMAL_SNB,
                       'status': self._get_status(snb, self.NORMAL_SNB)},
                'anb': {'value': anb, 'normal_range': self.NORMAL_ANB,
                       'status': self._get_status(anb, self.NORMAL_ANB)},
                'overjet': {'value': overjet, 'normal_range': (2, 4),
                           'status': self._get_status(overjet, (2, 4))},
                'overbite': {'value': overbite, 'normal_range': (2, 4),
                            'status': self._get_status(overbite, (2, 4))},
            },
            'skeletal_pattern': skeletal_class.value,
            'recommendations': self._get_recommendations(skeletal_class),
        }
        
        return analysis
    
    def _get_status(self, value: Optional[float], 
                   normal_range: tuple) -> str:
        """Determine if measurement is normal or abnormal"""
        if value is None:
            return "missing"
        if normal_range[0] <= value <= normal_range[1]:
            return "normal"
        elif value < normal_range[0]:
            return "low"
        else:
            return "high"
    
    def _get_recommendations(self, skeletal_class: SkeletalClass) -> list:
        """Get additional recommendations based on classification"""
        recommendations = []
        
        if skeletal_class == SkeletalClass.CLASS_II:
            recommendations.extend([
                "Consider molar relationship evaluation",
                "Assess vertical dimension and facial profile",
                "Evaluate lip competence and tongue posture"
            ])
        elif skeletal_class == SkeletalClass.CLASS_III:
            recommendations.extend([
                "Evaluate for pseudo vs true Class III",
                "Assess mandibular prognathism vs maxillary deficiency",
                "Consider TMJ health and function"
            ])
        else:
            recommendations.extend([
                "Continue regular monitoring",
                "Assess dental alignment and aesthetics"
            ])
        
        return recommendations


# Singleton instance
assessment_engine = CephalometricRuleEngine()

def assess_dental_measurements(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for dental assessment.
    
    Args:
        measurements: Dictionary with keys: SNA, SNB, ANB, Overjet, Overbite
        
    Returns:
        Dictionary with assessment results
    """
    result = assessment_engine.assess(measurements)
    
    return {
        'skeletal_class': result.skeletal_class.value,
        'severity': result.severity.value,
        'treatment_suggestion': result.treatment_suggestion,
        'confidence_score': result.confidence_score,
        'detailed_analysis': result.detailed_analysis
    }