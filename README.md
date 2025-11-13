# mcraes_website_analytics

# McRAE's Website Analytics API

A FastAPI server that syncs data from Scrunch AI API to Supabase database.

## Features

- Fetch brands, prompts, and responses from Scrunch AI API
- Store data in Supabase database
- Automatic pagination handling
- RESTful API endpoints for syncing data
- Background task support

## Setup Steps

### 1. Prerequisites

- Python 3.8+
- Supabase account and project
- Scrunch AI API access (already configured)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

### 4. Set Up Supabase Database

Create the following tables in your Supabase project:

#### Brands Table
```sql
CREATE TABLE brands (
    id INTEGER PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMPTZ
);
```

#### Prompts Table
```sql
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY,
    prompt_text TEXT,
    stage TEXT,
    persona_id INTEGER,
    persona_name TEXT,
    tags TEXT[],
    key_topics TEXT[],
    created_at TIMESTAMPTZ
);
```

#### Responses Table
```sql
CREATE TABLE responses (
    id INTEGER PRIMARY KEY,
    prompt_id INTEGER,
    prompt TEXT,
    response_text TEXT,
    platform TEXT,
    country TEXT,
    persona_name TEXT,
    stage TEXT,
    branded BOOLEAN,
    key_topics TEXT[],
    brand_present BOOLEAN,
    brand_sentiment TEXT,
    brand_position TEXT,
    competitors_present TEXT[],
    competitors TEXT[],
    created_at TIMESTAMPTZ,
    citations JSONB
);
```

#### Citations Table (Optional - if storing citations separately)
```sql
CREATE TABLE citations (
    id SERIAL PRIMARY KEY,
    response_id INTEGER REFERENCES responses(id),
    url TEXT,
    domain TEXT,
    source_type TEXT,
    title TEXT,
    snippet TEXT
);
```

### 5. Run the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /health` - Check server health

### Sync Endpoints

- `POST /api/v1/sync/brands` - Sync all brands
- `POST /api/v1/sync/prompts` - Sync all prompts
  - Query params: `stage`, `persona_id`
- `POST /api/v1/sync/responses` - Sync all responses
  - Query params: `platform`, `prompt_id`, `start_date`, `end_date`
- `POST /api/v1/sync/all` - Sync all data (brands, prompts, responses)
- `GET /api/v1/sync/status` - Get current sync status from database

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Sync all data
```bash
curl -X POST "http://localhost:8000/api/v1/sync/all"
```

### Sync prompts for a specific stage
```bash
curl -X POST "http://localhost:8000/api/v1/sync/prompts?stage=Evaluation"
```

### Sync responses with date range
```bash
curl -X POST "http://localhost:8000/api/v1/sync/responses?start_date=2025-10-01&end_date=2025-10-08"
```

### Check sync status
```bash
curl -X GET "http://localhost:8000/api/v1/sync/status"
```

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── sync.py          # API endpoints for syncing
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   └── database.py       # Supabase client setup
│   └── services/
│       ├── scrunch_client.py # Scrunch AI API client
│       └── supabase_service.py # Supabase service layer
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Notes

- The server handles pagination automatically (max 1000 items per request)
- Data is upserted (insert or update) based on ID
- Responses are immutable in Scrunch AI, so upserts are safe
- All timestamps are stored in UTC

## Troubleshooting

1. **Database connection errors**: Verify your Supabase URL and key in `.env`
2. **API errors**: Check your Scrunch AI token is valid
3. **Table errors**: Ensure all tables are created in Supabase with correct schemas

