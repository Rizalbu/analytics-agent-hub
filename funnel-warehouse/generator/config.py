"""Static configuration for the FitFlow synthetic data generator.

Everything here is fictional. Studios, cities, plans and rates are invented;
the 'mess' settings deliberately inject real-world data-quality problems so
the dbt staging layer has something honest to clean.
"""

from datetime import date

START_DATE = date(2025, 1, 1)

# studio_code -> (studio_name, city, capacity_tier, header_variant)
# header_variant simulates per-studio spreadsheet drift (A/B/C).
STUDIOS = {
    "S01": ("FitFlow Arden Central", "Arden", "large", "A"),
    "S02": ("FitFlow Arden North", "Arden", "medium", "A"),
    "S03": ("FitFlow Arden Park", "Arden", "small", "B"),
    "S04": ("FitFlow Arden East", "Arden", "medium", "C"),
    "S05": ("FitFlow Brightwater Bay", "Brightwater", "large", "A"),
    "S06": ("FitFlow Brightwater Hills", "Brightwater", "medium", "B"),
    "S07": ("FitFlow Brightwater Quay", "Brightwater", "small", "B"),
    "S08": ("FitFlow Brightwater West", "Brightwater", "medium", "C"),
    "S09": ("FitFlow Crestline Square", "Crestline", "large", "A"),
    "S10": ("FitFlow Crestline Valley", "Crestline", "medium", "B"),
    "S11": ("FitFlow Crestline Ridge", "Crestline", "small", "C"),
    "S12": ("FitFlow Crestline Gate", "Crestline", "medium", "C"),
}

CAPACITY_LEAD_BASE = {"large": 16, "medium": 10, "small": 6}  # avg leads/day

# raw channel label -> (daily mix weight, is_paid)
# Multiple raw labels map to the same conformed channel (see reference/channel_map.csv)
CHANNELS = {
    "FB Ads": (0.16, True),
    "facebook": (0.06, True),
    "Instagram Ads": (0.14, True),
    "IG": (0.05, True),
    "google search": (0.10, True),
    "Google Ads": (0.07, True),
    "tiktok ads": (0.10, True),
    "TikTok": (0.04, True),
    "referral": (0.08, False),
    "Member Referral": (0.04, False),
    "walk-in": (0.07, False),
    "Walk In": (0.03, False),
    "partner gym": (0.04, False),
    "Partner": (0.02, False),
}

# funnel stage probabilities (base)
P_QUALIFIED = 0.55      # lead -> qualified
P_BOOKED = 0.62         # qualified -> booked trial
P_CANCELLED = 0.08      # booked -> cancelled before trial
P_PURCHASE = 0.33       # attended visit -> membership purchase

# attendance depends on lead time (days between lead creation and trial):
# longer wait -> more no-shows. (lead_time_days, p_attend)
ATTEND_BY_LEADTIME = [(2, 0.88), (4, 0.80), (7, 0.72), (99, 0.58)]

# channel-group quality multipliers on P_QUALIFIED
GROUP_QUALITY = {
    "paid_social": 1.00,
    "paid_search": 1.15,
    "referral": 1.35,
    "organic": 1.20,
    "partner": 0.90,
}

# scripted anomaly: Crestline paid-social lead quality collapses from Sep 2025.
# This is the story the dashboard should surface (masked by blended averages).
ANOMALY = {
    "city": "Crestline",
    "channel_group": "paid_social",
    "from": date(2025, 9, 1),
    "qualified_multiplier": 0.55,
}

# membership plans: weights for purchase choice
PLAN_WEIGHTS = {"STARTER": 0.35, "FLEX8": 0.30, "UNLIMITED": 0.25, "ANNUAL": 0.10}

# discount applied to list price at sale time (sampled)
DISCOUNTS = [0.0, 0.0, 0.0, 0.0, 0.05, 0.10]

# paid channels: cost per lead range (fictional Rp)
CPL_RANGE = (15_000, 45_000)

# mess injection
DUP_RATE = {"leads": 0.015, "bookings": 0.012, "visits": 0.010, "sales": 0.008}
SPEND_AS_TEXT_RATE = 0.15   # "Rp 1.250.000" instead of 1250000
ATTENDED_TOKENS_TRUE = ["Y", "yes", "1", "TRUE", "y"]
ATTENDED_TOKENS_FALSE = ["N", "no", "0", "FALSE", "n"]

# per-variant leads headers (the drift the loader must normalize)
LEADS_HEADERS = {
    "A": ["lead_id", "studio_code", "channel", "created_at", "full_name", "phone", "status"],
    "B": ["LeadID", "Studio", "Channel Name", "Created Date", "Name", "Phone Number", "Status"],
    "C": ["id_lead", "kode_studio", "kanal", "tanggal_dibuat", "nama", "telepon", "status"],
}
# per-variant date rendering for leads.created_at
DATE_FMT = {"A": "%Y-%m-%d", "B": "%d/%m/%Y", "C": "%d-%b-%Y"}
