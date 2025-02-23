import os
import yaml
from datetime import datetime, timezone
import requests
from typing import Optional, List, Dict
from ..models.overdrive import OverdriveBook, OverdriveLoan, OverdriveHold
from ..models.base import SessionLocal

class OverdriveService:
    def __init__(self):
        self.session = SessionLocal()
        self._load_config()
        self._token = None
        self._token_expires = None

    def _load_config(self):
        """Load Overdrive configuration from yaml file"""
        config_path = os.path.join('config', 'overdrive.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['overdrive']

    def _get_token(self) -> str:
        """Get or refresh OAuth token"""
        if self._token and self._token_expires > datetime.now(timezone.utc):
            return self._token

        auth_response = requests.post(
            self.config['oauth_url'],
            data={
                'grant_type': 'client_credentials',
                'client_id': self.config['client_id'],
                'client_secret': self.config['client_secret']
            }
        )
        auth_response.raise_for_status()
        auth_data = auth_response.json()

        self._token = auth_data['access_token']
        self._token_expires = datetime.now(timezone.utc).timestamp() + auth_data['expires_in']
        return self._token

    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Dict:
        """Make authenticated request to Overdrive API"""
        headers = {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type': 'application/json'
        }

        url = f"{self.config['base_url']}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_book_cover(self, overdrive_id: str) -> Optional[str]:
        """Get book cover URL from Overdrive"""
        try:
            metadata = self._make_request(
                f"{self.config['endpoints']['metadata']}/{overdrive_id}"
            )
            return metadata.get('images', {}).get('cover', {}).get('href')
        except Exception as e:
            print(f"Error fetching cover for {overdrive_id}: {e}")
            return None

    def get_current_loans(self) -> List[OverdriveLoan]:
        """Get user's current loans"""
        try:
            loans_data = self._make_request(self.config['endpoints']['loans'])
            current_loans = []

            for loan in loans_data.get('loans', []):
                book = self._get_or_create_book(loan['id'], loan)
                loan_record = OverdriveLoan(
                    overdrive_book_id=book.id,
                    expires_at=datetime.fromisoformat(loan['expires']),
                    borrowed_at=datetime.fromisoformat(loan['borrowed'])
                )
                current_loans.append(loan_record)

            return current_loans
        except Exception as e:
            print(f"Error fetching loans: {e}")
            return []

    def get_current_holds(self) -> List[OverdriveHold]:
        """Get user's current holds"""
        try:
            holds_data = self._make_request(self.config['endpoints']['holds'])
            current_holds = []

            for hold in holds_data.get('holds', []):
                book = self._get_or_create_book(hold['id'], hold)
                hold_record = OverdriveHold(
                    overdrive_book_id=book.id,
                    position=hold.get('position'),
                    total_holds=hold.get('total_holds'),
                    placed_at=datetime.fromisoformat(hold['placed']),
                    is_ready=hold.get('ready_to_borrow', False),
                    estimated_wait_days=hold.get('estimated_wait_days')
                )
                current_holds.append(hold_record)

            return current_holds
        except Exception as e:
            print(f"Error fetching holds: {e}")
            return []

    def _get_or_create_book(self, overdrive_id: str, metadata: Dict) -> OverdriveBook:
        """Get existing book record or create new one"""
        book = self.session.query(OverdriveBook).filter_by(
            overdrive_id=overdrive_id
        ).first()

        if not book:
            book = OverdriveBook(
                overdrive_id=overdrive_id,
                title=metadata.get('title'),
                author=metadata.get('creator'),
                media_type=metadata.get('type', {}).get('name'),
                cover_url=self.get_book_cover(overdrive_id),
                isbn=metadata.get('formats', [{}])[0].get('isbn')
            )
            self.session.add(book)
            self.session.commit()

        return book

    def check_availability(self, overdrive_id: str) -> Dict:
        """Check if a book is available"""
        try:
            return self._make_request(
                f"{self.config['endpoints']['availability']}/{overdrive_id}"
            )
        except Exception as e:
            print(f"Error checking availability for {overdrive_id}: {e}")
            return {}