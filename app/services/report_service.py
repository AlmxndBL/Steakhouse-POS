import csv
import io
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Order, OrderItem, OrderStatus, MenuItem, RecipeBOM, Ingredient, StockTransaction, StockTxType

class ReportService:
    @staticmethod
    def get_sales_report(db: Session, period: str = "today") -> Dict[str, Any]:
        """
        Retrieves sales metrics, top sellers, food cost, charts data, and orders based on period:
        - 'today': Current day
        - '7days': Last 7 days
        - 'month': Current month
        - 'all': All historical data
        """
        now = datetime.now(timezone.utc)
        query = db.query(Order).filter(Order.status == OrderStatus.PAID)

        if period == "today":
            start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
            query = query.filter(Order.created_at >= start_of_day)
        elif period == "7days":
            start_7days = now - timedelta(days=7)
            query = query.filter(Order.created_at >= start_7days)
        elif period == "month":
            start_month = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
            query = query.filter(Order.created_at >= start_month)

        orders = query.order_by(Order.created_at.desc()).all()

        # 1. Financial Metrics
        total_gross = sum(float(o.subtotal) for o in orders)
        total_discount = sum(float(o.discount_amount) for o in orders)
        total_sc = sum(float(o.service_charge_amount) for o in orders)
        total_vat = sum(float(o.vat_amount) for o in orders)
        total_net = sum(float(o.net_amount) for o in orders)
        bill_count = len(orders)
        avg_bill = total_net / bill_count if bill_count > 0 else 0.0

        cash_sales = sum(float(o.net_amount) for o in orders if o.payment_method and ("เงินสด" in o.payment_method or o.payment_method.upper() == "CASH"))
        qr_sales = sum(float(o.net_amount) for o in orders if o.payment_method and ("QR" in o.payment_method or "PROMPTPAY" in o.payment_method.upper()))
        other_sales = total_net - (cash_sales + qr_sales)

        cash_pct = (cash_sales / total_net * 100.0) if total_net > 0 else 0.0
        qr_pct = (qr_sales / total_net * 100.0) if total_net > 0 else 0.0

        # 2. Product Sales, Top Sellers & Category Share
        item_sales_map = {}
        category_sales_map = {}
        for o in orders:
            for item in o.items:
                m_id = item.menu_item_id
                m_name = item.menu_item.name if item.menu_item else f"Item #{m_id}"
                cat_name = item.menu_item.category.name if item.menu_item and item.menu_item.category else "ทั่วไป"
                price = float(item.price_per_unit)
                qty = item.quantity
                revenue = price * qty

                # Item Aggregation
                if m_id not in item_sales_map:
                    item_sales_map[m_id] = {
                        "name": m_name,
                        "category": cat_name,
                        "qty": 0,
                        "revenue": 0.0
                    }
                item_sales_map[m_id]["qty"] += qty
                item_sales_map[m_id]["revenue"] += revenue

                # Category Aggregation
                if cat_name not in category_sales_map:
                    category_sales_map[cat_name] = 0.0
                category_sales_map[cat_name] += revenue

        top_sellers = sorted(item_sales_map.values(), key=lambda x: x["qty"], reverse=True)[:5]
        
        category_breakdown = []
        for cat_name, rev in category_sales_map.items():
            pct = (rev / total_gross * 100.0) if total_gross > 0 else 0.0
            category_breakdown.append({
                "name": cat_name,
                "revenue": rev,
                "pct": pct
            })
        category_breakdown = sorted(category_breakdown, key=lambda x: x["revenue"], reverse=True)

        # 3. 7-Day Daily Trend
        daily_trend = []
        day_names = ["จันทร์", "อังคาร", "พุธ", "พฤหัส", "ศุกร์", "เสาร์", "อาทิตย์"]
        all_paid_orders = db.query(Order).filter(
            Order.status == OrderStatus.PAID,
            Order.created_at >= (now - timedelta(days=6))
        ).all()

        for i in range(6, -1, -1):
            d = (now - timedelta(days=i)).date()
            day_orders = [o for o in all_paid_orders if o.created_at and o.created_at.date() == d]
            day_sales = sum(float(o.net_amount) for o in day_orders)
            daily_trend.append({
                "date": d.strftime("%d/%m"),
                "day_name": day_names[d.weekday()],
                "day_label": f"{day_names[d.weekday()][:2]} {d.strftime('%d/%m')}",
                "sales": day_sales,
                "bills": len(day_orders)
            })

        # 4. Food Cost Calculation
        total_food_cost = 0.0
        for o in orders:
            for item in o.items:
                boms = db.query(RecipeBOM).filter(RecipeBOM.menu_item_id == item.menu_item_id).all()
                for bom in boms:
                    ing_cost = float(bom.ingredient.cost_per_unit) if bom.ingredient else 0.0
                    total_food_cost += float(bom.quantity_required) * ing_cost * item.quantity

        food_cost_pct = (total_food_cost / total_net * 100.0) if total_net > 0 else 0.0
        gross_profit = total_net - total_food_cost
        gross_margin_pct = (gross_profit / total_net * 100.0) if total_net > 0 else 0.0

        # 5. Wastage Cost in period
        wastage_query = db.query(StockTransaction).filter(StockTransaction.tx_type == StockTxType.WASTAGE)
        if period == "today":
            start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
            wastage_query = wastage_query.filter(StockTransaction.timestamp >= start_of_day)
        elif period == "7days":
            start_7days = now - timedelta(days=7)
            wastage_query = wastage_query.filter(StockTransaction.timestamp >= start_7days)
        elif period == "month":
            start_month = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
            wastage_query = wastage_query.filter(StockTransaction.timestamp >= start_month)

        wastage_txs = wastage_query.all()
        total_wastage_cost = 0.0
        for tx in wastage_txs:
            unit_cost = float(tx.lot.unit_cost) if tx.lot else 0.0
            total_wastage_cost += abs(float(tx.quantity)) * unit_cost

        return {
            "period": period,
            "total_gross": total_gross,
            "total_discount": total_discount,
            "total_sc": total_sc,
            "total_vat": total_vat,
            "total_net": total_net,
            "bill_count": bill_count,
            "avg_bill": avg_bill,
            "cash_sales": cash_sales,
            "qr_sales": qr_sales,
            "other_sales": other_sales,
            "cash_pct": cash_pct,
            "qr_pct": qr_pct,
            "top_sellers": top_sellers,
            "category_breakdown": category_breakdown,
            "daily_trend": daily_trend,
            "total_food_cost": total_food_cost,
            "food_cost_pct": food_cost_pct,
            "gross_profit": gross_profit,
            "gross_margin_pct": gross_margin_pct,
            "total_wastage_cost": total_wastage_cost,
            "orders": orders
        }

    @staticmethod
    def generate_sales_csv(db: Session, period: str = "today") -> str:
        """
        Generates CSV format string of sales data for export to Excel.
        """
        report = ReportService.get_sales_report(db, period)
        orders = report["orders"]

        output = io.StringIO()
        writer = csv.writer(output, delimiter=",")
        
        # Write Header Summary
        writer.writerow(["Steakhouse POS - รายงานสรุปยอดขาย"])
        writer.writerow(["ช่วงเวลา", report["period"]])
        writer.writerow(["ยอดขายสุทธิรวม (บาท)", f"{report['total_net']:.2f}"])
        writer.writerow(["ยอดส่วนลดรวม (บาท)", f"{report['total_discount']:.2f}"])
        writer.writerow(["จำนวนบิลทั้งหมด", report["bill_count"]])
        writer.writerow(["ยอดเงินสด (บาท)", f"{report['cash_sales']:.2f}"])
        writer.writerow(["ยอดสแกน QR PromptPay (บาท)", f"{report['qr_sales']:.2f}"])
        writer.writerow(["Food Cost %", f"{report['food_cost_pct']:.2f}%"])
        writer.writerow([])

        # Write Order Details Table
        writer.writerow(["เลขที่บิล", "วันที่/เวลา", "ประเภทบิล", "โต๊ะ/ลูกค้า", "พนักงาน", "ช่องทางชำระ", "ยอดรวม (บาท)", "ส่วนลด (บาท)", "ยอดสุทธิ (บาท)"])
        for o in orders:
            staff_name = o.user.name if o.user else "-"
            tbl = f"โต๊ะ {o.table.table_number}" if o.table else o.customer_name
            writer.writerow([
                o.order_number,
                o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "-",
                o.order_type.value if hasattr(o.order_type, "value") else str(o.order_type),
                tbl,
                staff_name,
                o.payment_method or "-",
                f"{float(o.subtotal):.2f}",
                f"{float(o.discount_amount):.2f}",
                f"{float(o.net_amount):.2f}"
            ])

        return output.getvalue()
