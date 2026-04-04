import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

import stripe

from utils.customer_helpers import init_customers_db


CUSTOMERS_DB = "customers.db"
ACTIVE_STRIPE_STATUSES = {"active", "trialing", "past_due", "unpaid"}
IGNORED_NEW_CUSTOMER_STATUSES = {"incomplete_expired"}
DEFAULT_GA4_PROPERTY_ID = "513395528"
DEFAULT_YOUTUBE_CHANNEL_ID = "UC3t_dvpXmdwg79V7SwvpNJA"
SNAPSHOT_MANUAL_COLUMNS = {
    "tiktok_views": "INTEGER",
    "tiktok_followers": "INTEGER",
    "instagram_followers": "INTEGER",
    "facebook_page_followers": "INTEGER",
    "facebook_page_likes": "INTEGER",
    "facebook_groups_joined": "INTEGER",
}
SOCIAL_ACCOUNT_LINKS = {
    "tiktok": "https://www.tiktok.com/@minipass.me",
    "facebook": "https://www.facebook.com/profile.php?id=61578842160404",
    "instagram": "https://www.instagram.com/minipass.me/",
}
ANALYTICS_LINKS = {
    "tiktok": "https://www.tiktok.com/analytics",
    "meta_business": "https://business.facebook.com/latest/insights",
}
MANUAL_KPI_FIELDS = [
    {
        "key": "tiktok_views",
        "label": "TikTok views this week",
        "format": "int",
        "link": SOCIAL_ACCOUNT_LINKS["tiktok"],
        "link_label": "Open TikTok",
        "help": "Preferred: use TikTok analytics for this week's account views. Fallback: sum the views of videos published during this week only.",
        "analytics_link": ANALYTICS_LINKS["tiktok"],
        "analytics_label": "Open TikTok Analytics",
    },
    {
        "key": "tiktok_followers",
        "label": "TikTok followers",
        "format": "int",
        "link": SOCIAL_ACCOUNT_LINKS["tiktok"],
        "link_label": "Open TikTok",
        "help": "Current TikTok followers total from TikTok analytics or the profile header.",
        "analytics_link": ANALYTICS_LINKS["tiktok"],
        "analytics_label": "Open TikTok Analytics",
    },
    {
        "key": "instagram_followers",
        "label": "Instagram followers",
        "format": "int",
        "link": SOCIAL_ACCOUNT_LINKS["instagram"],
        "link_label": "Open Instagram",
        "help": "Use Instagram Insights or Meta Business Suite. Public profile totals are fine if Insights are not available.",
        "analytics_link": ANALYTICS_LINKS["meta_business"],
        "analytics_label": "Open Meta Insights",
    },
    {
        "key": "facebook_page_followers",
        "label": "Facebook page followers",
        "format": "int",
        "link": SOCIAL_ACCOUNT_LINKS["facebook"],
        "link_label": "Open Facebook page",
        "help": "Use Meta Business Suite Insights for weekly page metrics and follower totals.",
        "analytics_link": ANALYTICS_LINKS["meta_business"],
        "analytics_label": "Open Meta Insights",
    },
    {
        "key": "facebook_page_likes",
        "label": "Facebook page likes",
        "format": "int",
        "link": SOCIAL_ACCOUNT_LINKS["facebook"],
        "link_label": "Open Facebook page",
        "help": "Use Meta Business Suite Insights or the page profile to capture the current likes total.",
        "analytics_link": ANALYTICS_LINKS["meta_business"],
        "analytics_label": "Open Meta Insights",
    },
]
PLAN_KPI_TARGETS = [
    {
        "category": "Site",
        "metric": "Unique visitors / week",
        "key": "site_visitors",
        "targets": {"M1": 200, "M3": 500, "M6": 1000},
        "format": "int",
        "source": "GA4",
        "actual_period": "Current week",
    },
    {
        "category": "Email",
        "metric": "Subscribers total",
        "key": "email_subscribers",
        "targets": {"M1": 25, "M3": 100, "M6": 300},
        "format": "int",
        "source": "Local leads DB",
        "actual_period": "Current total",
    },
    {
        "category": "Social",
        "metric": "TikTok views this week",
        "key": "tiktok_views",
        "targets": {"M1": 1000, "M3": 5000, "M6": 15000},
        "format": "int",
        "source": "Manual entry",
        "actual_period": "This week snapshot",
    },
    {
        "category": "Social",
        "metric": "TikTok followers",
        "key": "tiktok_followers",
        "targets": {"M1": None, "M3": None, "M6": None},
        "format": "int",
        "source": "Manual entry",
        "actual_period": "Current total",
    },
    {
        "category": "Social",
        "metric": "YouTube subscribers",
        "key": "youtube_subscribers",
        "targets": {"M1": 10, "M3": 50, "M6": 150},
        "format": "int",
        "source": "YouTube Data API",
        "actual_period": "Current total",
    },
    {
        "category": "Social",
        "metric": "Instagram followers",
        "key": "instagram_followers",
        "targets": {"M1": None, "M3": None, "M6": None},
        "format": "int",
        "source": "Manual entry",
        "actual_period": "Current total",
    },
    {
        "category": "Social",
        "metric": "Facebook page followers",
        "key": "facebook_page_followers",
        "targets": {"M1": None, "M3": None, "M6": None},
        "format": "int",
        "source": "Manual entry",
        "actual_period": "Current total",
    },
    {
        "category": "Social",
        "metric": "Facebook page likes",
        "key": "facebook_page_likes",
        "targets": {"M1": None, "M3": None, "M6": None},
        "format": "int",
        "source": "Manual entry",
        "actual_period": "Current total",
    },
    {
        "category": "Community",
        "metric": "Facebook groups joined",
        "key": "facebook_groups_joined",
        "targets": {"M1": 10, "M3": 75, "M6": 200},
        "format": "int",
        "source": "Manual URL list",
        "actual_period": "Current total",
    },
    {
        "category": "Revenue",
        "metric": "New customers / month",
        "key": "new_customers",
        "targets": {"M1": 3, "M3": 5, "M6": 8},
        "format": "int",
        "source": "Stripe",
        "actual_period": "Month to date",
    },
    {
        "category": "Revenue",
        "metric": "MRR",
        "key": "mrr",
        "targets": {"M1": 105, "M3": 294, "M6": 672},
        "format": "currency",
        "source": "Stripe",
        "actual_period": "Current month-end estimate",
    },
    {
        "category": "Revenue",
        "metric": "Churn rate",
        "key": "churn_rate",
        "targets": {"M1": 5, "M3": 5, "M6": 5},
        "format": "percent_threshold",
        "source": "Stripe",
        "actual_period": "Month to date",
    },
]


def init_kpi_snapshots_db(db_path=CUSTOMERS_DB):
    init_customers_db()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kpi_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                period_key TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                snapshot_date TEXT NOT NULL,
                site_visitors INTEGER,
                email_subscribers INTEGER,
                new_customers INTEGER,
                mrr REAL,
                churn_rate REAL,
                youtube_views INTEGER,
                youtube_subscribers INTEGER,
                source_status TEXT NOT NULL DEFAULT '{}',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(period, period_key)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'lead_magnet'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_kpi_values (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS facebook_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _ensure_snapshot_columns(conn)
        conn.commit()


def capture_kpi_snapshots(db_path=CUSTOMERS_DB, today=None):
    init_kpi_snapshots_db(db_path)
    reference_day = today or datetime.now(timezone.utc).date()
    results = {}
    for period in ("weekly", "monthly"):
        snapshot = collect_kpi_snapshot(period, db_path=db_path, today=reference_day)
        save_kpi_snapshot(snapshot, db_path=db_path)
        results[period] = snapshot
    return results


def collect_kpi_snapshot(period, db_path=CUSTOMERS_DB, today=None):
    if period not in {"weekly", "monthly"}:
        raise ValueError(f"Unsupported KPI period: {period}")

    reference_day = today or datetime.now(timezone.utc).date()
    start_day, end_day, period_key = _get_period_window(period, reference_day)
    source_status = {}

    snapshot = {
        "period": period,
        "period_key": period_key,
        "period_start": start_day.isoformat(),
        "period_end": end_day.isoformat(),
        "snapshot_date": datetime.now(timezone.utc).isoformat(),
        "site_visitors": None,
        "email_subscribers": None,
        "new_customers": None,
        "mrr": None,
        "churn_rate": None,
        "youtube_views": None,
        "youtube_subscribers": None,
        "tiktok_views": None,
        "tiktok_followers": None,
        "instagram_followers": None,
        "facebook_page_followers": None,
        "facebook_page_likes": None,
        "facebook_groups_joined": None,
        "source_status": source_status,
        "notes": None,
    }

    manual_values = get_manual_kpi_values(db_path=db_path)
    facebook_groups = get_facebook_groups(db_path=db_path)
    snapshot["tiktok_views"] = manual_int_value(manual_values, "tiktok_views")
    snapshot["tiktok_followers"] = manual_int_value(manual_values, "tiktok_followers")
    snapshot["instagram_followers"] = manual_int_value(manual_values, "instagram_followers")
    snapshot["facebook_page_followers"] = manual_int_value(manual_values, "facebook_page_followers")
    snapshot["facebook_page_likes"] = manual_int_value(manual_values, "facebook_page_likes")
    snapshot["facebook_groups_joined"] = len(facebook_groups)

    try:
        snapshot["email_subscribers"] = get_email_subscriber_count(db_path=db_path)
        source_status["local_db"] = _status(True, f"{snapshot['email_subscribers']} subscriber(s) in leads")
    except Exception as exc:
        source_status["local_db"] = _status(False, str(exc))

    try:
        snapshot["site_visitors"] = get_ga4_active_users(start_day, end_day)
        source_status["ga4"] = _status(True, f"{snapshot['site_visitors']} active users")
    except Exception as exc:
        source_status["ga4"] = _status(False, str(exc))

    try:
        stripe_metrics = get_stripe_metrics(start_day, end_day, include_churn=(period == "monthly"))
        snapshot["new_customers"] = stripe_metrics["new_customers"]
        snapshot["mrr"] = stripe_metrics["mrr"]
        snapshot["churn_rate"] = stripe_metrics["churn_rate"]
        stripe_detail = f"{snapshot['new_customers']} new / ${snapshot['mrr']:.2f} MRR"
        if snapshot["churn_rate"] is not None:
            stripe_detail += f" / {snapshot['churn_rate']:.2f}% churn"
        source_status["stripe"] = _status(True, stripe_detail)
    except Exception as exc:
        source_status["stripe"] = _status(False, str(exc))

    try:
        youtube_metrics = get_youtube_channel_stats()
        snapshot["youtube_views"] = youtube_metrics["view_count"]
        snapshot["youtube_subscribers"] = youtube_metrics["subscriber_count"]
        source_status["youtube"] = _status(
            True,
            f"{snapshot['youtube_subscribers']} subscribers / {snapshot['youtube_views']} views",
        )
    except Exception as exc:
        source_status["youtube"] = _status(False, str(exc))

    return snapshot


def save_kpi_snapshot(snapshot, db_path=CUSTOMERS_DB):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO kpi_snapshots (
                period, period_key, period_start, period_end, snapshot_date,
                site_visitors, email_subscribers, new_customers, mrr, churn_rate,
                youtube_views, youtube_subscribers,
                tiktok_views, tiktok_followers, instagram_followers,
                facebook_page_followers, facebook_page_likes, facebook_groups_joined,
                source_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(period, period_key) DO UPDATE SET
                period_start = excluded.period_start,
                period_end = excluded.period_end,
                snapshot_date = excluded.snapshot_date,
                site_visitors = excluded.site_visitors,
                email_subscribers = excluded.email_subscribers,
                new_customers = excluded.new_customers,
                mrr = excluded.mrr,
                churn_rate = excluded.churn_rate,
                youtube_views = excluded.youtube_views,
                youtube_subscribers = excluded.youtube_subscribers,
                tiktok_views = excluded.tiktok_views,
                tiktok_followers = excluded.tiktok_followers,
                instagram_followers = excluded.instagram_followers,
                facebook_page_followers = excluded.facebook_page_followers,
                facebook_page_likes = excluded.facebook_page_likes,
                facebook_groups_joined = excluded.facebook_groups_joined,
                source_status = excluded.source_status,
                notes = excluded.notes
            """,
            (
                snapshot["period"],
                snapshot["period_key"],
                snapshot["period_start"],
                snapshot["period_end"],
                snapshot["snapshot_date"],
                snapshot["site_visitors"],
                snapshot["email_subscribers"],
                snapshot["new_customers"],
                snapshot["mrr"],
                snapshot["churn_rate"],
                snapshot["youtube_views"],
                snapshot["youtube_subscribers"],
                snapshot["tiktok_views"],
                snapshot["tiktok_followers"],
                snapshot["instagram_followers"],
                snapshot["facebook_page_followers"],
                snapshot["facebook_page_likes"],
                snapshot["facebook_groups_joined"],
                json.dumps(snapshot["source_status"]),
                snapshot.get("notes"),
            ),
        )
        conn.commit()


def get_kpi_dashboard_data(db_path=CUSTOMERS_DB, today=None):
    init_kpi_snapshots_db(db_path)
    reference_day = today or datetime.now(timezone.utc).date()
    latest_weekly = collect_kpi_snapshot("weekly", db_path=db_path, today=reference_day)
    latest_monthly = collect_kpi_snapshot("monthly", db_path=db_path, today=reference_day)
    weekly_history = get_live_weekly_history(reference_day, weeks=8, db_path=db_path)
    monthly_history = get_live_monthly_history(reference_day, months=6, db_path=db_path)
    technical_status = latest_monthly.get("source_status") or latest_weekly.get("source_status")
    manual_values = get_manual_kpi_values(db_path=db_path)
    facebook_groups = get_facebook_groups(db_path=db_path)

    return {
        "latest_weekly": latest_weekly,
        "latest_monthly": latest_monthly,
        "weekly_history": weekly_history,
        "monthly_history": monthly_history,
        "plan_rows": build_plan_kpi_rows(latest_weekly, latest_monthly, manual_values, facebook_groups),
        "technical_status": technical_status,
        "config_status": get_kpi_config_status(),
        "stripe_mode": get_stripe_mode(),
        "manual_form": build_manual_kpi_form(manual_values),
        "facebook_groups": facebook_groups,
    }


def build_plan_kpi_rows(latest_weekly, latest_monthly, manual_values, facebook_groups):
    current_values = {
        "site_visitors": latest_weekly.get("site_visitors") if latest_weekly else None,
        "email_subscribers": latest_monthly.get("email_subscribers") if latest_monthly else None,
        "tiktok_views": manual_int_value(manual_values, "tiktok_views"),
        "tiktok_followers": manual_int_value(manual_values, "tiktok_followers"),
        "youtube_subscribers": latest_monthly.get("youtube_subscribers") if latest_monthly else None,
        "instagram_followers": manual_int_value(manual_values, "instagram_followers"),
        "facebook_page_followers": manual_int_value(manual_values, "facebook_page_followers"),
        "facebook_page_likes": manual_int_value(manual_values, "facebook_page_likes"),
        "facebook_groups_joined": len(facebook_groups),
        "new_customers": latest_monthly.get("new_customers") if latest_monthly else None,
        "mrr": latest_monthly.get("mrr") if latest_monthly else None,
        "churn_rate": latest_monthly.get("churn_rate") if latest_monthly else None,
    }

    rows = []
    for row in PLAN_KPI_TARGETS:
        actual_value = current_values.get(row["key"])
        rows.append({
            "category": row["category"],
            "metric": row["metric"],
            "actual_value": actual_value,
            "actual_display": format_metric_value(actual_value, row["format"]),
            "targets": {
                milestone: format_metric_value(value, row["format"], target=True)
                for milestone, value in row["targets"].items()
            },
            "source": row["source"],
            "actual_period": row["actual_period"],
            "available": actual_value is not None,
            "pending_label": "Manual update needed" if row["source"] in {"Manual entry", "Manual URL list"} else "Pending API setup",
        })
    return rows


def get_live_weekly_history(reference_day, weeks=8, db_path=CUSTOMERS_DB):
    current_week_start = reference_day - timedelta(days=reference_day.weekday())
    history = []
    for offset in range(weeks - 1, -1, -1):
        start_day = current_week_start - timedelta(days=7 * offset)
        end_day = min(start_day + timedelta(days=6), reference_day)
        row = {
            "period_label": f"{start_day.isoformat()} to {end_day.isoformat()}",
            "period_start": start_day.isoformat(),
            "period_end": end_day.isoformat(),
            "site_visitors": None,
            "new_customers": None,
        }
        try:
            row["site_visitors"] = get_ga4_active_users(start_day, end_day)
        except Exception:
            row["site_visitors"] = None
        try:
            row["new_customers"] = get_stripe_metrics(start_day, end_day)["new_customers"]
        except Exception:
            row["new_customers"] = None
        history.append(row)
    return history


def get_live_monthly_history(reference_day, months=6, db_path=CUSTOMERS_DB):
    history = []
    month_anchor = reference_day.replace(day=1)
    for offset in range(months - 1, -1, -1):
        month_start = _month_start(month_anchor, -offset)
        month_end = _month_end(month_start)
        end_day = min(month_end, reference_day) if month_start.year == reference_day.year and month_start.month == reference_day.month else month_end
        stripe_metrics = {"new_customers": None, "mrr": None, "churn_rate": None}

        try:
            stripe_metrics = get_stripe_metrics(month_start, end_day, include_churn=True, as_of_day=end_day)
        except Exception:
            pass

        try:
            site_visitors = get_ga4_active_users(month_start, end_day)
        except Exception:
            site_visitors = None

        history.append({
            "period_key": month_start.strftime("%Y-%m"),
            "period_start": month_start.isoformat(),
            "period_end": end_day.isoformat(),
            "site_visitors": site_visitors,
            "email_subscribers": get_email_subscriber_count(db_path=db_path, as_of_day=end_day),
            "new_customers": stripe_metrics["new_customers"],
            "mrr": stripe_metrics["mrr"],
            "churn_rate": stripe_metrics["churn_rate"],
            "youtube_subscribers": _youtube_snapshot_value("youtube_subscribers", month_start.strftime("%Y-%m"), db_path=db_path),
            "youtube_views": _youtube_snapshot_value("youtube_views", month_start.strftime("%Y-%m"), db_path=db_path),
            "tiktok_views": _snapshot_value("monthly", month_start.strftime("%Y-%m"), "tiktok_views", db_path=db_path),
            "instagram_followers": _snapshot_value("monthly", month_start.strftime("%Y-%m"), "instagram_followers", db_path=db_path),
            "facebook_page_followers": _snapshot_value("monthly", month_start.strftime("%Y-%m"), "facebook_page_followers", db_path=db_path),
            "facebook_groups_joined": _snapshot_value("monthly", month_start.strftime("%Y-%m"), "facebook_groups_joined", db_path=db_path),
        })
    return history


def get_manual_kpi_values(db_path=CUSTOMERS_DB):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT key, value, updated_at FROM manual_kpi_values ORDER BY key"
        ).fetchall()
    return {row["key"]: {"value": row["value"], "updated_at": row["updated_at"]} for row in rows}


def build_manual_kpi_form(manual_values):
    fields = []
    for field in MANUAL_KPI_FIELDS:
        current = manual_values.get(field["key"], {})
        fields.append({
            **field,
            "value": current.get("value", ""),
            "updated_at": current.get("updated_at"),
        })
    return fields


def save_manual_kpi_form(form_data, db_path=CUSTOMERS_DB):
    init_kpi_snapshots_db(db_path)
    with sqlite3.connect(db_path) as conn:
        for field in MANUAL_KPI_FIELDS:
            raw_value = (form_data.get(field["key"]) or "").strip()
            if raw_value:
                normalized = str(int(raw_value.replace(",", "")))
                conn.execute(
                    """
                    INSERT INTO manual_kpi_values (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (field["key"], normalized),
                )
            else:
                conn.execute("DELETE FROM manual_kpi_values WHERE key = ?", (field["key"],))

        urls = []
        for line in (form_data.get("facebook_groups_text") or "").splitlines():
            normalized = line.strip()
            if normalized and normalized not in urls:
                urls.append(normalized)

        conn.execute("DELETE FROM facebook_groups")
        for url in urls:
            conn.execute("INSERT INTO facebook_groups (url) VALUES (?)", (url,))
        conn.commit()


def get_facebook_groups(db_path=CUSTOMERS_DB):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, url, created_at FROM facebook_groups ORDER BY created_at ASC, id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_kpi_history(period, limit=8, db_path=CUSTOMERS_DB):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM kpi_snapshots
            WHERE period = ?
            ORDER BY period_end DESC, id DESC
            LIMIT ?
            """,
            (period, limit),
        ).fetchall()
    snapshots = [_row_to_snapshot(row) for row in rows]
    snapshots.reverse()
    return snapshots


def get_kpi_config_status():
    ga4_json_path = _get_ga4_credentials_path()
    return {
        "ga4": {
            "configured": bool(_get_ga4_property_id()) and bool(ga4_json_path and os.path.exists(ga4_json_path)),
            "detail": ga4_json_path if ga4_json_path else "Set GA4_SERVICE_ACCOUNT_JSON or add secrets/ga4-service.json",
        },
        "stripe": {
            "configured": bool(os.getenv("STRIPE_SECRET_KEY")),
            "detail": "STRIPE_SECRET_KEY" if os.getenv("STRIPE_SECRET_KEY") else "Missing STRIPE_SECRET_KEY",
        },
        "youtube": {
            "configured": bool(os.getenv("YOUTUBE_API_KEY")) and bool(_get_youtube_channel_id()),
            "detail": "YOUTUBE_API_KEY" if os.getenv("YOUTUBE_API_KEY") else "Set YOUTUBE_API_KEY",
        },
        "local_db": {
            "configured": True,
            "detail": db_path_label(db_path=CUSTOMERS_DB),
        },
    }


def get_email_subscriber_count(db_path=CUSTOMERS_DB, as_of_day=None):
    with sqlite3.connect(db_path) as conn:
        if as_of_day:
            row = conn.execute(
                "SELECT COUNT(DISTINCT LOWER(email)) FROM leads WHERE DATE(created_at) <= DATE(?)",
                (as_of_day.isoformat(),),
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(DISTINCT LOWER(email)) FROM leads").fetchone()
        return row[0] or 0


def get_ga4_active_users(start_day, end_day):
    property_id = _get_ga4_property_id()
    credentials_path = _get_ga4_credentials_path()
    if not property_id:
        raise RuntimeError("Missing GA4_PROPERTY_ID")
    if not credentials_path or not os.path.exists(credentials_path):
        raise RuntimeError("Missing GA4 service account JSON")

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
        from google.oauth2 import service_account
    except ImportError as exc:
        raise RuntimeError("Install google-analytics-data to read GA4 metrics") from exc

    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    client = BetaAnalyticsDataClient(credentials=credentials)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date=start_day.isoformat(), end_date=end_day.isoformat())],
    )
    response = client.run_report(request)
    if not response.rows:
        return 0
    return int(response.rows[0].metric_values[0].value)


def get_youtube_channel_stats():
    api_key = os.getenv("YOUTUBE_API_KEY")
    channel_id = _get_youtube_channel_id()
    if not api_key or not channel_id:
        raise RuntimeError("Missing YOUTUBE_API_KEY or YOUTUBE_CHANNEL_ID")

    query = urlencode({"part": "statistics", "id": channel_id, "key": api_key})
    url = f"https://www.googleapis.com/youtube/v3/channels?{query}"
    with urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    items = payload.get("items") or []
    if not items:
        raise RuntimeError("YouTube channel not found or API access denied")

    stats = items[0].get("statistics") or {}
    return {
        "view_count": int(stats.get("viewCount", 0)),
        "subscriber_count": int(stats.get("subscriberCount", 0)),
    }


def get_stripe_metrics(start_day, end_day, include_churn=False, as_of_day=None):
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("Missing STRIPE_SECRET_KEY")

    stripe.api_key = secret_key
    as_of_day = as_of_day or end_day
    new_customer_ids = set()
    active_at_period_start = 0
    canceled_in_period = 0
    mrr_cents = 0.0

    for subscription in stripe.Subscription.list(status="all", limit=100).auto_paging_iter():
        created_on = _stripe_timestamp_to_date(subscription.get("created"))
        canceled_on = _stripe_timestamp_to_date(subscription.get("canceled_at"))
        status = subscription.get("status")

        if _subscription_active_on_date(created_on, canceled_on, status, as_of_day):
            mrr_cents += subscription_monthly_value_cents(subscription)

        if created_on and start_day <= created_on <= end_day and status not in IGNORED_NEW_CUSTOMER_STATUSES:
            customer_id = subscription.get("customer")
            if customer_id:
                new_customer_ids.add(str(customer_id))

        if include_churn:
            if _subscription_active_at_period_start(created_on, canceled_on, status, start_day):
                active_at_period_start += 1
            if canceled_on and start_day <= canceled_on <= end_day:
                canceled_in_period += 1

    churn_rate = None
    if include_churn and active_at_period_start > 0:
        churn_rate = round((canceled_in_period / active_at_period_start) * 100, 2)

    return {
        "new_customers": len(new_customer_ids),
        "mrr": round(mrr_cents / 100, 2),
        "churn_rate": churn_rate,
    }


def subscription_monthly_value_cents(subscription):
    monthly_cents = 0.0
    for item in (subscription.get("items") or {}).get("data", []):
        price = item.get("price") or {}
        recurring = price.get("recurring") or {}
        unit_amount = price.get("unit_amount") or 0
        quantity = item.get("quantity") or 1
        interval = recurring.get("interval")
        interval_count = recurring.get("interval_count") or 1
        total_cents = unit_amount * quantity

        if interval == "month":
            monthly_cents += total_cents / interval_count
        elif interval == "year":
            monthly_cents += total_cents / (12 * interval_count)
        elif interval == "week":
            monthly_cents += total_cents * 52 / (12 * interval_count)
        elif interval == "day":
            monthly_cents += total_cents * 30 / interval_count
        else:
            monthly_cents += total_cents
    return monthly_cents


def db_path_label(db_path=CUSTOMERS_DB):
    return os.path.abspath(db_path)


def format_metric_value(value, format_type, target=False):
    if value is None:
        return "Pending" if not target else "-"
    if format_type == "currency":
        return f"${value:,.0f}" if target else f"${value:,.2f}"
    if format_type == "percent_threshold":
        return f"<{value:.0f}%" if target else f"{value:.2f}%"
    return f"{int(value):,}"


def get_stripe_mode():
    secret_key = os.getenv("STRIPE_SECRET_KEY", "")
    if secret_key.startswith("sk_test_"):
        return "test"
    if secret_key.startswith("sk_live_"):
        return "live"
    return "unknown"


def _get_ga4_credentials_path():
    configured_path = os.getenv("GA4_SERVICE_ACCOUNT_JSON")
    if configured_path:
        return configured_path

    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "secrets", "ga4-service.json")
    if os.path.exists(default_path):
        return default_path
    return None


def _get_ga4_property_id():
    return os.getenv("GA4_PROPERTY_ID", DEFAULT_GA4_PROPERTY_ID)


def _get_youtube_channel_id():
    return os.getenv("YOUTUBE_CHANNEL_ID", DEFAULT_YOUTUBE_CHANNEL_ID)


def _get_period_window(period, today):
    if period == "weekly":
        start_day = today - timedelta(days=today.weekday())
        period_key = f"{today.isocalendar().year}-W{today.isocalendar().week:02d}"
        return start_day, today, period_key

    start_day = today.replace(day=1)
    return start_day, today, today.strftime("%Y-%m")


def _row_to_snapshot(row):
    snapshot = dict(row)
    snapshot["source_status"] = json.loads(snapshot.get("source_status") or "{}")
    return snapshot


def _status(ok, detail):
    return {"ok": ok, "detail": detail}


def _stripe_timestamp_to_date(timestamp):
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()


def _subscription_active_on_date(created_on, canceled_on, status, day):
    if status in IGNORED_NEW_CUSTOMER_STATUSES:
        return False
    if not created_on or created_on > day:
        return False
    if canceled_on and canceled_on <= day:
        return False
    return True


def _subscription_active_at_period_start(created_on, canceled_on, status, start_day):
    if status in IGNORED_NEW_CUSTOMER_STATUSES:
        return False
    if not created_on or created_on >= start_day:
        return False
    if canceled_on and canceled_on < start_day:
        return False
    return True


def _month_start(anchor_day, month_delta):
    year = anchor_day.year + ((anchor_day.month - 1 + month_delta) // 12)
    month = ((anchor_day.month - 1 + month_delta) % 12) + 1
    return date(year, month, 1)


def _month_end(month_start):
    next_month = _month_start(month_start, 1)
    return next_month - timedelta(days=1)


def _youtube_snapshot_value(column_name, period_key, db_path=CUSTOMERS_DB):
    return _snapshot_value("monthly", period_key, column_name, db_path=db_path)


def _snapshot_value(period, period_key, column_name, db_path=CUSTOMERS_DB):
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            f"SELECT {column_name} FROM kpi_snapshots WHERE period=? AND period_key=? ORDER BY id DESC LIMIT 1",
            (period, period_key),
        ).fetchone()
    return row[0] if row else None


def _ensure_snapshot_columns(conn):
    existing_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(kpi_snapshots)").fetchall()
    }
    for column_name, column_type in SNAPSHOT_MANUAL_COLUMNS.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE kpi_snapshots ADD COLUMN {column_name} {column_type}")


def manual_int_value(manual_values, key):
    raw_value = (manual_values.get(key) or {}).get("value")
    if raw_value in (None, ""):
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None
