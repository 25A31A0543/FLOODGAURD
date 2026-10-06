import json
from datetime import datetime
from typing import List, Optional, Dict
from floodguard.schemas.sources import UnifiedTelemetryFrame
from floodguard.schemas.common import IngestionReceipt
from floodguard.config import settings


class IngestionStorageBuffer:
    """
    In-memory and file-backed staging storage buffer for FloodGuard Step 1.
    Maintains time-series circular memory buffer of recent telemetry frames and receipts.
    """

    def __init__(self, max_frames: int = 50, max_receipts: int = 100):
        self.max_frames = max_frames
        self.max_receipts = max_receipts
        self._frames: List[UnifiedTelemetryFrame] = []
        self._receipts: List[IngestionReceipt] = []

    def save_receipt(self, receipt: IngestionReceipt):
        """Append an ingestion transaction receipt."""
        self._receipts.insert(0, receipt)
        if len(self._receipts) > self.max_receipts:
            self._receipts.pop()

    def get_receipts(self, limit: int = 20) -> List[IngestionReceipt]:
        """Retrieve recent ingestion receipts."""
        return self._receipts[:limit]

    def save_frame(self, frame: UnifiedTelemetryFrame):
        """Store a harmonized multimodal telemetry snapshot."""
        self._frames.insert(0, frame)
        if len(self._frames) > self.max_frames:
            self._frames.pop()

        # Persist frame to disk for replay/inspection
        filename = f"frame_{frame.frame_id}.json"
        target_path = settings.BUFFER_STORAGE_DIR / filename
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(frame.model_dump_json(indent=2))
        except Exception:
            pass

    def get_latest_frame(self) -> Optional[UnifiedTelemetryFrame]:
        """Get the most recent unified telemetry frame."""
        return self._frames[0] if self._frames else None

    def get_history(self, limit: int = 10) -> List[UnifiedTelemetryFrame]:
        """Get recent historical frames."""
        return self._frames[:limit]


# Global buffer instance
storage_buffer = IngestionStorageBuffer()
