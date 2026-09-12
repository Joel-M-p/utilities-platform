from pydantic import BaseModel
from typing import Optional

class TenantRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    cellphone: Optional[str] = None
    rent_outstanding: float = 0
    electricity_outstanding: float = 0
    water_outstanding: float = 0
    unit_number: Optional[str] = None
    property_id: int

class TenantUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    cellphone: Optional[str] = None
    status: str

class ExitFormRequest(BaseModel):
    exit_date: str
    exit_reason: str

class InspectionResultRequest(BaseModel):
    status: str
    notes: str

class BillRequest(BaseModel):
    tenant_id: int
    utility_type: str
    amount: float
    peak_units: float = 0
    offpeak_units: float = 0
    manual_entry: bool = False

class MeterRequest(BaseModel):
    tenant_id: int
    serial_number: str
    meter_type: str
    billing_type: str
    tariff_id: int

class MeterUpdateRequest(BaseModel):
    meter_type: str
    billing_type: str
    serial_number: str
    tariff_id: int

class InvoiceGenerateRequest(BaseModel):
    tenant_id: int
    billing_period: str
    cycle_type: str

class ReconRequest(BaseModel):
    month: str
    utility_type: str
    municipal_units: float
    submeter_units: float

class CreditNoteRequest(BaseModel):
    tenant_id: int
    amount: float
    reason: str

class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str
    property_id: Optional[int] = None

class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = None
    logo_path: Optional[str] = None
    address: Optional[str] = None
    vat_number: Optional[str] = None
    vat_percent: Optional[float] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None