from pydantic import BaseModel
from datetime import date

class PaymentRequest(BaseModel):
    tenant_id: int
    amount: float

class TenantRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    rent_outstanding: float = 0.0
    electricity_outstanding: float = 0.0
    water_outstanding: float = 0.0

class BillRequest(BaseModel):
    tenant_id: int
    utility_type: str
    amount: float
    manual_entry: bool = False
    peak_units: float = 0.0
    offpeak_units: float = 0.0

class TokenRequest(BaseModel):
    tenant_id: int
    utility_type: str
    amount: float

class MeterRequest(BaseModel):
    tenant_id: int
    meter_type: str
    billing_type: str
    serial_number: str
    tariff_id: int = None

class MeterUpdateRequest(BaseModel):
    meter_type: str
    billing_type: str
    serial_number: str
    tariff_id: int = None

class TenantUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    status: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TenantLoginRequest(BaseModel):
    tenant_id: int
    email: str

class AdjustmentRequest(BaseModel):
    target: str
    amount: float
    reason: str

class TariffRequest(BaseModel):
    name: str
    meter_type: str
    structure_type: str
    rate_flat: float = 0.0
    tier_1_limit: int = 0
    tier_1_rate: float = 0.0
    tier_2_rate: float = 0.0
    tou_peak_rate: float = 0.0
    tou_offpeak_rate: float = 0.0

class ExitFormRequest(BaseModel):
    exit_date: date
    exit_reason: str

class InspectionResultRequest(BaseModel):
    status: str
    notes: str

class ReconRequest(BaseModel):
    utility_type: str
    reading_month: str
    municipal_units: float
    submeter_units: float

# NEW: Invoice Schema
class InvoiceGenerateRequest(BaseModel):
    tenant_id: int
    billing_period: str
    cycle_type: str # MONTHLY, BI_MONTHLY, QUARTERLY