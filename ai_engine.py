"""AI Contract Auditor - Engine Module (Groq Version)"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from knowledge_base import get_context_for_type
from utils import detect_contract_type

load_dotenv()

_client = None


class MissingAPIKeyError(RuntimeError):
    """يُرفع عند عدم توفر GROQ_API_KEY وقت التدقيق الفعلي (وليس عند الاستيراد)،
    حتى لا يمنع تشغيل بقية الموقع (تسجيل الدخول، لوحة التحكم...) في حال نسي
    أحد إعداد المفتاح."""
    pass


def _get_client():
    """ينشئ عميل Groq بشكل كسول (lazy) عند أول استخدام فعلي فقط."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise MissingAPIKeyError(
            "لم يتم العثور على مفتاح GROQ_API_KEY. أضِفه في ملف .env "
            "(احصل عليه من https://console.groq.com) ثم أعد المحاولة."
        )

    _client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    return _client


def audit_contract(text, supplier_name, contract_type=None):
    """Analyze contract text and return structured audit results."""

    client = _get_client()

    if not contract_type:
        contract_type = detect_contract_type(text)

    regulatory_context = get_context_for_type(contract_type, text=text)

    schema = (
        '{"supplier_name":"string",'
        '"contract_type":"string",'
        '"is_template":"true or false",'
        '"overall_status":"PASS or PARTIAL or FAIL",'
        '"compliance_score":"0-100",'
        '"risk_level":"CRITICAL or HIGH or MEDIUM or LOW",'
        '"violations":['
        '{"clause":"string","severity":"CRITICAL or HIGH or MEDIUM or LOW",'
        '"description":"string","recommendation":"string"}'
        '],"strengths":[],'
        '"missing_clauses":[],'
        '"incomplete_clauses":[{"clause":"string","note":"string"}],'
        '"recommendations":[]}'
    )

    prompt = (
        "أنت مدقق عقود قانوني سعودي خبير. قم بتحليل هذا العقد بدقة واستخرج المخالفات "
        "ونقاط الضعف والثغرات القانونية بناءً على المبادئ التنظيمية المرجعية أدناه:\n\n"
        "--- المبادئ التنظيمية المرجعية (استخدمها كمعيار للتدقيق) ---\n"
        f"{regulatory_context}\n"
        "--- نهاية المبادئ المرجعية ---\n\n"
        "تعليمات مهمة قبل التحليل:\n"
        "1. بعض العقود تكون نماذج/تعاميم فارغة (Template) حيث تكون البنود موجودة شكلاً "
        "لكن قيمها الفعلية مكتوبة كنقاط أو فراغات مثل (...........) أو (00/00/00) بدل أرقام وأسماء حقيقية.\n"
        "2. إذا كان العقد نموذجاً فارغاً بهذا الشكل، ضع is_template=true، ولا تضع البنود الموجودة "
        "شكلياً (حتى لو فارغة القيمة) ضمن missing_clauses — بدلاً من ذلك ضعها ضمن incomplete_clauses "
        "مع توضيح أنها موجودة كبند لكن تنقصها القيم الفعلية.\n"
        "3. missing_clauses تستخدم فقط للبنود الغائبة كلياً عن العقد (لا يوجد لها أي ذكر أو بند مخصص إطلاقاً).\n"
        "4. incomplete_clauses تستخدم للبنود الموجودة كصياغة لكن قيمها فارغة أو غير مكتملة.\n"
        "5. مهم جداً: قبل إدراج أي بند ضمن missing_clauses، اقرأ نص العقد كاملاً بعناية وتأكد أنه لا يوجد "
        "أي ذكر له بصياغة مشابهة أو مرادفة (مثلاً 'بند السرية' قد يُذكر باسم 'المحافظة على سرية المعلومات'). "
        "إدراج بند موجود فعلياً ضمن missing_clauses يُعتبر خطأً جسيماً في التدقيق.\n\n"
        f"المورد: {supplier_name}\n"
        f"نوع العقد المكتشف: {contract_type}\n\n"
        "--- بداية العقد ---\n"
        f"{text[:6000]}\n"
        "--- نهاية العقد ---\n\n"
        "أرجع الرد بصيغة JSON نظيفة ومطابقة تماماً لهذا الهيكل وبدون أي مقدمات أو شرح خارج الـ JSON:\n"
        f"{schema}"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "أنت مدقق عقود قانوني سعودي. واجبك الوحيد هو إرجاع رد بصيغة JSON فقط."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=3000,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```json"):
        raw = raw[7:-3].strip()
    elif raw.startswith("```"):
        raw = raw[3:-3].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"رد الموديل مش JSON صحيح ({e}).\n"
            f"طول الرد: {len(raw)} حرف.\n"
            f"آخر 300 حرف من الرد (للتشخيص):\n{raw[-300:]}"
        )
