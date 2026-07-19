# -*- coding: utf-8 -*-
"""
database.py
============
طبقة تخزين خفيفة (SQLite بدون أي مكتبة خارجية) للحسابات والتقارير المحفوظة.

الجداول:
    users   -> id, full_name, email, password_hash, created_at
    reports -> id, user_id, supplier_name, contract_type, overall_status,
               compliance_score, risk_level, violations_count, audit_json,
               pdf_filename, created_at
"""

import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_data.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            supplier_name TEXT NOT NULL,
            contract_type TEXT,
            overall_status TEXT,
            compliance_score INTEGER,
            risk_level TEXT,
            violations_count INTEGER,
            audit_json TEXT NOT NULL,
            pdf_filename TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- المستخدمون


def create_user(full_name, email, password_hash):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (full_name.strip(), email.strip().lower(), password_hash, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------- التقارير


def save_report(user_id, audit_json, pdf_filename):
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO reports
               (user_id, supplier_name, contract_type, overall_status, compliance_score,
                risk_level, violations_count, audit_json, pdf_filename, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                audit_json.get("supplier_name", "غير محدد"),
                audit_json.get("contract_type", "غير محدد"),
                audit_json.get("overall_status", "PARTIAL"),
                int(audit_json.get("compliance_score", 0) or 0),
                audit_json.get("risk_level", "MEDIUM"),
                len(audit_json.get("violations", []) or []),
                json.dumps(audit_json, ensure_ascii=False),
                pdf_filename,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_reports_for_user(user_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_report(report_id, user_id):
    """يرجع تقرير محدد بشرط أنه يخص نفس المستخدم (حماية IDOR)."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM reports WHERE id = ? AND user_id = ?", (report_id, user_id)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_dashboard_stats(user_id):
    reports = get_reports_for_user(user_id)
    total = len(reports)
    if total == 0:
        return {"total": 0, "avg_score": 0, "high_risk": 0, "passed": 0}

    avg_score = round(sum(r["compliance_score"] or 0 for r in reports) / total)
    high_risk = sum(1 for r in reports if r["risk_level"] in ("CRITICAL", "HIGH"))
    passed = sum(1 for r in reports if r["overall_status"] == "PASS")
    return {"total": total, "avg_score": avg_score, "high_risk": high_risk, "passed": passed}