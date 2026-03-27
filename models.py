from sqlmodel import SQLModel, Field, create_engine
from typing import Optional
from datetime import datetime


class Inventory(SQLModel, table=True):
    inventory_id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True)
    product_name: str
    sport: str = Field(index=True)
    category: str = Field(index=True)
    brand: Optional[str] = None
    warehouse_zone: str
    aisle: str
    shelf: str
    bin: str
    quantity_on_hand: int = Field(default=0, ge=0)
    quantity_reserved: int = Field(default=0, ge=0)
    unit_cost: float = Field(ge=0)
    unit_price: float = Field(ge=0)
    reorder_level: int = Field(default=0, ge=0)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


engine = create_engine("sqlite:///warehouse_inventory.db")