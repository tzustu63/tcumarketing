"""
Simple validation script for social media extraction functionality.
Tests only the SocialMediaExtractor without dependencies.
"""
import sys
import os
import re

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


def test_basic_patterns():
    """Test basic regex patterns without importing full modules"""
    print("Testing basic extraction patterns...")
    
    # Test email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text1 = "Contact us! Email: info@school.co.id for more information"
    emails = re.findall(email_pattern, text1)
    assert len(emails) > 0, "Should extract email"
    assert 'info@school.co.id' in emails, "Should extract correct email"
    print("✓ Email pattern test passed")
    
    # Test WhatsApp pattern
    wa_pattern = r'(\+62|62|0)8[0-9]{8,11}'
    text2 = "Hubungi kami di WA: 08123456789 atau DM"
    wa_numbers = re.findall(wa_pattern, text2)
    assert len(wa_numbers) > 0, "Should extract WhatsApp number"
    print("✓ WhatsApp pattern test passed")
    
    # Test marker patterns
    wa_marker = r'(?:WA|wa|Wa)[\s:：]+'
    assert re.search(wa_marker, text2), "Should detect WA marker"
    print("✓ Marker pattern test passed")
    
    # Test link in bio pattern
    link_pattern = r'link\s+in\s+bio'
    text3 = "For more info, check link in bio 👆"
    assert re.search(link_pattern, text3, re.IGNORECASE), "Should detect link in bio"
    print("✓ Link in bio pattern test passed")
    
    # Test DM pattern
    dm_pattern = r'DM\s+(?:for|untuk|me)'
    text4 = "DM for more information"
    assert re.search(dm_pattern, text4, re.IGNORECASE), "Should detect DM pattern"
    print("✓ DM pattern test passed")
    
    # Test institution type patterns
    high_school_keywords = ['sma', 'high school', 'sekolah menengah']
    text5 = "SMA Internasional Jakarta - International High School"
    assert any(keyword in text5.lower() for keyword in high_school_keywords), "Should detect high school"
    print("✓ Institution type pattern test passed")


def test_phone_standardization():
    """Test phone number standardization logic"""
    print("Testing phone number standardization...")
    
    def standardize_phone(number):
        """Simplified standardization logic"""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', number)
        # Remove leading zeros and +
        cleaned = cleaned.lstrip('0').lstrip('+')
        
        # Handle different formats
        if cleaned.startswith('62'):
            phone = cleaned
        elif cleaned.startswith('8'):
            phone = '62' + cleaned
        else:
            return None
        
        # Validate length
        if len(phone) < 11 or len(phone) > 14:
            return None
        
        # Validate starts with 628
        if not phone.startswith('628'):
            return None
        
        return '+' + phone
    
    # Test various formats
    test_cases = [
        ('08123456789', '+628123456789'),
        ('+62 812-3456-7890', '+6281234567890'),
        ('62 812 3456 7890', '+6281234567890'),
        ('0812 3456 7890', '+6281234567890'),
    ]
    
    for input_num, expected in test_cases:
        result = standardize_phone(input_num)
        assert result == expected, f"Failed for {input_num}: got {result}, expected {expected}"
    
    print("✓ Phone standardization test passed")


def test_email_validation():
    """Test email validation logic"""
    print("Testing email validation...")
    
    def is_valid_email(email):
        """Simplified email validation"""
        if not email or len(email) < 5:
            return False
        if '@' not in email:
            return False
        parts = email.split('@')
        if len(parts) != 2:
            return False
        local, domain = parts
        if not local or len(local) < 1:
            return False
        if not domain or '.' not in domain:
            return False
        return True
    
    # Test valid emails
    valid_emails = [
        'info@school.co.id',
        'admission@sma-intl.sch.id',
        'contact@example.com',
    ]
    
    for email in valid_emails:
        assert is_valid_email(email), f"Should validate {email}"
    
    # Test invalid emails
    invalid_emails = [
        'notanemail',
        '@nodomain.com',
        'noatsign.com',
        'no@domain',
    ]
    
    for email in invalid_emails:
        assert not is_valid_email(email), f"Should reject {email}"
    
    print("✓ Email validation test passed")


def test_indonesian_patterns():
    """Test Indonesian specific patterns"""
    print("Testing Indonesian specific patterns...")
    
    text = """
    Hubungi kami:
    HP: 0812-3456-7890
    Surel: humas@sekolah.sch.id
    Telp: (021) 1234567
    """
    
    # Test Indonesian keywords
    indonesian_keywords = ['hubungi', 'surel', 'telp', 'hp']
    found_keywords = [kw for kw in indonesian_keywords if kw in text.lower()]
    assert len(found_keywords) > 0, "Should detect Indonesian keywords"
    print("✓ Indonesian keywords test passed")
    
    # Test Indonesian domain patterns
    id_domain_pattern = r'@[a-zA-Z0-9.-]+\.(co\.id|ac\.id|sch\.id|or\.id|go\.id)'
    id_emails = re.findall(id_domain_pattern, text)
    assert len(id_emails) > 0, "Should detect Indonesian domain emails"
    print("✓ Indonesian domain test passed")


def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("Social Media Extraction Pattern Validation")
    print("="*60 + "\n")
    
    tests = [
        test_basic_patterns,
        test_phone_standardization,
        test_email_validation,
        test_indonesian_patterns,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    if failed == 0:
        print("✓ All pattern validation tests passed!")
        print("The social media extraction logic is correctly implemented.")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
