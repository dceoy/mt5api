"""API routes for pdmt5 REST API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from pdmt5_api.rest.schemas import ConnectionRequest, OperationResult, OrderRequest
from pdmt5_api.rest.service import Pdmt5Service, get_service

router = APIRouter()


@router.get("/health")
def health() -> OperationResult:
    return OperationResult(success=True, detail={"status": "ok"})


@router.post("/connect")
def connect(
    payload: ConnectionRequest, service: Pdmt5Service = Depends(get_service)
) -> OperationResult:
    data = payload.model_dump(exclude_none=True)
    config = data.pop("config", None)
    if config:
        data.update(config)
    try:
        result = service.initialize(data)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))


@router.post("/shutdown")
def shutdown(service: Pdmt5Service = Depends(get_service)) -> OperationResult:
    try:
        result = service.shutdown()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))


@router.get("/account")
def account(service: Pdmt5Service = Depends(get_service)) -> OperationResult:
    try:
        result = service.account_info()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))


@router.get("/symbols")
def symbols(service: Pdmt5Service = Depends(get_service)) -> OperationResult:
    try:
        result = service.symbols()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))


@router.get("/symbols/{symbol}")
def symbol_info(
    symbol: str, service: Pdmt5Service = Depends(get_service)
) -> OperationResult:
    try:
        result = service.symbol_info(symbol)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))


@router.get("/positions")
def positions(service: Pdmt5Service = Depends(get_service)) -> OperationResult:
    try:
        result = service.positions()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))


@router.get("/orders")
def orders(service: Pdmt5Service = Depends(get_service)) -> OperationResult:
    try:
        result = service.orders()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))


@router.post("/orders")
def order_send(
    payload: OrderRequest, service: Pdmt5Service = Depends(get_service)
) -> OperationResult:
    try:
        result = service.order_send(payload.request)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationResult(success=True, detail=jsonable_encoder(result))
