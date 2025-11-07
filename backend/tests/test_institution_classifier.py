"""
Tests for Institution Classifier
"""
import pytest
from app.extractor.institution_classifier import InstitutionClassifier, ClassificationResult


class TestInstitutionClassifier:
    """Test institution type classification"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.classifier = InstitutionClassifier()
    
    def test_classify_high_school(self):
        """Test classification of high schools"""
        # Test with SMA keyword
        result = self.classifier.classify("SMA Internasional Jakarta")
        assert result is not None
        assert result.institution_type == "高中"
        assert result.confidence > 0
        
        # Test with high school keyword
        result = self.classifier.classify("International High School Bali")
        assert result is not None
        assert result.institution_type == "高中"
        
        # Test with SMK keyword
        result = self.classifier.classify("SMK Negeri 1 Surabaya")
        assert result is not None
        assert result.institution_type == "高中"
    
    def test_classify_language_center(self):
        """Test classification of language centers"""
        # Test with bahasa mandarin keyword
        result = self.classifier.classify("Pusat Bahasa Mandarin Jakarta")
        assert result is not None
        assert result.institution_type == "華語中心"
        assert result.confidence > 0
        
        # Test with chinese language keyword
        result = self.classifier.classify("Chinese Language Center Indonesia")
        assert result is not None
        assert result.institution_type == "華語中心"
        
        # Test with kursus mandarin keyword
        result = self.classifier.classify("Kursus Mandarin Bali")
        assert result is not None
        assert result.institution_type == "華語中心"
    
    def test_classify_education_agency(self):
        """Test classification of education agencies"""
        # Test with agen pendidikan keyword
        result = self.classifier.classify("Agen Pendidikan Luar Negeri")
        assert result is not None
        assert result.institution_type == "代辦"
        assert result.confidence > 0
        
        # Test with education consultant keyword
        result = self.classifier.classify("Education Consultant Indonesia")
        assert result is not None
        assert result.institution_type == "代辦"
        
        # Test with study abroad keyword
        result = self.classifier.classify("Study Abroad Services Jakarta")
        assert result is not None
        assert result.institution_type == "代辦"
    
    def test_classify_with_additional_text(self):
        """Test classification with additional context"""
        result = self.classifier.classify(
            "Sekolah ABC",
            "Kami adalah SMA internasional dengan kurikulum Cambridge"
        )
        assert result is not None
        assert result.institution_type == "高中"
    
    def test_classify_no_match(self):
        """Test classification with no matching keywords"""
        result = self.classifier.classify("Random Business Name")
        assert result is None
    
    def test_classify_negative_keywords(self):
        """Test that negative keywords reduce score"""
        # High school name with language center keywords should not be language center
        result = self.classifier.classify(
            "SMA Internasional Jakarta - Kursus Bahasa Mandarin"
        )
        # Should still be classified as high school due to primary keyword
        assert result is not None
        assert result.institution_type == "高中"
    
    def test_classify_batch(self):
        """Test batch classification"""
        institutions = [
            {"name": "SMA Jakarta", "text": ""},
            {"name": "Pusat Bahasa Mandarin", "text": ""},
            {"name": "Agen Pendidikan", "text": ""},
        ]
        
        results = self.classifier.classify_batch(institutions)
        
        assert len(results) == 3
        assert results[0].institution_type == "高中"
        assert results[1].institution_type == "華語中心"
        assert results[2].institution_type == "代辦"
    
    def test_get_classification_explanation(self):
        """Test getting human-readable explanation"""
        result = self.classifier.classify("SMA Internasional Jakarta")
        explanation = self.classifier.get_classification_explanation(result)
        
        assert "高中" in explanation
        assert "信心度" in explanation or "%" in explanation
    
    def test_validate_classification(self):
        """Test classification validation"""
        # Valid classification
        assert self.classifier.validate_classification(
            "SMA Jakarta",
            "高中"
        ) == True
        
        # Invalid classification
        assert self.classifier.validate_classification(
            "SMA Jakarta",
            "華語中心"
        ) == False
    
    def test_confidence_scores(self):
        """Test that confidence scores are reasonable"""
        # Strong match should have high confidence
        result = self.classifier.classify("SMA Internasional Jakarta")
        assert result.confidence > 30
        
        # Weak match should have lower confidence
        result = self.classifier.classify("Sekolah ABC siswa murid")
        if result:
            assert result.confidence < 50
    
    def test_matched_keywords(self):
        """Test that matched keywords are tracked"""
        result = self.classifier.classify("SMA Internasional Jakarta")
        assert result is not None
        assert len(result.matched_keywords) > 0
        assert any('sma' in kw.lower() for kw in result.matched_keywords)
