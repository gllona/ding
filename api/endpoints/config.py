"""Configuration management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
from pydantic import BaseModel

from core.database import get_db
from core.models import AppConfig
from api.auth import verify_api_key


router = APIRouter(prefix="/api/config", tags=["config"])


# Pydantic schemas
class ConfigUpdate(BaseModel):
    value: str


class ConfigResponse(BaseModel):
    key: str
    value: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=Dict[str, str])
def get_all_config(
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get all configuration parameters."""
    configs = db.query(AppConfig).all()
    return {config.key: config.value for config in configs}


@router.get("/{key}", response_model=ConfigResponse)
def get_config(
    key: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Get specific configuration value by key."""
    config = db.query(AppConfig).filter(AppConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key '{key}' not found"
        )

    return ConfigResponse(
        key=config.key,
        value=config.value,
        updated_at=config.updated_at.isoformat()
    )


@router.put("/{key}", response_model=ConfigResponse)
def update_config(
    key: str,
    config_update: ConfigUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
):
    """Update configuration value."""
    config = db.query(AppConfig).filter(AppConfig.key == key).first()
    if not config:
        # Create new config if doesn't exist
        config = AppConfig(key=key, value=config_update.value)
        db.add(config)
    else:
        config.value = config_update.value

    db.commit()
    db.refresh(config)

    return ConfigResponse(
        key=config.key,
        value=config.value,
        updated_at=config.updated_at.isoformat()
    )
