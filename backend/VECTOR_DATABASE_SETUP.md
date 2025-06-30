# Vector Database Setup Guide

This guide will help you set up the vector database for fuzzy string matching in SQL queries.

## 🔧 Prerequisites

### 1. Install Core Dependencies

First install the main project dependencies:

```bash
# From the backend directory
cd backend

# Install core dependencies (this should work without issues)
poetry install
```

### 2. Install Vector Database Dependencies

The vector database dependencies are installed separately to avoid PEP 517 build issues:

**Option A: Automated Installation (Recommended)**
```bash
python install_vector_deps.py
```

**Option B: Manual Installation**
```bash
pip install chromadb==0.4.15
pip install sentence-transformers==2.2.2
pip install torch==2.0.0
pip install spacy==3.6.1
python -m spacy download en_core_web_sm
```

**Option C: If Above Fails**
```bash
# Install core dependencies only, system will work without vector database
poetry install
# The fuzzy matching will be disabled but everything else works
```

### 2. Verify Installation

Test that all dependencies are working:

```bash
poetry run python test_imports.py
```

## 🗄️ Set Up Vector Database

### Option A: Quick Demo Setup (Recommended for Testing)

Use sample data to test the system quickly:

```bash
poetry run python setup_vector_db_demo.py
```

This will:
- Add sample employee names including "Rosalinda Rodriguez"
- Add sample locations including "Lincoln High School" and "Lincoln HS"
- Test entity resolution with common misspellings and abbreviations

### Option B: Full BigQuery Integration

Index actual data from your BigQuery tables:

```bash
# Index all entity types
poetry run python scripts/index_entities.py --all --verbose

# Or index specific types
poetry run python scripts/index_entities.py --entity employees --verbose
poetry run python scripts/index_entities.py --entity locations --verbose
```

## 🔍 Diagnostic Tools

### Check System Status

```bash
poetry run python diagnose_vector_db.py
```

This will show:
- Dependency status
- Vector database collection statistics  
- Entity extraction test results
- Similarity search examples

### Test Entity Indexing

```bash
poetry run python quick_test_indexing.py
```

## ⚙️ Configuration

The system can be configured via environment variables:

```bash
# Vector database settings
export VECTOR_DB_PERSIST_DIR="data/vector_db"
export EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"
export VECTOR_CONFIDENCE_THRESHOLD="0.5"      # Lower = more fuzzy matches
export MIN_QUERY_CONFIDENCE="0.3"             # Lower = more query enhancements

# Entity resolution settings  
export ENABLE_ENTITY_RESOLUTION="true"
export MAX_SUGGESTIONS_PER_ENTITY="3"
export ENABLE_NO_RESULTS_SUGGESTIONS="true"

# Logging
export LOG_ENTITY_RESOLUTIONS="true"
export LOG_VECTOR_SEARCH_DETAILS="false"
```

## 🚀 Usage

Once set up, the system will automatically enhance queries:

### Example 1: Name Misspelling
- **User asks:** "where does rosalinda rodrigues work"  
- **System resolves:** "rodrigues" → "rodriguez"
- **SQL generated:** Uses correct spelling "rodriguez"

### Example 2: Location Abbreviation  
- **User asks:** "who works at lincoln hs"
- **System resolves:** "lincoln hs" → "Lincoln High School"  
- **SQL generated:** Uses full location name

### Example 3: No Results Suggestions
- **User asks:** "where does john smyth work" (misspelling)
- **SQL returns:** No results
- **System suggests:** "Did you mean: John Smith (95% match)"

## 🔧 Troubleshooting

### "Failed to send telemetry event" Error
This is a ChromaDB issue that's been fixed. Restart the server.

### "No entities resolved" 
1. Check if vector database has data: `poetry run python diagnose_vector_db.py`
2. If empty, run entity indexing: `poetry run python setup_vector_db_demo.py`
3. Check confidence thresholds (lower = more matches)

### Import Errors
1. Install dependencies: `poetry install`
2. Install spaCy model: `poetry run python -m spacy download en_core_web_sm`
3. Verify: `poetry run python test_imports.py`

### No BigQuery Data
1. Ensure BigQuery credentials are configured
2. Check that tables exist: `poetry run python test_employee_schema.py`
3. Verify dataset/project settings in environment variables

## 📊 Monitoring

The system provides detailed logging when processing queries:

```
🔍 Entity Resolution: Processing query 'where does rosalinda rodrigues work'
🔍 Entity Resolution Results:
   Original: 'where does rosalinda rodrigues work'
   Enhanced: 'where does rosalinda rodriguez work'  
   Confidence: 0.85
   Fallback: false
   ✅ 1 entities resolved:
      'rosalinda rodrigues' → 'rosalinda rodriguez' (confidence: 0.85)
```

## 🎯 Expected Results

After proper setup, these test queries should work:

1. `"where does rosalinda rodrigues work"` → Finds "Rosalinda Rodriguez"
2. `"who works at lincoln hs"` → Finds "Lincoln High School" 
3. `"employees at washington es"` → Finds "Washington Elementary"

The system gracefully falls back to standard behavior if vector database is unavailable.