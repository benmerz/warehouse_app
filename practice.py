from sqlmodel import Session, select
from models import Inventory, engine

with Session(engine) as session:
    statement = select(Inventory).where(Inventory.inventory_id == 18)
    football_helmet = session.exec(statement).one()
    
    print(football_helmet)

    football_helmet.quantity_on_hand += 50

    session.add(football_helmet)
    session.commit()
    session.refresh(football_helmet)

    print(football_helmet)