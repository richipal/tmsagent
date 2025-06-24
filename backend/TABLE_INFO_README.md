# BigQuery Table Information & Query Suggestions

This module provides comprehensive table information and intelligent query suggestions for the ADK Data Science Chatbot's BigQuery integration.

## Features

### 📊 Table Information
- **Comprehensive Schema**: Get detailed schema information for all tables
- **Table Statistics**: Row counts, size, field counts, creation/modification dates
- **Sample Data**: Preview sample data from each table
- **Full DDL**: Complete CREATE TABLE statements

### 🧠 Intelligent Query Suggestions
- **AI-Generated**: Uses Gemini AI to generate contextual query suggestions
- **Categorized**: Organizes queries by purpose (Data Exploration, Statistical Analysis, etc.)
- **Difficulty Levels**: Beginner, Intermediate, and Advanced queries
- **Use Case Specific**: Tailored to your actual data schema

### 🚀 API Endpoints

#### GET `/api/table-info`
Get comprehensive table information including schemas, statistics, and sample data.

```bash
curl http://localhost:8000/api/table-info
```

**Response:**
```json
{
  "success": true,
  "data": {
    "database_info": {
      "type": "BigQuery",
      "project_id": "your-project-id",
      "dataset_id": "data_science_agents",
      "location": "US",
      "total_tables": 19
    },
    "tables": {
      "user": {
        "full_table_id": "project.dataset.user",
        "num_rows": 413,
        "size_gb": 0.00,
        "schema": [...],
        "sample_data": [...]
      }
    },
    "schema_ddl": "CREATE TABLE ..."
  }
}
```

#### GET `/api/table-info/suggestions`
Get table information with AI-generated query suggestions.

```bash
curl http://localhost:8000/api/table-info/suggestions
```

**Response includes:**
- Complete table information
- 15-20 intelligent query suggestions
- Query categories and organization
- Difficulty classifications

#### GET `/api/table-info/schema`
Get schema-only information (lightweight response).

```bash
curl http://localhost:8000/api/table-info/schema
```

#### GET `/api/table-info/sample-queries`
Get organized sample queries by category and difficulty.

```bash
curl http://localhost:8000/api/table-info/sample-queries
```

**Response:**
```json
{
  "success": true,
  "data": {
    "by_category": {
      "Data Exploration": [...],
      "Statistical Analysis": [...],
      "Business Intelligence": [...]
    },
    "by_difficulty": {
      "Beginner": [...],
      "Intermediate": [...],
      "Advanced": [...]
    },
    "total_queries": 17
  }
}
```

#### GET `/api/table-info/table/{table_name}`
Get detailed information about a specific table.

```bash
curl http://localhost:8000/api/table-info/table/user
```

## Query Categories

The system generates queries across multiple categories:

### 📈 Data Exploration
- Record counts and basic statistics
- Distinct value analysis
- Sample data queries
- Table structure exploration

### 📊 Statistical Analysis
- Min/Max/Average calculations
- Distribution analysis
- Outlier detection
- Correlation queries

### 🔍 Filtering and Sorting
- Date range filtering
- Conditional queries
- Top/Bottom N records
- Custom filters

### 🔗 Join Operations
- Multi-table analysis
- Relationship exploration
- Cross-reference queries
- Data integration

### 💼 Business Intelligence
- KPI calculations
- Trend analysis
- Performance metrics
- Comparative analysis

### ✅ Data Quality
- Null value detection
- Data validation
- Consistency checks
- Completeness analysis

## Usage Examples

### Python Service Usage

```python
from app.services.table_info_service import table_info_service

# Get comprehensive table info
table_info = table_info_service.get_comprehensive_table_info()

# Get table info with AI suggestions
result = await table_info_service.get_table_info_with_suggestions()

# Access specific table details
user_table = table_info['tables']['user']
print(f"User table has {user_table['num_rows']} rows")
```

### Frontend Integration

```javascript
// Get table schema for UI
const schemaResponse = await fetch('/api/table-info/schema');
const schema = await schemaResponse.json();

// Get query suggestions for autocomplete
const suggestionsResponse = await fetch('/api/table-info/suggestions');
const suggestions = await suggestionsResponse.json();

// Display organized queries
const queriesResponse = await fetch('/api/table-info/sample-queries');
const organizedQueries = await queriesResponse.json();
```

## Current Database Schema

**Project**: `adk-rag-462901`  
**Dataset**: `data_science_agents`  
**Location**: `US`  
**Total Tables**: 19

### Key Tables:
- **user** (413 rows) - User management and authentication
- **activity** (4,732 rows) - Activity tracking and management
- **absence** (56,394 rows) - Employee absence records
- **calculation_rate** (2.3M rows) - Rate calculations
- **time_entry_calculation_rates** (2.3M rows) - Time entry rates

### Sample Queries Generated:

**Data Exploration:**
```sql
SELECT COUNT(*) as total_records FROM `adk-rag-462901.data_science_agents.user`
```

**Statistical Analysis:**
```sql
SELECT MIN(rate) as min_rate, MAX(rate) as max_rate, AVG(rate) as avg_rate 
FROM `adk-rag-462901.data_science_agents.pay_rate`
```

**Business Intelligence:**
```sql
SELECT u.email, COUNT(ua.activity_id) as total_activities 
FROM `adk-rag-462901.data_science_agents.user` u 
LEFT JOIN `adk-rag-462901.data_science_agents.user_activities` ua 
ON u.user_id = ua.user_id 
GROUP BY u.email 
ORDER BY total_activities DESC
```

## Configuration

The service uses the following environment variables:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
BIGQUERY_DATASET_ID=data_science_agents
BIGQUERY_LOCATION=US
GOOGLE_API_KEY=your-gemini-api-key
```

## Files Structure

```
backend/
├── app/services/table_info_service.py    # Main service implementation
├── app/api/table_info.py                 # API endpoints
├── example_table_info_usage.py           # Usage examples
└── TABLE_INFO_README.md                  # This documentation
```

## Testing

Run the example script to see the system in action:

```bash
python example_table_info_usage.py
```

This will display:
- All available tables and their statistics
- AI-generated query suggestions organized by category
- Example queries for different use cases
- Detailed schema information
- API endpoint usage examples

## Integration with Chatbot

The table information service integrates seamlessly with the ADK Data Science Chatbot:

1. **Schema Context**: Provides schema information to the BigQuery agent for better NL2SQL conversion
2. **Query Suggestions**: Powers autocomplete and suggestion features in the UI
3. **Data Discovery**: Helps users understand what data is available for analysis
4. **Query Validation**: Supports query validation against actual table schemas

This comprehensive table information system makes it easy for users to discover, understand, and query your BigQuery data effectively!