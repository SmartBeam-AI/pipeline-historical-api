"""Configuration for the pump lifecycle API."""

import os
from dotenv import load_dotenv

load_dotenv()

HYPERTABLE = os.getenv("HYPERTABLE_NAME", "pump_lifecycle_metrics")
SCHEMA = os.getenv("HYPERTABLE_SCHEMA", "public")
FQN = f'"{SCHEMA}"."{HYPERTABLE}"'