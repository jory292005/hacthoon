# -*- coding: utf-8 -*-
"""
app.py
======
الواجهة الكاملة لموقع "بَيِّن" — المساعد الذكي لتدقيق العقود.

يربط بين:
    - pdf_reader.py   (سحر)   : استخراج نص العقد من PDF
    - ai_engine.py    (جوري)  : تحليل العقد وإرجاع JSON للمخالفات
    - rules.py        (زينب)  : التحقق من صحة الـ JSON وتطبيعه + قواميس الترجمة
    - report_builder.py (زينب): توليد تقرير PDF عربي
    - database.py     : حسابات المستخدمين + حفظ التقارير (SQLite)
"""

import os
import re
import traceback
from datetime import datetime
from functools import wraps

from flask import (
    Flask, request, render_template, redirect, url_for,
    session, flash, send_from_directory, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

import database as db
from pdf_reader import extract_text_from_pdf
from ai_engine import audit_contract, MissingAPIKeyError
from rules import (
    validate_audit_json, normalize_audit_json, InvalidAuditDataError,
    STATUS_LABELS_AR, RISK_LABELS_AR, SEVERITY_LABELS_AR, CONTRACT_TYPE_LABELS_AR,
)
from report_builder import generate_report

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me-in-production")

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

db.init_db()


# ============================================================= أدوات مساعدة

def _safe_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name).strip() or "تقرير"
    return f"{name}_{int(datetime.utcnow().timestamp())}.pdf"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("الرجاء تسجيل الدخول أولاً للوصول لهذه الصفحة.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.utcnow().year,
        "status_labels": STATUS_LABELS_AR,
        "risk_labels": RISK_LABELS_AR,
        "severity_labels": SEVERITY_LABELS_AR,
        "contract_type_labels": CONTRACT_TYPE_LABELS_AR,
    }


def _show_splash_once():
    """تُعرض شاشة الافتتاح مرة واحدة فقط لكل جلسة متصفح (أول فتح للموقع)."""
    if session.get("splash_seen"):
        return False
    session["splash_seen"] = True
    return True


# ==================================================================== auth

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm") or ""

        if not full_name or not email or not password:
            flash("الرجاء تعبئة جميع الحقول المطلوبة.", "error")
        elif "@" not in email or "." not in email.split("@")[-1]:
            flash("صيغة البريد الإلكتروني غير صحيحة.", "error")
        elif len(password) < 6:
            flash("كلمة المرور يجب ألا تقل عن 6 أحرف.", "error")
        elif password != password_confirm:
            flash("كلمتا المرور غير متطابقتين.", "error")
        elif db.get_user_by_email(email):
            flash("هذا البريد الإلكتروني مسجل بالفعل. جرب تسجيل الدخول.", "error")
        else:
            try:
                user_id = db.create_user(full_name, email, generate_password_hash(password))
            except Exception:
                flash("تعذّر إنشاء الحساب حالياً بسبب خطأ فني. حاول مرة أخرى.", "error")
            else:
                session["user_id"] = user_id
                session["user_name"] = full_name
                flash(f"أهلاً بك {full_name}! تم إنشاء حسابك بنجاح.", "success")
                return redirect(url_for("dashboard"))

        return render_template(
            "signup.html", full_name=full_name, email=email,
            show_splash=_show_splash_once(),
        )

    return render_template("signup.html", show_splash=_show_splash_once())


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = db.get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("البريد الإلكتروني أو كلمة المرور غير صحيحة.", "error")
            return render_template("login.html", email=email, show_splash=_show_splash_once())

        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        flash(f"مرحباً بعودتك، {user['full_name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html", show_splash=_show_splash_once())


@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل خروجك بنجاح.", "success")
    return redirect(url_for("login"))


# ================================================================= dashboard

@app.route("/dashboard")
@login_required
def dashboard():
    reports = db.get_reports_for_user(session["user_id"])
    stats = db.get_dashboard_stats(session["user_id"])
    return render_template(
        "dashboard.html", reports=reports, stats=stats,
        show_splash=_show_splash_once(),
    )


# ==================================================================== audit

@app.route("/audit", methods=["GET", "POST"])
@login_required
def audit():
    if request.method == "GET":
        return render_template("audit.html", audit=None, show_splash=_show_splash_once())

    supplier_name = (request.form.get("supplier_name") or "").strip()
    uploaded_file = request.files.get("contract_file")

    if not supplier_name:
        flash("الرجاء إدخال اسم المورد.", "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)

    if not uploaded_file or uploaded_file.filename == "":
        flash("الرجاء رفع ملف العقد بصيغة PDF.", "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)

    if not uploaded_file.filename.lower().endswith(".pdf"):
        flash("صيغة الملف غير مدعومة. الرجاء رفع ملف PDF فقط.", "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)

    # 1) استخراج النص من PDF
    try:
        text = extract_text_from_pdf(uploaded_file.stream)
    except ValueError as e:
        flash(str(e), "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)
    except Exception:
        flash("تعذّرت قراءة ملف PDF. تأكد أن الملف غير تالف وحاول مرة أخرى.", "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)

    # 2) تشغيل محرك التدقيق (الذكاء الاصطناعي)
    try:
        audit_result = audit_contract(text=text, supplier_name=supplier_name)
    except MissingAPIKeyError as e:
        flash(str(e), "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)
    except Exception:
        flash("تعذّر إتمام عملية التدقيق حالياً. قد تكون هناك مشكلة في الاتصال بمحرك الذكاء الاصطناعي — حاول مرة أخرى بعد قليل.", "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)

    # 3) التحقق من صحة الناتج وتطبيعه
    try:
        validate_audit_json(audit_result)
        normalized = normalize_audit_json(audit_result)
    except InvalidAuditDataError:
        flash("رد محرك التدقيق كان غير مكتمل. الرجاء إعادة المحاولة.", "error")
        return render_template("audit.html", audit=None, supplier_name=supplier_name)

    # 4) توليد تقرير PDF (مُغلَّف بشكل منفصل — فشل هذه الخطوة لا يخفي نتيجة التدقيق)
    pdf_filename = None
    try:
        filename = _safe_filename(supplier_name)
        output_path = os.path.join(REPORTS_DIR, filename)
        generate_report(normalized, output_path)
        pdf_filename = filename
    except Exception:
        flash("تم التدقيق بنجاح، لكن تعذّر توليد ملف PDF للتقرير. النتيجة أدناه سليمة ومتاحة رغم ذلك.", "error")

    # 5) حفظ التقرير في حساب المستخدم
    try:
        report_id = db.save_report(session["user_id"], normalized, pdf_filename)
    except Exception:
        report_id = None
        flash("تم التدقيق، لكن تعذّر حفظ التقرير في حسابك.", "error")

    download_url = url_for("download_report", report_id=report_id) if (report_id and pdf_filename) else None

    return render_template(
        "audit.html", audit=normalized, supplier_name=supplier_name,
        download_url=download_url,
    )


# ============================================================ saved reports

@app.route("/report/<int:report_id>")
@login_required
def view_report(report_id):
    report = db.get_report(report_id, session["user_id"])
    if not report:
        abort(404)

    import json
    audit_data = json.loads(report["audit_json"])
    download_url = url_for("download_report", report_id=report["id"]) if report["pdf_filename"] else None

    return render_template(
        "report_view.html", report=report, audit=audit_data,
        download_url=download_url, show_splash=_show_splash_once(),
    )


@app.route("/report/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = db.get_report(report_id, session["user_id"])
    if not report or not report["pdf_filename"]:
        abort(404)
    return send_from_directory(REPORTS_DIR, report["pdf_filename"], as_attachment=True)


# =================================================================== errors

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", show_splash=False), 404


@app.errorhandler(500)
def server_error(e):
    traceback.print_exc()
    return render_template("500.html", show_splash=False), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
