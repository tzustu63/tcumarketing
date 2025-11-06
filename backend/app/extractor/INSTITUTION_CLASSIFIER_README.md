# Institution Type Classifier

## Overview

The Institution Classifier automatically categorizes educational institutions into three types based on keywords found in their names and descriptions:

- **高中** (High School) - International schools, SMA, SMK, boarding schools
- **華語中心** (Chinese Language Center) - Mandarin language centers, Chinese courses
- **代辦** (Education Agency) - Study abroad consultants, education agents

## Features

- **Keyword-based Classification**: Uses primary and secondary keywords to identify institution types
- **Negative Keyword Filtering**: Prevents misclassification by penalizing conflicting keywords
- **Confidence Scoring**: Provides confidence scores (0-100%) for each classification
- **Context-aware**: Can use both institution name and additional text for better accuracy
- **Batch Processing**: Supports classifying multiple institutions at once

## Usage

### Basic Classification

```python
from app.extractor.institution_classifier import InstitutionClassifier

classifier = InstitutionClassifier()

# Classify by name only
result = classifier.classify("SMA Internasional Jakarta")
print(f"Type: {result.institution_type}")  # Output: 高中
print(f"Confidence: {result.confidence}%")  # Output: 33.3%
print(f"Keywords: {result.matched_keywords}")  # Output: ['sma']
```

### Classification with Additional Context

```python
# Classify with additional text for better accuracy
result = classifier.classify(
    institution_name="Sekolah ABC",
    additional_text="Kami adalah SMA internasional dengan kurikulum Cambridge"
)
print(f"Type: {result.institution_type}")  # Output: 高中
print(f"Confidence: {result.confidence}%")  # Output: 43.3%
```

### Batch Classification

```python
institutions = [
    {"name": "SMA Jakarta", "text": ""},
    {"name": "Pusat Bahasa Mandarin", "text": ""},
    {"name": "Agen Pendidikan", "text": ""},
]

results = classifier.classify_batch(institutions)

for inst, result in zip(institutions, results):
    if result:
        print(f"{inst['name']} -> {result.institution_type}")
```

### Get Human-Readable Explanation

```python
result = classifier.classify("SMA Internasional Jakarta")
explanation = classifier.get_classification_explanation(result)
print(explanation)
# Output: 分類為 高中 (信心度: 33.3%, 匹配關鍵字: sma)
```

### Validate Classification

```python
# Check if a claimed type matches the classification
is_valid = classifier.validate_classification(
    institution_name="SMA Jakarta",
    claimed_type="高中"
)
print(is_valid)  # Output: True
```

## Integration with Contact Extraction

The classifier is automatically integrated into the contact extraction workflow:

### In HTML Parser

```python
from app.extractor.html_parser import HTMLParser

parser = HTMLParser()
parsed_data = parser.parse_html(
    html=html_content,
    institution_name="SMA Jakarta"
)

# Institution type is automatically included
print(parsed_data['institution_type'])  # Output: 高中
```

### In Contact Extractor

```python
from app.extractor.contact_extractor import ContactExtractor

extractor = ContactExtractor()
contact_info = extractor.extract_from_text(
    text=text_content,
    institution_name="Pusat Bahasa Mandarin"
)

# Institution type is automatically classified
print(contact_info.institution_type)  # Output: 華語中心
print(contact_info.classification_confidence)  # Output: 66.7
```

### In Scraping Tasks

The classification is automatically applied when contacts are saved:

```python
# In extract_website_task
parsed_data = html_parser.parse_html(
    page_content.html,
    institution_name=institution_name
)

# Institution type is automatically extracted
institution_type = parsed_data.get("institution_type")

# Saved to database
contact = Contact(
    institution_name=institution_name,
    institution_type=institution_type,  # Automatically classified
    ...
)
```

## Classification Rules

### 高中 (High School)

**Primary Keywords** (10 points each):
- sma, sekolah menengah atas, high school, senior high
- smk, sekolah menengah kejuruan, vocational school
- madrasah aliyah, ma, pesantren

**Secondary Keywords** (3 points each):
- international school, sekolah internasional
- boarding school, asrama, siswa, murid
- kelas, grade, kurikulum, curriculum

**Negative Keywords** (-15 points each):
- universitas, university, perguruan tinggi
- bahasa mandarin, chinese language, agen, agency

### 華語中心 (Chinese Language Center)

**Primary Keywords** (10 points each):
- bahasa mandarin, chinese language, mandarin center
- pusat bahasa, language center, kursus mandarin
- les mandarin, belajar mandarin, chinese course
- confucius institute, institut confucius

**Secondary Keywords** (3 points each):
- hsk, hanyu, 汉语, 中文, chinese class
- mandarin class, bahasa china, chinese teacher
- guru mandarin

**Negative Keywords** (-15 points each):
- sma, high school, sekolah menengah
- agen, agency, konsultan

### 代辦 (Education Agency)

**Primary Keywords** (10 points each):
- agen pendidikan, education agent, education agency
- konsultan pendidikan, education consultant
- study abroad, kuliah luar negeri, beasiswa
- scholarship, visa, admission, pendaftaran universitas

**Secondary Keywords** (3 points each):
- konsultasi, consultation, layanan, service
- overseas, luar negeri, taiwan, china, australia
- uk, usa, canada, jepang, korea

**Negative Keywords** (-15 points each):
- sma, high school, sekolah menengah
- bahasa mandarin, chinese language, kursus

## Confidence Scoring

Confidence is calculated based on:
- Number and type of matched keywords
- Presence of negative keywords
- Normalized to 0-100% scale

**Interpretation**:
- **> 60%**: Strong match (multiple primary keywords)
- **30-60%**: Good match (primary keyword + secondary keywords)
- **< 30%**: Weak match (secondary keywords only)

## Testing

Run the standalone test:

```bash
python3 test_classifier_standalone.py
```

Expected output:
```
Testing Institution Classifier...
============================================================
✓ PASS | SMA Internasional Jakarta                | Expected: 高中       | Got: 高中       | Confidence: 33.3%
✓ PASS | International High School Bali           | Expected: 高中       | Got: 高中       | Confidence: 33.3%
...
============================================================
Results: 9 passed, 0 failed out of 9 tests
✓ All tests passed!
```

## Extending the Classifier

To add new keywords or institution types:

1. Edit `CLASSIFICATION_RULES` in `institution_classifier.py`
2. Add keywords to appropriate categories (primary, secondary, negative)
3. Run tests to verify changes
4. Update this documentation

Example:

```python
CLASSIFICATION_RULES = {
    '高中': {
        'primary_keywords': [
            'sma',
            'your_new_keyword',  # Add here
        ],
        ...
    }
}
```

## Performance

- Classification is fast (< 1ms per institution)
- Regex patterns are compiled once at initialization
- Suitable for batch processing thousands of institutions

## Limitations

- Keyword-based approach may miss context-specific cases
- Requires Indonesian or English keywords
- May need manual review for ambiguous cases
- Confidence scores are relative, not absolute probabilities
