# -*- coding: utf-8 -*-
"""
sample_data.py
===============
بيانات تجريبية بنفس الشكل الحقيقي الذي يُنتجه ai_engine.audit_contract()،
تُستخدم لاختبار rules.py و report_builder.py دون الحاجة لاستدعاء الـ API
فعلياً (لا تحتاج GROQ_API_KEY).
"""

# مثال 1: عقد غير مطابق (مخالفات جوهرية + بند مفقود بالكامل)
SAMPLE_FAIL = {
    "supplier_name": "شركة الخليج الدولية للتجارة",
    "contract_type": "supply",
    "is_template": False,
    "overall_status": "FAIL",
    "compliance_score": 38,
    "risk_level": "CRITICAL",
    "violations": [
        {
            "clause": "بند الضمان",
            "severity": "CRITICAL",
            "description": "الدفعة كاملة مقدماً بدون أي ضمان ابتدائي أو نهائي، وهذا يخالف مبادئ نظام المشتريات الحكومية.",
            "recommendation": "اشتراط ضمان بنكي لا يقل عن 10% من قيمة العقد قبل صرف أي دفعة.",
        },
        {
            "clause": "بند الغرامات التأخيرية",
            "severity": "HIGH",
            "description": "الغرامة اليومية 10% من قيمة العقد بدون حد أقصى، وهذا مبلغ غير معقول ومخالف للمبدأ العام بوضع سقف للغرامات.",
            "recommendation": "تحديد حد أقصى للغرامة التأخيرية (عادة لا يتجاوز 10% من قيمة العقد الإجمالية).",
        },
        {
            "clause": "بند الفسخ",
            "severity": "HIGH",
            "description": "الشرط غير متوازن: يحق للمورد الفسخ بإشعار 24 ساعة فقط، بينما يُطلب من العميل إشعار 90 يوماً مع غرامة 50%.",
            "recommendation": "إعادة صياغة بند الفسخ بحيث تكون المدد والغرامات متوازنة بين الطرفين.",
        },
    ],
    "strengths": [
        "تحديد واضح لأطراف العقد وموضوعه (توريد 500 خيمة بمواصفات PVC).",
    ],
    "missing_clauses": ["شهادة فحص مختبري مستقلة للمواد المورَّدة"],
    "incomplete_clauses": [
        {"clause": "بند تسوية النزاعات", "note": "لم يُحدَّد بوضوح إن كانت التسوية عبر التحكيم أو القضاء المختص."},
    ],
    "recommendations": [
        "مراجعة العقد من محامٍ مرخّص قبل التوقيع النهائي نظراً لعدد المخالفات الجوهرية.",
        "طلب شهادات جودة وفحص مختبري مستقلة قبل استلام أي دفعة من الخيام.",
    ],
}

# مثال 2: عقد مطابق جزئياً (مخالفة واحدة متوسطة + بند غير مكتمل)
SAMPLE_PARTIAL = {
    "supplier_name": "مؤسسة البناء المتكامل للمقاولات",
    "contract_type": "construction",
    "is_template": False,
    "overall_status": "PARTIAL",
    "compliance_score": 78,
    "risk_level": "MEDIUM",
    "violations": [
        {
            "clause": "بند القوة القاهرة",
            "severity": "MEDIUM",
            "description": "بند القوة القاهرة عام جداً ولا يحدد أمثلة أو آلية إثبات الحالة الاستثنائية.",
            "recommendation": "تفصيل الحالات المشمولة (كوارث طبيعية، قرارات حكومية...) وآلية الإخطار بها.",
        },
    ],
    "strengths": [
        "وجود ضمان ابتدائي ونهائي واضح ومحدد النسبة.",
        "آلية فحص واستلام رسمية موثقة قبل اعتماد التوريد النهائي.",
    ],
    "missing_clauses": [],
    "incomplete_clauses": [
        {"clause": "شهادة التأهيل الفني", "note": "تنتهي صلاحيتها خلال 20 يوماً من تاريخ التقديم."},
    ],
    "recommendations": [
        "طلب تجديد شهادة التأهيل الفني كشرط للتعاقد النهائي.",
    ],
}

# مثال 3: عقد مطابق بالكامل (بدون أي مخالفات)
SAMPLE_PASS = {
    "supplier_name": "الشركة الوطنية للحلول الصناعية",
    "contract_type": "technology",
    "is_template": False,
    "overall_status": "PASS",
    "compliance_score": 97,
    "risk_level": "LOW",
    "violations": [],
    "strengths": [
        "جميع البنود التجارية والقانونية الأساسية موثقة بوضوح.",
        "آلية دفع وجدولة واضحة مع ضمانات مالية كافية.",
        "بند سرية شامل يحمي معلومات الطرفين.",
    ],
    "missing_clauses": [],
    "incomplete_clauses": [],
    "recommendations": [],
}


if __name__ == "__main__":
    import json
    print(json.dumps(SAMPLE_FAIL, ensure_ascii=False, indent=2))
