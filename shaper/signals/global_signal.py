"""
Global signal processing with precedence logic

Handles:
- Signal precedence: row signal > global signal > empty
- Signal prefix application
- Signal text formatting
"""

from typing import Optional


def apply_signal(
    row_signal: Optional[str],
    global_signal: Optional[str],
    signal_prefix: Optional[str] = None
) -> str:
    """
    Apply signal with precedence logic and optional prefix.

    Precedence order (GLOBAL OVERRIDES EVERYTHING):
    1. Global signal (CLI flag) - if set, applies to ALL rows
    2. Row signal (from dataset) - used only if no global signal
    3. Empty string

    Args:
        row_signal: Signal from the data row (e.g., "VP of Sales")
        global_signal: Global signal to apply to ALL rows (overrides row signals)
        signal_prefix: Optional prefix to prepend (e.g., "Supply: ")

    Returns:
        Final signal string with prefix applied if provided

    Examples:
        >>> apply_signal("VP of Sales", "needs deal flow", "Supply: ")
        "Supply: needs deal flow"  # Global overrides row signal!

        >>> apply_signal("VP of Sales", None, "Supply: ")
        "Supply: VP of Sales"  # No global, uses row signal

        >>> apply_signal("", "needs deal flow", None)
        "needs deal flow"
    """
    # Step 1: Choose signal based on precedence (GLOBAL FIRST!)
    signal = ""
    if global_signal and global_signal.strip():
        # Global signal overrides everything when provided
        signal = global_signal.strip()
    elif row_signal and row_signal.strip():
        # Use row signal only if no global signal
        signal = row_signal.strip()

    # Step 2: Apply prefix if provided
    if signal_prefix and signal:
        # Smart spacing: add space after prefix if it ends with punctuation
        if signal_prefix.endswith((':', '!', '-')):
            signal = f"{signal_prefix} {signal}"
        else:
            signal = f"{signal_prefix}{signal}"

    return signal


class SignalProcessor:
    """
    Process signals for a batch of records.

    Example:
        processor = SignalProcessor(
            global_signal="Hiring 3 engineers",
            signal_prefix="Demand: "
        )

        for record in records:
            record['signal'] = processor.process(record.get('signal'))
    """

    def __init__(
        self,
        global_signal: Optional[str] = None,
        signal_prefix: Optional[str] = None
    ):
        """
        Initialize signal processor.

        Args:
            global_signal: Signal to apply to ALL rows (overrides individual row signals)
            signal_prefix: Prefix to prepend to all signals
        """
        self.global_signal = global_signal
        self.signal_prefix = signal_prefix

    def process(self, row_signal: Optional[str]) -> str:
        """
        Process a single row's signal.

        Args:
            row_signal: Signal from the row

        Returns:
            Processed signal with prefix applied
        """
        return apply_signal(row_signal, self.global_signal, self.signal_prefix)

    def process_batch(self, records: list, signal_field: str = 'signal') -> list:
        """
        Process signals for multiple records.

        Args:
            records: List of record dicts
            signal_field: Name of the signal field in records

        Returns:
            Records with processed signals (modifies in place)
        """
        for record in records:
            row_signal = record.get(signal_field)
            record[signal_field] = self.process(row_signal)

        return records

    def get_stats(self, records: list, signal_field: str = 'signal') -> dict:
        """
        Get statistics about signal sources.

        Args:
            records: List of processed records
            signal_field: Name of the signal field

        Returns:
            Dict with counts of row signals vs global signals
        """
        total = len(records)
        empty = sum(1 for r in records if not r.get(signal_field))
        has_signal = total - empty

        return {
            'total': total,
            'with_signal': has_signal,
            'empty': empty,
            'fill_rate': (has_signal / total * 100) if total > 0 else 0
        }
