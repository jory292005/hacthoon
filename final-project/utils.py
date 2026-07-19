import json


def normalize_arabic(text):
    if not text:
        return ""
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه")
    text = text.replace("ى", "ي")
    return text.strip()


def detect_contract_type(text):
    keywords = {
        "supply": ["توريد", "مشتريات", "سلع", "منتج", "مواد", "بضاعة", "تسليم"],
        "service": ["خدمات", "صيانة", "استشارات", "تدريب", "اشراف", "ادارة"],
        "construction": ["مقاولة", "انشاء", "بناء", "تشييد", "مقايسة", "اعمال"],
        "franchise": ["امتياز", "فرنشايز", "علامة تجارية"],
        "employment": ["عمل", "موظف", "راتب", "اجازة", "فصل", "تأمين"],
        "technology": ["تقنية", "برمجيات", "برمجة", "software", "IT", "تطوير"],
        "partnership": ["شراكة", "شريك", "بنسبة", "ربح", "خسارة"]
    }
    text_norm = normalize_arabic(text)
    scores = {}
    for ctype, words in keywords.items():
        score = sum(1 for w in words if normalize_arabic(w) in text_norm)
        scores[ctype] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "supply"


def format_report_data(audit_result):
    lines = []
    lines.append(f"المورد: {audit_result.get('supplier_name', 'غير معروف')}")
    lines.append(f"نوع العقد: {audit_result.get('contract_type', 'غير محدد')}")
    lines.append(f"الحالة: {audit_result.get('overall_status', '-')}")
    lines.append(f"النقاط: {audit_result.get('compliance_score', 0)}/100")
    lines.append(f"المخاطر: {audit_result.get('risk_level', 'UNKNOWN')}")
    lines.append(f"المخالفات: {len(audit_result.get('violations', []))}")
    return "\n".join(lines)


def severity_priority(sev):
    mapping = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    return mapping.get(sev, 0)


def sort_violations(violations):
    return sorted(violations, key=lambda v: severity_priority(v.get("severity", "LOW")), reverse=True)