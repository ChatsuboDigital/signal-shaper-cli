"""
Apify dataset loader

Fetches data from Apify datasets via API.
Supports both public datasets (no auth) and private datasets (requires token).
"""

import requests
from typing import List, Tuple, Optional
from .base import DataLoader


class ApifyLoader(DataLoader):
    """
    Load data from Apify datasets.

    Example:
        loader = ApifyLoader(dataset_id="your_dataset_id")
        records, headers = loader.load()
    """

    def __init__(self, dataset_id: str, api_token: Optional[str] = None):
        """
        Initialize Apify loader.

        Args:
            dataset_id: Apify dataset ID
            api_token: Optional API token for private datasets
        """
        self.dataset_id = dataset_id
        self.api_token = api_token
        self.base_url = "https://api.apify.com/v2"

    def load(self) -> Tuple[List[dict], List[str]]:
        """
        Fetch dataset from Apify API.

        Returns:
            Tuple of (records, headers)

        Raises:
            requests.HTTPError: If API request fails
            ValueError: If dataset is empty or invalid
        """
        # Build URL
        url = f"{self.base_url}/datasets/{self.dataset_id}/items"

        # Set query parameters
        params = {
            "format": "json",
            "clean": "true",  # Remove empty fields
        }

        # Add auth header if token provided
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        # Make request
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse response
        records = response.json()

        if not records:
            raise ValueError(f"Apify dataset {self.dataset_id} is empty")

        if not isinstance(records, list):
            raise ValueError(f"Invalid Apify response format (expected list, got {type(records).__name__})")

        # Extract headers from first record
        headers_list = list(records[0].keys()) if records else []

        return records, headers_list

    def get_dataset_info(self) -> dict:
        """
        Get metadata about the dataset.

        Returns:
            dict with dataset metadata (itemCount, created, modified, etc.)
        """
        url = f"{self.base_url}/datasets/{self.dataset_id}"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json()
