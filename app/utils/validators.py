import re
from datetime import datetime, date
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class ValidationResult:
    is_valid: bool
    value: Any = None
    error: Optional[str] = None

class Validator:
    @staticmethod
    def validate_required_text(
        raw_val: Optional[str],
        field_name: str = "ข้อมูล",
        min_len: int = 1,
        max_len: int = 100
    ) -> ValidationResult:
        if raw_val is None:
            return ValidationResult(is_valid=False, error=f"กรุณากรอก{field_name}")
        
        cleaned = str(raw_val).strip()
        if not cleaned:
            return ValidationResult(is_valid=False, error=f"กรุณากรอก{field_name}")
        
        if len(cleaned) < min_len:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องมีความยาวอย่างน้อย {min_len} ตัวอักษร")
            
        if len(cleaned) > max_len:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องมีความยาวไม่เกิน {max_len} ตัวอักษร")
            
        return ValidationResult(is_valid=True, value=cleaned)

    @staticmethod
    def validate_username(raw_val: Optional[str]) -> ValidationResult:
        if not raw_val:
            return ValidationResult(is_valid=False, error="กรุณากรอกชื่อผู้ใช้ (Username)")
            
        cleaned = str(raw_val).strip().lower()
        if len(cleaned) < 3:
            return ValidationResult(is_valid=False, error="ชื่อผู้ใช้ต้องมีความยาวอย่างน้อย 3 ตัวอักษร")
            
        if len(cleaned) > 30:
            return ValidationResult(is_valid=False, error="ชื่อผู้ใช้ต้องมีความยาวไม่เกิน 30 ตัวอักษร")
            
        if not re.match(r"^[a-z0-9_]+$", cleaned):
            return ValidationResult(is_valid=False, error="ชื่อผู้ใช้ต้องประกอบด้วยตัวอักษรภาษาอังกฤษ ตัวเลข หรือขีดล่าง (_) เท่านั้น")
            
        return ValidationResult(is_valid=True, value=cleaned)

    @staticmethod
    def validate_password(raw_val: Optional[str], min_len: int = 4) -> ValidationResult:
        if not raw_val:
            return ValidationResult(is_valid=False, error="กรุณากรอกรหัสผ่าน")
            
        cleaned = str(raw_val).strip()
        if len(cleaned) < min_len:
            return ValidationResult(is_valid=False, error=f"รหัสผ่านต้องมีความยาวอย่างน้อย {min_len} ตัวอักษร")
            
        return ValidationResult(is_valid=True, value=cleaned)

    @staticmethod
    def validate_phone(raw_val: Optional[str], required: bool = False) -> ValidationResult:
        if raw_val is None or not str(raw_val).strip():
            if required:
                return ValidationResult(is_valid=False, error="กรุณากรอกเบอร์โทรศัพท์")
            return ValidationResult(is_valid=True, value=None)
            
        raw_str = str(raw_val).strip()
        cleaned = re.sub(r"[^\d]", "", raw_str)
        if not cleaned or not re.match(r"^0[0-9]{8,9}$", cleaned):
            return ValidationResult(is_valid=False, error="เบอร์โทรศัพท์ไม่ถูกต้อง (ต้องขึ้นต้นด้วย 0 และมี 9-10 หลัก เช่น 081-234-5678)")
            
        # Format as 08x-xxx-xxxx or 02-xxx-xxxx
        if len(cleaned) == 10:
            formatted = f"{cleaned[:3]}-{cleaned[3:6]}-{cleaned[6:]}"
        else:
            formatted = f"{cleaned[:2]}-{cleaned[2:5]}-{cleaned[5:]}"
            
        return ValidationResult(is_valid=True, value=formatted)

    @staticmethod
    def validate_price(
        raw_val: Any,
        min_val: float = 0.01,
        max_val: float = 100000.0,
        field_name: str = "ราคาขาย"
    ) -> ValidationResult:
        if raw_val is None or str(raw_val).strip() == "":
            return ValidationResult(is_valid=False, error=f"กรุณากรอก{field_name}")
            
        cleaned = str(raw_val).strip().replace(",", "")
        try:
            val = float(cleaned)
        except ValueError:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องเป็นตัวเลขเท่านั้น (เช่น 250 หรือ 199.50)")
            
        if val < min_val:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องไม่น้อยกว่า {min_val:,.2f} บาท")
            
        if val > max_val:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องไม่เกิน {max_val:,.2f} บาท")
            
        return ValidationResult(is_valid=True, value=round(val, 2))

    @staticmethod
    def validate_integer(
        raw_val: Any,
        field_name: str = "จำนวน",
        min_val: int = 0,
        max_val: int = 1000000
    ) -> ValidationResult:
        if raw_val is None or str(raw_val).strip() == "":
            return ValidationResult(is_valid=False, error=f"กรุณากรอก{field_name}")
            
        cleaned = str(raw_val).strip().replace(",", "")
        try:
            val = int(cleaned)
        except ValueError:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องเป็นจำนวนเต็มเท่านั้น (เช่น 1, 2, 4)")
            
        if val < min_val:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องไม่น้อยกว่า {min_val}")
            
        if val > max_val:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องไม่เกิน {max_val}")
            
        return ValidationResult(is_valid=True, value=val)

    @staticmethod
    def validate_float(
        raw_val: Any,
        field_name: str = "จำนวน",
        min_val: float = 0.0,
        max_val: float = 1000000.0
    ) -> ValidationResult:
        if raw_val is None or str(raw_val).strip() == "":
            return ValidationResult(is_valid=False, error=f"กรุณากรอก{field_name}")
            
        cleaned = str(raw_val).strip().replace(",", "")
        try:
            val = float(cleaned)
        except ValueError:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องเป็นตัวเลขเท่านั้น (เช่น 10.5 หรือ 250)")
            
        if val < min_val:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องไม่น้อยกว่า {min_val}")
            
        if val > max_val:
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องไม่เกิน {max_val}")
            
        return ValidationResult(is_valid=True, value=val)

    @staticmethod
    def validate_date(
        raw_val: Optional[str],
        field_name: str = "วันที่",
        allow_past: bool = True
    ) -> ValidationResult:
        if not raw_val or not str(raw_val).strip():
            return ValidationResult(is_valid=False, error=f"กรุณากรอก{field_name} (รูปแบบ YYYY-MM-DD)")
            
        cleaned = str(raw_val).strip()
        try:
            parsed_date = datetime.strptime(cleaned, "%Y-%m-%d").date()
        except ValueError:
            return ValidationResult(is_valid=False, error=f"{field_name}รูปแบบไม่ถูกต้อง กรุณาใช้ YYYY-MM-DD (เช่น 2026-12-31)")
            
        if not allow_past and parsed_date < date.today():
            return ValidationResult(is_valid=False, error=f"{field_name}ต้องไม่เป็นวันที่ในอดีต (ต้องเป็นวันนี้หรือหลังจากนี้)")
            
        return ValidationResult(is_valid=True, value=parsed_date)

    @staticmethod
    def validate_discount(raw_val: Any, subtotal: float) -> ValidationResult:
        if raw_val is None or str(raw_val).strip() == "":
            return ValidationResult(is_valid=True, value=0.0)
            
        cleaned = str(raw_val).strip().replace(",", "")
        try:
            disc = float(cleaned)
        except ValueError:
            return ValidationResult(is_valid=False, error="ส่วนลดต้องเป็นตัวเลขเท่านั้น")
            
        if disc < 0:
            return ValidationResult(is_valid=False, error="ส่วนลดต้องไม่ติดลบ")
            
        if disc > subtotal:
            return ValidationResult(is_valid=False, error=f"ส่วนลดต้องไม่เกินยอดรวม ({subtotal:,.2f} บาท)")
            
        return ValidationResult(is_valid=True, value=round(disc, 2))

    @staticmethod
    def validate_menu_code(raw_val: Optional[str]) -> ValidationResult:
        if not raw_val:
            return ValidationResult(is_valid=False, error="กรุณากรอกรหัสเมนู (เช่น STK001)")
            
        cleaned = str(raw_val).strip().upper()
        if len(cleaned) < 2:
            return ValidationResult(is_valid=False, error="รหัสเมนูต้องมีความยาวอย่างน้อย 2 ตัวอักษร")
            
        if len(cleaned) > 20:
            return ValidationResult(is_valid=False, error="รหัสเมนูต้องมีความยาวไม่เกิน 20 ตัวอักษร")
            
        if not re.match(r"^[A-Z0-9\-_]+$", cleaned):
            return ValidationResult(is_valid=False, error="รหัสเมนูต้องเป็นตัวอักษรภาษาอังกฤษ ตัวเลข หรือขีด (-) เท่านั้น")
            
        return ValidationResult(is_valid=True, value=cleaned)

    @staticmethod
    def validate_table_number(raw_val: Optional[str]) -> ValidationResult:
        if not raw_val:
            return ValidationResult(is_valid=False, error="กรุณากรอกหมายเลขโต๊ะ (เช่น T01, VIP1)")
            
        cleaned = str(raw_val).strip().upper()
        if len(cleaned) < 1:
            return ValidationResult(is_valid=False, error="กรุณากรอกหมายเลขโต๊ะ")
            
        if len(cleaned) > 20:
            return ValidationResult(is_valid=False, error="หมายเลขโต๊ะต้องมีความยาวไม่เกิน 20 ตัวอักษร")
            
        return ValidationResult(is_valid=True, value=cleaned)
