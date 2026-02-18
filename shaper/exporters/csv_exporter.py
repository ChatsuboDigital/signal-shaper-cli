"""
CSV exporter

Exports normalized records to clean CSV format.
Automatically saves to output/ folder with timestamped filenames.
"""

import csv
from typing import List, Literal, Optional
from pathlib import Path
from datetime import datetime


class CSVExporter:
    """
    Export records to CSV format.

    Example:
        exporter = CSVExporter()
        exporter.export_standard(records, "output.csv")
    """

    # Standard 6-column format
    STANDARD_COLUMNS = [
        'Full Name',
        'Company Name',
        'Domain',
        'Email',
        'Context',
        'Signal'
    ]

    def export_standard(
        self,
        records: List[dict],
        output_path: str,
        include_header: bool = True
    ) -> int:
        """
        Export records in standard 6-column format.

        Columns: Full Name, Company Name, Domain, Email, Context, Signal

        Args:
            records: List of record dicts
            output_path: Path to output CSV file
            include_header: Whether to include header row

        Returns:
            Number of records exported
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.STANDARD_COLUMNS)

            if include_header:
                writer.writeheader()

            for record in records:
                row = self._map_to_standard(record)
                writer.writerow(row)

        return len(records)

    def _map_to_standard(self, record: dict) -> dict:
        """Map record to standard format columns."""
        return {
            'Full Name': record.get('full_name', ''),
            'Company Name': record.get('company', '') or record.get('company_name', ''),
            'Domain': record.get('domain', ''),
            'Email': record.get('email', ''),
            'Context': record.get('company_description', '') or record.get('context', ''),
            'Signal': record.get('signal', '')
        }

    @staticmethod
    def generate_filename(
        data_type: Literal['supply', 'demand'],
        base_dir: Optional[str] = None
    ) -> str:
        """
        Generate a timestamped filename for export.

        Format: {base_dir}/{supply|demand}_YYYY-MM-DD_HHMMSS.csv
        Example: output/supply_2024-02-15_143022.csv

        Args:
            data_type: 'supply' or 'demand'
            base_dir: Base directory for output (default: uses centralized config)

        Returns:
            Full path to output file
        """
        # Use centralized config if base_dir not provided
        if base_dir is None:
            from core.config import get_config
            config = get_config()
            output_dir = config.get_output_dir('shaper')
        else:
            output_dir = Path(base_dir)

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')

        # Build filename
        filename = f"{data_type}_{timestamp}.csv"
        return str(output_dir / filename)
