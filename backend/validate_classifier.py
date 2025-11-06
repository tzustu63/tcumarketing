"""
Simple validation script for institution classifier
"""
import sys
sys.path.insert(0, '.')

from app.extractor.institution_classifier import InstitutionClassifier


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
    
    # Test batch classification
    print("\nTesting batch classification...")
    print("-" * 60)
    
    institutions = [
        {"name": "SMA Jakarta", "text": ""},
        {"name": "Pusat Bahasa Mandarin", "text": ""},
        {"name": "Agen Pendidikan", "text": ""},
    ]
    
    results = classifier.classify_batch(institutions)
    
    for inst, result in zip(institutions, results):
        if result:
            print(f"{inst['name']:30} -> {result.institution_type} ({result.confidence:.1f}%)")
        else:
            print(f"{inst['name']:30} -> No classification")
    
    print("\n" + "=" * 60)
    
    if failed == 0:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = test_classifier()
    sys.exit(exit_code)
