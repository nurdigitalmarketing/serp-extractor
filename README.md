# Google Search Extractor Pro

A Streamlit application for extracting and analyzing Google search results using SerpApi.

## Features

- Advanced Google search functionality with multiple filters
- Support for different search types (Web, Images, News, Videos, Shopping)
- Advanced domain and directory filtering
- Date-based filtering
- File type filtering
- CSV and JSON export capabilities
- Italian localization support

## Requirements

```
streamlit
requests
pandas
python-dateutil
```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The application requires:

1. A SerpApi API key
2. API key configuration through either:
   - Streamlit secrets (recommended)
   - Manual input in the interface

Create a `.streamlit/secrets.toml` file with:

```toml
[serp_api]
api_key = "YOUR_API_KEY"
```

## Usage

Execute the following command to start the application:

```bash
streamlit run app.py
```

The application provides functionality for:

- Basic search query input
- Exact phrase matching
- Domain-specific filtering
- Directory inclusion/exclusion
- Domain and keyword exclusion
- File type filtering
- Date range selection
- Maximum page retrieval configuration

## Technical Notes

- Default configuration for Italian locale
- Results limited to 100 per page
- Implements basic rate limiting (1 second between requests)
- Image results are filtered to remove invalid entries
- Supports multiple export formats (CSV, JSON)

## Development

The application is built using Streamlit and integrates with the SerpApi service for search result retrieval. It implements a modular architecture with separate components for:

- Search query construction
- API interaction
- Result processing
- Data export

## License

MIT License
