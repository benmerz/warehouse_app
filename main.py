from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime
from models import Inventory, engine

app = FastAPI()


class InventoryUpdate(SQLModel):
    sku: Optional[str] = None
    product_name: Optional[str] = None
    sport: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    warehouse_zone: Optional[str] = None
    aisle: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None
    quantity_on_hand: Optional[int] = None
    quantity_reserved: Optional[int] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    reorder_level: Optional[int] = None


@app.get("/inventory")
async def get_inventory():
    with Session(engine) as session:
        statement = select(Inventory)
        items = session.exec(statement).all()
        return items

@app.post("/inventory/add_record")
async def add_inventory_record(record: Inventory):
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


@app.patch("/inventory/{inventory_id}")
async def edit_inventory_record(inventory_id: int, updates: InventoryUpdate):
    with Session(engine) as session:
        record = session.get(Inventory, inventory_id)
        if not record:
            raise HTTPException(status_code=404, detail="Inventory record not found")

        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        for field_name, value in update_data.items():
            setattr(record, field_name, value)

        record.last_updated = datetime.utcnow().isoformat()
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


@app.delete("/inventory/{inventory_id}")
async def delete_inventory_record(inventory_id: int):
    with Session(engine) as session:
        record = session.get(Inventory, inventory_id)
        if not record:
            raise HTTPException(status_code=404, detail="Inventory record not found")

        session.delete(record)
        session.commit()
        return {
            "message": "Inventory record deleted",
            "inventory_id": inventory_id
        }

app.mount("/", StaticFiles(directory="static", html=True), name="static")