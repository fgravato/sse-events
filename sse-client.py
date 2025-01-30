import requests
import json
import sseclient
import datetime
import os
from dotenv import load_dotenv
from typing import Optional, List, Generator, Union
from urllib.parse import quote
from dataclasses import dataclass
import argparse
from dateutil import parser
from dateutil.relativedelta import relativedelta

@dataclass
class LookoutAuth:
    """Handles OAuth2 authentication for Lookout API"""
    app_key: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_at: Optional[int] = None

    def authenticate(self) -> None:
        """Get OAuth2 access token using application key"""
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.app_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(
            'https://api.lookout.com/oauth2/token',
            headers=headers,
            data=data
        )
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        self.token_type = token_data['token_type']
        self.expires_at = token_data['expires_at']

    @property
    def auth_header(self) -> dict:
        """Return authorization header for API requests"""
        if not self.access_token:
            self.authenticate()
        return {'Authorization': f'Bearer {self.access_token}'}

class LookoutEventStream:
    """Client for Lookout's Server-Sent Events stream"""
    
    def __init__(self, auth: LookoutAuth):
        self.auth = auth
        self.base_url = 'https://api.lookout.com/mra/stream/v2/events'

    def _build_url(self, 
                   start_time: Optional[Union[str, datetime.datetime]] = None,
                   last_event_id: Optional[str] = None,
                   event_types: Optional[List[str]] = None) -> str:
        """Build URL with query parameters"""
        params = []
        
        if start_time:
            if isinstance(start_time, datetime.datetime):
                start_time = start_time.isoformat()
            params.append(f'start_time={quote(start_time)}')
            
        if last_event_id:
            params.append(f'id={last_event_id}')
            
        if event_types:
            valid_types = {'DEVICE', 'THREAT', 'AUDIT'}
            types = [t.upper() for t in event_types if t.upper() in valid_types]
            if types:
                params.append(f'types={",".join(types)}')
        
        return f'{self.base_url}{"?" + "&".join(params) if params else ""}'

    def stream_events(self,
                     start_time: Optional[Union[str, datetime.datetime]] = None,
                     last_event_id: Optional[str] = None,
                     event_types: Optional[List[str]] = None) -> Generator[dict, None, None]:
        """
        Stream events from Lookout API
        
        Args:
            start_time: Start time for historical events (ISO8601 string or datetime)
            last_event_id: Resume from specific event ID
            event_types: List of event types to filter ('DEVICE', 'THREAT', 'AUDIT')
            
        Yields:
            Dict containing event data
        """
        url = self._build_url(start_time, last_event_id, event_types)
        headers = {
            'Accept': 'text/event-stream',
            **self.auth.auth_header
        }
        
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        
        for event in client.events():
            if event.event == 'heartbeat':
                continue
                
            try:
                event_data = json.loads(event.data)
                yield event_data
            except json.JSONDecodeError:
                print(f"Failed to parse event data: {event.data}")
                continue

def validate_date(date_str: str) -> datetime.datetime:
    """
    Validate the date string and ensure it's within the 10-day limit
    """
    try:
        date = parser.parse(date_str)
        if not date.tzinfo:
            date = date.replace(tzinfo=datetime.UTC)
            
        # Check if date is within allowed range
        ten_days_ago = datetime.datetime.now(datetime.UTC) - relativedelta(days=10)
        if date < ten_days_ago:
            raise ValueError("Date must be within the last 10 days")
            
        return date
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid date format: {str(e)}")

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Lookout Event Stream Client')
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--current', action='store_true',
                           help='Stream current events')
    mode_group.add_argument('--historical', action='store_true',
                           help='Stream historical events from a specific date')
    
    # Historical mode options
    parser.add_argument('--start-time', type=validate_date,
                       help='Start time for historical events (ISO8601 format or human-readable)')
    
    # Event type filtering
    parser.add_argument('--event-types', nargs='+', choices=['DEVICE', 'THREAT', 'AUDIT'],
                       help='Filter specific event types')
    
    # Optional last event ID
    parser.add_argument('--last-event-id',
                       help='Resume from specific event ID')
    
    args = parser.parse_args()
    
    # Validate historical mode requirements
    if args.historical and not args.start_time:
        parser.error("--historical mode requires --start-time")
    
    return args

def main():
    """Main entry point"""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get application key from environment variable
        app_key = os.getenv('LOOKOUT_APP_KEY')
        if not app_key:
            raise ValueError("LOOKOUT_APP_KEY not found in environment variables")
        
        # Parse command line arguments
        args = parse_arguments()
        
        # Initialize authentication with app key
        auth = LookoutAuth(app_key=app_key)
        
        # Create event stream client
        stream = LookoutEventStream(auth)
        
        # Configure stream parameters based on arguments
        stream_params = {
            'event_types': args.event_types,
            'last_event_id': args.last_event_id
        }
        
        if args.historical:
            stream_params['start_time'] = args.start_time
        
        # Start streaming events
        print(f"Starting event stream...")
        if args.historical:
            print(f"From: {args.start_time.isoformat()}")
        if args.event_types:
            print(f"Event types: {', '.join(args.event_types)}")
            
        for event in stream.stream_events(**stream_params):
            print(json.dumps(event, indent=2))
    
    except KeyboardInterrupt:
        print("\nStream interrupted by user")
    except requests.exceptions.RequestException as e:
        print(f"API request error: {str(e)}")
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == '__main__':
    main()