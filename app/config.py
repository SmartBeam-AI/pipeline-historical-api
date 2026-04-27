"""Configuration and constants for the pump lifecycle API."""

import os
from dotenv import load_dotenv

load_dotenv()

HYPERTABLE = os.getenv("HYPERTABLE_NAME", "pump_lifecycle_metrics")
SCHEMA = os.getenv("HYPERTABLE_SCHEMA", "public")

FQN = f'"{SCHEMA}"."{HYPERTABLE}"'

METRIC_COLUMNS = {
    "rpm", "suction_pressure", "discharge_pressure", "flow_rate",
    "pump_velocity_x", "pump_velocity_y", "pump_velocity_z",
    "pump_acceleration_x", "pump_acceleration_y", "pump_acceleration_z",
    "pump_acoustic_db", "pump_temperature",
    "motor_velocity_x", "motor_velocity_y", "motor_velocity_z",
    "motor_acceleration_x", "motor_acceleration_y", "motor_acceleration_z",
    "motor_acoustic_db", "motor_temperature",
    "power_voltage_r", "power_voltage_y", "power_voltage_b",
    "power_current_r", "power_current_y", "power_current_b",
    "fluid_temperature",
}

ALLOWED_AGGS = {"avg", "sum", "min", "max", "count", "stddev"}
FILTER_COLUMNS = {"pump_id", "testbed", "owner", "gateway_id", "pump_type", "label"}
