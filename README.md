# Document to Audio Summary

Automatically fetch documents from various sources (Gmail, Google Calendar, Hacker News) and generate compelling audio summaries.

## Project Structure

```
my-audio-summaries/
├── docs-to-audio/          # Legacy audio generation code
├── src/
│   ├── fetchers/          # Document fetchers
│   │   ├── __init__.py
│   │   ├── base.py       # Base fetcher class
│   │   ├── gmail.py      # Gmail fetcher
│   │   ├── gcalendar.py  # Google Calendar fetcher
│   │   └── hackernews.py # Hacker News fetcher
│   ├── processors/        # Document processors
│   │   ├── __init__.py
│   │   ├── base.py       # Base processor class
│   │   ├── pdf.py        # PDF processor
│   │   └── text.py       # Plain text processor
│   ├── audio/            # Audio generation
│   │   ├── __init__.py
│   │   ├── generator.py  # Audio generation logic
│   │   └── utils.py      # Audio utilities
│   ├── utils/            # Shared utilities
│   │   ├── __init__.py
│   │   ├── auth.py       # Authentication utilities
│   │   └── config.py     # Configuration management
│   └── main.py           # Main application entry point
├── tests/                # Test files
│   ├── fetchers/         # Fetcher tests
│   ├── processors/       # Processor tests
│   └── audio/           # Audio generation tests
├── config/              # Configuration files
│   ├── default.yaml     # Default configuration
│   └── .env.example     # Example environment variables
├── logs/               # Log files
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Setup

1. Install dependencies and activate virtual environment:

```bash
uv sync
source .venv/bin/activate
```

2. Configure authentication:

- Copy `.env.example` to `.env`
- Add your API keys and credentials

3. Run the application:

```bash
python -m src.main
```

## Development

- `src/fetchers/`: Add new document sources by implementing the base fetcher class
- `src/processors/`: Add support for new document types by implementing the base processor class
- `src/audio/`: Audio generation logic (migrated from docs-to-audio)
- `tests/`: Unit and integration tests

## Configuration

The application uses two types of configuration:

1. `config/default.yaml`: General application settings
2. `.env`: Sensitive credentials and API keys

## Testing

Run tests with:

```bash
pytest tests/
```
