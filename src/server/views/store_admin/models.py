from pydantic import BaseModel
from typing import List, Optional


class Empty(BaseModel): ...


class SealResponse(BaseModel):
    success: bool
    message: str


class UnsealRequest(BaseModel):
    shares: List[str]


class UnsealResponse(BaseModel):
    success: bool
    message: str


class IsSealResponse(BaseModel):
    is_sealed: bool


class InitStorageRequest(BaseModel):
    shares: int
    threshold: int


class InitStorageResponse(BaseModel):
    success: bool
    message: str
    shares: List[str] = []


class ServiceStatusResponse(BaseModel):
    is_healthy: bool
    is_initialized: bool
    is_sealed: Optional[bool] = None
