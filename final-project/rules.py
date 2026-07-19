# -*- coding: utf-8 -*-
"""
rules.py
=========
مشروع: AI Vendor Compliance Auditor
المسؤول عن هذا الملف: زينب (Rule Engine + Report Builder).

⚠️ تحديث مهم (بعد مراجعة شغل جوري وسحر):
    النسخة الأولى من هذا الملف كانت مبنية على شكل JSON مختلف تماماً عن اللي
    فعلياً يرجّعه ai_engine.py الحالي. هذه النسخة أُعيد بناؤها بالكامل لتطابق
    الـ schema الحقيقي المستخدم في ai_engine.audit_contract() حرفياً.

    ملاحظة: ai_engine.py عنده الـ System Prompt الخاص به مكتوب مباشرة داخله
    (ولا يستورد أي prompt من هذا الملف) — وهذا شيء طبيعي ولا يحتاج تغيير.
    دور هذا الملف الآن هو فقط: التحقق من صحة الـ JSON الراجع من جوري
    (validate) وتطبيعه/تعبئة النواقص (normalize) وتوفير قواميس الترجمة
    للعربية (Arabic labels) التي يستخدمها report_builder.py.

الـ schema الحقيقي الذي يرجعه ai_engine.audit_contract():
{
  "supplier_name": "string",
  "contract_type": "string",              # supply | service | construction | ...
  "is_template": true/false,
  "overall_status": "PASS | PARTIAL | FAIL",
  "compliance_score": 0-100,
  "risk_level": "CRITICAL | HIGH | MEDIUM | LOW",
  "violations": [
      {"clause": "...", "severity": "CRITICAL|HIGH|MEDIUM|LOW",
       "description": "...", "recommendation": "..."}
  ],
  "strengths": ["..."],
  "missing_clauses": ["..."],
  "incomplete_clauses": [{"clause": "...", "note": "..."}],
  "recommendations": ["..."]
}
"""

from typing import Any, Dict, List


# =============================================================================
# 1) الحقول والقيم المسموح بها
# =============================================================================

# حقول أساسية لازم تكون موجودة دائماً (لو ai_engine.py ما رجّعها، فيه مشكلة حقيقية)
REQUIRED_FIELDS: List[str] = [
    "supplier_name",
    "overall_status",
    "compliance_score",
    "violations",
]

# حقول اختيارية: لو ناقصة، normalize_audit_json تعبّيها بقيمة افتراضية آمنة
# بدل ما توقف التقرير عن الاشتغال
OPTIONAL_FIELDS_DEFAULTS: Dict[str, Any] = {
    "contract_type": "غير محدد",
    "is_template": False,
    "risk_level": "MEDIUM",
    "strengths": [],
    "missing_clauses": [],
    "incomplete_clauses": [],
    "recommendations": [],
}

VALID_STATUS_VALUES: List[str] = ["PASS", "PARTIAL", "FAIL"]
VALID_RISK_VALUES: List[str] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
VALID_SEVERITY_VALUES: List[str] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


# =============================================================================
# 2) قواميس الترجمة للعربية (يستخدمها report_builder.py مباشرة)
# =============================================================================

STATUS_LABELS_AR: Dict[str, str] = {
    "PASS": "مطابق",
    "PARTIAL": "مطابق جزئياً",
    "FAIL": "غير مطابق",
}

# القرار النهائي المُشتق من overall_status (مطلوب لعرضه في التقرير كتوصية ختامية)
FINAL_DECISION_AR: Dict[str, str] = {
    "PASS": "قبول",
    "PARTIAL": "قبول مشروط",
    "FAIL": "رفض",
}

RISK_LABELS_AR: Dict[str, str] = {
    "CRITICAL": "حرج",
    "HIGH": "عالٍ",
    "MEDIUM": "متوسط",
    "LOW": "منخفض",
}

SEVERITY_LABELS_AR: Dict[str, str] = {
    "CRITICAL": "حرجة",
    "HIGH": "عالية",
    "MEDIUM": "متوسطة",
    "LOW": "بسيطة",
}

CONTRACT_TYPE_LABELS_AR: Dict[str, str] = {
    "supply": "توريد",
    "service": "خدمات",
    "construction": "مقاولات",
    "franchise": "امتياز تجاري",
    "employment": "عمالة/توظيف",
    "technology": "تقنية",
    "partnership": "شراكة",
    "humanitarian": "إغاثي/إنساني",
}

# ترتيب الخطورة من الأعلى للأقل (يُستخدم لترتيب المخالفات في التقرير)
_SEVERITY_PRIORITY: Dict[str, int] = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def severity_priority(severity: str) -> int:
    """يرجع أولوية رقمية للخطورة (أعلى = أخطر)، تُستخدم للترتيب."""
    return _SEVERITY_PRIORITY.get(str(severity).upper(), 0)


# =============================================================================
# 3) دوال Rule Engine: التحقق من صحة البيانات وتطبيعها
# =============================================================================

class InvalidAuditDataError(Exception):
    """يُرفع هذا الاستثناء عندما لا تكون بيانات التدقيق (JSON) بالشكل المتوقع."""
    pass


def validate_audit_json(audit_json: Dict[str, Any]) -> None:
    """
    يتحقق من أن بيانات التدقيق (الناتجة من ai_engine.audit_contract) تحتوي
    على الحقول الأساسية المطلوبة وبأنواع بيانات منطقية، قبل تمريرها لـ
    Report Builder.

    Args:
        audit_json: القاموس (dict) الناتج مباشرة من audit_contract(...).

    Raises:
        InvalidAuditDataError: إذا كان أي حقل أساسي مفقوداً أو من نوع غير صحيح.
    """
    if not isinstance(audit_json, dict):
        raise InvalidAuditDataError("بيانات التدقيق يجب أن تكون كائن JSON (dict).")

    missing = [f for f in REQUIRED_FIELDS if f not in audit_json]
    if missing:
        raise InvalidAuditDataError(
            f"الحقول الأساسية التالية مفقودة في بيانات التدقيق: {', '.join(missing)}"
        )

    if not isinstance(audit_json["supplier_name"], str) or not audit_json["supplier_name"].strip():
        raise InvalidAuditDataError("حقل 'supplier_name' يجب أن يكون نصاً غير فارغ.")

    score = audit_json["compliance_score"]
    if not isinstance(score, (int, float)):
        raise InvalidAuditDataError("حقل 'compliance_score' يجب أن يكون رقماً.")
    if not (0 <= float(score) <= 100):
        raise InvalidAuditDataError("حقل 'compliance_score' يجب أن يكون بين 0 و 100.")

    if not isinstance(audit_json["violations"], list):
        raise InvalidAuditDataError("حقل 'violations' يجب أن يكون قائمة (list).")

    for i, v in enumerate(audit_json["violations"]):
        if not isinstance(v, dict):
            raise InvalidAuditDataError(f"عنصر المخالفة رقم {i} يجب أن يكون كائن JSON.")
        if "clause" not in v:
            raise InvalidAuditDataError(f"عنصر المخالفة رقم {i} يجب أن يحتوي على 'clause' على الأقل.")

    # ملاحظة: لا نرفض قيماً غير متوقعة لـ overall_status/risk_level/severity هنا
    # (تسامحاً مع اختلافات طفيفة قد يخرجها النموذج)، لكن normalize_audit_json
    # تتعامل معها بأمان عند العرض.


def normalize_audit_json(audit_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    يطبّع بيانات التدقيق: يعبّي الحقول الاختيارية الناقصة بقيم افتراضية آمنة،
    يطبّع القيم غير المعروفة (مثل overall_status بقيمة غريبة)، ويرتّب
    المخالفات من الأخطر إلى الأقل خطورة. النتيجة جاهزة مباشرة لـ
    report_builder.generate_report.

    Args:
        audit_json: بيانات التدقيق (يُفضّل تمريرها بعد validate_audit_json).

    Returns:
        نسخة مطبَّعة من بيانات التدقيق.
    """
    normalized = dict(audit_json)

    # تعبئة الحقول الاختيارية الناقصة
    for field, default in OPTIONAL_FIELDS_DEFAULTS.items():
        if field not in normalized or normalized[field] is None:
            normalized[field] = default() if callable(default) else (
                list(default) if isinstance(default, list) else default
            )

    # تطبيع overall_status و risk_level لقيم معروفة (fallback آمن)
    status = str(normalized.get("overall_status", "FAIL")).upper()
    normalized["overall_status"] = status if status in VALID_STATUS_VALUES else "FAIL"

    risk = str(normalized.get("risk_level", "MEDIUM")).upper()
    normalized["risk_level"] = risk if risk in VALID_RISK_VALUES else "MEDIUM"

    # تطبيع المخالفات (تعبئة الحقول الناقصة داخل كل مخالفة)
    normalized_violations = []
    for v in normalized.get("violations", []):
        nv = dict(v)
        nv.setdefault("severity", "MEDIUM")
        sev = str(nv["severity"]).upper()
        nv["severity"] = sev if sev in VALID_SEVERITY_VALUES else "MEDIUM"
        nv.setdefault("description", "لم يتم تحديد وصف تفصيلي لهذه المخالفة.")
        nv.setdefault("recommendation", "")
        normalized_violations.append(nv)

    # ترتيب المخالفات من الأخطر (CRITICAL) إلى الأقل (LOW)
    normalized_violations.sort(key=lambda v: severity_priority(v["severity"]), reverse=True)
    normalized["violations"] = normalized_violations

    # تطبيع incomplete_clauses (التأكد إنها dict فيها clause/note)
    normalized_incomplete = []
    for item in normalized.get("incomplete_clauses", []):
        if isinstance(item, dict):
            normalized_incomplete.append({
                "clause": item.get("clause", "بند غير محدد"),
                "note": item.get("note", ""),
            })
        else:
            normalized_incomplete.append({"clause": str(item), "note": ""})
    normalized["incomplete_clauses"] = normalized_incomplete

    # تطبيع missing_clauses (تأكد إنها قائمة نصوص)
    normalized["missing_clauses"] = [
        (c if isinstance(c, str) else c.get("clause", str(c)))
        for c in normalized.get("missing_clauses", [])
    ]

    return normalized
