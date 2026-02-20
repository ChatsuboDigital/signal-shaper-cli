"""
CSV loader with auto-delimiter detection

Loads CSV files with automatic detection of:
- Delimiter (comma, tab, pipe, semicolon)
- Encoding (UTF-8, latin1, etc.)
- Header row
"""

import csv
from typing import List, Tuple, Optional
from pathlib import Path
from .base import DataLoader


class CSVLoader(DataLoader):
    """
    Load data from CSV files with auto-detection.

    Example:
        loader = CSVLoader("data.csv")
        records, headers = loader.load()
    """

    def __init__(self, file_path: str):
        """
        Initialize CSV loader.

        Args:
            file_path: Path to CSV file
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

    def load(self) -> Tuple[List[dict], List[str]]:
        """
        Load CSV file with auto-delimiter detection.

        Returns:
            Tuple of (records, headers)

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If CSV is invalid or empty
        """
        # Detect delimiter
        delimiter = self._detect_delimiter()

        # Detect encoding
        encoding = self._detect_encoding()

        # Load CSV
        records = []
        headers = []

        with open(self.file_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames or []

            if not headers:
                raise ValueError(f"CSV file has no headers: {self.file_path}")

            for row in reader:
                records.append(row)

        if not records:
            raise ValueError(f"CSV file is empty: {self.file_path}")

        return records, headers

    def _detect_delimiter(self) -> str:
        """
        Auto-detect CSV delimiter.

        Tries common delimiters: comma, tab, pipe, semicolon

        Returns:
            Detected delimiter character
        """
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first few lines
            sample = ''.join([f.readline() for _ in range(5)])

        # Use csv.Sniffer
        try:
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            return delimiter
        except Exception:
            # Fallback: count occurrences of common delimiters
            delimiters = [',', '\t', '|', ';']
            counts = {d: sample.count(d) for d in delimiters}

            # Return delimiter with highest count
            detected = max(counts.items(), key=lambda x: x[1])[0]
            return detected

    def _detect_encoding(self) -> str:
        """
        Auto-detect file encoding.

        Returns:
            Encoding name (utf-8, latin1, etc.)
        """
        # Try common encodings
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # Try reading first 1KB
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Fallback to utf-8 with error handling
        return 'utf-8'

    def get_preview(self, limit: int = 5) -> List[dict]:
        """
        Get a preview of the CSV data.

        Args:
            limit: Number of rows to preview

        Returns:
            Limited list of records
        """
        records, _ = self.load()
        return records[:limit]

    def get_info(self) -> dict:
        """
        Get metadata about the CSV file.

        Returns:
            Dict with file info (row_count, column_count, delimiter, etc.)
        """
        records, headers = self.load()

        return {
            'file_path': str(self.file_path),
            'file_size': self.file_path.stat().st_size,
            'row_count': len(records),
            'column_count': len(headers),
            'delimiter': self._detect_delimiter(),
            'encoding': self._detect_encoding(),
            'headers': headers
        }
