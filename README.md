# snowflake-cortex-search-demo
Service user registry with RSA key expiry alerting using Snowflake Cortex Search and Streamlit
# Snowflake Service User Registry — Cortex Search + Streamlit

A fully native Snowflake solution to search, filter, and audit service user 
credentials with intelligent RSA key expiry alerting.

## What this does
- Tracks RSA key pair expiry dates for all Snowflake service users
- Surfaces OVERDUE / CRITICAL / HIGH urgency tiers before pipelines break
- Provides a searchable Streamlit app (read-only) for security and DBA teams

## Tech stack
`Snowflake` `Cortex Search` `Streamlit` `SQL`

## Architecture
```
SOURCE TABLE → Enriched VIEW → Cortex Search Service → Streamlit App
                                                      
```

## Setup — step by step
1. Run `sql/02_create_view.sql` to create the enriched search view
2. Run `sql/03_create_cortex_search_service.sql` to deploy the search index
3. Deploy `streamlit/app.py` in Snowflake → Streamlit
4. Import `adf/pipeline_definition.json` into your Azure Data Factory instance

## Key concepts demonstrated
- Snowflake Cortex Search (hybrid keyword + semantic)
- Multi-format date parsing with `TRY_TO_DATE` and null handling

## Screenshots
![Streamlit App](docs/streamlit_screenshot.png)
