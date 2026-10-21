"""
Confidence / reliability classification for sensing detections.

Raw numbers (model confidence 0..1, signal quality 0..100) are stored on events and alerts.
The labels below are derived at read time so the thresholds can be tuned without migrating data.
A detection is only treated as confirmable when BOTH confidence and signal quality are known and good;
anything else is marked "Verification Required" and needs a staff decision.
"""
from typing import Optional

CONFIDENCE_HIGH_MIN = 0.85
CONFIDENCE_MEDIUM_MIN = 0.65
SIGNAL_GOOD_MIN = 75
SIGNAL_FAIR_MIN = 50


def confidence_level(confidence: Optional[float]) -> str:
    if confidence is None:
        return "UNKNOWN"
    if confidence >= CONFIDENCE_HIGH_MIN:
        return "HIGH"
    if confidence >= CONFIDENCE_MEDIUM_MIN:
        return "MEDIUM"
    return "LOW"


def signal_level(signal_quality: Optional[int]) -> str:
    if signal_quality is None:
        return "UNKNOWN"
    if signal_quality >= SIGNAL_GOOD_MIN:
        return "GOOD"
    if signal_quality >= SIGNAL_FAIR_MIN:
        return "FAIR"
    return "POOR"


def requires_verification(confidence: Optional[float], signal_quality: Optional[int]) -> bool:
    return confidence_level(confidence) in ("LOW", "UNKNOWN") or signal_level(signal_quality) in ("POOR", "UNKNOWN")
