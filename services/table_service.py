from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Table, TableStatus

class TableService:
    @staticmethod
    def get_tables(db: Session, zone: Optional[str] = None) -> List[Table]:
        query = db.query(Table)
        if zone:
            query = query.filter(Table.zone == zone)
        return query.order_by(Table.table_number.asc()).all()

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
        existing = db.query(Table).filter(Table.table_number == table_number).first()
        if existing:
            raise ValueError(f"โต๊ะหมายเลข {table_number} มีอยู่ในระบบแล้ว")
        
        table = Table(
            table_number=table_number,
            capacity=capacity,
            zone=zone,
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
        table = db.query(Table).filter(Table.id == table_id).first()
        if not table:
            return None
        table.table_number = table_number
        table.capacity = capacity
        table.zone = zone
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
