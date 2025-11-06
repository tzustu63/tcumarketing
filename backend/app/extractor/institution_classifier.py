"""
Institution Type Classifier

Automatically classifies institutions based on keywords in their name and content.
"""
import re
from typing import Optional, List, Dict
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
        # Compile regex patterns for better performance
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
        
        Args:
            institution_name: Name of the institution
            additional_text: Additional text (description, URL, etc.)
            
        Returns:
            ClassificationResult with type, confidence, and matched keywords, or None if no match
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
        
        # Only return if score is positive (at least one keyword matched)
        if best_score > 0:
            # Calculate confidence (0-100)
            # Normalize based on maximum possible score
            max_possible_score = self.PRIMARY_KEYWORD_WEIGHT * 3  # Assume max 3 primary keywords
            confidence = min(100.0, (best_score / max_possible_score) * 100)
            
            return ClassificationResult(
                institution_type=best_type,
                confidence=confidence,
                matched_keywords=matched_keywords_dict[best_type]
            )
        
        return None
    
    def classify_batch(self, institutions: List[Dict[str, str]]) -> List[Optional[ClassificationResult]]:
        """
        Classify multiple institutions at once
        
        Args:
            institutions: List of dicts with 'name' and optional 'text' keys
            
        Returns:
            List of ClassificationResult objects
        """
        results = []
        for inst in institutions:
            name = inst.get('name', '')
            text = inst.get('text', '')
            result = self.classify(name, text)
            results.append(result)
        
        return results
    
    def get_classification_explanation(self, result: ClassificationResult) -> str:
        """
        Get human-readable explanation of classification
        
        Args:
            result: ClassificationResult object
            
        Returns:
            Explanation string
        """
        if not result:
            return "無法分類 (No classification)"
        
        keywords_str = ', '.join(result.matched_keywords[:3])  # Show first 3 keywords
        return (
            f"分類為 {result.institution_type} "
            f"(信心度: {result.confidence:.1f}%, "
            f"匹配關鍵字: {keywords_str})"
        )
    
    def validate_classification(self, institution_name: str, claimed_type: str) -> bool:
        """
        Validate if a claimed institution type matches the classification
        
        Args:
            institution_name: Name of the institution
            claimed_type: The claimed institution type
            
        Returns:
            True if classification matches claimed type
        """
        result = self.classify(institution_name)
        if not result:
            return False
        
        return result.institution_type == claimed_type
