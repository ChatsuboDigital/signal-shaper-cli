"""
Abstract base class for data loaders
"""

from abc import ABC, abstractmethod
from typing import List, Tuple


class DataLoader(ABC):
    """
    Abstract base class for loading data from various sources.

    All loaders must implement the load() method which returns:
    - records: List of dictionaries (raw data)
    - headers: List of column names
    """

    @abstractmethod
    def load(self) -> Tuple[List[dict], List[str]]:
        """
        Load data from source.

        Returns:
            Tuple of (records, headers)
            - records: List[dict] - Raw data records
            - headers: List[str] - Column names/fields
        """
        pass
