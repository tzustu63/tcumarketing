"""
Standalone test for institution classifier (no dependencies)
"""
import re
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Classification result with confidence score"""
    institution_type: str
    confidence: float
    matched_keywords: List[str]


class InstitutionClassifier:
    """
    Classifier for automatically categorizing institutions into types:
    - 高中 (High School)
    - 華語中心 (Chinese Language Center)
    - 代辦 (Education Agency)
    """
    
    # Keyword mapping rules
    CLASSIFICATION_RULES = {
        '高中': {
            'primary_keywords': [
                'sma', 'sekolah menengah atas', 'high school', 'senior high',
                'smk', 'sekolah menengah kejuruan', 'vocational school',
                'madrasah aliyah', 'ma ', 'pesantren'
            ],
            'secondary_keywords': [
                'international school', 'sekolah internasional',
                'boarding school', 'asrama', 'siswa', 'murid',
                'kelas', 'grade', 'kurikulum', 'curriculum'
            ],
            'negative_keywords': [
                'universitas', 'university', 'perguruan tinggi',
                'bahasa mandarin', 'chinese language', 'agen', 'agency'
            ]
        },
        '華語中心': {
            'primary_keywords': [
                'bahasa mandarin', 'chinese language', 'mandarin center',
                'pusat bahasa', 'language center', 'kursus mandarin',
                'les mandarin', 'belajar mandarin', 'chinese course',
                'confucius institute', 'institut confucius'
            ],
            'secondary_keywords': [
                'hsk', 'hanyu', '汉语', '中文', 'chinese class',
                'mandarin class', 'bahasa china', 'chinese teacher',
                'guru mandarin'
            ],
            'negative_keywords': [
                'sma', 'high school', 'sekolah menengah',
                'agen', 'agency', 'konsultan'
            ]
        },
        '代辦': {
            'primary_keywords': [
                'agen pendidikan', 'education agent', 'education agency',
                'konsultan pendidikan', 'education consultant',
                'study abroad', 'kuliah luar negeri', 'beasiswa',
                'scholarship', 'visa', 'admission', 'pendaftaran universitas'
            ],
            'secondary_keywords': [
                'konsultasi', 'consultation', 'layanan', 'service',
                'overseas', 'luar negeri', 'taiwan', 'china', 'australia',
                'uk', 'usa', 'canada', 'jepang', 'korea'
            ],
            'negative_keywords': [
                'sma', 'high school', 'sekolah menengah',
                'bahasa mandarin', 'chinese language', 'kursus'
            ]
        }
    }
    
    # Confidence weights
    PRIMARY_KEYWORD_WEIGHT = 10.0
    SECONDARY_KEYWORD_WEIGHT = 3.0
    NEGATIVE_KEYWORD_PENALTY = -15.0
    
    def __init__(self):
        """Initialize the classifier"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for all keywords"""
        self.compiled_rules = {}
        
        for inst_type, rules in self.CLASSIFICATION_RULES.items():
            self.compiled_rules[inst_type] = {
                'primary': [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                           for kw in rules['primary_keywords']],
                'secondary': [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                             for kw in rules['secondary_keywords']],
                'negative': [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                            for kw in rules['negative_keywords']]
            }
    
    def classify(self, institution_name: str, additional_text: Optional[str] = None) -> Optional[ClassificationResult]:
        """
        Classify institution based on name and optional additional text
        """
        if not institution_name:
            return None
        
        # Combine texts for analysis
        combined_text = institution_name.lower()
        if additional_text:
            combined_text += ' ' + additional_text.lower()
        
        # Calculate scores for each institution type
        scores = {}
        matched_keywords_dict = {}
        
        for inst_type, patterns in self.compiled_rules.items():
            score = 0.0
            matched = []
            
            # Check primary keywords
            for pattern in patterns['primary']:
                if pattern.search(combined_text):
                    score += self.PRIMARY_KEYWORD_WEIGHT
                    matched.append(pattern.pattern.strip(r'\b'))
            
            # Check secondary keywords
            for pattern in patterns['secondary']:
                if pattern.search(combined_text):
                    score += self.SECONDARY_KEYWORD_WEIGHT
                    matched.append(pattern.pattern.strip(r'\b'))
            
            # Check negative keywords (penalties)
            for pattern in patterns['negative']:
                if pattern.search(combined_text):
                    score += self.NEGATIVE_KEYWORD_PENALTY
            
            scores[inst_type] = score
            matched_keywords_dict[inst_type] = matched
        
        # Find the best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Only return if score is positive
        if best_score > 0:
            max_possible_score = self.PRIMARY_KEYWORD_WEIGHT * 3
            confidence = min(100.0, (best_score / max_possible_score) * 100)
            
            return ClassificationResult(
                institution_type=best_type,
                confidence=confidence,
                matched_keywords=matched_keywords_dict[best_type]
            )
        
        return None


def test_classifier():
    """Test the institution classifier"""
    classifier = InstitutionClassifier()
    
    print("Testing Institution Classifier...")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        ("SMA Internasional Jakarta", "高中"),
        ("International High School Bali", "高中"),
        ("SMK Negeri 1 Surabaya", "高中"),
        ("Pusat Bahasa Mandarin Jakarta", "華語中心"),
        ("Chinese Language Center Indonesia", "華語中心"),
        ("Kursus Mandarin Bali", "華語中心"),
        ("Agen Pendidikan Luar Negeri", "代辦"),
        ("Education Consultant Indonesia", "代辦"),
        ("Study Abroad Services Jakarta", "代辦"),
    ]
    
    passed = 0
    failed = 0
    
    for name, expected_type in test_cases:
        result = classifier.classify(name)
        
        if result and result.institution_type == expected_type:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
            
        actual_type = result.institution_type if result else "None"
        confidence = f"{result.confidence:.1f}%" if result else "N/A"
        
        print(f"{status} | {name:40} | Expected: {expected_type:8} | Got: {actual_type:8} | Confidence: {confidence}")
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    # Test with additional context
    print("\nTesting with additional context...")
    print("-" * 60)
    
    result = classifier.classify(
        "Sekolah ABC",
        "Kami adalah SMA internasional dengan kurikulum Cambridge"
    )
    
    if result:
        print(f"Name: Sekolah ABC")
        print(f"Context: SMA internasional dengan kurikulum Cambridge")
        print(f"Classification: {result.institution_type}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Matched keywords: {', '.join(result.matched_keywords[:3])}")
    
    print("\n" + "=" * 60)
    
    if failed == 0:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = test_classifier()
    sys.exit(exit_code)
