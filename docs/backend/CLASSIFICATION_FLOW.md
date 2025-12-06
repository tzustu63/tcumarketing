# Institution Classification Flow

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Scraping Tasks Layer                         │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │ Website Scraping │              │ Social Scraping  │         │
│  └────────┬─────────┘              └────────┬─────────┘         │
└───────────┼──────────────────────────────────┼──────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Extraction Layer                               │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │   HTML Parser    │              │ Social Extractor │         │
│  │  - Parse HTML    │              │ - Extract bio    │         │
│  │  - Extract text  │              │ - Find markers   │         │
│  └────────┬─────────┘              └────────┬─────────┘         │
│           │                                  │                   │
│           └──────────────┬───────────────────┘                   │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │  Contact Extractor    │                          │
│              │  - Extract emails     │                          │
│              │  - Extract WhatsApp   │                          │
│              └───────────┬───────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Classification Layer                             │
│              ┌───────────────────────┐                          │
│              │ Institution Classifier│                          │
│              │  - Match keywords     │                          │
│              │  - Calculate score    │                          │
│              │  - Return type        │                          │
│              └───────────┬───────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                                 │
│              ┌───────────────────────┐                          │
│              │   Contact Model       │                          │
│              │  - institution_name   │                          │
│              │  - institution_type ✓ │ ← Auto-classified       │
│              │  - email              │                          │
│              │  - whatsapp           │                          │
│              │  - quality_score      │                          │
│              └───────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## Classification Process

### Step 1: Data Collection
```
Website/Social Media → HTML/Text Content
```

### Step 2: Text Extraction
```
HTML Parser / Social Extractor
    ↓
Institution Name + Description Text
```

### Step 3: Classification
```
Institution Classifier
    ↓
Keyword Matching:
  - Primary Keywords (+10 points)
  - Secondary Keywords (+3 points)
  - Negative Keywords (-15 points)
    ↓
Best Match Selection
    ↓
Confidence Calculation (0-100%)
```

### Step 4: Storage
```
Contact Object
    ↓
institution_type: "高中" | "華語中心" | "代辦"
    ↓
Database
```

## Example Flow

### Website Scraping Example

```
1. Scrape: https://sma-jakarta.sch.id
   ↓
2. HTML Parser extracts:
   - Title: "SMA Internasional Jakarta"
   - Text: "Sekolah menengah atas dengan kurikulum internasional..."
   ↓
3. Contact Extractor calls Classifier:
   - Input: "SMA Internasional Jakarta" + text
   - Matched: "sma", "sekolah menengah atas", "kurikulum"
   - Score: 10 + 10 + 3 = 23 points
   ↓
4. Classification Result:
   - Type: "高中"
   - Confidence: 43.3%
   - Keywords: ["sma", "sekolah menengah atas", "kurikulum"]
   ↓
5. Save to Database:
   - institution_name: "SMA Internasional Jakarta"
   - institution_type: "高中"
   - email: "info@sma-jakarta.sch.id"
   - whatsapp: "+628123456789"
```

### Social Media Scraping Example

```
1. Scrape: https://instagram.com/pusat_mandarin_bali
   ↓
2. Social Extractor extracts:
   - Name: "Pusat Bahasa Mandarin Bali"
   - Bio: "Kursus bahasa Mandarin untuk semua tingkat. HSK preparation."
   ↓
3. Classifier processes:
   - Input: "Pusat Bahasa Mandarin Bali" + bio
   - Matched: "pusat bahasa", "mandarin", "kursus", "hsk"
   - Score: 10 + 10 + 10 + 3 = 33 points
   ↓
4. Classification Result:
   - Type: "華語中心"
   - Confidence: 66.7%
   - Keywords: ["pusat bahasa", "mandarin", "kursus", "hsk"]
   ↓
5. Save to Database:
   - institution_name: "Pusat Bahasa Mandarin Bali"
   - institution_type: "華語中心"
   - email: "info@mandarinbali.com"
   - whatsapp: "+628987654321"
```

## Keyword Matching Logic

### High School (高中)
```
Primary Keywords (10 pts each):
  ✓ sma, high school, smk
  ✓ sekolah menengah atas
  ✓ madrasah aliyah, pesantren

Secondary Keywords (3 pts each):
  ✓ international school
  ✓ boarding school, siswa
  ✓ kurikulum, curriculum

Negative Keywords (-15 pts each):
  ✗ universitas, university
  ✗ bahasa mandarin
  ✗ agen, agency
```

### Language Center (華語中心)
```
Primary Keywords (10 pts each):
  ✓ bahasa mandarin, chinese language
  ✓ pusat bahasa, language center
  ✓ kursus mandarin, chinese course

Secondary Keywords (3 pts each):
  ✓ hsk, hanyu, 中文
  ✓ chinese class, mandarin class
  ✓ chinese teacher, guru mandarin

Negative Keywords (-15 pts each):
  ✗ sma, high school
  ✗ agen, agency
  ✗ konsultan
```

### Education Agency (代辦)
```
Primary Keywords (10 pts each):
  ✓ agen pendidikan, education agent
  ✓ konsultan pendidikan
  ✓ study abroad, kuliah luar negeri
  ✓ visa, admission, beasiswa

Secondary Keywords (3 pts each):
  ✓ konsultasi, consultation
  ✓ overseas, luar negeri
  ✓ taiwan, china, australia

Negative Keywords (-15 pts each):
  ✗ sma, high school
  ✗ bahasa mandarin
  ✗ kursus
```

## Confidence Scoring

```
Score Calculation:
  Total Score = (Primary × 10) + (Secondary × 3) + (Negative × -15)

Confidence Percentage:
  Confidence = min(100%, (Total Score / 30) × 100)

Interpretation:
  > 60%  : Strong match (multiple primary keywords)
  30-60% : Good match (primary + secondary keywords)
  < 30%  : Weak match (secondary keywords only)
  0%     : No match (no classification)
```

## Integration Points

### 1. HTML Parser Integration
```python
parsed_data = html_parser.parse_html(
    html=html_content,
    institution_name="SMA Jakarta"
)
# Returns: {'institution_type': '高中', ...}
```

### 2. Contact Extractor Integration
```python
contact_info = contact_extractor.extract_from_text(
    text=text_content,
    institution_name="Pusat Mandarin"
)
# Returns: ContactInfo(institution_type='華語中心', ...)
```

### 3. Social Media Integration
```python
institution_type = social_extractor.extract_institution_type_from_social(
    text=bio_text,
    page_name="Education Consultant"
)
# Returns: '代辦'
```

### 4. Database Storage
```python
contact = Contact(
    institution_name="SMA Jakarta",
    institution_type="高中",  # Auto-classified
    email="info@sma.sch.id",
    whatsapp="+628123456789"
)
```

## Benefits

✅ **Automatic**: No manual categorization needed
✅ **Consistent**: Same logic across all sources
✅ **Fast**: < 1ms per classification
✅ **Transparent**: Confidence scores provided
✅ **Extensible**: Easy to add new keywords
✅ **Integrated**: Works seamlessly with existing workflow
