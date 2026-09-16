from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, Enum as SQLEnum, Numeric
)
from sqlalchemy.orm import relationship
import enum
from database.connection import Base

class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"
    WAITER = "WAITER"
    KITCHEN = "KITCHEN"

class TableStatus(str, enum.Enum):
    VACANT = "VACANT"
    OCCUPIED = "OCCUPIED"
    CLEANING = "CLEANING"

class OrderType(str, enum.Enum):
    DINE_IN = "DINE_IN"
    TAKEAWAY = "TAKEAWAY"

class OrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    COOKING = "COOKING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class OrderItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    COOKING = "COOKING"
    SERVED = "SERVED"
    CANCELLED = "CANCELLED"

class StockTxType(str, enum.Enum):
    PURCHASE_IN = "PURCHASE_IN"
    SALE_OUT = "SALE_OUT"
    WASTAGE = "WASTAGE"
    ADJUSTMENT = "ADJUSTMENT"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CASHIER)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="user")
    stock_txs = relationship("StockTransaction", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String(20), unique=True, nullable=False)
    capacity = Column(Integer, default=4)
    zone = Column(String(50), default="Indoor")
    status = Column(SQLEnum(TableStatus), default=TableStatus.VACANT)
    current_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    current_order = relationship("Order", foreign_keys=[current_order_id])

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)

    menu_items = relationship("MenuItem", back_populates="category")

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="menu_items")
    recipes = relationship("RecipeBOM", back_populates="menu_item", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="menu_item")

class ModifierGroup(Base):
    __tablename__ = "modifier_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    options = relationship("ModifierOption", back_populates="group", cascade="all, delete-orphan")

class ModifierOption(Base):
    __tablename__ = "modifier_options"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("modifier_groups.id"), nullable=False)
    name = Column(String(100), nullable=False)
    extra_price = Column(Numeric(10, 2), default=0.0)

    group = relationship("ModifierGroup", back_populates="options")

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    min_stock_alert = Column(Numeric(10, 2), default=100.0)
    cost_per_unit = Column(Numeric(10, 2), default=0.0)
    is_active = Column(Boolean, default=True)

    recipes = relationship("RecipeBOM", back_populates="ingredient")
    lots = relationship("StockLot", back_populates="ingredient")

class RecipeBOM(Base):
    __tablename__ = "recipes_bom"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity_required = Column(Numeric(10, 4), nullable=False)
    unit = Column(String(20), nullable=False)

    menu_item = relationship("MenuItem", back_populates="recipes")
    ingredient = relationship("Ingredient", back_populates="recipes")

class StockLot(Base):
    __tablename__ = "stock_lots"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    lot_number = Column(String(50), nullable=False)
    initial_quantity = Column(Numeric(10, 4), nullable=False)
    remaining_quantity = Column(Numeric(10, 4), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False, default=0.0)
    expiry_date = Column(Date, nullable=True)
    received_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_depleted = Column(Boolean, default=False)

    ingredient = relationship("Ingredient", back_populates="lots")
    transactions = relationship("StockTransaction", back_populates="lot")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True)
    order_type = Column(SQLEnum(OrderType), default=OrderType.DINE_IN)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.OPEN)
    customer_name = Column(String(100), nullable=True)
    subtotal = Column(Numeric(10, 2), default=0.0)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    service_charge_amount = Column(Numeric(10, 2), default=0.0)
    vat_amount = Column(Numeric(10, 2), default=0.0)
    net_amount = Column(Numeric(10, 2), default=0.0)
    payment_method = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)

    table = relationship("Table", foreign_keys=[table_id])
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    stock_txs = relationship("StockTransaction", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    options_json = Column(Text, nullable=True)
    item_status = Column(SQLEnum(OrderItemStatus), default=OrderItemStatus.PENDING)
    sent_to_kitchen_at = Column(DateTime, nullable=True)
    notes = Column(String(255), nullable=True)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")

class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("stock_lots.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    tx_type = Column(SQLEnum(StockTxType), nullable=False)
    quantity = Column(Numeric(10, 4), nullable=False)
    reason = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    lot = relationship("StockLot", back_populates="transactions")
    order = relationship("Order", back_populates="stock_txs")
    user = relationship("User", back_populates="stock_txs")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")
