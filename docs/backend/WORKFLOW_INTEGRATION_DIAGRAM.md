# Workflow Integration Visual Guide

## Complete System Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                    (React Frontend + API)                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP Request
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API ENDPOINTS                                │
│  POST /api/tasks/{id}/start  →  Triggers workflow                  │
│  GET  /api/tasks/{id}/progress  →  Check status                    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Queue Task
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CELERY TASK QUEUE                               │
│                    (Redis as Broker)                                 │
│                                                                       │
│  scrape_google_task  →  Main orchestration task                    │
│  extract_website_task  →  Website extraction (parallel)            │
│  extract_social_task  →  Social media extraction (parallel)        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Execute
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW ORCHESTRATOR                             │
│                   (ScrapingWorkflow Class)                           │
│                                                                       │
│  • Coordinates all components                                        │
│  • Manages data flow                                                 │
│  • Handles errors and retries                                        │
│  • Tracks progress and metrics                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │   SCRAPING   │  │  EXTRACTION  │  │  VALIDATION  │
        │    LAYER     │  │    LAYER     │  │    LAYER     │
        └──────────────┘  └──────────────┘  └──────────────┘
                │                 │                 │
                └─────────────────┼─────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      REPOSITORY LAYER                                │
│                                                                       │
│  TaskRepository  →  Manage tasks                                    │
│  ContactRepository  →  Store contacts (with duplicate check)        │
│  ScrapingLogRepository  →  Log all operations                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ SQL
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATABASE                                     │
│                    (PostgreSQL)                                      │
│                                                                       │
│  tasks  →  Task definitions and status                              │
│  contacts  →  Extracted contact information                         │
│  scraping_logs  →  Operation logs and errors                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Integration

### 1. Scraping Layer Components

```
┌─────────────────────────────────────────────────────────────┐
│                    SCRAPING LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ScrapingEngine                                              │
│  ├─ Browser automation (Selenium)                           │
│  ├─ Anti-detection measures                                 │
│  ├─ Rate limiting                                            │
│  └─ Retry logic with exponential backoff                    │
│                                                               │
│  GoogleScraper                                               │
│  ├─ Search query execution                                  │
│  ├─ Result parsing                                           │
│  └─ Platform detection (website/facebook/instagram)         │
│                                                               │
│  ContactPageFinder                                           │
│  ├─ Locate contact pages                                    │
│  ├─ Try common paths (/contact, /kontak, etc.)             │
│  └─ Fallback to main URL                                    │
│                                                               │
│  FacebookScraper / InstagramScraper                         │
│  ├─ Profile data extraction                                 │
│  ├─ Bio/about section parsing                               │
│  └─ External link detection                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ PageContent / ProfileData
                        ▼
```

### 2. Extraction Layer Components

```
┌─────────────────────────────────────────────────────────────┐
│                   EXTRACTION LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  HTMLParser                                                  │
│  ├─ Parse HTML with BeautifulSoup                           │
│  ├─ Extract text content                                     │
│  ├─ Call ContactExtractor                                    │
│  └─ Call InstitutionClassifier                              │
│                                                               │
│  ContactExtractor                                            │
│  ├─ Email pattern matching (Indonesian domains)             │
│  ├─ WhatsApp number extraction                              │
│  ├─ Text cleaning and normalization                         │
│  └─ Context-aware extraction                                │
│                                                               │
│  InstitutionClassifier                                       │
│  ├─ Keyword-based classification                            │
│  ├─ Types: 高中, 華語中心, 代辦                              │
│  ├─ Confidence scoring                                       │
│  └─ Negative keyword filtering                              │
│                                                               │
│  SocialMediaExtractor                                        │
│  ├─ Platform-specific patterns                              │
│  ├─ Marker detection (WA:, Email:)                          │
│  └─ Link-in-bio parsing                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ ContactInfo / ParsedData
                        ▼
```

### 3. Validation Layer Components

```
┌─────────────────────────────────────────────────────────────┐
│                   VALIDATION LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ContactValidator                                            │
│  ├─ Email validation                                         │
│  │  ├─ Format checking                                      │
│  │  ├─ Domain validation                                    │
│  │  ├─ Indonesian domain detection                          │
│  │  └─ Disposable email filtering                           │
│  │                                                            │
│  ├─ Phone validation                                         │
│  │  ├─ Format checking                                      │
│  │  ├─ Indonesian number validation                         │
│  │  ├─ Normalization to +62 format                          │
│  │  └─ Length validation                                    │
│  │                                                            │
│  └─ Quality score calculation                                │
│     ├─ Email present: +40 points                            │
│     ├─ WhatsApp present: +40 points                         │
│     ├─ Website source: +10 points                           │
│     └─ Institution name: +10 points                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ Validated Contact Data
                        ▼
```

### 4. Repository Layer Components

```
┌─────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  TaskRepository                                              │
│  ├─ CRUD operations for tasks                               │
│  ├─ Status updates                                           │
│  ├─ Progress tracking                                        │
│  └─ Results count increment                                  │
│                                                               │
│  ContactRepository                                           │
│  ├─ CRUD operations for contacts                            │
│  ├─ Duplicate checking                                       │
│  │  ├─ By source URL                                        │
│  │  ├─ By email                                             │
│  │  └─ By WhatsApp number                                   │
│  ├─ Search and filtering                                     │
│  └─ Quality-based queries                                    │
│                                                               │
│  ScrapingLogRepository                                       │
│  ├─ Log all operations                                       │
│  ├─ Track success/failure                                    │
│  ├─ Record error messages                                    │
│  └─ Response time tracking                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ SQL Queries
                        ▼
```

## Data Flow Example: Website Extraction

```
1. INPUT
   ┌─────────────────────────────────────┐
   │ URL: https://smajakarta.sch.id      │
   │ Institution: SMA Internasional      │
   └─────────────────────────────────────┘
                    ↓
2. SCRAPING
   ┌─────────────────────────────────────┐
   │ ScrapingEngine.fetch_page()         │
   │ → Returns PageContent               │
   │   - HTML: <html>...</html>          │
   │   - Title: SMA Internasional        │
   └─────────────────────────────────────┘
                    ↓
3. EXTRACTION
   ┌─────────────────────────────────────┐
   │ HTMLParser.parse_html()             │
   │ → Returns ParsedData                │
   │   - emails: [info@sma.sch.id]       │
   │   - whatsapp: [+62812...]           │
   │   - institution_type: 高中          │
   └─────────────────────────────────────┘
                    ↓
4. VALIDATION
   ┌─────────────────────────────────────┐
   │ ContactValidator.validate_email()   │
   │ → Valid: info@sma.sch.id            │
   │                                      │
   │ ContactValidator.validate_phone()   │
   │ → Valid: +628123456789              │
   │                                      │
   │ ContactValidator.calculate_quality()│
   │ → Score: 100.0                      │
   └─────────────────────────────────────┘
                    ↓
5. DUPLICATE CHECK
   ┌─────────────────────────────────────┐
   │ ContactRepository.check_duplicate() │
   │ → Not duplicate                     │
   └─────────────────────────────────────┘
                    ↓
6. STORAGE
   ┌─────────────────────────────────────┐
   │ ContactRepository.create()          │
   │ → Contact saved to database         │
   │                                      │
   │ TaskRepository.increment_results()  │
   │ → Task results_count += 1           │
   │                                      │
   │ ScrapingLogRepository.create()      │
   │ → Operation logged                  │
   └─────────────────────────────────────┘
                    ↓
7. OUTPUT
   ┌─────────────────────────────────────┐
   │ WorkflowResult                      │
   │ - success: True                     │
   │ - contacts_saved: 1                 │
   │ - quality_score: 100.0              │
   │ - execution_time: 8.5s              │
   └─────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    ERROR OCCURS                              │
│  (Network timeout, parsing error, validation failure, etc.) │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              CATCH IN WORKFLOW                               │
│  try:                                                         │
│      execute_extraction()                                    │
│  except Exception as e:                                      │
│      handle_error(e)                                         │
└─────────────────────────────────────────────────────────────┘
                        │
            ┌───────────┼───────────┐
            ▼                       ▼
┌──────────────────┐      ┌──────────────────┐
│  LOG TO DATABASE │      │  CHECK IF RETRY  │
│                  │      │                  │
│ ScrapingLog:     │      │ - Retry count    │
│ - status: failed │      │ - Error type     │
│ - error_message  │      │ - Max retries    │
│ - timestamp      │      │                  │
└──────────────────┘      └──────────────────┘
                                    │
                        ┌───────────┼───────────┐
                        ▼                       ▼
            ┌──────────────────┐      ┌──────────────────┐
            │  SHOULD RETRY    │      │  SHOULD NOT      │
            │                  │      │  RETRY           │
            │ - Retry with     │      │                  │
            │   exponential    │      │ - Mark as failed │
            │   backoff        │      │ - Continue with  │
            │ - Increment      │      │   next item      │
            │   retry count    │      │                  │
            └──────────────────┘      └──────────────────┘
```

## Parallel Execution Flow

```
Google Search Results
        │
        ├─ Result 1 (website)
        ├─ Result 2 (facebook)
        ├─ Result 3 (instagram)
        ├─ Result 4 (website)
        └─ Result 5 (website)
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              CELERY GROUP TASK                               │
│  group([                                                      │
│      extract_website_task.s(task_id, url1),                 │
│      extract_social_task.s(task_id, url2, "facebook"),      │
│      extract_social_task.s(task_id, url3, "instagram"),     │
│      extract_website_task.s(task_id, url4),                 │
│      extract_website_task.s(task_id, url5)                  │
│  ]).apply_async()                                            │
└─────────────────────────────────────────────────────────────┘
                │
    ┌───────────┼───────────┬───────────┬───────────┐
    ▼           ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Worker 1│ │Worker 2│ │Worker 3│ │Worker 4│ │Worker 5│
│        │ │        │ │        │ │        │ │        │
│Extract │ │Extract │ │Extract │ │Extract │ │Extract │
│Website │ │Facebook│ │Instagram│ │Website │ │Website │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
    │           │           │           │           │
    └───────────┴───────────┴───────────┴───────────┘
                        │
                        ▼
            All results aggregated
            Task marked as complete
```

## Quality Score Calculation

```
┌─────────────────────────────────────────────────────────────┐
│                 QUALITY SCORE CALCULATION                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Base Score: 0                                               │
│                                                               │
│  + Has Valid Email?                                          │
│    ├─ Yes → +40 points                                      │
│    └─ No  → +0 points                                       │
│                                                               │
│  + Has Valid WhatsApp?                                       │
│    ├─ Yes → +40 points                                      │
│    └─ No  → +0 points                                       │
│                                                               │
│  + Source Platform?                                          │
│    ├─ Website → +10 points                                  │
│    ├─ Facebook/Instagram → +5 points                        │
│    └─ Other → +0 points                                     │
│                                                               │
│  + Has Institution Name?                                     │
│    ├─ Yes → +10 points                                      │
│    └─ No  → +0 points                                       │
│                                                               │
│  = Total Score (0-100)                                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Examples:
┌────────────────────────────────────────────────────────┐
│ Complete website contact:                              │
│ Email ✓ + WhatsApp ✓ + Website ✓ + Name ✓ = 100      │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Email only from website:                               │
│ Email ✓ + WhatsApp ✗ + Website ✓ + Name ✓ = 60       │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Complete social media contact:                         │
│ Email ✓ + WhatsApp ✓ + Facebook ✓ + Name ✓ = 95      │
└────────────────────────────────────────────────────────┘
```

## Integration Success Indicators

✅ **Module Integration**
- All components can be imported
- No circular dependencies
- Clear interfaces between layers

✅ **Data Flow**
- Data flows seamlessly through all layers
- Type safety maintained
- No data loss between components

✅ **Error Handling**
- Errors caught at each layer
- Proper logging and retry logic
- Graceful degradation

✅ **Quality Assurance**
- Validation at every step
- Duplicate detection working
- Quality scoring accurate

✅ **Performance**
- Parallel execution working
- Rate limiting effective
- Resource cleanup proper

✅ **Observability**
- Comprehensive logging
- Metrics collection
- Progress tracking
