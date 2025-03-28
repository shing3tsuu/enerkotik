from pydantic import BaseModel, Extra, Field, validator
from typing import Dict, Optional, Any
from datetime import date


class ConnectionParamsSchema(BaseModel):
    headers: Dict[str, str] = Field(default_factory=dict)
    cookies: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)

    @validator('headers', 'cookies', 'params', pre=True)
    def convert_to_dict(cls, v):
        return v.dict() if isinstance(v, BaseModel) else v


class ScraperConfigSchema(BaseModel):
    main_class: str
    main_link: str
    name_class: str
    name_link: str
    cost_class: str
    cost_link: str


class ShopScraperSchema(BaseModel):
    shop_name: str
    link: str
    connection_params: ConnectionParamsSchema
    scraper_config: ScraperConfigSchema
    website_method: str
    debug_info: Dict[str, Any] = Field(
        default_factory=lambda: {
            "errors": [],
            "status_code": None,
            "element_count": 0
        }
    )
    utc_date: date = Field(default_factory=date.today)

    @validator('debug_info', pre=True, always=True)
    def init_errors(cls, v):
        if 'errors' not in v:
            v['errors'] = []
        return v