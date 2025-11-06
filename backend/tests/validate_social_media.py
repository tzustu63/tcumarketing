"""
Simple validation script for social media extraction functionality.
"""
import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.scraper.social_media_extractor import SocialMediaExtractor, SocialMediaContact


def test_email_extraction():
    """Test email extraction with markers"""
    print("Testing email extraction with markers...")
    extractor = SocialMediaExtractor()
    
    text = "Contact us! Email: info@school.co.id for more information"
    result = extractor.extract_from_social_media(text, 'instagram')
    
    assert len(result.emails) > 0, "Should extract at least one email"
    assert 'info@school.co.id' in result.emails, "Should extract the correct email"
    assert 'email_marker' in result.markers_found, "Should detect email marker"
    print("✓ Email extraction test passed")


def test_whatsapp_extraction():
    """Test WhatsApp extraction with markers"""
    print("Testing WhatsApp extraction with markers...")
    extractor = SocialMediaExtractor()
    
    text = "Hubungi kami di WA: 08123456789 atau DM"
    result = extractor.extract_from_social_media(text, 'instagram')
    
    assert len(result.whatsapp_numbers) > 0, "Should extract at least one WhatsApp number"
    assert 'whatsapp_marker' in result.markers_found, "Should detect WhatsApp marker"
    assert any(num.startswith('+62') for num in result.whatsapp_numbers), "Should standardize to +62 format"
    print("✓ WhatsApp extraction test passed")


def test_multiple_formats():
    """Test extraction of multiple contact formats"""
    print("Testing multiple contact formats...")
    extractor = SocialMediaExtractor()
    
    text = """
    SMA Internasional Jakarta
    📧 Email: admission@sma-intl.sch.id
    📱 WhatsApp: +62 812-3456-7890
    ☎️ Phone: (021) 1234567
    """
    result = extractor.extract_from_social_media(text, 'facebook')
    
    assert len(result.emails) > 0, "Should extract emails"
    assert len(result.whatsapp_numbers) > 0, "Should extract WhatsApp numbers"
    assert 'email_marker' in result.markers_found, "Should detect email marker"
    assert 'whatsapp_marker' in result.markers_found, "Should detect WhatsApp marker"
    print("✓ Multiple formats test passed")


def test_link_in_bio():
    """Test link in bio detection"""
    print("Testing link in bio detection...")
    extractor = SocialMediaExtractor()
    
    text = "For more info, check link in bio 👆"
    result = extractor.extract_from_social_media(text, 'instagram')
    
    assert 'link_in_bio' in result.markers_found, "Should detect link in bio pattern"
    print("✓ Link in bio test passed")


def test_dm_only():
    """Test DM only detection"""
    print("Testing DM only detection...")
    extractor = SocialMediaExtractor()
    
    text = "DM for more information. No public contact available."
    result = extractor.extract_from_social_media(text, 'instagram')
    
    assert 'dm_only' in result.markers_found, "Should detect DM only pattern"
    print("✓ DM only test passed")


def test_institution_type():
    """Test institution type extraction"""
    print("Testing institution type extraction...")
    extractor = SocialMediaExtractor()
    
    # High school
    text1 = "SMA Internasional Jakarta - International High School"
    type1 = extractor.extract_institution_type_from_social(text1)
    assert type1 == '高中', f"Should detect high school, got {type1}"
    
    # Language center
    text2 = "Pusat Bahasa Mandarin - Chinese Language Center"
    type2 = extractor.extract_institution_type_from_social(text2)
    assert type2 == '華語中心', f"Should detect language center, got {type2}"
    
    # Education agency
    text3 = "Agen Pendidikan - Study Abroad Consultant"
    type3 = extractor.extract_institution_type_from_social(text3)
    assert type3 == '代辦', f"Should detect education agency, got {type3}"
    
    print("✓ Institution type test passed")


def test_external_links():
    """Test external link processing"""
    print("Testing external link processing...")
    extractor = SocialMediaExtractor()
    
    links = [
        'https://wa.me/628123456789',
        'mailto:info@school.co.id',
        'https://school.co.id'
    ]
    
    whatsapp = []
    emails = []
    processed = extractor._process_external_links(links, whatsapp, emails)
    
    assert len(whatsapp) > 0, "Should extract WhatsApp from wa.me link"
    assert len(emails) > 0, "Should extract email from mailto link"
    assert 'https://school.co.id' in processed, "Should keep other links"
    print("✓ External links test passed")


def test_indonesian_patterns():
    """Test Indonesian specific patterns"""
    print("Testing Indonesian specific patterns...")
    extractor = SocialMediaExtractor()
    
    text = """
    Hubungi kami:
    HP: 0812-3456-7890
    Surel: humas@sekolah.sch.id
    """
    result = extractor.extract_from_social_media(text, 'facebook')
    
    assert len(result.emails) > 0, "Should extract emails"
    assert len(result.whatsapp_numbers) > 0, "Should extract WhatsApp numbers"
    assert 'humas@sekolah.sch.id' in result.emails, "Should extract Indonesian email"
    print("✓ Indonesian patterns test passed")


def test_log_extraction():
    """Test extraction result logging"""
    print("Testing extraction result logging...")
    extractor = SocialMediaExtractor()
    
    contact = SocialMediaContact(
        emails=['test@example.com'],
        whatsapp_numbers=['+628123456789'],
        phone_numbers=[],
        external_links=[],
        raw_text='test',
        markers_found=['email_marker', 'whatsapp_marker']
    )
    
    log_entry = extractor.log_extraction_result(
        platform='facebook',
        url='https://facebook.com/test',
        contact=contact,
        page_name='Test School'
    )
    
    assert log_entry['platform'] == 'facebook', "Should log correct platform"
    assert log_entry['has_contact'] is True, "Should detect contact presence"
    assert log_entry['email_count'] == 1, "Should count emails correctly"
    assert log_entry['whatsapp_count'] == 1, "Should count WhatsApp numbers correctly"
    assert log_entry['status'] == 'success', "Should mark as success"
    print("✓ Extraction logging test passed")


def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("Social Media Extraction Validation")
    print("="*60 + "\n")
    
    tests = [
        test_email_extraction,
        test_whatsapp_extraction,
        test_multiple_formats,
        test_link_in_bio,
        test_dm_only,
        test_institution_type,
        test_external_links,
        test_indonesian_patterns,
        test_log_extraction,
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
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
