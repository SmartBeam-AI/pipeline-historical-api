"""Request/response schemas for pump lifecycle testbed API."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class PumpTestRecord(BaseModel):
    time: datetime
    owner: Optional[str] = None
    gateway_id: Optional[str] = None
    pump_id: Optional[str] = None
    testbed: Optional[int] = None
    rpm: Optional[float] = None
    suction_pressure: Optional[float] = None
    discharge_pressure: Optional[float] = None
    pump_velocity_x: Optional[float] = None
    pump_velocity_y: Optional[float] = None
    pump_velocity_z: Optional[float] = None
    pump_acceleration_x: Optional[float] = None
    pump_acceleration_y: Optional[float] = None
    pump_acceleration_z: Optional[float] = None
    pump_acoustic_db: Optional[float] = None
    pump_temperature: Optional[float] = None
    motor_velocity_x: Optional[float] = None
    motor_velocity_y: Optional[float] = None
    motor_velocity_z: Optional[float] = None
    motor_acceleration_x: Optional[float] = None
    motor_acceleration_y: Optional[float] = None
    motor_acceleration_z: Optional[float] = None
    motor_acoustic_db: Optional[float] = None
    motor_temperature: Optional[float] = None
    power_voltage_r: Optional[float] = None
    power_voltage_y: Optional[float] = None
    power_voltage_b: Optional[float] = None
    power_current_r: Optional[float] = None
    power_current_y: Optional[float] = None
    power_current_b: Optional[float] = None
    pump_type: Optional[str] = None
    label: Optional[str] = None
    flow_rate: Optional[float] = None
    fluid_temperature: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    timestamp: datetime


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    query_time_ms: float


class PumpListItem(BaseModel):
    pump_id: str
    pump_type: Optional[str] = None
    testbed: Optional[int] = None
    owner: Optional[str] = None
    last_seen: Optional[datetime] = None
    record_count: int


class TestbedListItem(BaseModel):
    testbed: int
    pump_count: int
    last_activity: Optional[datetime] = None


class AggregationPoint(BaseModel):
    bucket: datetime
    value: Optional[float] = None


class TimeSeriesResponse(BaseModel):
    pump_id: str
    metric: str
    bucket_interval: str
    data: list[AggregationPoint]
    point_count: int
    query_time_ms: float


class PumpSummary(BaseModel):
    pump_id: str
    testbed: Optional[int] = None
    pump_type: Optional[str] = None
    last_reading: Optional[datetime] = None
    rpm: Optional[float] = None
    suction_pressure: Optional[float] = None
    discharge_pressure: Optional[float] = None
    flow_rate: Optional[float] = None
    pump_temperature: Optional[float] = None
    motor_temperature: Optional[float] = None
    fluid_temperature: Optional[float] = None
    pump_acoustic_db: Optional[float] = None
    motor_acoustic_db: Optional[float] = None
    power_voltage_r: Optional[float] = None
    power_voltage_y: Optional[float] = None
    power_voltage_b: Optional[float] = None
    power_current_r: Optional[float] = None
    power_current_y: Optional[float] = None
    power_current_b: Optional[float] = None


class VibrationSnapshot(BaseModel):
    time: datetime
    pump_velocity_x: Optional[float] = None
    pump_velocity_y: Optional[float] = None
    pump_velocity_z: Optional[float] = None
    pump_acceleration_x: Optional[float] = None
    pump_acceleration_y: Optional[float] = None
    pump_acceleration_z: Optional[float] = None
    motor_velocity_x: Optional[float] = None
    motor_velocity_y: Optional[float] = None
    motor_velocity_z: Optional[float] = None
    motor_acceleration_x: Optional[float] = None
    motor_acceleration_y: Optional[float] = None
    motor_acceleration_z: Optional[float] = None


class PowerSnapshot(BaseModel):
    time: datetime
    power_voltage_r: Optional[float] = None
    power_voltage_y: Optional[float] = None
    power_voltage_b: Optional[float] = None
    power_current_r: Optional[float] = None
    power_current_y: Optional[float] = None
    power_current_b: Optional[float] = None
