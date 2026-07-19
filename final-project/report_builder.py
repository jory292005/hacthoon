import os
from datetime import datetime
from typing import Any, Dict
from weasyprint import HTML

def generate_report(audit_json: Dict[str, Any], output_path: str) -> str:
    supplier_name = audit_json.get("supplier_name", "غير معروف")
    contract_type = audit_json.get("contract_type", "supply")
    
    contract_type_map = {
        "supply": "توريد", "service": "خدمات", "construction": "مقاولات",
        "franchise": "امتياز تجاري", "employment": "عمالة/توظيف",
        "technology": "تقنية", "partnership": "شراكة", "humanitarian": "إغاثي/إنساني"
    }
    contract_type_ar = contract_type_map.get(contract_type, contract_type)
    is_template = audit_json.get("is_template", False)
    overall_status = audit_json.get("overall_status", "FAIL")
    
    status_map = {"PASS": "مطابق", "PARTIAL": "مطابق جزئياً", "FAIL": "غير مطابق"}
    decision_map = {"PASS": "قبول", "PARTIAL": "قبول مشروط", "FAIL": "رفض"}
    risk_map = {"CRITICAL": "حرج", "HIGH": "عالٍ", "MEDIUM": "متوسط", "LOW": "منخفض"}
    severity_map = {"CRITICAL": "حرجة", "HIGH": "عالية", "MEDIUM": "متوسطة", "LOW": "بسيطة"}
    
    status_ar = status_map.get(overall_status, "غير مطابق")
    final_decision = decision_map.get(overall_status, "رفض")
    score = audit_json.get("compliance_score", 0)
    risk_level = audit_json.get("risk_level", "MEDIUM")
    risk_ar = risk_map.get(risk_level, "متوسط")
    
    violations = audit_json.get("violations", [])
    strengths = audit_json.get("strengths", [])
    missing_clauses = audit_json.get("missing_clauses", [])
    incomplete_clauses = audit_json.get("incomplete_clauses", [])
    recommendations = audit_json.get("recommendations", [])
    
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    status_color = "#00796b" if overall_status == "PASS" else ("#c27c0e" if overall_status == "PARTIAL" else "#b02a2a")
    risk_color = "#00796b" if risk_level == "LOW" else ("#c27c0e" if risk_level == "MEDIUM" else "#b02a2a")

    violations_html = ""
    if not violations:
        violations_html = '<p style="color: #00796b; font-size: 14px;">لا توجد أي مخالفات مسجّلة على هذا العقد.</p>'
    else:
        for i, v in enumerate(violations, start=1):
            sev = v.get("severity", "MEDIUM")
            sev_ar = severity_map.get(sev, "متوسطة")
            sev_color = "#00796b" if sev == "LOW" else ("#c27c0e" if sev == "MEDIUM" else "#b02a2a")
            rec_text = v.get("recommendation", "")
            rec_html = f'<p style="margin: 5px 0 0 0; color: #6e6e6e; font-size: 13px; font-style: italic;"><b>التوصية:</b> {rec_text}</p>' if rec_text else ''
            
            violations_html += f'''
            <div class="violation-card">
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 5px;">
                    <tr>
                        <td style="text-align: right; font-weight: bold; color: #212121; font-size: 15px;">{i}. {v.get("clause", "بند غير محدد")}</td>
                        <td style="text-align: left; font-weight: bold; color: {sev_color}; font-size: 14px;">({sev_ar})</td>
                    </tr>
                </table>
                <p style="margin: 5px 0; color: #333333; font-size: 14px; line-height: 1.5;">{v.get("description", "")}</p>
                {rec_html}
            </div>
            '''

    missing_html = ""
    if missing_clauses:
        missing_html = f'<div class="section-title" style="color: #b02a2a;">بنود مفقودة كلياً من العقد ({len(missing_clauses)})</div><ul class="bullet-list">'
        for item in missing_clauses:
            missing_html += f'<li>{item}</li>'
        missing_html += '</ul>'

    incomplete_html = ""
    if incomplete_clauses:
        incomplete_html = f'<div class="section-title" style="color: #c27c0e;">بنود موجودة لكن غير مكتملة ({len(incomplete_clauses)})</div><ul class="bullet-list">'
        for c in incomplete_clauses:
            text = f"<b>{c['clause']}:</b> {c['note']}" if isinstance(c, dict) and c.get('note') else (c['clause'] if isinstance(c, dict) else str(c))
            incomplete_html += f'<li>{text}</li>'
        incomplete_html += '</ul>'

    strengths_html = ""
    if strengths:
        strengths_html = f'<div class="section-title" style="color: #00796b;">نقاط القوة في العقد ({len(strengths)})</div><ul class="bullet-list">'
        for item in strengths:
            strengths_html += f'<li>{item}</li>'
        strengths_html += '</ul>'

    recommendations_html = ""
    if recommendations:
        recommendations_html = f'<div class="section-title" style="color: #141450;">توصيات عامة ({len(recommendations)})</div><ul class="bullet-list">'
        for item in recommendations:
            recommendations_html += f'<li>{item}</li>'
        recommendations_html += '</ul>'

    template_note = '<p style="color: #c27c0e; margin: 10px 0 0 0; font-size: 13px; font-weight: bold;">ملاحظة: هذا المستند نموذج/تعميم فارغ وليس عقداً موقّعاً فعلياً.</p>' if is_template else ''

    # جلب المسار الحالي للمجلد لضمان استقرار قراءة الملفات في الأنظمة المختلفة
    base_dir = os.path.dirname(os.path.abspath(__file__))

    html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4;
            margin: 20mm 15mm;
            background-color: #f7f7f7;
        }}
        body {{
            font-family: "Arial", "Helvetica", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f7f7f7;
            color: #212121;
        }}
        .header-container {{
        display: flex;
        flex-direction: row-reverse;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        }}

        .header-text {{
        flex: 1;
        text-align: center;
        }}

        .logo {{
        max-height: 70px;
        margin-left: 15px;
        }}
        .title {{
            font-size: 22px;
            font-weight: bold;
            color: #141450;
            margin: 0;
        }}
        .subtitle {{
            font-size: 13px;
            color: #6e6e6e;
            margin: 3px 0 0 0;
        }}
        .date {{
            font-size: 12px;
            color: #6e6e6e;
            margin: 5px 0 20px 0;
        }}
        .info-box {{
            background-color: #f5f6f8;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 25px;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .info-table td {{
            padding: 6px 4px;
            font-size: 14px;
            vertical-align: top;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            margin: 20px 0 10px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #d2d2d2;
            page-break-inside: avoid;
            page-break-after: avoid;
        }}
        .violation-card {{
            background-color: #ffffff;
            border-right: 4px solid #d2d2d2;
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 4px;
            page-break-inside: avoid;
        }}
        .bullet-list {{
            margin: 0 20px 15px 0;
            padding: 0;
            font-size: 14px;
        }}
        .bullet-list li {{
            margin-bottom: 6px;
            line-height: 1.5;
        }}
        .summary-box {{
            margin-top: 25px;
            padding-top: 15px;
            border-top: 2px solid #141450;
        }}
    </style>
</head>
<body>

<div class="header-container">

    <img class="logo" src="assets/logo.png" alt="شعار بيّن">

    <div class="header-text">
        <p class="title">تقرير تدقيق العقد</p>
        <p class="subtitle">منصة بَيِّن — المساعد الذكي لتدقيق العقود</p>
    </div>

    </div>

    <div class="info-box">
        <table class="info-table">
            <tr>
                <td style="font-weight: bold; font-size: 16px; color: #212121;" colspan="2">اسم المورد: {supplier_name}</td>
            <td style="text-align: left; color: #6e6e6e; font-size: 13px;">
             تاريخ التقرير: {report_date}
             </td>
            
            
            </tr>
            
            <tr>
                <td style="color: #6e6e6e;" colspan="2">نوع العقد: {contract_type_ar}</td>
            </tr>
            <tr>
                <td style="width: 50%;"><b>الحالة العامة:</b> <span style="color: {status_color}; font-weight: bold;">{status_ar}</span></td>
                <td style="width: 50%; text-align: left;"><b>نسبة الامتثال:</b> <span style="color: #141450; font-weight: bold;">{score}%</span></td>
            </tr>
            <tr>
                <td style="width: 50%;"><b>مستوى الخطورة:</b> <span style="color: {risk_color}; font-weight: bold;">{risk_ar}</span></td>
                <td style="width: 50%; text-align: left;"><b>التوصية النهائية:</b> <span style="color: {status_color}; font-weight: bold;">{final_decision}</span></td>
            </tr>
        </table>
        {template_note}
    </div>

    <div class="section-title" style="color: #141450;">المخالفات المكتشفة ({len(violations)})</div>
    {violations_html}

    {missing_html}
    {incomplete_html}
    {strengths_html}
    {recommendations_html}

    <div class="summary-box">
        <div class="section-title" style="color: #141450; border: none; margin: 0 0 8px 0; padding: 0;">الملخص النهائي</div>
        <p style="font-size: 14px; line-height: 1.6; margin: 0;">
            بناءً على مراجعة مستندات المورد "{supplier_name}" (عقد {contract_type_ar}), 
            تم تصنيف حالته كـ "{status_ar}" بنسبة امتثال تقديرية {score}%, 
            ومستوى خطورة "{risk_ar}", مع رصد {len(violations)} من المخالفات. 
            التوصية النهائية للجنة التدقيق الآلي هي: "{final_decision}".
        </p>
    </div>

</body>
</html>
"""
    HTML(string=html_content, base_url=base_dir).write_pdf(output_path)
    return output_path 