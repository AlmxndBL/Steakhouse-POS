import unittest
from database.connection import SessionLocal
from services.report_service import ReportService

class TestReportsAnalytics(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_sales_report_aggregation(self):
        """Test sales report metrics (gross, net, discounts, bill count, payment splits)."""
        report = ReportService.get_sales_report(self.db, period="all")
        self.assertIsNotNone(report)
        self.assertIn("total_net", report)
        self.assertIn("cash_sales", report)
        self.assertIn("qr_sales", report)
        self.assertIn("food_cost_pct", report)
        self.assertIn("gross_margin_pct", report)
        self.assertIn("top_sellers", report)
        self.assertIn("orders", report)
        self.assertGreaterEqual(report["total_net"], 0.0)

    def test_top_sellers_ranking(self):
        """Test top sellers ranking structure."""
        report = ReportService.get_sales_report(self.db, period="all")
        top_sellers = report["top_sellers"]
        self.assertIsInstance(top_sellers, list)
        if len(top_sellers) > 0:
            first = top_sellers[0]
            self.assertIn("name", first)
            self.assertIn("qty", first)
            self.assertIn("revenue", first)

    def test_csv_export_generation(self):
        """Test generating CSV formatted sales report string."""
        csv_str = ReportService.generate_sales_csv(self.db, period="all")
        self.assertIsInstance(csv_str, str)
        self.assertIn("Steakhouse POS - รายงานสรุปยอดขาย", csv_str)
        self.assertIn("ยอดขายสุทธิรวม (บาท)", csv_str)
        self.assertIn("เลขที่บิล", csv_str)

if __name__ == '__main__':
    unittest.main()
