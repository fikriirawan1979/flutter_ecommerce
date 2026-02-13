import pytest
from assessment_engine.cephalometric_engine import (
    CephalometricRuleEngine, SkeletalClass, Severity,
    assess_dental_measurements
)

class TestCephalometricRuleEngine:
    """Test suite for cephalometric assessment engine"""
    
    @pytest.fixture
    def engine(self):
        return CephalometricRuleEngine()
    
    def test_class_i_classification(self, engine):
        """Test Class I skeletal classification"""
        measurements = {
            'SNA': 82,
            'SNB': 80,
            'ANB': 2,
            'Overjet': 3,
            'Overbite': 3
        }
        
        result = engine.assess(measurements)
        
        assert result.skeletal_class == SkeletalClass.CLASS_I
        assert result.confidence_score > 0.8
        assert len(result.treatment_suggestion) > 0
    
    def test_class_ii_moderate(self, engine):
        """Test Class II moderate classification"""
        measurements = {
            'SNA': 82,
            'SNB': 78,
            'ANB': 4,
            'Overjet': 6,
            'Overbite': 4
        }
        
        result = engine.assess(measurements)
        
        assert result.skeletal_class == SkeletalClass.CLASS_II
        assert result.severity == Severity.MODERATE
        assert 'Non-extraction' in result.treatment_suggestion or 'growth modification' in result.treatment_suggestion.lower()
    
    def test_class_iii_severe(self, engine):
        """Test Class III severe classification"""
        measurements = {
            'SNA': 78,
            'SNB': 82,
            'ANB': -4,
            'Overjet': -3,
            'Overbite': 2
        }
        
        result = engine.assess(measurements)
        
        assert result.skeletal_class == SkeletalClass.CLASS_III
        assert result.severity == Severity.SEVERE
        assert 'surgery' in result.treatment_suggestion.lower() or 'Orthognathic' in result.treatment_suggestion
    
    def test_missing_measurements(self, engine):
        """Test handling of missing measurements"""
        measurements = {
            'SNA': 82,
            'ANB': 5
        }
        
        result = engine.assess(measurements)
        
        # Should still work with partial data
        assert result.skeletal_class is not None
        assert result.confidence_score < 1.0  # Lower confidence with missing data
    
    def test_confidence_calculation(self, engine):
        """Test confidence score calculation"""
        # All measurements present
        complete = {
            'SNA': 82, 'SNB': 80, 'ANB': 2,
            'Overjet': 3, 'Overbite': 3
        }
        result_complete = engine.assess(complete)
        
        # Missing measurements
        incomplete = {'SNA': 82, 'ANB': 2}
        result_incomplete = engine.assess(incomplete)
        
        assert result_complete.confidence_score > result_incomplete.confidence_score
    
    def test_public_api(self):
        """Test the public API function"""
        measurements = {
            'SNA': 82,
            'SNB': 78,
            'ANB': 4,
            'Overjet': 6,
            'Overbite': 4
        }
        
        result = assess_dental_measurements(measurements)
        
        assert 'skeletal_class' in result
        assert 'severity' in result
        assert 'treatment_suggestion' in result
        assert 'confidence_score' in result
        assert 'detailed_analysis' in result
        
        assert result['skeletal_class'] == 'Class II'
        assert result['severity'] == 'Moderate'
        assert result['confidence_score'] > 0.8