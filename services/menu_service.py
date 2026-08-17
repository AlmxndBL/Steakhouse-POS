from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import Category, MenuItem, RecipeBOM

class MenuService:
    @staticmethod
    def get_categories(db: Session) -> List[Category]:
        return db.query(Category).order_by(Category.sort_order.asc(), Category.id.asc()).all()

    @staticmethod
    def create_category(db: Session, name: str, sort_order: int = 0) -> Category:
        category = Category(name=name, sort_order=sort_order)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_menu_items(db: Session, category_id: Optional[int] = None, active_only: bool = True) -> List[MenuItem]:
        query = db.query(MenuItem)
        if active_only:
            query = query.filter(MenuItem.is_active == True)
        if category_id:
            query = query.filter(MenuItem.category_id == category_id)
        return query.order_by(MenuItem.id.asc()).all()

    @staticmethod
    def get_menu_item_by_id(db: Session, item_id: int) -> Optional[MenuItem]:
        return db.query(MenuItem).filter(MenuItem.id == item_id).first()

    @staticmethod
    def get_item_bom_cost(db: Session, item_id: int) -> float:
        """
        Calculates the theoretical ingredient BOM cost for a specific menu item.
        """
        recipes = db.query(RecipeBOM).filter(RecipeBOM.menu_item_id == item_id).all()
        total_cost = 0.0
        for r in recipes:
            if r.ingredient and r.ingredient.cost_per_unit:
                total_cost += float(r.quantity_required) * float(r.ingredient.cost_per_unit)
        return total_cost

    @staticmethod
    def create_menu_item(
        db: Session,
        category_id: int,
        code: str,
        name: str,
        price: float,
        description: Optional[str] = None
    ) -> MenuItem:
        clean_code = code.strip().upper()
        existing = db.query(MenuItem).filter(MenuItem.code == clean_code).first()
        if existing:
            raise ValueError(f"รหัสเมนู '{clean_code}' มีอยู่ในระบบแล้ว กรุณาใช้รหัสอื่น")

        item = MenuItem(
            category_id=category_id,
            code=clean_code,
            name=name.strip(),
            price=price,
            description=description.strip() if description else None,
            is_active=True
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_menu_item(
        db: Session,
        item_id: int,
        name: str,
        price: float,
        category_id: int,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Optional[MenuItem]:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            return None
        item.name = name.strip()
        item.price = price
        item.category_id = category_id
        item.description = description.strip() if description else None
        item.is_active = is_active
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def toggle_menu_item_status(db: Session, item_id: int) -> Optional[MenuItem]:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            return None
        item.is_active = not item.is_active
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_menu_item(db: Session, item_id: int, soft: bool = True) -> bool:
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            return False
        if soft:
            item.is_active = False
            db.commit()
        else:
            db.delete(item)
            db.commit()
        return True
