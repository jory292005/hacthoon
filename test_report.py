# -*- coding: utf-8 -*-
"""
test_report.py
================
يولّد 3 تقارير PDF تجريبية داخل reports/ لاختبار rules.py + report_builder.py
معاً، باستخدام بيانات sample_data.py (بدون الحاجة لاستدعاء ai_engine.py أو
GROQ_API_KEY).
"""

from rules import validate_audit_json, normalize_audit_json, InvalidAuditDataError
from report_builder import generate_report
from sample_data import SAMPLE_FAIL, SAMPLE_PARTIAL, SAMPLE_PASS

CASES = [
    ("تقرير_غير_مطابق", SAMPLE_FAIL),
    ("تقرير_مطابق_جزئياً", SAMPLE_PARTIAL),
    ("تقرير_مطابق_بالكامل", SAMPLE_PASS),
]


def run():
    for filename, raw in CASES:
        try:
            validate_audit_json(raw)
        except InvalidAuditDataError as e:
            print(f"❌ {filename}: بيانات غير صالحة - {e}")
            continue

        normalized = normalize_audit_json(raw)
        output_path = f"reports/{filename}.pdf"
        path = generate_report(normalized, output_path)
        print(f"✅ تم إنشاء: {path}")


if __name__ == "__main__":
    run()
