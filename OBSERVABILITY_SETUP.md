# Observability Setup Guide

This guide explains how to set up user query tracking and observability for the TMS chatbot using Langfuse.

## Overview

The observability system tracks:
- User queries and responses
- Agent performance metrics
- Session data and conversation flows
- Error tracking and debugging information
- Cost and token usage analytics

## Quick Setup

### Option 1: Langfuse Cloud (Recommended)

1. **Sign up at [Langfuse Cloud](https://cloud.langfuse.com)**

2. **Create a new project** and get your API keys

3. **Configure environment variables** in your `.env` file:
   ```bash
   # Observability Configuration
   LANGFUSE_ENABLED=true
   LANGFUSE_HOST=https://cloud.langfuse.com
   LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
   LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
   
   # Privacy Settings
   TRACK_USER_QUERIES=true
   ANONYMIZE_USER_DATA=false
   EXCLUDE_TRACKING_PATTERNS=password,secret,key
   ```

4. **Install dependencies**:
   ```bash
   poetry install
   ```

5. **Start the application** - observability will be automatically enabled

### Option 2: Self-Hosted Langfuse

1. **Deploy Langfuse locally** using Docker:
   ```bash
   git clone https://github.com/langfuse/langfuse.git
   cd langfuse
   docker compose up -d
   ```

2. **Configure environment variables**:
   ```bash
   LANGFUSE_ENABLED=true
   LANGFUSE_HOST=http://localhost:3000
   LANGFUSE_PUBLIC_KEY=your-local-public-key
   LANGFUSE_SECRET_KEY=your-local-secret-key
   ```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGFUSE_ENABLED` | `true` | Enable/disable observability |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse instance URL |
| `LANGFUSE_PUBLIC_KEY` | - | Public API key from Langfuse |
| `LANGFUSE_SECRET_KEY` | - | Secret API key from Langfuse |
| `TRACK_USER_QUERIES` | `true` | Track user queries |
| `ANONYMIZE_USER_DATA` | `false` | Anonymize sensitive data |
| `EXCLUDE_TRACKING_PATTERNS` | - | Comma-separated patterns to exclude |
| `LANGFUSE_DEBUG` | `false` | Enable debug logging |
| `APP_VERSION` | `1.0.0` | Application version for tracking |

### Privacy Settings

- **Anonymization**: When `ANONYMIZE_USER_DATA=true`, the system will:
  - Remove email addresses, phone numbers, and IDs from queries
  - Limit response content to 1000 characters
  - Exclude user IDs from traces

- **Exclusion Patterns**: Use `EXCLUDE_TRACKING_PATTERNS` to prevent tracking of queries containing sensitive patterns:
  ```bash
  EXCLUDE_TRACKING_PATTERNS=password,secret,apikey,token
  ```

## What Gets Tracked

### Query Analytics
- Query text and metadata
- Session information
- Response generation time
- Query classification (chart, SQL, analysis)
- Error tracking

### Agent Performance
- Which agents are called for each query
- Agent execution time
- Success/failure rates
- SQL query generation and execution

### User Behavior
- Session duration
- Query patterns
- Feature usage (charts, analysis)
- Follow-up question patterns

## Viewing Analytics

### Langfuse Dashboard

1. **Login to your Langfuse instance**
2. **View Traces** - See individual query flows
3. **Analytics** - View aggregated metrics:
   - Query volume over time
   - Most common query types
   - Agent performance metrics
   - Error rates and types
   - Cost analysis

### Key Dashboards

- **Query Types**: Distribution of chart vs. data vs. analysis requests
- **Agent Usage**: Which agents are called most frequently
- **Performance**: Response times and success rates
- **User Patterns**: Session lengths and query patterns
- **Errors**: Common failure points and debugging info

## Testing the Setup

1. **Start the application**:
   ```bash
   cd backend && poetry run uvicorn main:app --reload
   ```

2. **Check startup logs** for observability initialization:
   ```
   ✅ Observability (Langfuse) initialized
   ```

3. **Send test queries** through the frontend

4. **View traces** in your Langfuse dashboard

## Troubleshooting

### Common Issues

1. **"Langfuse initialization failed"**
   - Check API keys are correct
   - Verify network connectivity to Langfuse host
   - Check firewall settings

2. **"No traces appearing"**
   - Verify `LANGFUSE_ENABLED=true`
   - Check API keys have correct permissions
   - Look for error logs in application

3. **Missing data in traces**
   - Check exclusion patterns aren't too broad
   - Verify agent calls are being tracked
   - Review privacy settings

### Debug Mode

Enable debug logging:
```bash
LANGFUSE_DEBUG=true
```

This will provide detailed logs about what's being tracked.

## Privacy Compliance

The observability system is designed with privacy in mind:

- **Opt-out**: Set `LANGFUSE_ENABLED=false` to disable tracking
- **Data anonymization**: Enable with `ANONYMIZE_USER_DATA=true`
- **Selective exclusion**: Use patterns to exclude sensitive queries
- **Self-hosting**: Deploy Langfuse locally for full data control

## Next Steps

1. **Set up alerting** for error rates or performance issues
2. **Create custom dashboards** for your specific use cases
3. **Implement user feedback collection** through Langfuse
4. **Set up cost monitoring** for LLM usage optimization

For more advanced configuration, see the [Langfuse documentation](https://langfuse.com/docs).