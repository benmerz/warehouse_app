import os

from fastapi.staticfiles import StaticFiles
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlmodel import Session, select
from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime
import bcrypt
from starlette.middleware.sessions import SessionMiddleware
from models import Inventory, User, engine

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", "dev-session-secret-change-me"),
)


class UserCreate(SQLModel):
    username: str
    password: str


class UserLogin(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    username: str


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


def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_current_username(request: Request) -> str:
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return username


@app.post("/users/register", response_model=UserRead)
async def register_user(user: UserCreate):
    with Session(engine) as session:
        existing_user = session.get(User, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        new_user = User(
            username=user.username,
            password_hash=hash_password(user.password),
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return UserRead(username=new_user.username)


@app.post("/users/login", response_model=UserRead)
async def login_user(user: UserLogin, request: Request):
    with Session(engine) as session:
        existing_user = session.get(User, user.username)
        if not existing_user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not verify_password(user.password, existing_user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        request.session["username"] = existing_user.username
        return UserRead(username=existing_user.username)


@app.get("/inventory")
async def get_inventory(current_username: str = Depends(get_current_username)):
    with Session(engine) as session:
        statement = select(Inventory)
        items = session.exec(statement).all()
        return items

@app.post("/inventory/add_record")
async def add_inventory_record(record: Inventory, current_username: str = Depends(get_current_username)):
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


@app.patch("/inventory/{inventory_id}")
async def edit_inventory_record(
    inventory_id: int,
    updates: InventoryUpdate,
    current_username: str = Depends(get_current_username),
):
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
async def delete_inventory_record(
    inventory_id: int,
    current_username: str = Depends(get_current_username),
):
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
