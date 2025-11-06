"""
Tests for social media extraction functionality.
"""
import pytest
from app.scraper.social_media_extractor import SocialMediaExtractor, SocialMediaContact


class TestSocialMediaExtractor:
    """Test social media specific extraction patterns"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = SocialMediaExtractor()
    
    def test_extract_email_with_marker(self):
        """Test email extraction with Email: marker"""
        text = "Contact us! Email: info@school.co.id for more information"
        result = self.extractor.extract_from_social_media(text, 'instagram')
        
        assert len(result.emails) > 0
        assert 'info@school.co.id' in result.emails
        assert 'email_marker' in result.markers_found
    
    def test_extract_whatsapp_with_marker(self):
        """Test WhatsApp extraction with WA: marker"""
        text = "Hubungi kami di WA: 08123456789 atau DM"
        result = self.extractor.extract_from_social_media(text, 'instagram')
        
        assert len(result.whatsapp_numbers) > 0
        assert 'whatsapp_marker' in result.markers_found
        # Should be standardized to +62 format
        assert any(num.startswith('+62') for num in result.whatsapp_numbers)
    
    def test_extract_multiple_formats(self):
        """Test extraction of multiple contact formats"""
        text = """
        SMA Internasional Jakarta
        📧 Email: admission@sma-intl.sch.id
        📱 WhatsApp: +62 812-3456-7890
        ☎️ Phone: (021) 1234567
        """
        result = self.extractor.extract_from_social_media(text, 'facebook')
        
        assert len(result.emails) > 0
        assert len(result.whatsapp_numbers) > 0
        assert 'email_marker' in result.markers_found
        assert 'whatsapp_marker' in result.markers_found
    
    def test_link_in_bio_detection(self):
        """Test detection of link in bio pattern"""
        text = "For more info, check link in bio 👆"
        result = self.extractor.extract_from_social_media(text, 'instagram')
        
        assert 'link_in_bio' in result.markers_found
    
    def test_dm_only_detection(self):
        """Test detection of DM only pattern"""
        text = "DM for more information. No public contact available."
        result = self.extractor.extract_from_social_media(text, 'instagram')
        
        assert 'dm_only' in result.markers_found
    
    def test_institution_type_extraction(self):
        """Test institution type extraction from social media content"""
        # High school
        text1 = "SMA Internasional Jakarta - International High School"
        type1 = self.extractor.extract_institution_type_from_social(text1)
        assert type1 == '高中'
        
        # Language center
        text2 = "Pusat Bahasa Mandarin - Chinese Language Center"
        type2 = self.extractor.extract_institution_type_from_social(text2)
        assert type2 == '華語中心'
        
        # Education agency
        text3 = "Agen Pendidikan - Study Abroad Consultant"
        type3 = self.extractor.extract_institution_type_from_social(text3)
        assert type3 == '代辦'
    
    def test_process_external_links(self):
        """Test processing of external links"""
        links = [
            'https://wa.me/628123456789',
            'mailto:info@school.co.id',
            'https://school.co.id'
        ]
        
        whatsapp = []
        emails = []
        processed = self.extractor._process_external_links(links, whatsapp, emails)
        
        assert len(whatsapp) > 0
        assert len(emails) > 0
        assert 'https://school.co.id' in processed
    
    def test_contact_unavailable_indicators(self):
        """Test detection of unavailable contact indicators"""
        text1 = "No contact information available. DM only."
        assert self.extractor.has_contact_unavailable_indicators(text1)
        
        text2 = "Email: info@school.co.id"
        assert not self.extractor.has_contact_unavailable_indicators(text2)
    
    def test_indonesian_specific_patterns(self):
        """Test Indonesian specific contact patterns"""
        text = """
        Hubungi kami:
        HP: 0812-3456-7890
        Surel: humas@sekolah.sch.id
        """
        result = self.extractor.extract_from_social_media(text, 'facebook')
        
        assert len(result.emails) > 0
        assert len(result.whatsapp_numbers) > 0
        assert 'humas@sekolah.sch.id' in result.emails
    
    def test_emoji_markers(self):
        """Test extraction with emoji markers"""
        text = "📧 contact@school.co.id 📱 +62812345678"
        result = self.extractor.extract_from_social_media(text, 'instagram')
        
        assert len(result.emails) > 0
        assert len(result.whatsapp_numbers) > 0
    
    def test_log_extraction_result(self):
        """Test logging of extraction results"""
        contact = SocialMediaContact(
            emails=['test@example.com'],
            whatsapp_numbers=['+628123456789'],
            phone_numbers=[],
            external_links=[],
            raw_text='test',
            markers_found=['email_marker', 'whatsapp_marker']
        )
        
        log_entry = self.extractor.log_extraction_result(
            platform='facebook',
            url='https://facebook.com/test',
            contact=contact,
            page_name='Test School'
        )
        
        assert log_entry['platform'] == 'facebook'
        assert log_entry['has_contact'] is True
        assert log_entry['email_count'] == 1
        assert log_entry['whatsapp_count'] == 1
        assert log_entry['status'] == 'success'
    
    def test_empty_text_handling(self):
        """Test handling of empty text"""
        result = self.extractor.extract_from_social_media('', 'instagram')
        
        assert len(result.emails) == 0
        assert len(result.whatsapp_numbers) == 0
        assert len(result.markers_found) == 0


class TestSocialMediaContact:
    """Test SocialMediaContact dataclass"""
    
    def test_contact_creation(self):
        """Test creating a SocialMediaContact object"""
        contact = SocialMediaContact(
            emails=['test@example.com'],
            whatsapp_numbers=['+628123456789'],
            phone_numbers=['02112345678'],
            external_links=['https://example.com'],
            raw_text='test text',
            markers_found=['email_marker']
        )
        
        assert contact.emails == ['test@example.com']
        assert contact.whatsapp_numbers == ['+628123456789']
        assert contact.phone_numbers == ['02112345678']
        assert contact.external_links == ['https://example.com']
        assert contact.raw_text == 'test text'
        assert contact.markers_found == ['email_marker']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
