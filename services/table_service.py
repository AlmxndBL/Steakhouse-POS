from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Table, TableStatus
from utils.validators import Validator

class TableService:
    @staticmethod
    def get_tables(db: Session, zone: Optional[str] = None) -> List[Table]:
        query = db.query(Table)
        if zone:
            query = query.filter(Table.zone == zone)
        return query.order_by(Table.table_number.asc()).all()

    @staticmethod
    def get_table_by_id(db: Session, table_id: int) -> Optional[Table]:
        return db.query(Table).filter(Table.id == table_id).first()

    @staticmethod
    def get_zones(db: Session) -> List[str]:
        results = db.query(Table.zone).distinct().all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def create_table(
        db: Session,
        table_number: str,
        capacity: int = 4,
        zone: str = "Indoor"
    ) -> Table:
        t_res = Validator.validate_table_number(table_number)
        if not t_res.is_valid:
            raise ValueError(t_res.error)
        clean_tbl = t_res.value

        c_res = Validator.validate_integer(capacity, field_name="จำนวนที่นั่ง", min_val=1, max_val=50)
        if not c_res.is_valid:
            raise ValueError(c_res.error)

        z_res = Validator.validate_required_text(zone, field_name="โซนที่นั่ง", min_len=1, max_len=50)
        if not z_res.is_valid:
            raise ValueError(z_res.error)

        existing = db.query(Table).filter(Table.table_number == clean_tbl).first()
        if existing:
            raise ValueError(f"โต๊ะหมายเลข {clean_tbl} มีอยู่ในระบบแล้ว")
        
        table = Table(
            table_number=clean_tbl,
            capacity=c_res.value,
            zone=z_res.value,
            status=TableStatus.VACANT
        )
        db.add(table)
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def update_table(
        db: Session,
        table_id: int,
        table_number: str,
        capacity: int,
        zone: str
    ) -> Optional[Table]:
        t_res = Validator.validate_table_number(table_number)
        if not t_res.is_valid:
            raise ValueError(t_res.error)
        clean_tbl = t_res.value

        c_res = Validator.validate_integer(capacity, field_name="จำนวนที่นั่ง", min_val=1, max_val=50)
        if not c_res.is_valid:
            raise ValueError(c_res.error)

        z_res = Validator.validate_required_text(zone, field_name="โซนที่นั่ง", min_len=1, max_len=50)
        if not z_res.is_valid:
            raise ValueError(z_res.error)

        table = db.query(Table).filter(Table.id == table_id).first()
        if not table:
            return None

        # Check unique if changed
        if table.table_number != clean_tbl:
            existing = db.query(Table).filter(Table.table_number == clean_tbl).first()
            if existing:
                raise ValueError(f"โต๊ะหมายเลข {clean_tbl} มีอยู่ในระบบแล้ว")

        table.table_number = clean_tbl
        table.capacity = c_res.value
        table.zone = z_res.value
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def delete_table(db: Session, table_id: int) -> bool:
        table = db.query(Table).filter(Table.id == table_id).first()
        if not table:
            return False
        # Do not delete if currently occupied
        if table.status == TableStatus.OCCUPIED:
            raise ValueError("ไม่สามารถลบโต๊ะที่มีลูกค้าใช้งานอยู่ได้")
        db.delete(table)
        db.commit()
        return True
