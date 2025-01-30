# Lookout SSE Event Stream Client

A Python client for consuming Lookout's Mobile Risk API Server-Sent Events (SSE) stream. This client supports both real-time and historical event streaming within the last 10 days, with flexible filtering options.

## Features

- Real-time event streaming
- Historical event retrieval (within 10-day limit)
- Event type filtering (DEVICE, THREAT, AUDIT)
- Resume from specific event ID
- Environment variable configuration
- OAuth2 authentication handling
- Flexible date/time input formats

## Prerequisites

- Python 3.7+
- Lookout API Application Key


1. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` file and add your Lookout application key:
```
LOOKOUT_APP_KEY=your-application-key-here
```

## Usage

### Command Line Options

The client supports various command-line arguments for flexible event streaming:

```bash
python sse_client.py [--current | --historical] [options]
```

#### Required Arguments (mutually exclusive):
- `--current`: Stream current events
- `--historical`: Stream historical events (requires --start-time)

#### Optional Arguments:
- `--start-time`: Start time for historical events (ISO8601 or human-readable)
- `--event-types`: Filter specific event types (DEVICE, THREAT, AUDIT)
- `--last-event-id`: Resume from specific event ID

### Examples

1. Stream current events:
```bash
python sse_client.py --current
```

2. Stream current events with specific event types:
```bash
python sse_client.py --current --event-types DEVICE THREAT
```

3. Stream historical events from a specific date/time:
```bash
python sse_client.py --historical --start-time "2024-01-25T10:00:00Z"
```

4. Stream historical events with human-readable date:
```bash
python sse_client.py --historical --start-time "2 days ago"
```

5. Resume from a specific event ID:
```bash
python sse_client.py --current --last-event-id "0190bc7d-974b-7b64-9fa6-5b9ecca6fbc6"
```

### Date Format Support

The `--start-time` argument accepts various date formats:

- ISO8601: `"2024-01-25T10:00:00Z"`
- Human readable: `"2 days ago"`, `"yesterday"`, `"1 hour ago"`
- Natural language: `"Jan 25 2024 10:00 AM"`

Note: All dates must be within the last 10 days due to API limitations.

## Event Types

The client supports three types of events:

1. `DEVICE`: Device-related events
2. `THREAT`: Security threat events
3. `AUDIT`: Audit and system events

## Error Handling

The client includes comprehensive error handling for:

- Invalid date formats
- Dates outside the 10-day limit
- Missing or invalid authentication
- Network connectivity issues
- Invalid event types
- API rate limiting

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```
LOOKOUT_APP_KEY=your-application-key-here
```

Optional configuration:
```
LOOKOUT_API_BASE_URL=https://api.lookout.com  # Override base URL if needed
```

