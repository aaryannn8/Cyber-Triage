import os
from dataclasses import dataclass

@dataclass
class Config:
    APP_NAME: str = "CIPHER-FUSION"
    LEGAL_DISCLAIMER: str = (
        "Forensic-ready investigative summary; final investigative and legal decisions remain with authorized personnel."
    )
    FULL_DISCLAIMER: str = (
        "Forensic-ready investigative summary generated from supplied artifacts. "
        "Findings require review and verification by authorized personnel. "
        "This report does not independently establish identity, intent, guilt, or legal admissibility."
    )
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "cipher_fusion.db"))
    UPLOADS_DIR: str = os.environ.get("UPLOADS_DIR", os.path.join(BASE_DIR, "data", "uploads"))
    DEMO_DATA_DIR: str = os.environ.get("DEMO_DATA_DIR", os.path.join(BASE_DIR, "data", "demo"))
    REPORTS_DIR: str = os.environ.get("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))

    # Configurable Thresholds
    RAPID_FORWARDING_MINUTES: int = 15
    REPEATED_ENTITY_CASE_THRESHOLD: int = 3
    HIGH_VALUE_TRANSACTION_THRESHOLD: float = 25000.0
    HIGH_VELOCITY_HOPS_THRESHOLD: int = 2
    HIGH_VELOCITY_WINDOW_MINUTES: int = 30
    DEFAULT_TIME_WINDOW_HOURS: int = 24

config = Config()
