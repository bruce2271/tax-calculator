import json
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from calculators.form_1120 import calculate_1120, calc_drd_246b

st.set_page_config(
    page_title="Form 1120 Tax Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Appearance ─────────────────────────────────────────────────────────────────
# Editable from the sidebar. Read here, before the stylesheet is injected, because the
# CSS is written once at the top of the run; the widgets that set these render later in
# the sidebar and their values are already in session_state by then.
# Each area has its own colour so one region can be adjusted without repainting the
# rest. THEME_AREAS drives both the stylesheet variables and the sidebar controls.
THEME_AREAS = [
    ("Text", [
        ("theme_heading", "--c-heading", "#1B3A6B", "Headings"),
        ("theme_body", "--c-body", "#1A202C", "Body text"),
        ("theme_label", "--c-label", "#1B3A6B", "Input labels"),
    ]),
    ("Law reference boxes", [
        ("theme_law_text", "--c-law-text", "#2C5282", "Text"),
        ("theme_law_bg", "--c-law-bg", "#EBF4FF", "Background"),
    ]),
    ("Tables", [
        ("theme_table_text", "--c-table-text", "#1A202C", "Body text"),
        ("theme_th_text", "--c-th-text", "#1B3A6B", "Header text"),
        ("theme_th_bg", "--c-th-bg", "#EBF4FF", "Header background"),
    ]),
    ("Figures", [
        ("theme_metric_lbl", "--c-metric-lbl", "#35435C", "Metric label"),
        ("theme_metric_val", "--c-metric-val", "#1B3A6B", "Metric value"),
    ]),
    ("Emphasis", [
        ("theme_rule", "--c-rule", "#C53030", "Formulas and special rules"),
    ]),
]
THEME_DEFAULTS = {
    "theme_font": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "theme_size": 15,
}
for _area, _items in THEME_AREAS:
    for _key, _var, _default, _label in _items:
        THEME_DEFAULTS[_key] = _default

_t = {k: st.session_state.get(k, v) for k, v in THEME_DEFAULTS.items()}
_theme_vars = ":root{" + f"--app-font:{_t['theme_font']};--app-size:{_t['theme_size']}px;" + "".join(
    f"{v}:{_t[k]};" for _a, _items in THEME_AREAS for k, v, _d, _l in _items
) + "}"

# ── Custom CSS — injected directly into parent document head via iframe ─────────
# (st.markdown <style> gets overridden by Streamlit's Emotion CSS-in-JS;
#  parent.document.head injection wins because it runs after component render)
components.html("""
<script>
(function() {
    var el = parent.document.getElementById('__app-styles');
    if (!el) {
        el = parent.document.createElement('style');
        el.id = '__app-styles';
        parent.document.head.appendChild(el);
    }
    el.textContent = `""" + _theme_vars + """
    .stApp { background-color: #F7F9FC; }
    [data-testid="stSidebar"] { background-color: #1B3A6B; }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"] {
        --text-color: #E8EFF8; --secondary-text-color: #C8D8EE;
        --body-text-color: #E8EFF8; color: #E8EFF8 !important;
    }
    html body [data-testid="stSidebar"] p,
    html body [data-testid="stSidebar"] span,
    html body [data-testid="stSidebar"] div,
    html body [data-testid="stSidebar"] label,
    html body [data-testid="stSidebar"] h1,
    html body [data-testid="stSidebar"] h2,
    html body [data-testid="stSidebar"] h3,
    html body [data-testid="stSidebar"] h4,
    html body [data-testid="stSidebar"] small,
    html body [data-testid="stSidebar"] strong,
    html body [data-testid="stSidebar"] em,
    html body [data-testid="stSidebar"] a,
    html body [data-testid="stSidebar"] button,
    html body [data-testid="stSidebar"] input { color: #E8EFF8 !important; -webkit-text-fill-color: #E8EFF8 !important; }
    html body [data-testid="stSidebar"] [data-baseweb="radio"] label,
    html body [data-testid="stSidebar"] [data-baseweb="radio"] span,
    html body [data-testid="stSidebar"] [data-baseweb="select"] span,
    html body [data-testid="stSidebar"] [data-baseweb="input"] input,
    html body [data-testid="stSidebar"] [data-baseweb="input"] div { color: #E8EFF8 !important; -webkit-text-fill-color: #E8EFF8 !important; }
    html body [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    html body [data-testid="stSidebar"] [data-testid="stNumberInput"] *,
    html body [data-testid="stSidebar"] [data-testid="stRadio"] * { color: #E8EFF8 !important; -webkit-text-fill-color: #E8EFF8 !important; }
    html body [data-testid="stSidebar"] input[type="number"],
    html body [data-testid="stSidebar"] input[type="text"] {
        background-color: #2D5A9E !important; color: #E8EFF8 !important;
        border-color: #4A7AC7 !important; -webkit-text-fill-color: #E8EFF8 !important;
    }
    [data-testid="stSidebar"] .stRadio label { font-size: 0.9rem; padding: 4px 0; }
    h1 { color: var(--c-heading) !important; font-size: 1.6rem !important; }
    h2 { color: var(--c-heading) !important; font-size: 1.2rem !important; border-bottom: 2px solid #3A7BD5; padding-bottom: 4px; }
    h3 { color: #2C5282 !important; font-size: 1rem !important; }
    .stMarkdown p { color: var(--c-body) !important; }
    .stMarkdown li { color: var(--c-body) !important; }
    .stCaption p { color: #4A5568 !important; }
    [data-testid="stText"] { color: var(--c-body) !important; }
    .line-badge { display:inline-block; background:#3A7BD5; color:white; border-radius:4px; padding:1px 8px; font-size:0.75rem; font-weight:600; margin-right:8px; vertical-align:middle; }
    label, .stNumberInput label, .stTextInput label,
    .stSelectbox label, .stCheckbox label, .stRadio label, .stSlider label {
        color: var(--c-label) !important; font-size: 0.85rem !important; font-weight: 500 !important;
    }
    .stRadio [data-testid="stMarkdownContainer"] p,
    .stRadio label span { color: var(--c-body) !important; }
    input[type="number"] { background-color: #FFFFFF !important; color: var(--c-body) !important; }
    .irc-note { background:var(--c-law-bg); border-left:3px solid #3A7BD5; padding:6px 10px; border-radius:0 4px 4px 0; font-size:0.8rem; color:var(--c-law-text); margin:2px 0 10px 0; }
    .irc-note ul { margin:4px 0 0 0; padding-left:18px; }
    .irc-note li { margin-bottom:2px; }
    .result-card { background:white; border-radius:8px; padding:16px; border:1px solid #BEE3F8; box-shadow:0 1px 4px rgba(0,0,0,0.06); margin-bottom:12px; }
    .safe-harbor { background:#F0FFF4; border:1px solid #9AE6B4; border-radius:6px; padding:12px 16px; font-size:0.85rem; color:#276749; }
    .warn-box { background:#FFFBEB; border:1px solid #F6AD55; border-radius:6px; padding:10px 14px; font-size:0.85rem; color:#7B341E; }
    [data-testid="stMetricValue"] { font-size:1.4rem !important; color:var(--c-metric-val) !important; }
    [data-testid="stMetricDelta"] { font-size:0.85rem !important; }
    table { width:100%; border-collapse:collapse; font-size:0.88rem; }
    /* Scoped to markdown-generated tables so raw HTML tables keep their own inline
       header colours instead of being repainted pale blue. */
    table:not([style]) th { background:var(--c-th-bg); color:var(--c-th-text); padding:6px 10px; text-align:left; }
    table:not([style]) td { padding:5px 10px; border-bottom:1px solid #E2ECF8; }
    table:not([style]) tr:last-child td { border-bottom:none; font-weight:600; }

    /* Markdown pipe tables carry no inline styling and inherit the theme's
       near-white text, which is invisible on the light page. Tables written as raw
       HTML always have style= on the <table>, so :not([style]) leaves their dark
       header rows alone. */
    [data-testid="stMarkdownContainer"] table:not([style]) { background:#f8f9fa; }
    [data-testid="stMarkdownContainer"] table:not([style]) td,
    [data-testid="stMarkdownContainer"] table:not([style]) td * {
        color:var(--c-body) !important; -webkit-text-fill-color:var(--c-body) !important;
    }
    [data-testid="stMarkdownContainer"] table:not([style]) th,
    [data-testid="stMarkdownContainer"] table:not([style]) th * {
        color:var(--c-heading) !important; -webkit-text-fill-color:var(--c-heading) !important;
        background:#EBF4FF !important;
    }
    hr { border:none; border-top:1px solid #CBD5E0; margin:16px 0; }
    .adj-auto  { font-size:0.8rem; color:var(--c-rule) !important; padding:4px 0 2px 0; font-style:italic; }
    .adj-label { font-size:0.8rem; color:#718096 !important; padding:4px 0 2px 0; }
    .stExpander summary p, .stExpander summary span { color:var(--c-heading) !important; }
    div[role="tab"],
    div[role="tab"] p,
    div[role="tab"] span,
    div[role="tab"] div,
    div[role="tab"][aria-selected="false"],
    div[role="tab"][aria-selected="false"] *,
    div[role="tab"][aria-selected="true"],
    div[role="tab"][aria-selected="true"] * {
        color: var(--c-body) !important;
        -webkit-text-fill-color: var(--c-body) !important;
        opacity: 1 !important;
    }

    /* Streamlit alerts (st.info / warning / success / error) inherit the theme's
       near-white text, which is invisible on their pale backgrounds. */
    [data-testid="stAlert"],
    [data-testid="stAlert"] * ,
    [data-testid="stAlertContentInfo"] *,
    [data-testid="stAlertContentWarning"] *,
    [data-testid="stAlertContentSuccess"] *,
    [data-testid="stAlertContentError"] * {
        color: var(--c-body) !important;
        -webkit-text-fill-color: var(--c-body) !important;
        opacity: 1 !important;
    }
    [data-testid="stAlertContentWarning"], [data-testid="stAlertContentWarning"] * {
        color: #7A4B00 !important; -webkit-text-fill-color: #7A4B00 !important;
    }
    [data-testid="stAlertContentError"], [data-testid="stAlertContentError"] * {
        color: #7A1C1C !important; -webkit-text-fill-color: #7A1C1C !important;
    }
    [data-testid="stAlertContentSuccess"], [data-testid="stAlertContentSuccess"] * {
        color: #14532D !important; -webkit-text-fill-color: #14532D !important;
    }
    [data-testid="stAlertContentInfo"], [data-testid="stAlertContentInfo"] * {
        color: #10365B !important; -webkit-text-fill-color: #10365B !important;
    }

    /* Metric label / value / delta — delta pills render light-on-light by default. */
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
        color: var(--c-metric-lbl) !important; -webkit-text-fill-color: var(--c-metric-lbl) !important; opacity: 1 !important;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
        color: var(--c-metric-val) !important; -webkit-text-fill-color: var(--c-metric-val) !important;
    }
    [data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {
        color: #14532D !important; -webkit-text-fill-color: #14532D !important; opacity: 1 !important;
    }
    [data-testid="stMetricDelta"] svg { fill: #14532D !important; }
    
    /* Appearance controls. Inline colours written throughout the page are remapped here
       so the pickers reach them without editing hundreds of strings. Matching on
       "color:#xxxxxx" avoids catching borders and backgrounds that use the same hex. */
    /* Browsers normalise an inline hex colour to rgb() in the style attribute, so both
       forms are matched. "color:" must precede the value or borders sharing the same
       hue would be caught too. */
    [style*="color:#C53030"], [style*="color: rgb(197, 48, 48)"] {
        color: var(--c-rule) !important; -webkit-text-fill-color: var(--c-rule) !important;
    }
    [style*="color:#1B3A6B"], [style*="color: rgb(27, 58, 107)"] {
        color: var(--c-heading) !important; -webkit-text-fill-color: var(--c-heading) !important;
    }
    [style*="color:#1a1a2e"], [style*="color: rgb(26, 26, 46)"] {
        color: var(--c-body) !important; -webkit-text-fill-color: var(--c-body) !important;
    }
    [data-testid="stMarkdownContainer"] table:not([style]) td,
    [data-testid="stMarkdownContainer"] table:not([style]) td * {
        color: var(--c-table-text) !important; -webkit-text-fill-color: var(--c-table-text) !important;
    }
    [data-testid="stMarkdownContainer"] table:not([style]) th,
    [data-testid="stMarkdownContainer"] table:not([style]) th * {
        color: var(--c-th-text) !important; -webkit-text-fill-color: var(--c-th-text) !important;
    }
    /* Font is applied to text elements only — Streamlit's expander arrows and icons are
       ligature icon fonts and would render as literal words if overridden. */
    [data-testid="stMain"] p, [data-testid="stMain"] li,
    [data-testid="stMain"] td, [data-testid="stMain"] th,
    [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] h4,
    [data-testid="stMain"] label { font-family: var(--app-font); }
    [data-testid="stMain"] p, [data-testid="stMain"] li,
    [data-testid="stMain"] td, [data-testid="stMain"] th { font-size: var(--app-size); }
`;
})();
</script>
""", height=0)

# ── Session State Init ─────────────────────────────────────────────────────────
DEFAULTS = {
    "tax_year": 2025,
    # ── Income — _book = AFS amount, _adj = excluded from tax ────────────────
    "gross_receipts_book": 0.0, "gross_receipts_adj": 0.0,
    "returns_allowances_book": 0.0,
    "dividends_book": 0.0, "dividends_adj": 0.0, "ownership_pct": 0,
    "interest_income_book": 0.0, "interest_income_adj": 0.0,
    "gross_rents_book": 0.0, "gross_rents_adj": 0.0,
    "gross_royalties_book": 0.0, "gross_royalties_adj": 0.0,
    "gain_4797_book": 0.0, "gain_4797_adj": 0.0,
    "has_cfc": False,
    "other_income_book": 0.0, "other_income_adj": 0.0,
    # ── Deductions — _book = AFS amount, _adj = non-deductible ──────────────
    "comp_officers_book": 0.0, "comp_officers_adj": 0.0,
    "is_public": False, "covered_employees": 5, "m162_total_disallowed": 0.0,
    "salaries_book": 0.0, "salaries_adj": 0.0,
    "repairs_book": 0.0, "repairs_adj": 0.0,
    "bad_debt_tax": 0.0, "bad_debt_book_reserve": 0.0,
    "rents_book": 0.0, "rents_adj": 0.0,
    "taxes_book": 0.0, "taxes_adj": 0.0,
    "interest_book": 0.0, "ati_override": 0.0, "interest_cf_prior": 0.0,
    "bii_income": 0.0, "floor_plan_interest": 0.0,
    "f351_n": 1, "f351_boot_cash": 0.0, "f351_boot_other": 0.0,
    "f351_prop_fmv_mixed": 0.0, "f351_stock_fmv_mixed": 0.0,
    "charitable_book": 0.0, "cc_current": 0.0, "cc_cf_prior": 0.0, "cc_ti_base": 0.0,
    "dep_method": "MACRS",
    "asset_cost": 0.0, "year_placed": 2025,
    "total_placed_in_service": 0.0, "macrs_month": 1, "q4_tpp": 0.0,
    "macrs_life": 7,
    "book_depreciation": 0.0,
    "pension_book": 0.0, "pension_adj": 0.0,
    "benefits_book": 0.0, "benefits_adj": 0.0,
    "advertising_book": 0.0, "advertising_adj": 0.0,
    "meals_book": 0.0, "entertainment_book": 0.0,
    "travel_book": 0.0, "travel_adj": 0.0,
    "fines_book": 0.0,
    "lobbying_book": 0.0,
    "bribes_book": 0.0,
    "political_book": 0.0,
    "key_ins_book": 0.0,
    "other_perm_book": 0.0,
    "other_ded_book": 0.0, "other_ded_adj": 0.0,
    "indirect_costs": 0.0, "total_inventory_costs": 0.0,
    "nol_n": 1,
    # Book-vs-tax pairs for the differences that dominate real filings.
    "s174_book": 0.0, "s174_prior_amort": 0.0,
    "intang_book": 0.0, "intang_tax": 0.0,
    "sbc_book": 0.0, "sbc_tax": 0.0,
    "lease_book": 0.0, "lease_tax": 0.0,
    "m1_fed_tax": 0.0, "m1_book_override": 0.0,
    "m1_l4_other": 0.0, "m1_l5_other": 0.0, "m1_l7_other": 0.0, "m1_l8_other": 0.0,
    "m3_fed_tax": 0.0, "m3_book_override": 0.0,
    "m3_other_ii_temp": 0.0, "m3_other_ii_perm": 0.0,
    "m3_other_iii_temp": 0.0, "m3_other_iii_perm": 0.0,
    # Credits
    "current_qre": 0.0, "avg_prior_3yr_qre": 0.0,
    "fixed_base_pct": 3,
    "avg_gross_receipts_rd": 0.0,
    "ftc": 0.0, "other_credits": 0.0,
    # CAMT / BEAT
    "afsi": 0.0, "avg_afsi_3yr": 0.0,
    "avg_gross_receipts_3yr": 0.0,
    "base_erosion_payments": 0.0,
    "modified_ti": 0.0,
    # Estimated Tax
    "prior_year_tax": 0.0,
    "large_corp": False,
    "q1": 0.0, "q2": 0.0, "q3": 0.0, "q4": 0.0,
    "prior_overpayment": 0.0,
    # M-1
    "book_income": 0.0,
    # M-3
    "total_assets": 0.0,
    "worldwide_book_income": 0.0,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

for k, v in THEME_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.pop("_theme_reset", False):
    for k, v in THEME_DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("theme_font_name", None)

# Button keys reject a pre-set value at st.button() time; add any new one here.
BUTTON_KEYS = {"rc_loss_to_line9", "rc_to_cap", "rc_to_other",
               "sd_lb_to_l9", "roll_forward_btn", "export_btn", "import_btn",
               "theme_reset"}
# Widgets whose value is not JSON-serialisable and must never be saved or restored.
NON_PORTABLE_KEYS = {"import_file"}

SAVE_MARKER = "form-1120-calculator"
SAVE_SCHEMA = 1


def export_state_json():
    """Everything needed to reconstruct the return, as a JSON string."""
    state = {}
    for k, v in st.session_state.items():
        if k.startswith("_") or k in BUTTON_KEYS or k in NON_PORTABLE_KEYS:
            continue
        if isinstance(v, (int, float, str, bool)) or v is None:
            state[k] = v
    return json.dumps({
        "app": SAVE_MARKER,
        "schema": SAVE_SCHEMA,
        "tax_year": st.session_state.get("tax_year"),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "closed_years": st.session_state.get("_closed_years", []),
        "state": state,
    }, indent=2)


def parse_state_json(raw):
    """Return (payload, error). Never raises on bad input."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"Not valid JSON — {e}"
    if not isinstance(data, dict) or data.get("app") != SAVE_MARKER:
        return None, "This file was not saved by the Form 1120 calculator."
    if data.get("schema") != SAVE_SCHEMA:
        return None, f"Unsupported save format (schema {data.get('schema')}; this build reads {SAVE_SCHEMA})."
    if not isinstance(data.get("state"), dict):
        return None, "The file is missing its state section."
    return data, None

# ── Year-end rollforward ───────────────────────────────────────────────────────
# Settings that describe the corporation rather than one year's activity. These
# survive a year-end close; everything else numeric is a current-year amount and is
# zeroed so the new year starts clean.
STANDING_KEYS = {
    "tax_year", "active_form", "topic", "f1065_nav", "section",
    "is_public", "covered_employees", "ownership_pct", "large_corp", "total_assets",
    "has_cfc", "sf_owner_pct", "g_owner_pct", "gilti_regime",
    "dep_method", "macrs_life", "year_placed", "macrs_month", "fixed_base_pct",
    "avg_prior_3yr_qre", "avg_gross_receipts_rd", "avg_afsi_3yr", "avg_gross_receipts_3yr",
    "nol_n", "interest_cf_prior", "cc_cf_prior", "prior_year_tax", "prior_overpayment",
    "ati_override", "f4797_n_props", "roll_confirm", "roll_credit_overpay",
    "s267_accrual",
    "theme_font", "theme_font_name", "theme_size",
} | set(THEME_DEFAULTS)
# Prefixes whose keys hold prior-year history and must never be zeroed.
KEEP_PREFIXES = ("sd_cf_loss_", "f4797_lb_loss_", "f4797_lb_recap_",
                 "f4797_desc_", "f4797_type_", "nol_year_", "nol_amt_")
# Prefixes of current-year amount fields that are not declared in DEFAULTS.
# "sf_" and "g_" cover the Subpart F and GILTI/NCTI calculators; their ownership
# percentages are listed in STANDING_KEYS and so are skipped before this is reached.
ANNUAL_PREFIXES = ("sd_l", "f4797_l", "f4797_price_", "f4797_basis_", "f4797_dep_",
                   "m1_", "m3_", "sj_l", "f1125a_", "rc_", "f351_", "p316_",
                   "sf_", "g_")


def _is_annual_amount(key, value):
    if key in STANDING_KEYS or key.startswith("_") or key in BUTTON_KEYS:
        return False
    if key.startswith(KEEP_PREFIXES):
        return False
    if not isinstance(value, float):
        return False
    return key in DEFAULTS or key.startswith(ANNUAL_PREFIXES)


# ── Restore a saved return, applied before any widget is instantiated ─────────
_imp = st.session_state.pop("_import_payload", None)
if _imp:
    for _k, _v in _imp["state"].items():
        if _k in BUTTON_KEYS or _k in NON_PORTABLE_KEYS:
            continue
        st.session_state[_k] = _v
    st.session_state["_closed_years"] = _imp.get("closed_years", [])
    st.session_state["_import_done"] = (
        f"Loaded return for tax year {_imp.get('tax_year')} "
        f"(saved {_imp.get('saved_at', 'unknown')}). {len(_imp['state'])} fields restored.")

_rp = st.session_state.pop("_roll_payload", None)
if _rp:
    _cy_r, _ny_r = _rp["cy"], _rp["next_y"]

    # 1. Zero every current-year amount so the new year starts from a clean sheet.
    for _k in list(st.session_state.keys()):
        if _is_annual_amount(_k, st.session_state.get(_k)):
            st.session_state[_k] = 0.0

    # 2. Write the carryforwards computed from the closing year.
    for _y, _u in _rp["cap_used"]:                       # §1212(a) sources drawn down
        _k = f"sd_cf_loss_{_y}"
        st.session_state[_k] = max(0.0, st.session_state.get(_k, 0.0) - _u)
    if _rp["cap_new"] > 0:
        st.session_state[f"sd_cf_loss_{_cy_r}"] = _rp["cap_new"]
    for _y, _u in _rp["s1231_used"]:                     # §1231(c) already-recaptured
        _k = f"f4797_lb_recap_{_y}"
        st.session_state[_k] = st.session_state.get(_k, 0.0) + _u
    if _rp["s1231_new"] > 0:
        st.session_state[f"f4797_lb_loss_{_cy_r}"] = _rp["s1231_new"]
    for _y, _u in _rp["nol_used"]:                       # §172 tranches drawn down
        for _j in range(int(st.session_state.get("nol_n", 1))):
            if int(st.session_state.get(f"nol_year_{_j}", 0)) == _y:
                _k = f"nol_amt_{_j}"
                st.session_state[_k] = max(0.0, st.session_state.get(_k, 0.0) - _u)
    if _rp["nol_new"] > 0:                               # this year's loss becomes a tranche
        _slot = int(st.session_state.get("nol_n", 1))
        st.session_state["nol_n"] = _slot + 1
        st.session_state[f"nol_year_{_slot}"] = _cy_r
        st.session_state[f"nol_amt_{_slot}"] = _rp["nol_new"]
    st.session_state["interest_cf_prior"] = _rp["i163j"]
    st.session_state["cc_cf_prior"] = _rp["char"]

    # 3. Estimated-tax basis for the new year.
    st.session_state["prior_year_tax"] = _rp["total_tax"]
    st.session_state["prior_overpayment"] = _rp["overpay_credit"]

    # 4. Advance the year and record the close so it cannot be run twice.
    st.session_state["tax_year"] = _ny_r
    st.session_state["roll_confirm"] = False
    st.session_state["_closed_years"] = sorted(
        set(st.session_state.get("_closed_years", [])) | {_cy_r})
    st.session_state["_roll_done"] = (
        f"Closed {_cy_r}. Carryforwards written, current-year entries cleared, "
        f"and the tax year advanced to {_ny_r}.")

# ── Persist widget state across page navigation ────────────────────────────────
# Streamlit garbage-collects the session_state entry of any keyed widget that is not
# rendered in the current run. This app is a multi-page radio nav, so every page the
# user is not looking at would silently lose its inputs. Re-asserting each key at the
# top of the run (before any widget is instantiated) pins the values.
# Buttons and file uploaders must be excluded: Streamlit rejects a pre-set value when
# those widgets are created. Register any new one in BUTTON_KEYS / NON_PORTABLE_KEYS.
for _k in list(st.session_state.keys()):
    if _k.startswith("_") or _k in BUTTON_KEYS or _k in NON_PORTABLE_KEYS:
        continue
    st.session_state[_k] = st.session_state[_k]

# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    active_form = st.radio("Form", ["📋 Form 1120", "🤝 Form 1065"],
                           horizontal=True, label_visibility="collapsed", key="active_form")
    st.markdown("---")
    TAX_YEAR = st.number_input("Tax Year", min_value=2018, max_value=2040, step=1, key="tax_year")

    with st.expander("🎨 Appearance"):
        st.caption("Applies across every page. Saved with the return.")
        _fonts = {
            "System default": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            "Serif": "Georgia, 'Times New Roman', serif",
            "Monospace": "'SF Mono', Consolas, 'Courier New', monospace",
            "Helvetica / Arial": "Helvetica, Arial, sans-serif",
            "Verdana (wide)": "Verdana, Geneva, sans-serif",
        }
        _cur = st.session_state.get("theme_font", THEME_DEFAULTS["theme_font"])
        _names = list(_fonts)
        _idx = next((i for i, n in enumerate(_names) if _fonts[n] == _cur), 0)
        _pick = st.selectbox("Font", _names, index=_idx, key="theme_font_name")
        st.session_state["theme_font"] = _fonts[_pick]

        st.slider("Body text size (px)", 12, 20, key="theme_size")

        st.caption("Each group below is independent — change one area without touching the others.")
        for _area, _items in THEME_AREAS:
            st.markdown(f"**{_area}**")
            for _key, _var, _default, _label in _items:
                st.color_picker(_label, key=_key)

        if st.button("Reset to defaults", key="theme_reset", use_container_width=True):
            st.session_state["_theme_reset"] = True
            st.rerun()

    with st.expander("💾 Save / Load"):
        _done_imp = st.session_state.pop("_import_done", None)
        if _done_imp:
            st.success(_done_imp)

        st.caption("Everything is held in this browser session and is lost when the tab "
                   "closes. Save after each year-end close — the file carries the "
                   "carryforwards and the record of which years are already closed.")

        st.download_button(
            "⬇️ Save return as JSON",
            data=export_state_json(),
            file_name=f"form1120_{st.session_state.get('tax_year', 'return')}.json",
            mime="application/json",
            key="export_btn",
            use_container_width=True,
            help="Everything entered, including carryforwards and closed-year history. "
                 "Session state is lost when the browser closes — save before you leave.")

        _up = st.file_uploader("Load a saved return", type=["json"], key="import_file")
        if _up is not None:
            _payload, _err = parse_state_json(_up.getvalue().decode("utf-8"))
            if _err:
                st.error(_err)
            else:
                st.caption(f"Tax year {_payload.get('tax_year')} · saved {_payload.get('saved_at', '—')} · "
                           f"{len(_payload['state'])} fields")
                st.warning("Loading replaces everything currently entered.")
                if st.button("Replace current return with this file", key="import_btn",
                             use_container_width=True):
                    st.session_state["_import_payload"] = _payload
                    st.rerun()

    # Always visible — a disclaimer behind a click is a disclaimer nobody reads.
    st.markdown(
        "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:10px 12px;"
        "margin:4px 0;color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;font-size:0.8rem;"
        "line-height:1.45;'><b>Educational tool — not tax advice.</b><br>"
        "Does not produce a filable return. Use illustrative figures only.</div>",
        unsafe_allow_html=True)

    with st.expander("⚠️ Full disclaimer — read before use"):
        st.markdown(
            "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 14px;"
            "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;font-size:0.85rem;line-height:1.5;'>"
            "<b>Educational tool. Not tax advice.</b><br><br>"
            "This app was written to study how the mechanics of Form 1120 fit together. "
            "It is <b>not</b> prepared or reviewed by a CPA or an enrolled agent, it does "
            "<b>not</b> produce a filable return, and it simplifies or omits many rules that "
            "apply to a real taxpayer.<br><br>"
            "Do not rely on it to compute an actual tax liability. Verify everything against "
            "the current IRS forms and instructions, and consult a qualified tax professional.<br><br>"
            "<b>Do not enter real taxpayer data.</b> Figures are held in server memory for the "
            "life of the session. Nothing is stored permanently, but the hosted demo is a public "
            "service you do not control — use illustrative numbers only.<br><br>"
            "Provided under the MIT License, without warranty of any kind."
            "</div>", unsafe_allow_html=True)

    st.markdown("---")

    topic = None
    f1065_nav = None
    section = None

    if active_form == "📋 Form 1120":
        st.markdown("### 📋 Form 1120")

        def _reset_topic():
            st.session_state["topic"] = None

        section = st.radio("Navigate", [
            "📥 Page 1 — Income",
            "📤 Page 1 — Deductions",
            "💰 Schedule C — Dividends",
            "📉 Schedule D — Capital Gains",
            "🏭 Form 4797 — Business Property",
            "🧮 Schedule J — Tax Computation",
            "📅 Estimated Tax & Safe Harbor",
            "📚 Schedule M-1",
            "📊 Schedule M-3",
            "📈 Results Summary",
        ], label_visibility="collapsed", on_change=_reset_topic)
        st.markdown("---")
        st.markdown("### 🏛️ Tax Topics")
        topic = st.radio("Topics", [
            "📐 Corporate Formation — §351",
            "💸 Corporate Distributions",
            "🏛️ CAMT & Estimated Tax",
            "✂️ QBI Deduction — §199A",
        ], label_visibility="collapsed", key="topic", index=None)

    else:  # Form 1065
        st.markdown("### 🤝 Form 1065")
        f1065_nav = st.radio("Navigate", [
            "📖 Overview",
            "📥 Income (Lines 1–8)",
            "📤 Deductions (Lines 9–22)",
            "📋 Schedule K — Distributive Share Items",
            "🧾 Schedule K-1 — Per Partner Summary",
        ], label_visibility="collapsed", key="f1065_nav")

def irc(items):
    if isinstance(items, str):
        items = [items]
    bullets = "".join(f"<li>{i}</li>" for i in items)
    st.markdown(f'<div class="irc-note">⚖️ <ul>{bullets}</ul></div>', unsafe_allow_html=True)

def L(num, label, unit="$"):
    return f"[Line {num}] {label} ({unit})" if unit else f"[Line {num}] {label}"

def tax_row(line_num, label, book_key, adj_key=None, auto_adj_pct=None,
            computed_adj=None, step=1_000.0, allow_negative=False, mode="income",
            show_metric=True):
    """3-column: Book/AFS | Disallowed (auto) | Tax (auto). Returns (book, adj, tax).
    Income mode: adj_key triggers manual Tax Exclusion input.
    Deduction mode: adj_key is ignored — use auto_adj_pct or computed_adj instead."""
    c1, c2, c3 = st.columns([5, 4, 3])
    min_v = None if allow_negative else 0.0
    book = c1.number_input(f"[Line {line_num}] {label}", min_value=min_v,
                           step=step, format="%.2f", key=book_key)
    if auto_adj_pct == 1.0:
        adj = book
        lbl = "100% disallowed (auto)" if mode == "deduction" else "100% excluded (auto)"
        c2.markdown(f'<div class="adj-auto">{lbl}</div>', unsafe_allow_html=True)
    elif auto_adj_pct is not None and auto_adj_pct > 0:
        adj = book * auto_adj_pct
        pct_str = f"{auto_adj_pct:.0%}"
        lbl = f"{pct_str} disallowed → ${adj:,.0f}" if mode == "deduction" else f"{pct_str} excluded → ${adj:,.0f}"
        c2.markdown(f'<div class="adj-auto">{lbl}</div>', unsafe_allow_html=True)
    elif computed_adj is not None:
        adj = computed_adj
        if adj > 0:
            c2.markdown(f'<div class="adj-auto">Disallowed (auto) → ${adj:,.0f}</div>', unsafe_allow_html=True)
        else:
            c2.markdown('<div class="adj-label">—</div>', unsafe_allow_html=True)
    elif adj_key and mode == "income":
        adj = c2.number_input("Tax Exclusion ($)", min_value=0.0, step=step, format="%.2f", key=adj_key)
    else:
        adj = 0.0
        c2.markdown('<div class="adj-label">—</div>', unsafe_allow_html=True)
    tax = book - adj
    if show_metric:
        tax_label = "Tax Deduction" if mode == "deduction" else "Taxable Amount"
        c3.metric(tax_label, f"${tax:,.0f}")
    return book, adj, tax

def col_headers(mode="income"):
    h1, h2, h3 = st.columns([5, 4, 3])
    if mode == "income":
        h1.markdown("**Book / AFS Amount ($)**")
        h2.markdown("**Tax Exclusion ($)**")
        h3.markdown("**Taxable Amount ($)**")
    else:
        h1.markdown("**Book / AFS Expense ($)**")
        h2.markdown("**Disallowed (auto)**")
        h3.markdown("**Tax Deduction ($)**")

def build_1120_inputs(dividends_and_inclusions, special_deductions, nol_carryforward,
                      pre2018_nol_carryforward=0.0):
    """Assemble calculate_1120() inputs from session_state. Called twice: once in the
    shared pass with special deductions and NOL zeroed to obtain line 28 (the §246(b)
    limit base), then again by Results Summary with the real figures."""
    s = st.session_state
    dep_map = {"§179 Expensing": "179", "Bonus Depreciation": "bonus",
               "MACRS": "macrs", "Cost Segregation": "cost_seg"}
    return {
            "tax_year": int(s.tax_year),
            "gross_revenue": (s.gross_receipts_book - s.gross_receipts_adj) - s.returns_allowances_book,
            "other_income": (
                (s.interest_income_book - s.interest_income_adj) +
                (s.gross_rents_book     - s.gross_rents_adj) +
                (s.gross_royalties_book - s.gross_royalties_adj) +
                (s.other_income_book    - s.other_income_adj) +
                s.get("f4797_line17", 0.0)      # Form 1120 line 9 — Form 4797 Part II line 17
            ),
            "short_term_capital_gain": s.get("sd_line7", 0.0),
            "long_term_capital_gain":  s.get("sd_line15", 0.0),
            "capital_loss_carryforward": 0.0,
            "dividends_and_inclusions": dividends_and_inclusions,
            "special_deductions": special_deductions,
            "dividends_received": s.dividends_book - s.dividends_adj,
            "ownership_pct": s.ownership_pct / 100,
            "cogs": F1125A["cogs"],
            "indirect_costs": S263A["pool"],
            "depreciation_capitalized": S263A["l20"],
            # One §448(c) test gates both §263A(i) and §163(j)(3).
            "small_business_exempt": S263A["exempt"],
            "total_inventory_costs": F1125A["pool"],
            "operating_expenses": (
                (s.salaries_book - S267["l13"] - S263A["l13"]) +
                (s.repairs_book - S263A["l14"]) +
                (s.rents_book - S263A["l16"]) +
                (s.taxes_book - S263A["l17"]) +
                s.advertising_book +
                s.pension_book +
                s.benefits_book +
                s.other_ded_book +
                s.travel_book +
                s.meals_book * 0.5 +
                MODERN["tax_total"]
            ),
            "bad_debt_expense": s.bad_debt_tax,
            "bad_debt_reserve_book": s.bad_debt_book_reserve,
            "meals_entertainment": s.meals_book,
            "fines_penalties": s.fines_book,
            "lobbying_expense": s.lobbying_book,
            "bribes": s.bribes_book,
            "political_contributions": s.political_book,
            "key_employee_insurance": s.key_ins_book,
            "travel": s.travel_book,
            "charitable_contributions": s.charitable_book,
            "officer_compensation": (s.comp_officers_book
                                     - s.get("m162_total_disallowed", 0.0)
                                     - S267["l12"] - S263A["l12"]),
            "is_public": s.is_public,
            "covered_employees": s.covered_employees if s.is_public else 0,
            "interest_expense": s.interest_book,
            "ati": s.ati_override if s.ati_override > 0 else None,
            "interest_carryforward": s.interest_cf_prior,
            "depreciation_method": dep_map.get(s.dep_method, "macrs"),
            "asset_cost": s.asset_cost,
            "year_placed": int(s.year_placed),
            "total_placed_in_service": s.total_placed_in_service,
            "macrs_life": s.macrs_life,
            "book_depreciation": s.book_depreciation,
            "nol_carryforward": nol_carryforward,
            "pre2018_nol_carryforward": pre2018_nol_carryforward,
            "current_qre": s.current_qre,
            "avg_prior_3yr_qre": s.avg_prior_3yr_qre,
            "fixed_base_pct": s.fixed_base_pct / 100,
            "avg_gross_receipts": s.avg_gross_receipts_rd if s.avg_gross_receipts_rd > 0 else max(s.gross_receipts_book, 1),
            "foreign_tax_credit": s.ftc,
            "other_credits": s.other_credits,
            "afsi": s.afsi,
            "avg_afsi_3yr": s.avg_afsi_3yr,
            "avg_gross_receipts_3yr": s.avg_gross_receipts_3yr,
            "base_erosion_payments": s.base_erosion_payments,
            "modified_taxable_income": s.modified_ti,
            "q1_payment": s.q1, "q2_payment": s.q2,
            "q3_payment": s.q3, "q4_payment": s.q4,
            "prior_year_overpayment": s.prior_overpayment,
            "book_income": s.book_income,
    }

# ─────────────────────────────────────────────────────────────────────────────
# SHARED COMPUTATION — runs every rerun, before any page branch.
# Streamlit renders one page per run, so anything computed inside a page branch is
# invisible to every other page until the user navigates there. Schedule C totals
# feed Page 1 line 4 and the Deductions line 29b, so they must be computed here.
# ─────────────────────────────────────────────────────────────────────────────
def calc_subpart_f(owner_pct, subf_inc, ep, gross_inc, foreign_tax):
    deminimis = gross_inc > 0 and (subf_inc / gross_inc) < 0.05 and subf_inc < 1_000_000
    full_incl = gross_inc > 0 and (subf_inc / gross_inc) > 0.70
    effective = gross_inc if full_incl else (0.0 if deminimis else subf_inc)
    return {"deminimis": deminimis, "full_inclusion": full_incl, "effective": effective,
            "inclusion": owner_pct * min(effective, ep),
            "grossup": owner_pct * foreign_tax}

def calc_gilti_ncti(regime, owner_pct, tested_inc, qbai, tested_tax):
    if regime == "Pre-2026 GILTI":
        ndtir, ded_pct, haircut, eff = 0.10 * qbai, 0.50, 1.0, 0.105
        base = max(0.0, tested_inc - ndtir)
    else:
        ndtir, ded_pct, haircut, eff = 0.0, 0.40, 0.90, 0.126
        base = tested_inc
    inclusion = owner_pct * base
    deduction = inclusion * ded_pct
    return {"ndtir": ndtir, "base": base, "inclusion": inclusion, "deduction": deduction,
            "deduction_pct": ded_pct, "net_inclusion": inclusion - deduction,
            "ftc_haircut": haircut, "effective_rate": eff,
            "avail_ftc": owner_pct * tested_tax * haircut}

def form_4797_totals():
    """Form 4797 Parts I–III. Computed in the shared pass because Part II line 17 feeds
    Form 1120 line 9 (Page 1) while Part I feeds Schedule D line 11 — different pages."""
    s = st.session_state
    _cy = int(s.get("tax_year", 2025))

    # ── Part III — recapture, computed first because line 31 and 32 feed Parts II and I
    props = []
    for i in range(int(s.get("f4797_n_props", 1))):
        price = s.get(f"f4797_price_{i}", 0.0)
        basis = s.get(f"f4797_basis_{i}", 0.0)
        dep   = s.get(f"f4797_dep_{i}", 0.0)
        kind  = s.get(f"f4797_type_{i}", "§1245 — Personal property")
        adj_basis = basis - dep                       # line 23
        gain = price - adj_basis                      # line 24
        if gain <= 0:
            recap = 0.0
        elif "1245" in kind:
            recap = min(gain, dep)                    # line 25b
        else:
            recap = 0.20 * min(gain, dep)             # §291(a)(1) for C corps — line 26g
        props.append({"i": i, "name": s.get(f"f4797_desc_{i}", f"Property {chr(65+i)}"),
                      "kind": kind, "price": price, "basis": basis, "dep": dep,
                      "adj_basis": adj_basis, "gain": gain, "recapture": recap,
                      "sec1231": gain - recap})
    l30 = sum(p["gain"] for p in props)
    l31 = sum(p["recapture"] for p in props)          # → Part II line 13
    l32 = l30 - l31                                   # → Part I line 6

    # ── Part I — §1231
    l2 = s.get("f4797_l2", 0.0)
    l3 = s.get("f4797_l3", 0.0)
    l4 = s.get("f4797_l4", 0.0)
    l5 = s.get("f4797_l5", 0.0)
    l6 = l32
    l7 = l2 + l3 + l4 + l5 + l6

    lb_rows, pool = [], 0.0
    for y in range(_cy - 5, _cy):
        loss = s.get(f"f4797_lb_loss_{y}", 0.0)
        prior = s.get(f"f4797_lb_recap_{y}", 0.0)
        avail = max(0.0, loss - prior)
        lb_rows.append({"year": y, "loss": loss, "prior": prior, "avail": avail})
        pool += avail
    l8 = pool if l7 > 0 else 0.0                      # line 8 only matters against a gain

    # §1231(c): apply oldest year first, for display
    remaining = l7 if l7 > 0 else 0.0
    for r in lb_rows:
        r["used"] = min(r["avail"], remaining)
        remaining -= r["used"]

    if l7 <= 0:
        l9, l11, l12, sd_ltcg = 0.0, l7, 0.0, 0.0     # net §1231 loss → ordinary, line 11
    else:
        l9 = max(0.0, l7 - l8)
        l11 = 0.0
        if l9 == 0:
            l12, sd_ltcg = l7, 0.0                    # fully recaptured as ordinary
        else:
            l12, sd_ltcg = l8, l9                     # line 8 ordinary, line 9 → Schedule D

    # ── Part II — ordinary
    l10 = s.get("f4797_l10", 0.0)
    l13 = l31
    l14 = s.get("f4797_l14", 0.0)
    l15 = s.get("f4797_l15", 0.0)
    l16 = s.get("f4797_l16", 0.0)
    l17 = l10 + l11 + l12 + l13 + l14 + l15 + l16     # → Form 1120 line 9

    return {"props": props, "l30": l30, "l31": l31, "l32": l32,
            "l2": l2, "l3": l3, "l4": l4, "l5": l5, "l6": l6, "l7": l7,
            "l8": l8, "l9": l9, "lb_rows": lb_rows,
            "l10": l10, "l11": l11, "l12": l12, "l13": l13, "l14": l14,
            "l15": l15, "l16": l16, "l17": l17,
            "schedule_d_ltcg": sd_ltcg}

def schedule_d_totals(sec1231_ltcg):
    """Schedule D Parts I–III. Computed in the shared pass because line 11 comes from
    Form 4797 (another page) and line 18 feeds Form 1120 line 8 (Page 1)."""
    s = st.session_state
    _cy = int(s.get("tax_year", 2025))
    g = lambda k: s.get(k, 0.0)

    part1_pre = g("sd_l1a") + g("sd_l1b") + g("sd_l2") + g("sd_l3") + g("sd_l4") + g("sd_l5")
    l11 = sec1231_ltcg
    l15 = (g("sd_l8a") + g("sd_l8b") + g("sd_l9") + g("sd_l10")
           + l11 + g("sd_l12") + g("sd_l13") + g("sd_l14"))

    # §1212(a) carryover — oldest first, 5-year window
    capacity = max(0.0, part1_pre + l15)
    cf_rows = []
    for y in range(_cy - 6, _cy):
        loss = g(f"sd_cf_loss_{y}")
        expires_after = y + 5
        alive = expires_after >= _cy
        use = min(loss, capacity) if alive else 0.0
        capacity -= use
        cf_rows.append({"year": y, "loss": loss, "alive": alive,
                        "expires_after": expires_after, "used": use})
    cf_applied = sum(r["used"] for r in cf_rows)
    cf_expired = sum(r["loss"] for r in cf_rows if not r["alive"])
    cf_unused = sum(r["loss"] - r["used"] for r in cf_rows if r["alive"])

    l6 = -cf_applied
    l7 = part1_pre + l6
    l16 = max(0.0, l7 + min(0.0, l15)) if l7 > 0 else 0.0
    l17 = max(0.0, l15 + min(0.0, l7)) if l15 > 0 else 0.0
    l18 = l16 + l17
    net_loss = max(0.0, -(l7 + l15))

    return {"part1_pre": part1_pre, "l6": l6, "l7": l7, "l11": l11, "l15": l15,
            "l16": l16, "l17": l17, "l18": l18, "net_loss": net_loss,
            "cf_rows": cf_rows, "cf_applied": cf_applied,
            "cf_expired": cf_expired, "cf_unused": cf_unused,
            "pre_cf_net": part1_pre + l15}

# §448(c) average annual gross receipts threshold, indexed for inflation. One constant
# so the §263A small-business exemption and every other test that cites §448(c) cannot
# drift apart. Later years fall back to the last published figure.
SEC448_THRESHOLD = {2018: 25_000_000.0, 2019: 26_000_000.0, 2020: 26_000_000.0,
                    2021: 26_000_000.0, 2022: 27_000_000.0, 2023: 29_000_000.0,
                    2024: 30_000_000.0, 2025: 31_000_000.0}


def sec448_threshold(year):
    return SEC448_THRESHOLD.get(int(year), max(SEC448_THRESHOLD.values()))


def nol_vintages():
    """§172 carryforwards by the year the loss arose. The vintage decides the rules:
    a pre-2018 loss offsets 100% of taxable income but dies 20 years out; a 2018-or-later
    loss lasts forever but is capped at 80%."""
    s = st.session_state
    cy = int(s.get("tax_year", 2025))
    rows = []
    for i in range(int(s.get("nol_n", 1))):
        s.setdefault(f"nol_year_{i}", cy - 1)
        s.setdefault(f"nol_amt_{i}", 0.0)
        yr = int(s[f"nol_year_{i}"])
        amt = s[f"nol_amt_{i}"]
        pre2018 = yr < 2018
        expires = yr + 20 if pre2018 else None
        expired = pre2018 and expires < cy
        rows.append({"i": i, "year": yr, "amount": amt, "pre2018": pre2018,
                     "expires": expires, "expired": expired,
                     "live": amt if not expired else 0.0})
    rows.sort(key=lambda r: r["year"])          # FIFO — oldest vintage first
    return {
        "rows": rows,
        "pre2018_pool": sum(r["live"] for r in rows if r["pre2018"]),
        "post2017_pool": sum(r["live"] for r in rows if not r["pre2018"]),
        "expired": sum(r["amount"] for r in rows if r["expired"]),
    }


def modern_diffs():
    """The four book-tax differences that dominate a real filer's deferred tax note
    but that a textbook Form 1120 problem never mentions.

    Each is a book amount paired with a tax amount; the gap is temporary in every case
    because all four eventually reverse. §174 is the one with a rule worth computing:
    since 2022 domestic research must be capitalised and amortised over 5 years on a
    mid-year convention, so only 10% of the current year's spend is deductible now."""
    s = st.session_state
    g = lambda k: s.get(k, 0.0)
    s174_tax = g("s174_book") * 0.10 + g("s174_prior_amort")
    rows = [
        ("§174 research and experimental", "36", g("s174_book"), s174_tax),
        ("§197 intangible amortisation and impairment", "29", g("intang_book"), g("intang_tax")),
        ("Stock-based compensation (ASC 718 vs deduction on vesting)", "9",
         g("sbc_book"), g("sbc_tax")),
        ("Leases (ASC 842 lease cost vs rent deducted)", "35", g("lease_book"), g("lease_tax")),
    ]
    return {"rows": [{"label": l, "m3_line": ln, "book": b, "tax": t} for l, ln, b, t in rows],
            "book_total": sum(r[2] for r in rows),
            "tax_total": sum(r[3] for r in rows),
            "s174_tax": s174_tax}


def form_1125a_base():
    """Form 1125-A before any §263A loading. These feed calculate_1120 so the module's
    own UNICAP computation reproduces the absorption split shown on screen instead of
    recomputing it from inputs nothing populates."""
    s = st.session_state
    g = lambda k: s.get(k, 0.0)
    pool = g("f1125a_beg_inv") + g("f1125a_purchases") + g("f1125a_labor") + g("f1125a_other")
    return {"pool": pool, "cogs": pool - g("f1125a_end_inv"), "end_inv": g("f1125a_end_inv")}


def sec263a_status(depreciation=0.0):
    """§263A UNICAP, including the §263A(i) small-business exemption.

    Post-TCJA the exemption applies to producers and resellers alike: any taxpayer
    meeting the §448(c) gross receipts test is out of §263A entirely. Below the
    threshold nothing is capitalised, so the labour allocations are forced to zero.
    """
    s = st.session_state
    thr = sec448_threshold(s.get("tax_year", 2025))
    avg = s.get("avg_gross_receipts_3yr", 0.0)
    exempt = avg <= thr
    # Entered as a share of the compensation already on lines 12 and 13, not re-keyed
    # as a dollar amount. That removes the duplicate entry and makes it impossible for
    # the allocation to exceed the expense it comes out of.
    pct12 = s.get("s263a_l12_pct", 0) / 100
    pct13 = s.get("s263a_l13_pct", 0) / 100
    pct14 = s.get("s263a_l14_pct", 0) / 100
    pct16 = s.get("s263a_l16_pct", 0) / 100
    pct17 = s.get("s263a_l17_pct", 0) / 100
    pct20 = s.get("s263a_l20_pct", 0) / 100
    l12 = 0.0 if exempt else s.get("comp_officers_book", 0.0) * pct12
    l13 = 0.0 if exempt else s.get("salaries_book", 0.0) * pct13
    l14 = 0.0 if exempt else s.get("repairs_book", 0.0) * pct14
    l16 = 0.0 if exempt else s.get("rents_book", 0.0) * pct16
    l17 = 0.0 if exempt else s.get("taxes_book", 0.0) * pct17
    # §179 expense is not a §263A cost, so only MACRS/bonus/cost-seg depreciation is
    # offered up for capitalisation.
    l20 = 0.0 if (exempt or s.get("dep_method") == "§179 Expensing") else depreciation * pct20
    other = 0.0 if exempt else s.get("f1125a_263a", 0.0)
    return {"threshold": thr, "avg": avg, "exempt": exempt,
            "pct12": pct12, "pct13": pct13, "pct14": pct14,
            "pct16": pct16, "pct17": pct17, "pct20": pct20,
            "l12": l12, "l13": l13, "l14": l14, "l16": l16, "l17": l17,
            "l20": l20, "dep_gross": depreciation, "other": other,
            "pool": l12 + l13 + l14 + l16 + l17 + l20 + other}


def sec267_deferral():
    """§267(a)(2) and the 2½-month rule for accrued but unpaid compensation.

    An accrual-basis corporation may not deduct compensation accrued to a related
    cash-basis person until that person includes it in income. For a C corporation a
    related person includes any shareholder owning more than 50% — so the deduction is
    deferred no matter how quickly it is paid. Amounts owed to unrelated employees are
    deferred only if they are still unpaid 2½ months after year-end.
    """
    s = st.session_state
    if not s.get("s267_accrual", True):
        return {"l12": 0.0, "l13": 0.0, "total": 0.0, "applies": False}
    paid_25 = s.get("s267_paid_25", False)
    unrelated_factor = 0.0 if paid_25 else 1.0
    l12 = s.get("s267_l12_related", 0.0) + unrelated_factor * s.get("s267_l12_unrelated", 0.0)
    l13 = s.get("s267_l13_related", 0.0) + unrelated_factor * s.get("s267_l13_unrelated", 0.0)
    return {"l12": l12, "l13": l13, "total": l12 + l13, "applies": True}


def schedule_c_totals():
    s = st.session_state
    if s.get("has_cfc", False):
        sf = calc_subpart_f(s.get("sf_owner_pct", 60.0) / 100, s.get("sf_subf_inc", 500_000.0),
                            s.get("sf_ep", 800_000.0), s.get("sf_gross_inc", 1_000_000.0),
                            s.get("sf_foreign_tax", 50_000.0))
        gl = calc_gilti_ncti(s.get("gilti_regime", "2026+ NCTI"), s.get("g_owner_pct", 100.0) / 100,
                             s.get("g_tested_inc", 1_000_000.0), s.get("g_qbai", 2_000_000.0),
                             s.get("g_tested_tax", 80_000.0))
        subf, g78, gilti_inc, d250 = sf["inclusion"], sf["grossup"], gl["inclusion"], gl["deduction"]
    else:
        subf = g78 = gilti_inc = d250 = 0.0

    divs = s.get("dividends_book", 0.0)
    line23 = divs + subf + gilti_inc + g78          # column (a) — gross, independent of the DRD

    # §246(b) limit base = Form 1120 line 28 (taxable income before NOL and special
    # deductions). It does not depend on the DRD — that is exactly why the DRD sits at
    # line 29b — so it can be computed here and fed straight into the limit.
    _probe = calculate_1120(build_1120_inputs(line23, 0.0, 0.0))
    line28 = _probe["taxable_income"]["before_nol"]

    drd = calc_drd_246b(divs, s.get("ownership_pct", 0), line28)

    # §250(a)(2): the FDII + GILTI amounts on which the deduction is computed cannot
    # exceed taxable income determined without regard to §250 — i.e. line 28 after the
    # DRD but before §250 itself. Unused amount is lost; there is no carryforward.
    sec250_base = max(0.0, line28 - drd["allowed"])
    sec250_uncapped = d250
    d250_pct = (d250 / gilti_inc) if gilti_inc else 0.0
    sec250 = d250_pct * min(gilti_inc, sec250_base)
    sec250_limited = sec250 < sec250_uncapped - 0.01

    return {"dividends": divs, "subpart_f": subf, "gilti": gilti_inc, "grossup78": g78,
            "sec250": sec250, "sec250_uncapped": sec250_uncapped,
            "sec250_base": sec250_base, "sec250_limited": sec250_limited,
            "drd": drd, "line28": line28,
            "line23": line23,
            "line24": drd["allowed"] + sec250}           # column (c) — special deductions

MODERN = modern_diffs()
F1125A = form_1125a_base()
S263A = sec263a_status()
S267 = sec267_deferral()

F4797 = form_4797_totals()
st.session_state["f4797_line17"] = F4797["l17"]
st.session_state["f4797_sd_ltcg"] = F4797["schedule_d_ltcg"]

SD = schedule_d_totals(F4797["schedule_d_ltcg"])
st.session_state["sd_line7"] = SD["l7"]
st.session_state["sd_line15"] = SD["l15"]
st.session_state["sd_line18"] = SD["l18"]
st.session_state["sd_net_capital_loss"] = SD["net_loss"]

# Depreciation is computed inside calculate_1120 but does not depend on the §263A pool,
# so one probe fixes it exactly — no iteration needed. S263A is then rebuilt with the
# depreciation slice included before anything downstream reads the pool.
_dep_probe = calculate_1120(build_1120_inputs(0.0, 0.0, 0.0))
S263A = sec263a_status(_dep_probe["deductions"]["depreciation_gross"])

SC = schedule_c_totals()
st.session_state["sc_subf_inclusion"]   = SC["subpart_f"]
st.session_state["sc_gilti_inclusion"]  = SC["gilti"]
st.session_state["sc_sec78_grossup"]    = SC["grossup78"]
st.session_state["sc_sec250_deduction"] = SC["sec250"]
st.session_state["sc_line23"] = SC["line23"]
st.session_state["sc_line24"] = SC["line24"]

# "Total receipts" is a defined term on Form 1120: line 1a plus lines 4 through 10.
# Deliberately not "gross receipts" (line 1a alone) and it skips lines 2 and 3, since
# COGS is a cost and gross profit would double-count line 1a. Drives the Form 1125-E
# filing threshold; the same figure drives the Schedule K test for Schedules L/M-1/M-2.
def total_receipts():
    s = st.session_state
    g = lambda a, b: s.get(a, 0.0) - s.get(b, 0.0)
    return {
        "l1a": g("gross_receipts_book", "gross_receipts_adj"),
        "l4": SC["line23"],
        "l5": g("interest_income_book", "interest_income_adj"),
        "l6": g("gross_rents_book", "gross_rents_adj"),
        "l7": g("gross_royalties_book", "gross_royalties_adj"),
        "l8": max(0.0, SD["l18"]),
        "l9": F4797["l17"],
        "l10": g("other_income_book", "other_income_adj"),
    }


TR = total_receipts()
TR["total"] = sum(TR.values())

# Full return, now that the special deductions are known. Schedule J and Results Summary
# both read this so they cannot disagree.
NOL = nol_vintages()
R1120 = calculate_1120(build_1120_inputs(SC["line23"], SC["line24"],
                                         NOL["post2017_pool"], NOL["pre2018_pool"]))
_nres = R1120["taxable_income"]["nol"]
NOL["line29a"] = _nres["nol_used"]
# Spread the two pool totals back over the individual tranches, oldest first, so the
# year-end close knows which vintages were consumed.
for _pre, _left in ((True, _nres.get("pre2018_used", 0.0)),
                    (False, _nres.get("post2017_used", _nres["nol_used"]))):
    for _r in NOL["rows"]:
        if _r["pre2018"] != _pre or _r["live"] <= 0:
            _r.setdefault("used", 0.0)
            continue
        _r["used"] = min(_r["live"], _left)
        _left -= _r["used"]
st.session_state["_taxable_income"] = R1120["taxable_income"]["taxable_income"]
st.session_state["_federal_tax_paid"] = R1120["tax"]["total_federal_tax"]


def book_income_derived(federal_tax_per_books=0.0):
    """Net income per books, built from the same Book / AFS columns the income and
    deduction pages already collect. Book ignores every tax rule: no §1211 cap, no
    §274 haircut, no §263A capitalisation, no §162(m) — it is simply what the ledger
    says. That is exactly what makes it the correct starting point for M-1 and M-3."""
    s = st.session_state
    g = lambda k: s.get(k, 0.0)
    revenue = (g("gross_receipts_book") - g("returns_allowances_book")
               - F1125A["cogs"]
               + g("dividends_book") + g("interest_income_book")
               + g("gross_rents_book") + g("gross_royalties_book")
               + SD["l18"]                      # books take the full capital result
               + F4797["l17"] + g("other_income_book"))
    expenses = sum(g(k) for k in (
        "comp_officers_book", "salaries_book", "repairs_book", "bad_debt_book_reserve",
        "rents_book", "taxes_book", "interest_book", "charitable_book",
        "book_depreciation", "advertising_book", "pension_book", "benefits_book",
        "meals_book", "entertainment_book", "travel_book", "fines_book",
        "lobbying_book", "bribes_book", "political_book", "key_ins_book",
        "other_ded_book", "other_perm_book")) + MODERN["book_total"]
    return {"pretax": revenue - expenses,
            "net": revenue - expenses - federal_tax_per_books,
            "revenue": revenue, "expenses": expenses}


def m1_lines():
    """Schedule M-1, every line derived. Lives here rather than in the page branch so
    the integrity check can read it no matter which page is open."""
    s = st.session_state
    g = lambda k: s.get(k, 0.0)
    d = R1120["deductions"]

    fed_tax = g("m1_fed_tax")
    bk = book_income_derived(fed_tax)
    ovr = g("m1_book_override")
    l1 = ovr if ovr else bk["net"]

    l3 = g("sd_net_capital_loss")          # §1211(a): books take the loss, tax caps it

    l4_items = [
        ("Subpart F inclusion (§951)", SC["subpart_f"]),
        ("GILTI / NCTI inclusion (§951A)", SC["gilti"]),
        ("§78 gross-up", SC["grossup78"]),
        ("Other (manual)", g("m1_l4_other")),
    ]
    cogs_diff = d["cogs"] - F1125A["cogs"]          # + means tax deducts more
    l5_items = [
        ("5a Depreciation — book in excess of tax", max(0.0, g("book_depreciation") - d["depreciation"])),
        ("5b Charitable — excess over the 10% limit (§170(b)(2))", d["charitable"]["carryforward_5yr"]),
        ("5c Travel and entertainment — §274(a) entertainment + 50% of meals",
         g("entertainment_book") + g("meals_book") * 0.5),
        ("Fines and penalties (§162(f))", g("fines_book")),
        ("Lobbying (§162(e))", g("lobbying_book")),
        ("Bribes and kickbacks (§162(c))", g("bribes_book")),
        ("Political contributions (§276)", g("political_book")),
        ("Key employee life insurance (§264)", g("key_ins_book")),
        ("Other permanently non-deductible expense", g("other_perm_book")),
        ("Bad debt — book reserve over §166 charge-off", max(0.0, g("bad_debt_book_reserve") - g("bad_debt_tax"))),
        ("§163(j) disallowed business interest", d["interest"]["excess_carryforward"]),
        ("§162(m) excess officer compensation", g("m162_total_disallowed") + d["section_162m_disallowed"]),
        ("§263A costs capitalised into inventory (lines 12\u201317)",
         S263A["l12"] + S263A["l13"] + S263A["l14"] + S263A["l16"] + S263A["l17"]),
        ("§267(a)(2) related-party accrual deferred", S267["l12"] + S267["l13"]),
        ("COGS — book in excess of tax", max(0.0, -cogs_diff)),
    ] + [
        (f"{r['label']} — book in excess of tax", max(0.0, r["book"] - r["tax"]))
        for r in MODERN["rows"]
    ] + [
        ("Other (manual)", g("m1_l5_other")),
    ]
    l7_items = [
        ("Gross receipts exclusion", g("gross_receipts_adj")),
        ("Dividends exclusion", g("dividends_adj")),
        ("7a Tax-exempt interest (§103)", g("interest_income_adj")),
        ("Rents exclusion", g("gross_rents_adj")),
        ("Royalties exclusion", g("gross_royalties_adj")),
        ("Form 4797 exclusion", g("gain_4797_adj")),
        ("Other income exclusion — §101 life insurance, §111 recoveries", g("other_income_adj")),
        ("Other (manual)", g("m1_l7_other")),
    ]
    l8_items = [
        ("8a Depreciation — tax in excess of book", max(0.0, d["depreciation"] - g("book_depreciation"))),
        ("Bad debt — §166 charge-off over book reserve", max(0.0, g("bad_debt_tax") - g("bad_debt_book_reserve"))),
        ("COGS — tax in excess of book", max(0.0, cogs_diff)),
    ] + [
        (f"{r['label']} — tax in excess of book", max(0.0, r["tax"] - r["book"]))
        for r in MODERN["rows"]
    ] + [
        ("Other (manual)", g("m1_l8_other")),
    ]

    l4 = sum(v for _, v in l4_items)
    l5 = sum(v for _, v in l5_items)
    l7 = sum(v for _, v in l7_items)
    l8 = sum(v for _, v in l8_items)
    l6 = l1 + fed_tax + l3 + l4 + l5
    l9 = l7 + l8
    return {"book": bk, "override": ovr, "fed_tax": fed_tax,
            "l1": l1, "l3": l3, "l4": l4, "l5": l5, "l6": l6,
            "l7": l7, "l8": l8, "l9": l9, "l10": l6 - l9,
            "l4_items": l4_items, "l5_items": l5_items,
            "l7_items": l7_items, "l8_items": l8_items}


def m3_lines():
    """Schedule M-3 Parts II and III. Each row fixes (a), (d) and the permanent slice
    (c); the temporary slice (b) is the residual, so (a)+(b)+(c)=(d) can never drift."""
    s = st.session_state
    g = lambda k: s.get(k, 0.0)
    d = R1120["deductions"]

    fed_tax = g("m3_fed_tax")
    bk = book_income_derived(fed_tax)
    ovr = g("m3_book_override")
    l1 = ovr if ovr else bk["net"]

    def row(line, label, a, dd, perm=0.0, note=""):
        return {"line": line, "label": label, "a": a, "b": dd - a - perm,
                "c": perm, "d": dd, "note": note}

    int_book, int_excl = g("interest_income_book"), g("interest_income_adj")
    part2 = [
        row("3", "Subpart F, QEF, and similar income inclusions", 0.0,
            SC["subpart_f"] + SC["gilti"],
            note="Tax-only inclusion — no book entry. Reverses as PTEP, so temporary."),
        row("4", "Section 78 gross-up", 0.0, SC["grossup78"], perm=SC["grossup78"],
            note="Pure tax construct that never reverses — permanent."),
        row("7", "U.S. dividends not eliminated in tax consolidation", SC["dividends"], SC["dividends"],
            note="No difference. The DRD is a special deduction at line 29b, not an M-3 item."),
        row("13", "Interest income", int_book, int_book - int_excl, perm=-int_excl,
            note="§103 municipal interest is excluded forever — permanent."),
        row("17", "Cost of goods sold (shown as negative)", -F1125A["cogs"], -d["cogs"],
            note="§263A capitalised costs sit in inventory until sold — temporary."),
        row("23b", "Gross capital gains from Schedule D", max(0.0, SD["l18"]), max(0.0, SD["l18"]),
            note="Book and tax agree on the gain itself."),
        row("23d", "Net gain (loss) from Form 4797", F4797["l17"], F4797["l17"],
            note="§1231 ordinary/capital character does not change the amount."),
        row("24", "Capital loss limitation and carryforward used", 0.0, g("sd_net_capital_loss"),
            note="§1211(a) — books take the loss now, tax defers it. Temporary."),
        row("25", "Other income (loss) items with differences", 0.0,
            g("m3_other_ii_temp") + g("m3_other_ii_perm"), perm=g("m3_other_ii_perm"), note="Manual."),
    ]

    o38 = [
        ("Salaries and wages (§263A / §267 deferral)", g("salaries_book"),
         g("salaries_book") - S267["l13"] - S263A["l13"], 0.0),
        ("Repairs and maintenance (§263A)", g("repairs_book"), g("repairs_book") - S263A["l14"], 0.0),
        ("Rents (§263A)", g("rents_book"), g("rents_book") - S263A["l16"], 0.0),
        ("Taxes and licenses (§263A)", g("taxes_book"), g("taxes_book") - S263A["l17"], 0.0),
        ("Lobbying (§162(e))", g("lobbying_book"), 0.0, -g("lobbying_book")),
        ("Bribes and kickbacks (§162(c))", g("bribes_book"), 0.0, -g("bribes_book")),
        ("Political contributions (§276)", g("political_book"), 0.0, -g("political_book")),
        ("Other permanently non-deductible", g("other_perm_book"), 0.0, -g("other_perm_book")),
        ("Other (manual)", 0.0, g("m3_other_iii_temp") + g("m3_other_iii_perm"), g("m3_other_iii_perm")),
    ]
    meals = g("meals_book")
    m162 = g("m162_total_disallowed") + d["section_162m_disallowed"]
    part3 = [
        row("1", "U.S. current income tax expense", fed_tax, 0.0, perm=-fed_tax,
            note="§275 — federal income tax is never deductible. Permanent."),
        row("8", "Interest expense", g("interest_book"), d["interest"]["deductible"],
            note="§163(j) disallowance carries forward indefinitely — temporary."),
        row("11", "Meals and entertainment", meals, meals * 0.5, perm=-meals * 0.5,
            note="§274(n) 50% haircut never reverses — permanent."),
        row("12", "Fines and penalties", g("fines_book"), 0.0, perm=-g("fines_book"),
            note="§162(f) — permanent."),
        row("15", "Compensation with §162(m) limitation", g("comp_officers_book"),
            d["officer_compensation"], perm=-m162,
            note="§162(m) excess is permanent; §263A / §267 slices are temporary."),
        row("19", "Charitable contribution of cash and tangible property",
            g("charitable_book"), g("charitable_book"), note="The contribution itself."),
        row("21", "Charitable contribution limitation", 0.0, -d["charitable"]["carryforward_5yr"],
            note="§170(b)(2) 10% cap — the excess carries forward 5 years. Temporary."),
        row("32", "Depreciation", g("book_depreciation"), d["depreciation"],
            note="MACRS vs book life — reverses over the asset's life. Temporary."),
        row("33", "Bad debt expense", g("bad_debt_book_reserve"), g("bad_debt_tax"),
            note="§166 specific charge-off vs book reserve — temporary."),
        row("34", "Corporate owned life insurance premiums", g("key_ins_book"), 0.0,
            perm=-g("key_ins_book"), note="§264 — permanent."),
        row("9", "Stock option and other equity-based compensation",
            g("sbc_book"), g("sbc_tax"),
            note="ASC 718 expenses over the vesting period; tax deducts on vesting or "
                 "exercise. Temporary."),
        row("29", "Other amortization or impairment write-offs",
            g("intang_book"), g("intang_tax"),
            note="§197 amortises acquired intangibles over 15 years regardless of the "
                 "book life, and book impairment is not a tax event. Temporary."),
        row("35", "Purchase versus lease",
            g("lease_book"), g("lease_tax"),
            note="ASC 842 splits a lease into amortisation and interest; tax deducts the "
                 "rent actually paid. Temporary."),
        row("36", "Research and development costs",
            g("s174_book"), MODERN["s174_tax"],
            note="§174 since 2022 — domestic research is capitalised and amortised over "
                 "5 years, mid-year convention, so only 10% of this year's spend is "
                 "deductible now. Temporary, and usually large."),
        row("38", "Other expense/deduction items with differences",
            sum(x[1] for x in o38), sum(x[2] for x in o38), perm=sum(x[3] for x in o38),
            note="Everything with no dedicated M-3 line — see the breakdown below."),
    ]

    # An income item moves taxable income by its own difference; an expense item moves
    # it by the opposite, because a bigger deduction is less income.
    temp = sum(r["b"] for r in part2) - sum(r["b"] for r in part3)
    perm = sum(r["c"] for r in part2) - sum(r["c"] for r in part3)
    return {"book": bk, "override": ovr, "fed_tax": fed_tax, "l1": l1,
            "part2": part2, "part3": part3, "o38": o38,
            "temp": temp, "perm": perm, "l30": l1 + temp + perm}


M1 = m1_lines()
M3 = m3_lines()


def return_checks():
    """The gate. Each reconciliation must land on Form 1120 line 28, and every schedule
    that feeds page 1 must agree with the line it feeds. A tolerance of $1 absorbs
    float noise; anything larger is a real break."""
    s = st.session_state
    l28 = SC["line28"]
    l29a, l29b = NOL["line29a"], SC["line24"]
    l30 = max(0.0, l28 - l29a - l29b)
    assets = s.get("total_assets", 0.0)
    required = "M-3" if assets >= 10_000_000 else "M-1"
    entered = abs(TR["total"]) > 0.5 or abs(R1120["deductions"]["total_deductions"]) > 0.5

    def chk(name, actual, expected, detail, active=True):
        if not active:
            return {"name": name, "state": "skip", "detail": detail,
                    "actual": actual, "expected": expected}
        ok = abs(actual - expected) < 1.0
        return {"name": name, "state": "pass" if ok else "fail", "detail": detail,
                "actual": actual, "expected": expected}

    rows = [
        chk("Book income is populated", 1.0 if abs(M1["l1"]) > 0.5 else 0.0, 1.0,
            f"Net income per books ${M1['l1']:,.0f} — derived from the Book / AFS columns"),
        chk("Taxable income is populated", 1.0 if abs(l28) > 0.5 else 0.0, 1.0,
            f"Form 1120 line 28 ${l28:,.0f}"),
        chk("Book-tax differences are computed",
            1.0 if (abs(M3["temp"]) + abs(M3["perm"])) > 0.5 else 0.0, 1.0,
            f"Temporary ${M3['temp']:+,.0f}, permanent ${M3['perm']:+,.0f}"),
        chk("Schedule M-1 line 10 = Form 1120 line 28", M1["l10"], l28,
            f"M-1 ${M1['l10']:,.0f} vs line 28 ${l28:,.0f}", active=(required == "M-1")),
        chk("Schedule M-3 Part II line 30 (d) = Form 1120 line 28", M3["l30"], l28,
            f"M-3 ${M3['l30']:,.0f} vs line 28 ${l28:,.0f}", active=(required == "M-3")),
        chk("M-1 and M-3 agree with each other", M1["l10"], M3["l30"],
            f"M-1 ${M1['l10']:,.0f} vs M-3 ${M3['l30']:,.0f}"),
        chk("Schedule C line 23 = page 1 line 4", SC["line23"], TR["l4"],
            f"Dividends and inclusions ${SC['line23']:,.0f}"),
        chk("Schedule C line 24 = line 29b", SC["line24"], l29b,
            f"DRD + §250 ${l29b:,.0f}"),
        chk("Schedule D = page 1 line 8", max(0.0, SD["l18"]), TR["l8"],
            f"Net capital gain ${TR['l8']:,.0f} (§1211(a) disallowed ${s.get('sd_net_capital_loss', 0.0):,.0f})"),
        chk("Form 4797 line 17 = page 1 line 9", F4797["l17"], TR["l9"],
            f"Ordinary gain (loss) ${TR['l9']:,.0f}"),
        # The §263A costs stripped out of lines 12-20 must reappear in cost of goods sold.
        # When they did not, $1.6M once vanished from the return without a trace.
        chk("§263A costs removed from lines 12–20 reach cost of goods sold",
            1.0 if (S263A["pool"] < 0.5 or R1120["deductions"]["unicap_adjustment"] > 0.5) else 0.0, 1.0,
            f"Capitalised ${S263A['pool']:,.0f}, absorbed into COGS "
            f"${R1120['deductions']['unicap_adjustment']:,.0f}, tax COGS "
            f"${R1120['deductions']['cogs']:,.0f}"),
        chk("Line 28 \u2212 29a \u2212 29b = line 30", l28 - l29a - l29b if l28 - l29a - l29b > 0 else 0.0, l30,
            f"${l28:,.0f} \u2212 ${l29a:,.0f} \u2212 ${l29b:,.0f} = ${l30:,.0f}"),
    ]
    failed = [r for r in rows if r["state"] == "fail"]
    return {"rows": rows, "failed": failed, "required": required,
            "entered": entered, "passed": entered and not failed}


def render_checks(compact=False):
    c = return_checks()
    if not c["entered"]:
        st.markdown(
            "<div style='background:#FFF7E6;border-left:5px solid #B7791F;padding:12px 16px;margin:8px 0;"
            "color:#744210;-webkit-text-fill-color:#744210;'>"
            "<b>Nothing entered yet.</b> Fill in the income and deduction pages first — "
            "with an empty return every check passes trivially and proves nothing."
            "</div>", unsafe_allow_html=True)
        return c
    if c["passed"]:
        st.markdown(
            "<div style='background:#E7F6EC;border-left:5px solid #1E7A3C;padding:12px 16px;margin:8px 0;"
            "color:#14532D;-webkit-text-fill-color:#14532D;'>"
            f"<b>PASS — the return is internally consistent.</b> Book income, the book-tax "
            f"differences and taxable income all carry figures, and Schedule {c['required']} "
            f"lands exactly on Form 1120 line 28."
            "</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
            "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
            f"<b>FAIL — {len(c['failed'])} check(s) did not tie.</b> "
            "The return does not yet hang together; the failing rows below say where."
            "</div>", unsafe_allow_html=True)
    if compact:
        return c
    def _out_by(r):
        if r["state"] == "skip":
            return ""
        return f"{r['actual'] - r['expected']:,.0f}"

    icon = {"pass": "\u2713", "fail": "\u2717", "skip": "\u2014"}
    colour = {"pass": "#1E7A3C", "fail": "#C53030", "skip": "#8A94A6"}
    st.markdown(
        "<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
        "<tr style='background:#EBF4FF;color:#1B3A6B'>"
        "<th style='padding:6px 8px;width:34px'></th>"
        "<th style='padding:6px 8px;text-align:left'>Check</th>"
        "<th style='padding:6px 8px;text-align:left'>Figures</th>"
        "<th style='padding:6px 8px;text-align:right'>Out by</th></tr>"
        + "".join(
            f"<tr><td style='padding:5px 8px;text-align:center;font-weight:700;"
            f"color:{colour[r['state']]}'>{icon[r['state']]}</td>"
            f"<td style='padding:5px 8px'>{r['name']}</td>"
            f"<td style='padding:5px 8px;color:#4A5568'>{r['detail']}</td>"
            f"<td style='padding:5px 8px;text-align:right'>"
            f"{'' if r['state'] == 'skip' else f'{r[chr(34)+chr(34)] if False else (r[chr(97)+chr(99)+chr(116)+chr(117)+chr(97)+chr(108)] - r[chr(101)+chr(120)+chr(112)+chr(101)+chr(99)+chr(116)+chr(101)+chr(100)]):,.0f}'}"
            f"</td></tr>"
            for r in c["rows"])
        + "</table></div>", unsafe_allow_html=True)
    st.caption("Rows marked \u2014 do not apply: Schedule M-1 and M-3 are alternatives, "
               "chosen by total assets at year-end (\u2265 $10M \u2192 M-3).")
    return c

# ─────────────────────────────────────────────────────────────────────────────
# TOPIC PAGES (override 1120 navigation)
# ─────────────────────────────────────────────────────────────────────────────
if topic is not None:
    section = None   # suppress 1120 pages

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — INCOME
# ─────────────────────────────────────────────────────────────────────────────
if section == "📥 Page 1 — Income":
    # Transfer staging keys must be applied before any widget renders
    for _src, _dst in [("_transfer_other", "other_income_book"), ("_transfer_4797", "gain_4797_book")]:
        if _src in st.session_state:
            st.session_state[_dst] = st.session_state.pop(_src)

    st.title("Page 1 — Income")
    st.markdown("Enter the **Book / AFS amount** in the first column. Use the **Tax Exclusion** column for amounts excluded from taxable income (e.g., §103 muni interest). The **Taxable Amount** is computed automatically.")

    st.markdown("## Gross Revenue")
    col_headers("income")
    # Line 1a — capture col3 as placeholder so Line 1c metric aligns with this row
    _r1a_c1, _r1a_c2, _r1a_c3 = st.columns([5, 4, 3])
    gr_book = _r1a_c1.number_input("[Line 1a] Gross receipts or sales", min_value=0.0, step=10_000.0, format="%.2f", key="gross_receipts_book")
    gr_adj  = _r1a_c2.number_input("Tax Exclusion ($)", min_value=0.0, step=10_000.0, format="%.2f", key="gross_receipts_adj")
    gr = gr_book - gr_adj
    _slot_1c = _r1a_c3.empty()
    _, _, ra  = tax_row("1b", "Returns and allowances", "returns_allowances_book", step=1_000.0, show_metric=False)
    net_sales = gr - ra
    _slot_1c.markdown(f"""<div style="padding-top:1.6rem;font-size:1.15rem;font-weight:700;color:#1B3A6B;">
Line 1c — Balance<br><span style="font-size:0.72rem;font-weight:400;color:#5a6a85;">Subtract line 1b from line 1a</span><br><span style="font-size:1.5rem;">${net_sales:,.0f}</span></div>""", unsafe_allow_html=True)
    irc([
        "§61: Gross income = all income from whatever source derived.",
        f"§448: Accrual method required if 3-yr average annual gross receipts exceed the §448(c) threshold — <b>${sec448_threshold(TAX_YEAR):,.0f}</b> for {int(TAX_YEAR)}.",
        "§451(b): Tax recognition cannot be later than AFS (Applicable Financial Statement — the highest-quality financial statement, typically audited GAAP) recognition — tax follows books, never defers beyond them.",
        "§451(c) / Reg. §1.451-8: Advance payments deferred max 1 year. Eligible: goods, services, IP/software, subscriptions, loyalty programs. NOT eligible: rent, interest, insurance premiums.",
        "§451(c): Cannot defer if already in AFS; cannot defer the completed-performance portion.",
    ])

    st.markdown("## Cost of Goods Sold")
    irc([
        "<b>Form 1125-A</b> required if inventory is a material income-producing factor. Compute tax COGS here; result flows to Line 2.",
        "<b>§263A UNICAP (Uniform Capitalization):</b> Indirect costs of production or resale must be capitalised into inventory rather than deducted — warehousing, purchasing department salaries, handling, processing overhead, and the share of officer pay attributable to those functions."
        "<br>These costs sit in SG&amp;A (Selling, General &amp; Administrative) on the books but must flow through inventory for tax."
        "<br><span style='color:#C53030'>Net effect: only the <i>sold portion</i> of §263A costs increases current-year COGS (deductible now); the unsold portion stays in ending inventory → temporary difference creating a DTL (Deferred Tax Liability).</span>",

        "<b>§263A(i) small-business exemption:</b> A taxpayer whose average annual gross receipts for the 3 prior years do not exceed the <b>§448(c) threshold</b> is exempt from §263A <b>entirely</b>."
        "<br><span style='color:#C53030'>Post-TCJA this covers <b>producers and resellers alike</b> — the old split, where only resellers had a dollar threshold and every producer was caught, no longer applies.</span>"
        "<br>The threshold is indexed annually, so it moves: "
        + " · ".join(f"{y} ${v/1e6:,.0f}M" for y, v in sorted(SEC448_THRESHOLD.items()) if y >= 2022)
        + ".",

        "<b>What is <i>not</i> capitalised:</b> selling and distribution, advertising and marketing, general administration not allocable to production, §174 research, §179 expense, income taxes, and bad debts."
        "<br>Interest is excluded too, unless the property has a long production period under §263A(f).",
        "<b>Inventory methods:</b> FIFO, LIFO (§472 — Form 970 required for first-year election), weighted average, or specific identification. Cannot change method without IRS consent (Form 3115).",
        "<b>Lower of cost or market:</b> For tax, 'market' = replacement cost (not NRV as under GAAP ASC 330), except for goods that can only be sold below cost.",
    ])
    st.markdown("### §263A — does it apply at all?")
    st.number_input("Average annual gross receipts, 3 prior years — §448(c) test ($)",
                    min_value=0.0, step=1_000_000.0, format="%.2f", key="avg_gross_receipts_3yr",
                    help="The same figure drives the §59A BEAT threshold on Schedule J.")
    if S263A["exempt"]:
        st.markdown(
            "<div style='background:#E7F6EC;border-left:5px solid #1E7A3C;padding:12px 16px;margin:8px 0;"
            "color:#14532D;-webkit-text-fill-color:#14532D;'>"
            f"<b>✅ Exempt from §263A.</b> Average gross receipts of <b>${S263A['avg']:,.0f}</b> do not exceed the "
            f"§448(c) threshold of <b>${S263A['threshold']:,.0f}</b> for {int(TAX_YEAR)}.<br>"
            "Nothing is capitalised — indirect costs stay fully deductible where they are, and the allocation "
            "fields below are ignored."
            "</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
            "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
            f"<b>⚠️ §263A applies.</b> Average gross receipts of <b>${S263A['avg']:,.0f}</b> exceed the §448(c) "
            f"threshold of <b>${S263A['threshold']:,.0f}</b> for {int(TAX_YEAR)}.<br>"
            "Indirect costs of production and resale must be capitalised into inventory — including the portion of "
            "officer compensation and wages attributable to those functions."
            "</div>", unsafe_allow_html=True)

    with st.expander("🧮 Form 1125-A — Cost of Goods Sold Calculator", expanded=False):
        st.caption("Complete this schedule. The computed Tax COGS flows to Line 2.")
        fa1, fa2 = st.columns(2)
        f_beg_inv   = fa1.number_input("Beginning Inventory ($)",       min_value=0.0, step=10_000.0, format="%.2f", key="f1125a_beg_inv")
        f_purchases = fa1.number_input("Purchases ($)",                  min_value=0.0, step=10_000.0, format="%.2f", key="f1125a_purchases")
        f_labor     = fa1.number_input("Cost of Labor ($)",              min_value=0.0, step=10_000.0, format="%.2f", key="f1125a_labor")
        fa1.caption("Direct production labour already in COGS — do not repeat it in the §263A fields.")

        fa2.markdown("**§263A cost pool**")
        fa2.number_input("Other indirect costs — rent, utilities, plant depreciation ($)",
                         min_value=0.0, step=1_000.0, format="%.2f", key="f1125a_263a",
                         disabled=S263A["exempt"])
        _comp12 = st.session_state.get("comp_officers_book", 0.0)
        _comp13 = st.session_state.get("salaries_book", 0.0)
        _rep14 = st.session_state.get("repairs_book", 0.0)
        _rent16 = st.session_state.get("rents_book", 0.0)
        _tax17 = st.session_state.get("taxes_book", 0.0)
        fa2.caption(f"Already entered: line 12 \\${_comp12:,.0f} · line 13 \\${_comp13:,.0f} · "
                    f"line 14 \\${_rep14:,.0f} · line 16 \\${_rent16:,.0f} · line 17 \\${_tax17:,.0f}. "
                    "Give the share attributable to production or resale — no need to retype the amounts.")
        fa2.slider("% of line 12 officer compensation — production or resale", 0, 100,
                   key="s263a_l12_pct", disabled=S263A["exempt"],
                   help="Substantiated by a time or headcount study. Selling and general admin time is excluded.")
        fa2.slider("% of line 13 wages — purchasing, handling, storage, QC", 0, 100,
                   key="s263a_l13_pct", disabled=S263A["exempt"],
                   help="Direct production labour belongs in Cost of Labor above, not here.")
        fa2.slider("% of line 14 repairs — production plant and equipment", 0, 100,
                   key="s263a_l14_pct", disabled=S263A["exempt"],
                   help="Repairs to manufacturing or warehouse assets are indirect production costs. "
                        "Repairs to the sales office or delivery vehicles are not.")
        fa2.slider("% of line 16 rents — factory, warehouse, production space", 0, 100,
                   key="s263a_l16_pct", disabled=S263A["exempt"],
                   help="Rent on production and storage space is an indirect production cost. "
                        "Sales office and showroom rent is not.")
        fa2.slider("% of line 17 taxes — production property and payroll taxes", 0, 100,
                   key="s263a_l17_pct", disabled=S263A["exempt"],
                   help="Property tax on the plant or warehouse, and employer payroll taxes on "
                        "production-support staff. State income tax is never a §263A cost.")
        _dep_is_179 = st.session_state.get("dep_method") == "§179 Expensing"
        fa2.slider(f"% of line 20 depreciation — production assets "
                   f"(computed: \\${S263A['dep_gross']:,.0f})", 0, 100,
                   key="s263a_l20_pct", disabled=S263A["exempt"] or _dep_is_179,
                   help="Plant, machinery and warehouse depreciation. Sales-office and delivery-"
                        "vehicle depreciation is not a §263A cost.")
        if _dep_is_179:
            fa2.caption("§179 expensing is excluded from §263A by Reg. §1.263A-1(e)(3)(iii) — "
                        "nothing is capitalised while that method is selected.")
        fa2.markdown(
            f"<div style='font-size:0.82rem;color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>"
            f"→ line 12 <b>${S263A['l12']:,.0f}</b> · line 13 <b>${S263A['l13']:,.0f}</b> · "
            f"line 14 <b>${S263A['l14']:,.0f}</b> · line 16 <b>${S263A['l16']:,.0f}</b> · "
            f"line 17 <b>${S263A['l17']:,.0f}</b> · line 20 <b>${S263A['l20']:,.0f}</b></div>",
            unsafe_allow_html=True)
        fa2.metric("Total §263A pool", f"${S263A['pool']:,.0f}",
                   "exempt — nothing capitalised" if S263A["exempt"] else "labour + other indirect")
        f_263a = S263A["pool"]
        f_other     = fa2.number_input("Other Costs ($)",                min_value=0.0, step=1_000.0,  format="%.2f", key="f1125a_other")
        f_end_inv   = fa1.number_input("Less: Ending Inventory — Book/GAAP ($)", min_value=0.0, step=10_000.0, format="%.2f", key="f1125a_end_inv")
        fa1.caption("Enter GAAP ending inventory. §263A adjustment to tax ending inventory is computed automatically.")

        st.markdown("""
**Which functions go into the percentage**

| Capitalise into inventory | Expense in full |
|---|---|
| Purchasing and procurement | Selling and sales commissions |
| Receiving, handling, warehousing | Marketing and advertising |
| Quality control and inspection | Distribution to customers |
| Production supervision, factory admin | General admin not tied to production |
| Repackaging, rework | R&D (§174), interest, income taxes |

The test is **function, not job title**. An officer who spends part of the week running
production and the rest selling is split by time — that split is the percentage above.
""")

        # Base pool (without §263A) — same figures the shared pass hands to the module.
        f_base_pool  = F1125A["pool"]
        f_base_cogs  = F1125A["cogs"]

        # §263A: allocate between COGS and ending inventory proportionally
        _263a_ratio    = f_base_cogs / f_base_pool if f_base_pool else 0
        _263a_in_cogs  = f_263a * _263a_ratio
        _263a_in_inv   = f_263a - _263a_in_cogs

        # Tax figures
        f_cogs_calc    = f_base_cogs + _263a_in_cogs
        f_tax_end_inv  = f_end_inv + _263a_in_inv
        f_total_before = f_base_pool + f_263a            # display only

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Base COGS (ex-§263A)", f"${f_base_cogs:,.0f}")
        m2.metric("§263A in COGS", f"${_263a_in_cogs:,.0f}",
                  f"= ${f_263a:,.0f} × {_263a_ratio:.2%}")
        m3.metric("Tax COGS (Line 2)", f"${f_cogs_calc:,.0f}")
        m4.metric("Tax Ending Inv.", f"${f_tax_end_inv:,.0f}",
                  f"Book \\${f_end_inv:,.0f} + §263A \\${_263a_in_inv:,.0f}")
        st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">§263A Allocation</th>
<th style="padding:8px 12px;text-align:left;">Formula</th>
<th style="padding:8px 12px;text-align:right;">Result</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;">
<td style="padding:8px 12px;">Absorption ratio</td>
<td style="padding:8px 12px;">Base COGS ÷ Base pool = {f_base_cogs:,.0f} ÷ {f_base_pool:,.0f}</td>
<td style="padding:8px 12px;text-align:right;font-weight:bold;">{_263a_ratio:.2%}</td>
</tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;">
<td style="padding:8px 12px;">§263A in COGS</td>
<td style="padding:8px 12px;">{f_263a:,.0f} × {_263a_ratio:.2%}</td>
<td style="padding:8px 12px;text-align:right;font-weight:bold;">${_263a_in_cogs:,.0f}</td>
</tr>
<tr>
<td style="padding:8px 12px;">§263A in ending inv</td>
<td style="padding:8px 12px;">{f_263a:,.0f} × {1-_263a_ratio:.2%}</td>
<td style="padding:8px 12px;text-align:right;font-weight:bold;">${_263a_in_inv:,.0f}</td>
</tr>
</tbody>
</table>
""", unsafe_allow_html=True)

    cogs_tax = f_base_cogs + S263A["pool"] * (f_base_cogs / f_base_pool if f_base_pool else 0)
    st.markdown(
        "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
        "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
        "<b>⚠️ Line 2 has NO input on Form 1120.</b> Cost of goods sold is carried from <b>Form 1125-A</b> above, "
        "including the §263A costs absorbed into goods sold this year."
        "</div>", unsafe_allow_html=True)
    st.metric("Line 2 — Cost of goods sold (attach Form 1125-A)", f"${cogs_tax:,.0f}",
              "carried from Form 1125-A")

    st.markdown("## Other Income")
    col_headers("income")

    # Line 4 — carried gross from Schedule C line 23; the DRD lives on line 29b
    _sc_line23 = st.session_state.get("sc_line23")
    div_tax = _sc_line23 if _sc_line23 is not None else 0.0

    st.markdown(
        "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
        "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
        "<b>⚠️ Line 4 has NO input on Form 1120.</b> The figure is carried from <b>Schedule C line 23</b> and cannot be "
        "typed in here.<br>You <b>must</b> enter dividends and foreign inclusions on the <b>💰 Schedule C — Dividends</b> "
        "page. Line 4 carries the <b>gross</b> amount — the DRD is <b>not</b> netted here, it is taken separately on "
        "<b>line 29b</b> and so appears on the Deductions page, not on this one."
        "</div>", unsafe_allow_html=True)

    st.metric("Line 4 — Dividends and inclusions", f"${div_tax:,.0f}",
              "carried from Schedule C line 23")

    if _sc_line23 is None:
        st.warning("Schedule C has not been filled in yet — Line 4 is \\$0. Open the **💰 Schedule C — Dividends** page.")

    irc([
        "<b>§243 DRD (Dividends Received Deduction):</b> Domestic corps receiving dividends from other domestic corps may deduct a portion to avoid triple taxation."
        "<br><span style='color:#C53030'><b>Rates:</b> &lt;20% owned → 50%; 20–80% → 65%; ≥80% affiliated group → 100%.</span>"
        "<br>DRD cannot exceed the applicable % of taxable income (§246(b) limitation) — <b>exception:</b> if applying the DRD limit would create or increase a NOL (Net Operating Loss), the full DRD is allowed.",
        "<b>Where the DRD actually goes:</b> Schedule C column (c) → line 24 → Form 1120 page 1 <b>line 29b</b> (special deductions)."
        "<br><span style='color:#C53030'>Line 4 is gross. Netting the DRD into line 4 would make the §246(b) taxable-income "
        "limit depend on the deduction it is supposed to be limiting.</span>",
        "<b>Foreign inclusions ride the same line:</b> §951 Subpart F, §951A NCTI/GILTI and the §78 gross-up all enter "
        "column (a) alongside ordinary dividends, which is why the line is titled <i>Dividends <b>and inclusions</b></i>."
        "<br>They are Schedule C lines <b>16a / 16b / 18</b>, so the CFC calculators live on the "
        "<b>💰 Schedule C — Dividends</b> page next to the rows they feed.",
    ])


    # Line 5 — Interest Income with §103 muni bond exclusion
    _, _, int_tax  = tax_row("5",  "Interest — enter total; use exclusion col for §103 muni bond interest", "interest_income_book", "interest_income_adj")
    _, _, rent_tax = tax_row("6",  "Gross rents",      "gross_rents_book",     "gross_rents_adj")
    _, _, roy_tax  = tax_row("7",  "Gross royalties",  "gross_royalties_book", "gross_royalties_adj")
    irc([
        "§109: Lessor excludes value of lessee improvements that revert to lessor at lease end — not taxable income when the lease terminates.",
        "§1033: If rental property is condemned or involuntarily converted, gain is DEFERRED if proceeds are reinvested in replacement property within 2 years (3 years for real property). Enter book gain; use Tax Exclusion column for the deferred portion.",
    ])

    st.markdown("## Line 8 — Capital gain net income (attach Schedule D (Form 1120))")
    _sd18   = st.session_state.get("sd_line18")
    _sd_l7  = st.session_state.get("sd_line7", 0.0)
    _sd_l15 = st.session_state.get("sd_line15", 0.0)
    _sd_loss = st.session_state.get("sd_net_capital_loss", 0.0)
    net_cap = _sd18 if _sd18 is not None else 0.0

    st.markdown(
        "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
        "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
        "<b>⚠️ Line 8 has NO input on Form 1120.</b> The figure is carried from <b>Schedule D line 18</b> and cannot be "
        "typed in here.<br>You <b>must</b> enter every capital transaction on the <b>📉 Schedule D — Capital Gains</b> "
        "page — Parts I and II, the §1212(a) carryover pool, and the §1231(c) look-back. Only then does this line populate."
        "</div>", unsafe_allow_html=True)

    _r8a, _r8b, _r8c = st.columns(3)
    _r8a.metric("Schedule D line 7 — Net short-term", f"${_sd_l7:,.0f}")
    _r8b.metric("Schedule D line 15 — Net long-term", f"${_sd_l15:,.0f}")
    _r8c.metric("Line 8 — Capital gain net income", f"${net_cap:,.0f}",
                "carried from Schedule D line 18")

    if _sd18 is None:
        st.warning("Schedule D has not been filled in yet — Line 8 is \\$0. Open the **📉 Schedule D — Capital Gains** page to enter transactions.")
    elif _sd_loss > 0:
        st.error(f"Schedule D produced a **net capital loss of \\${_sd_loss:,.0f}**. Under §1211(a) a C corporation cannot "
                 f"deduct it against ordinary income, so Line 8 is \\$0 — the loss is carried back 3 years and forward 5 years "
                 f"as a short-term capital loss instead.")

    irc([
        "<b>Line 8 is a carry-forward line, not an entry line.</b> On the real Form 1120 there is nothing to write here except "
        "the total from Schedule D line 18 — which is why this page shows it read-only."
        "<br><span style='color:#C53030'>Line 8 can never be negative. If Schedule D nets to a loss, Line 8 is $0 and the loss "
        "goes to the §1212(a) carryover — it never reduces ordinary income on page 1.</span>",
        "<b>Property types:</b> (1) <b>§1221 Capital assets</b> — investment property (stocks, bonds, land held for investment). (2) <b>§1231 Business property</b> — depreciable property used in trade/business; net §1231 gain → LTCG treatment; net §1231 loss → ordinary loss. (3) <b>Ordinary assets</b> — inventory, receivables; always ordinary income/loss.",
        "<b>C-Corp rules (§1211(a)):</b> Capital losses offset capital gains only — cannot offset ordinary income. Net capital loss: carryback 3 years, carryforward 5 years (always treated as short-term).",
        "<b>§1231 Look-back:</b> Prior 5-year §1231 ordinary losses recharacterize current §1231 gains as ordinary income — apply oldest year first.",
        "<b>§1033:</b> Involuntary conversion of a §1231 or capital asset (fire, condemnation, casualty) — gain DEFERRED if qualifying replacement property acquired within 2 yrs (3 yrs for real property). Enter only the taxable (non-deferred) portion on Schedule D. Deferred gain reduces replacement property's basis.",
        "<b>§1031:</b> Like-kind exchange of real property — gain DEFERRED into replacement property's basis. Post-TCJA: only real property qualifies (personal property no longer eligible). Identification within 45 days, acquisition within 180 days. No Schedule D entry if fully deferred.",
        "<b>§332:</b> Parent corporation (≥80% vote and value) recognizes NO gain or loss on liquidating distributions from a controlled subsidiary. Parent takes carryover basis in assets received. No entry on this return.",
    ])

    st.markdown("## Line 9 — Form 4797 Ordinary Gain")
    irc([
        "<b>What Form 4797 is:</b> <i>Sales of Business Property</i> — the return for disposing of <b>property used in a trade "
        "or business</b>, as opposed to Schedule D which covers investment assets. Four parts:"
        "<br>&nbsp;&nbsp;<b>Part I</b> — §1231 property held &gt; 1 year: nets to §1231 gain or loss."
        "<br>&nbsp;&nbsp;<b>Part II</b> — <b>ordinary</b> gains and losses: property held ≤ 1 year, net §1231 <i>losses</i>, and "
        "all depreciation recapture flowing up from Part III."
        "<br>&nbsp;&nbsp;<b>Part III</b> — computes §1245 / §1250 / §291 recapture, then pushes it into Part II."
        "<br>&nbsp;&nbsp;<b>Part IV</b> — §179 and §280F recapture when business use drops to 50% or less.",

        "<b>How it splits into two Form 1120 lines:</b>"
        "<br>&nbsp;&nbsp;Part II line 17 → <b>Line 9</b> (this line) — ordinary income, taxed at the full 21%."
        "<br>&nbsp;&nbsp;Part I net §1231 <i>gain</i> → §1231(c) look-back → Schedule D line 11 → <b>Line 8</b> — capital gain treatment."
        "<br><span style='color:#C53030'>A net §1231 <b>loss</b> never reaches Schedule D — it is an ordinary deduction and stays "
        "on Line 9, which is precisely the asymmetry §1231 gives: gains capital, losses ordinary.</span>",

        "<b>Deferrals have their own Form 4797 lines — there is no exclusion column:</b>"
        "<br>&nbsp;&nbsp;<b>§453 installment sale</b> → Part I line 4 (§1231) or Part II line 15 (ordinary). Gain is recognized "
        "as payments arrive, so only the recognized portion is entered."
        "<br>&nbsp;&nbsp;<b>§1031 like-kind exchange</b> → Part I line 5 or Part II line 16. Only the taxable boot is entered."
        "<br>&nbsp;&nbsp;<b>§1033 involuntary conversion</b> → Form 4684 flows in at Part I line 3 / Part II line 14."
        "<br><span style='color:#C53030'>This is why Line 9 needs no Tax Exclusion column: the deferral is handled by entering "
        "only the recognized amount on the right Form 4797 line, not by netting an adjustment against a book figure.</span>",
    ])

    _f_l17 = F4797["l17"]
    st.markdown(
        "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
        "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
        "<b>⚠️ Line 9 has NO input on Form 1120.</b> The figure is carried from <b>Form 4797, Part II, line 17</b> and "
        "cannot be typed in here.<br>You <b>must</b> enter dispositions of business property on the "
        "<b>🏭 Form 4797 — Business Property</b> page."
        "</div>", unsafe_allow_html=True)

    g4797_tax = _f_l17
    st.metric("Line 9 — Net gain or (loss) from Form 4797, Part II, line 17", f"${g4797_tax:,.0f}",
              "carried from Form 4797 Part II line 17")

    st.markdown("## Line 10 — Other Income")
    irc([
        "<b>§101:</b> Life insurance death benefit proceeds — 100% excluded from gross income. Enter full book amount in col 1; enter same amount as Tax Exclusion in col 2 → net taxable = $0. Exception §101(j): employer-owned life insurance (EOLI) requires employee notice-and-consent at policy inception; non-compliant policies: only premiums paid are excluded, excess is taxable.",
        "<b>§111:</b> Recovery of prior-year deductions (tax benefit rule) — if a deduction taken in a prior year produced a tax benefit and is now recovered (e.g., bad debt previously written off is paid), the recovery is taxable here.",
        "<b>Tax Exclusion column on Line 10 — what belongs there:</b>"
        "<br>&nbsp;&nbsp;<b>§101</b> life insurance death benefits — fully excluded."
        "<br>&nbsp;&nbsp;<b>§111</b> the portion of a recovery that produced <b>no</b> prior tax benefit — only the benefited part is taxable."
        "<br>&nbsp;&nbsp;<b>§108</b> cancellation of debt income excluded in bankruptcy or to the extent of insolvency "
        "<span style='color:#C53030'>(the excluded amount reduces tax attributes such as NOLs and basis under §108(b) — it is not free)</span>."
        "<br>&nbsp;&nbsp;<b>Federal income tax refunds</b> booked as income — never taxable, since the tax itself was never deductible."
        "<br>&nbsp;&nbsp;<b>§118</b> non-shareholder capital contributions that remain excludable post-TCJA.",
    ])
    _, _, oth_tax = tax_row("10", "Other income (see instructions—attach statement) — §101 life insurance, §111 recoveries", "other_income_book", "other_income_adj")

    st.markdown("---")
    gross_profit  = net_sales - cogs_tax
    line8_amount  = max(0.0, net_cap)
    total_income  = gross_profit + div_tax + int_tax + rent_tax + roy_tax + line8_amount + g4797_tax + oth_tax
    c1, c2, c3 = st.columns(3)
    c1.metric("Line 3 — Gross profit",          f"${gross_profit:,.0f}")
    c2.metric("Line 8 — Capital gain net income", f"${line8_amount:,.0f}",
              f"Net capital loss ${abs(net_cap):,.0f} carried forward" if net_cap < 0 else None)
    c3.metric("Line 11 — Total income",         f"${total_income:,.0f}")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — DEDUCTIONS
# ─────────────────────────────────────────────────────────────────────────────
elif section == "📤 Page 1 — Deductions":
    st.title("Page 1 — Deductions")
    st.markdown("Enter the **Book / AFS expense** in the first column. The **Disallowed (auto)** column is fully automatic — fixed rules (meals 50%, fines 100%) apply immediately; complex rules (§162(m), charitable 10%) pull from their calculators below. The **Tax Deduction** is computed automatically.")

    irc([
        '§162 General Rule: "All ordinary and necessary expenses paid or incurred during the taxable year in carrying on any trade or business."',
        "Ordinary: common in the industry. Necessary: appropriate and helpful. Reasonable: not extravagant — related-party transactions heavily scrutinized.",
        "Trade or business required — personal expenses (§262) and hobby losses (§183) do not qualify.",
    ])

    st.markdown("## Compensation")
    col_headers("deduction")
    m162_disallowed = st.session_state.get("m162_total_disallowed", 0.0)
    _, _, comp_tax = tax_row("12", "Compensation of Officers — Form 1125-E", "comp_officers_book",
                             computed_adj=m162_disallowed + S267["l12"] + S263A["l12"],
                             step=10_000.0, mode="deduction")
    if S267["l12"] > 0 or S263A["l12"] > 0:
        st.caption(
            f"§162(m) permanent disallowance ${m162_disallowed:,.0f} · "
            f"§267(a)(2) timing deferral ${S267['l12']:,.0f} · "
            f"§263A capitalised into inventory ${S263A['l12']:,.0f}")

    # Filing-requirement notice only — Form 1125-E changes no number on the return.
    _tr = TR["total"]
    if _tr >= 500_000:
        st.markdown(
            "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
            "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
            f"<b>📎 Form 1125-E must be attached.</b> Total receipts are <b>${_tr:,.0f}</b>, at or above the "
            "<b>$500,000</b> threshold.<br>List every officer with name, SSN, <b>percentage of time devoted to the "
            "business</b>, <b>percentage of stock owned</b>, and compensation. The total must agree with line 12 above."
            "</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#E7F6EC;border-left:5px solid #1E7A3C;padding:12px 16px;margin:8px 0;"
            "color:#14532D;-webkit-text-fill-color:#14532D;'>"
            f"<b>✅ Form 1125-E not required.</b> Total receipts are <b>${_tr:,.0f}</b>, below the "
            "<b>$500,000</b> threshold. Enter officer compensation on line 12 with no attachment."
            "</div>", unsafe_allow_html=True)

    with st.expander("How “total receipts” is measured for this threshold"):
        st.markdown(f"""
Not the same as **gross receipts**. The threshold uses line 1a **plus lines 4 through 10** —
so dividends, interest, rents, royalties and gains all count, even though none of them are
sales revenue.

| Line | Item | Amount |
|---|---|---|
| 1a | Gross receipts or sales | ${TR['l1a']:,.0f} |
| 4 | Dividends and inclusions | ${TR['l4']:,.0f} |
| 5 | Interest | ${TR['l5']:,.0f} |
| 6 | Gross rents | ${TR['l6']:,.0f} |
| 7 | Gross royalties | ${TR['l7']:,.0f} |
| 8 | Capital gain net income | ${TR['l8']:,.0f} |
| 9 | Net gain from Form 4797 | ${TR['l9']:,.0f} |
| 10 | Other income | ${TR['l10']:,.0f} |
| | **Total receipts** | **${_tr:,.0f}** |

Lines 2 and 3 are excluded: cost of goods sold is a cost, and gross profit is derived from
line 1a, so counting it would double up. A company with $480,000 of sales and $40,000 of
dividends is over the threshold at $520,000 even though its sales alone are not.

The same figure drives the Schedule K test for whether Schedules L, M-1 and M-2 can be
skipped, so it is worth knowing.
""")

    _, _, sal_tax  = tax_row("13", "Salaries & Wages (less employment credits)", "salaries_book",
                             computed_adj=S267["l13"] + S263A["l13"], step=10_000.0, mode="deduction")
    if S263A["l13"] > 0:
        st.caption(f"§263A moves ${S263A['l13']:,.0f} of wages into the inventory pool — the sold portion "
                   f"still reaches income through COGS this year.")

    if S263A["l12"] > 0 or S263A["l13"] > 0:
        st.caption(f"§263A share is set once as a percentage under **📥 Page 1 — Income → 🧮 Form 1125-A** "
                   f"({S263A['pct12']:.0%} of line 12, {S263A['pct13']:.0%} of line 13) — the amounts above are "
                   f"derived from the compensation entered here.")

    with st.expander("🧮 §267(a)(2) — Accrued Compensation Still Unpaid at Year-End"):
        st.checkbox("Corporation uses the accrual method", value=True, key="s267_accrual",
                    help="Cash-basis corporations deduct when paid, so this rule cannot apply.")
        if not st.session_state.get("s267_accrual", True):
            st.info("Cash method selected — §267(a)(2) does not apply. Nothing is deferred.")
        else:
            st.markdown("**Amounts accrued on the books but not yet paid at year-end**")
            k1, k2 = st.columns(2)
            k1.markdown("**Line 12 — Officers**")
            k1.number_input("Owed to a related person (>50% shareholder or family) ($)",
                            min_value=0.0, step=1_000.0, format="%.2f", key="s267_l12_related")
            k1.number_input("Owed to unrelated officers ($)",
                            min_value=0.0, step=1_000.0, format="%.2f", key="s267_l12_unrelated")
            k2.markdown("**Line 13 — Other salaries and wages**")
            k2.number_input("Owed to a related person ($)",
                            min_value=0.0, step=1_000.0, format="%.2f", key="s267_l13_related")
            k2.number_input("Owed to unrelated employees ($)",
                            min_value=0.0, step=1_000.0, format="%.2f", key="s267_l13_unrelated")

            st.checkbox("Unrelated amounts were actually paid within 2½ months after year-end",
                        key="s267_paid_25")

            d1, d2, d3 = st.columns(3)
            d1.metric("Line 12 deferred", f"${S267['l12']:,.0f}")
            d2.metric("Line 13 deferred", f"${S267['l13']:,.0f}")
            d3.metric("Total deferred", f"${S267['total']:,.0f}",
                      "deductible when paid" if S267["total"] else None)

            if S267["total"] > 0:
                st.warning(
                    f"**\\${S267['total']:,.0f} of accrued compensation is not deductible this year.** "
                    f"It is a **timing** difference, not a permanent one — the deduction returns in the year "
                    f"the recipient includes it in income. Track it as a temporary difference on Schedule M-1.")

        irc([
            "<b>§267(a)(2) — the matching rule:</b> An accrual-method corporation cannot deduct an accrued expense "
            "owed to a <b>related cash-method person</b> until that person actually includes it in income."
            "<br><span style='color:#C53030'>For a C corporation, §267(b)(2) makes any shareholder owning "
            "<b>more than 50%</b> a related person — and §267(c) attributes family members' shares, so a spouse or "
            "child's holding can push an owner over the line.</span>"
            "<br>Practical effect in a closely-held company: the owner-manager's year-end bonus accrued on 31 December "
            "and paid in March is <b>not deductible</b> in the accrual year.",

            "<b>The 2½-month rule — and why it does not rescue related parties:</b> Compensation accrued to "
            "<b>unrelated</b> employees is deductible in the accrual year provided it is actually paid within "
            "<b>2½ months</b> after year-end. Miss that window and it becomes deferred compensation under §404(a)(5), "
            "deductible only when included in the employee's income."
            "<br><span style='color:#C53030'>§267(a)(2) overrides this for related persons: no 2½-month grace period "
            "exists for them at all.</span>",

            "<b>This is a temporary difference, not a disallowance.</b> The deduction is not lost — it moves to the "
            "year of payment."
            "<br>On Schedule M-1 it is an addition in the accrual year and a subtraction when paid. Contrast §162(m), "
            "which is a <b>permanent</b> difference — that money is never deductible.",
        ])
    is_pub = st.checkbox("Publicly Traded Corporation — §162(m) applies", key="is_public")
    if is_pub:
        covered_label = (
            "# Covered Employees (CEO, CFO, next 5 highest-paid — 2027+ rule)"
            if int(TAX_YEAR) >= 2027
            else "# Covered Employees (CEO, CFO, next 3 highest-paid)"
        )
        st.number_input(covered_label, min_value=1, max_value=15, key="covered_employees")
        if int(TAX_YEAR) >= 2027:
            st.info("§162(m) expanded for 2027+: covered employees = CEO + CFO + next **7** highest-compensated (up from 5 total).")
    irc([
        f"<b>§162(m) — Publicly traded corps only:</b> Deduction for compensation paid to any <b>covered employee</b> is capped at <b>$1 million per person per year</b>."
        f"<br>Applies to: salary, bonuses, and any performance-based compensation — the performance-pay exception was repealed by <b>TCJA (Tax Cuts and Jobs Act) 2017</b>."
        f"<br><span style='color:#C53030'>Does <b>NOT</b> apply to: qualified retirement plan contributions, non-taxable fringe benefits.</span>",
        f"<b>Covered employees ({int(TAX_YEAR)}):</b> {'CEO + CFO + next <b>7</b> highest-compensated officers (expanded rule effective 2027)' if int(TAX_YEAR) >= 2027 else 'CEO (principal executive officer) + CFO (principal financial officer) + <b>3</b> other highest-paid officers'}. Once an employee is covered, they remain covered permanently — no rotation out even after leaving.",
        "Enter total book compensation in the Book column. Use the §162(m) calculator below to compute the disallowance — the result auto-fills the Disallowed column.",
        "<b>Subject to cap:</b> salary, bonuses, taxable fringe benefits (e.g., personal use of company jet). <b>NOT subject to cap:</b> qualified retirement plan contributions, non-taxable fringe benefits (e.g., employer-paid health insurance).",
    ])

    if is_pub:
        with st.expander("🧮 §162(m) Per-Employee Compensation Breakdown", expanded=False):
            st.caption("Enter each covered employee's compensation components. Non-taxable fringe benefits are excluded from the $1M cap.")
            n_emp = st.number_input("Number of covered employees to analyze", min_value=1, max_value=10, step=1, key="m162_n_emp")
            total_disallowed = 0.0
            for i in range(int(n_emp)):
                st.markdown(f"**Employee {i+1}**")
                e1, e2, e3, e4 = st.columns(4)
                cash   = e1.number_input("Cash Comp ($)",             min_value=0.0, step=10_000.0, format="%.2f", key=f"m162_cash_{i}")
                bonus  = e2.number_input("Performance Bonus ($)",     min_value=0.0, step=10_000.0, format="%.2f", key=f"m162_bonus_{i}")
                fringe = e3.number_input("Taxable Fringes ($)",       min_value=0.0, step=1_000.0,  format="%.2f", key=f"m162_fringe_{i}")
                exempt = e4.number_input("Non-Taxable Fringes + Retirement Plan ($)", min_value=0.0, step=1_000.0, format="%.2f", key=f"m162_exempt_{i}")
                subject_to_cap = cash + bonus + fringe
                deductible     = min(subject_to_cap, 1_000_000.0) + exempt
                disallowed     = max(0.0, subject_to_cap - 1_000_000.0)
                total_disallowed += disallowed
                m1e, m2e, m3e = st.columns(3)
                m1e.metric("Subject to $1M Cap", f"${subject_to_cap:,.0f}")
                m2e.metric("Deductible", f"${deductible:,.0f}")
                m3e.metric("Disallowed (§162(m))", f"${disallowed:,.0f}")
                st.divider()
            st.metric("Total §162(m) Disallowed (all employees)", f"${total_disallowed:,.0f}")
            st.session_state["m162_total_disallowed"] = total_disallowed

    st.markdown("## Operating Expenses")
    col_headers("deduction")
    _, _, rep_tax = tax_row("14", "Repairs & Maintenance", "repairs_book",
                            computed_adj=S263A["l14"], mode="deduction")
    if S263A["l14"] > 0:
        st.caption(f"§263A capitalises {S263A['pct14']:.0%} of repairs into inventory as an indirect production "
                   f"cost — set under **📥 Page 1 — Income → 🧮 Form 1125-A**. The sold portion still reaches "
                   f"income through COGS this year.")
    irc([
        "<b>Routine repair/maintenance — immediately deductible</b>: costs that are (1) <b>preventative or cyclical</b> in nature AND (2) essential to the <b>ongoing care</b> of the asset (e.g., oil changes, HVAC servicing, repainting).",
        "<b>Must be capitalized</b> if the cost is a <b>betterment</b> (cures a defect or materially adds capacity/quality), a <b>restoration</b> (rebuilds to like-new condition or replaces a major component), or adapts the asset to a <b>new and different use</b>. Capitalize and depreciate over remaining useful life.",
        "Enter only the deductible repair/maintenance portion here. Move capitalized improvement costs to the Depreciation section (Line 20) as a new asset.",
    ])

    st.markdown("**[Line 15] Bad Debt — §166 (book reserve ≠ tax charge-off)**")
    c1, c2, c3 = st.columns([5, 4, 3])
    c1.number_input("[15] Book Bad Debt Reserve (GAAP — not deductible)", min_value=0.0, step=1_000.0, format="%.2f", key="bad_debt_book_reserve")
    bad_debt_tax_val = c2.number_input("Tax Specific Charge-Off Only ($)", min_value=0.0, step=1_000.0, format="%.2f", key="bad_debt_tax")
    c3.metric("Tax Deduction", f"${bad_debt_tax_val:,.0f}")
    irc([
        "§166: Specific charge-off method only — deduct when debt is wholly/partially worthless with documented evidence.",
        "GAAP reserve (book) is NOT deductible — temporary difference. Enter book reserve left; actual charge-off in middle column as the tax amount.",
    ])
    _, _, rent_ded = tax_row("16", "Rents", "rents_book",
                             computed_adj=S263A["l16"], mode="deduction")
    if S263A["l16"] > 0:
        st.caption(f"§263A capitalises {S263A['pct16']:.0%} of rent into inventory — set under "
                   f"**📥 Page 1 — Income → 🧮 Form 1125-A**.")
    irc([
        "<b>§162(a)(3) — it has to be a true lease.</b> Rent is deductible only where the corporation is <b>not taking "
        "title</b> and has <b>no equity</b> in the property."
        "<br><span style='color:#C53030'>A “lease” with a bargain buyout, or where payments approximate the purchase "
        "price, is recharacterised as an instalment purchase: capitalise and depreciate the asset, and only the "
        "interest element is deductible.</span>",

        "<b>Related-party rent must be reasonable.</b> The classic closely-held pattern is the owner holding the "
        "building personally and leasing it to the corporation."
        "<br><span style='color:#C53030'>Excess rent is recharacterised as a constructive dividend — non-deductible to "
        "the corporation and still taxable to the shareholder, the same trap as excessive officer compensation.</span>",

        "<b>§467 stepped or deferred rent:</b> where a lease has rising or falling rents, or prepayments, and total "
        "consideration exceeds <b>$250,000</b>, rent must be levelled using constant or proportional rental accrual "
        "rather than followed as billed.",

        "<b>Prepaid rent — the 12-month rule</b> (Reg. §1.263(a)-4(f)): a prepayment is deductible now if the benefit "
        "does not exceed 12 months <i>and</i> does not run beyond the end of the following tax year. Otherwise "
        "capitalise and amortise."
        "<br>Leasehold improvements are not rent at all — capitalise and depreciate them (QIP 15 years, other "
        "nonresidential real property 39 years).",
    ])

    _, _, tax_lic  = tax_row("17", "Taxes & Licenses", "taxes_book",
                             computed_adj=S263A["l17"], mode="deduction")
    if S263A["l17"] > 0:
        st.caption(f"§263A capitalises {S263A['pct17']:.0%} of taxes into inventory — set under "
                   f"**📥 Page 1 — Income → 🧮 Form 1125-A**.")
    irc([
        "<b>Goes on this line:</b> state and local income and franchise taxes · real property tax · personal property "
        "tax · the <b>employer</b> share of payroll taxes (FICA, FUTA, SUTA) · excise taxes · business licences, "
        "permits and regulatory fees."
        "<br><span style='color:#C53030'>The $10,000 SALT cap is a §164(b)(6) rule for <b>individuals only</b>. A C "
        "corporation deducts state and local taxes in full.</span>",

        "<b>§275 — what is never deductible here:</b>"
        "<br>&nbsp;&nbsp;<b>Federal income tax</b>;"
        "<br>&nbsp;&nbsp;the <b>employee</b> share of FICA (that is the employee's tax, not the company's);"
        "<br>&nbsp;&nbsp;<b>foreign income taxes</b> if the Foreign Tax Credit is being claimed — credit or deduction, "
        "not both;"
        "<br>&nbsp;&nbsp;special assessments for local benefits that increase property value — those are capitalised "
        "into basis.",

        "<b>Tariffs and customs duties do not belong here.</b> They are a cost of acquiring the goods, so under §471 "
        "and §263A they enter <b>inventory</b> and are recovered through COGS."
        "<br><span style='color:#C53030'>Sales tax follows whatever it was paid on: inventory → inventory cost; a "
        "depreciable asset → added to basis and depreciated; ordinary supplies → deducted with that expense. Sales tax "
        "<i>collected from customers</i> is a liability, not an expense at all.</span>",

        "<b>Licences:</b> operating and professional licences, regulatory permits, annual franchise or trade-name fees, "
        "vehicle registration. A multi-year licence follows the same 12-month rule as prepaid rent — beyond that, "
        "capitalise and amortise.",
    ])

    st.markdown("## Interest Expense — §163(j)")
    col_headers("deduction")
    int_book_val = st.number_input("[18] Interest Expense — Book Amount", min_value=0.0, step=1_000.0, format="%.2f", key="interest_book")
    with st.expander("📚 §163(j) — Business Interest Limitation Rules"):
        irc([
            "<b>§163(j) Limitation:</b> BIE (Business Interest Expense) deduction cannot exceed the <b>sum</b> of:"
            "<br>&nbsp;&nbsp;(1) BII (Business Interest Income) for the year;"
            "<br>&nbsp;&nbsp;(2) <b>30%</b> of ATI (Adjusted Taxable Income) — cannot go below zero;"
            "<br>&nbsp;&nbsp;(3) Floor plan financing interest (dealer inventory financing — car dealerships).",
            "<b>C-Corp rule:</b> Congress treats <b>all interest income of a C-corp as BII</b> — so BII = total interest income reported on the return.",
            "<b>ATI</b> = taxable income <i>before</i>: BIE or BII, NOL (Net Operating Loss) deduction, depreciation/amortization/depletion, QBI (Qualified Business Income) deduction."
            "<br><span style='color:#C53030'><b>2022+: D&A (Depreciation &amp; Amortization) no longer added back</b> → ATI ≈ EBIT (Earnings Before Interest &amp; Taxes), not EBITDA.</span>",
            "<b>Disallowed BIE</b> carries forward indefinitely and retains its character.",
            f"<span style='color:#C53030'><b>Small business exemption §163(j)(3):</b> the limitation does not apply at all if "
            f"3-year average annual gross receipts do not exceed the <b>§448(c)</b> threshold — "
            f"<b>${sec448_threshold(TAX_YEAR):,.0f}</b> for {int(TAX_YEAR)}. Same test as the §263A(i) exemption.</span>",
            "§265(a)(2): Interest on debt used to purchase/carry tax-exempt bonds — fully non-deductible. Include only deductible business interest in the book amount above.",
        ])

    with st.expander("🧮 §163(j) Business Interest Limitation Calculator", expanded=False):
        st.caption("Computes the deductible BIE limit: BII + 30% ATI + floor plan financing.")
        ji1, ji2 = st.columns(2)
        j_bii       = ji1.number_input("Business Interest Income (BII) ($)", min_value=0.0, step=1_000.0, format="%.2f", key="bii_income",
                                       help="For C-corps: all interest income on the return")
        j_ati       = ji1.number_input("Adjusted Taxable Income (ATI) ($)",  min_value=0.0, step=10_000.0, format="%.2f", key="ati_override",
                                       help="TI before BIE/BII, NOL, D&A, QBI. 2022+: no D&A addback (≈EBIT)")
        j_floor     = ji2.number_input("Floor Plan Financing Interest ($)",   min_value=0.0, step=1_000.0, format="%.2f", key="floor_plan_interest",
                                       help="Dealer inventory financing (car dealerships). Leave 0 if N/A.")
        j_bie       = st.session_state.get("interest_book", 0.0)
        j_cf        = ji2.number_input("BIE Carryforward from prior years ($)", min_value=0.0, step=1_000.0, format="%.2f",
                                       key="interest_cf_prior")

        # §163(j)(3) uses the same §448(c) gross receipts test as the §263A(i) exemption.
        j_exempt = S263A["avg"] <= S263A["threshold"]
        j_30pct_ati = max(0.0, j_ati * 0.30)
        j_total_bie = j_bie + j_cf
        if j_exempt:
            j_limit   = j_total_bie
            j_allowed = j_total_bie
            j_excess  = 0.0
            st.markdown(
                "<div style='background:#E7F6EC;border-left:5px solid #1E7A3C;padding:12px 16px;margin:8px 0;"
                "color:#14532D;-webkit-text-fill-color:#14532D;'>"
                f"<b>✅ Exempt from §163(j).</b> Average gross receipts of <b>${S263A['avg']:,.0f}</b> do not exceed "
                f"the §448(c) threshold of <b>${S263A['threshold']:,.0f}</b> for {int(TAX_YEAR)}.<br>"
                "Business interest expense is fully deductible — the 30% ATI limit is not computed."
                "</div>", unsafe_allow_html=True)
        else:
            j_limit   = j_bii + j_30pct_ati + j_floor
            j_allowed = min(j_total_bie, j_limit)
            j_excess  = max(0.0, j_total_bie - j_limit)

        jc1, jc2, jc3 = st.columns(3)
        jc1.metric("30% of ATI", f"${j_30pct_ati:,.0f}", f"30% × ${j_ati:,.0f}")
        jc2.metric("§163(j) Limit", f"${j_limit:,.0f}",
                   "no limit — exempt" if j_exempt else f"BII {j_bii:,.0f} + 30%ATI + floor plan {j_floor:,.0f}")
        jc3.metric("Allowed Deduction", f"${j_allowed:,.0f}", f"Excess CF → ${j_excess:,.0f}")

        if j_total_bie > 0:
            st.markdown(f"""
| | Amount |
|---|---|
| Current-year BIE | ${j_bie:,.0f} |
| Prior-year carryforward applied | ${min(j_cf, max(0.0, j_limit - j_bie)):,.0f} |
| **Total deduction allowed** | **${j_allowed:,.0f}** |
| Disallowed BIE → carryforward | ${j_excess:,.0f} |
""")
        if j_excess > 0:
            st.warning(f"BIE exceeds §163(j) limit by \\${j_excess:,.0f} — carries forward indefinitely.")

    st.markdown("## Charitable Contributions")
    col_headers("deduction")
    _, _, char_tax = tax_row("19", "Charitable Contributions", "charitable_book", mode="deduction")
    irc([
        "<b>§170 General rule:</b> Deductible in the tax year <u>actually paid</u>, regardless of the corporation's accounting method.",
        "<b>§170(a)(2) Special rule — accrual method corps only:</b> May deduct in the <i>current</i> tax year if (1) contribution is <b>authorized by the board of directors</b> before the end of the tax year, AND (2) <b>paid by the due date</b> of the return (April 15 for calendar-year corps).",
        "<b>§170(b)(2) 10% limitation:</b> Deduction capped at <b>10% of taxable income</b> computed <i>before</i>: (a) the charitable deduction itself, (b) the DRD, (c) NOL carrybacks, (d) capital loss carrybacks. ⚠️ NOL and capital loss <u>carryforwards</u> <b>are</b> included in the 10% base.",
        "<b>5-year carryforward:</b> Excess contributions (above the 10% limit) carry forward up to 5 years. <b>Current-year contributions are always used first</b> before carryovers. The 10% limitation still applies in carryforward years.",
    ])

    with st.expander("🧮 Charitable Contribution Deduction Calculator", expanded=False):
        st.caption("Computes the 10% limitation and applies current-year contributions before carryforwards.")
        cc1, cc2 = st.columns(2)
        cc_current   = cc1.number_input("Current-Year Contribution ($)",          min_value=0.0, step=1_000.0, format="%.2f", key="cc_current")
        cc_cf_prior  = cc2.number_input("Carryforward from Prior Years ($)",       min_value=0.0, step=1_000.0, format="%.2f", key="cc_cf_prior")
        cc_ti_base   = cc1.number_input("Taxable Income Before Charitable & DRD ($)",
                                        min_value=0.0, step=10_000.0, format="%.2f", key="cc_ti_base",
                                        help="TI before charitable deduction, DRD, NOL carrybacks, cap loss carrybacks")

        limit_10pct  = cc_ti_base * 0.10
        total_avail  = cc_current + cc_cf_prior

        # Current year used first
        cy_used      = min(cc_current, limit_10pct)
        room_after_cy = max(0.0, limit_10pct - cy_used)
        cf_used      = min(cc_cf_prior, room_after_cy)
        total_allowed = cy_used + cf_used
        cy_excess    = cc_current - cy_used          # becomes new carryforward
        cf_remaining = cc_cf_prior - cf_used         # old carryforward not yet used

        r1, r2, r3 = st.columns(3)
        r1.metric("10% Limit", f"${limit_10pct:,.0f}", f"10% × ${cc_ti_base:,.0f}")
        r2.metric("Total Allowed Deduction", f"${total_allowed:,.0f}", "current year first, then CF")
        r3.metric("New Carryforward", f"${cy_excess + cf_remaining:,.0f}",
                  f"CY excess \\${cy_excess:,.0f} + prior CF remaining \\${cf_remaining:,.0f}")

        if total_avail > 0:
            st.markdown(f"""
| | Amount |
|---|---|
| Current-year contribution | ${cc_current:,.0f} |
| Used this year (current year first) | ${cy_used:,.0f} |
| Prior carryforward applied | ${cf_used:,.0f} |
| **Total deduction allowed** | **${total_allowed:,.0f}** |
| Current-year excess → 5-yr carryforward | ${cy_excess:,.0f} |
| Prior carryforward remaining | ${cf_remaining:,.0f} |
""")
        if cy_excess > 0:
            st.warning(f"Current-year contribution exceeds 10% limit by \\${cy_excess:,.0f} — carry forward up to 5 years.")

    st.markdown("## Depreciation & Amortization — Line 20 / Form 4562")
    if S263A["l20"] > 0:
        st.caption(f"§263A capitalises {S263A['pct20']:.0%} of the \\${S263A['dep_gross']:,.0f} computed "
                   f"depreciation — \\${S263A['l20']:,.0f} — into inventory, leaving "
                   f"\\${S263A['dep_gross'] - S263A['l20']:,.0f} deductible here. "
                   f"Set under **📥 Page 1 — Income → 🧮 Form 1125-A**.")
    with st.expander("📚 Depreciation — Capitalization, Basis & De Minimis Rules"):
        irc([
            "§263: Business-use assets with useful life &gt; 1 year must be <b>capitalized</b> — not expensed immediately — and recovered through depreciation or amortization over the asset's useful life.",
            "Depreciation begins on the <b>date placed in service</b> (the date the asset is ready and available for use), not the purchase date.",
            "<b>Cost basis</b> = purchase price + <b>all costs</b> incurred to prepare the asset for use (sales tax, installation, delivery charges, etc.).",
            "<b>Adjusted basis</b> = cost basis − accumulated cost recovery (depreciation taken to date). Used to compute gain/loss on disposal.",
            "If a single purchase includes multiple assets (e.g., building + land), allocate the purchase price among assets based on <b>FMV</b>. Land is non-depreciable.",
            "<b>Special acquisition basis rules</b> — (1) <b>Converted personal-use asset</b>: basis = lesser of original cost or FMV at date of conversion to business use; (2) <b>Gifted asset</b>: carryover basis from the donor (donor's adjusted basis transfers to recipient); (3) <b>Inherited asset</b>: stepped-up basis = FMV on the date of the decedent's death (§1014); (4) <b>Like-kind exchange (§1031)</b>: substituted basis = adjusted basis of the relinquished asset (gain deferred into replacement property).",
            "<b>De minimis safe harbor</b> (Treas. Reg. §1.263(a)-1(f)): may immediately deduct low-cost assets instead of capitalizing if both conditions are met:"
            "<br>&nbsp;&nbsp;(1) Written accounting policy in place at start of year to expense items below the threshold;"
            "<br><span style='color:#C53030'>&nbsp;&nbsp;(2) Cost per item ≤ <b>$5,000</b> (with AFS — Applicable Financial Statement, e.g., audited GAAP financials) or ≤ <b>$2,500</b> (without AFS).</span>"
            "<br>Per-item limit — each invoice line item is evaluated separately.",
        ])

    with st.expander("🧮 Asset Basis Calculator", expanded=False):
        st.caption("Determine the correct tax basis before entering asset cost into the depreciation section.")
        acq_type = st.radio("Acquisition Type", [
            "Purchase", "Personal-Use Conversion", "Gift", "Inheritance", "Like-Kind Exchange (§1031)"
        ], horizontal=False, key="basis_acq_type")

        if acq_type == "Purchase":
            bc1, bc2 = st.columns(2)
            b_price    = bc1.number_input("Purchase Price ($)",       min_value=0.0, step=1_000.0, format="%.2f", key="b_price")
            b_salestax = bc1.number_input("Sales Tax ($)",            min_value=0.0, step=100.0,   format="%.2f", key="b_salestax")
            b_install  = bc2.number_input("Installation Costs ($)",   min_value=0.0, step=100.0,   format="%.2f", key="b_install")
            b_delivery = bc2.number_input("Delivery / Other ($)",     min_value=0.0, step=100.0,   format="%.2f", key="b_delivery")
            basis = b_price + b_salestax + b_install + b_delivery
            st.metric("Tax Basis", f"${basis:,.0f}")
            st.caption("Cost basis = purchase price + all costs to prepare the asset for use.")

        elif acq_type == "Personal-Use Conversion":
            bc1, bc2 = st.columns(2)
            b_cost = bc1.number_input("Original Cost ($)",              min_value=0.0, step=1_000.0, format="%.2f", key="b_pu_cost")
            b_fmv  = bc2.number_input("FMV at Date of Conversion ($)",  min_value=0.0, step=1_000.0, format="%.2f", key="b_pu_fmv")
            basis  = min(b_cost, b_fmv) if (b_cost > 0 or b_fmv > 0) else 0.0
            lower  = "Original Cost" if b_cost <= b_fmv else "FMV"
            st.metric("Tax Basis (lesser of cost or FMV)", f"${basis:,.0f}")
            if b_cost > 0 or b_fmv > 0:
                st.caption(f"Using **{lower}** — the lower of the two values.")

        elif acq_type == "Gift":
            b_donor_basis = st.number_input("Donor's Adjusted Basis ($)", min_value=0.0, step=1_000.0, format="%.2f", key="b_gift_basis")
            b_donor_fmv   = st.number_input("FMV at Date of Gift ($)",    min_value=0.0, step=1_000.0, format="%.2f", key="b_gift_fmv")
            basis = b_donor_basis
            st.metric("Tax Basis (carryover from donor)", f"${basis:,.0f}")
            if b_donor_fmv > 0 and b_donor_basis > b_donor_fmv:
                st.warning("Donor's basis exceeds FMV at gift date. If the asset is later sold at a loss, the loss basis is FMV — not the donor's basis.")
            st.caption("Recipient takes the donor's adjusted basis. Holding period also carries over.")

        elif acq_type == "Inheritance":
            b_fmv_dod = st.number_input("FMV at Date of Decedent's Death ($)", min_value=0.0, step=1_000.0, format="%.2f", key="b_inherit_fmv")
            basis = b_fmv_dod
            st.metric("Tax Basis (stepped-up — §1014)", f"${basis:,.0f}")
            st.caption("Inherited assets receive a stepped-up basis to FMV on date of death. Any pre-death appreciation is permanently excluded.")

        elif acq_type == "Like-Kind Exchange (§1031)":
            bc1, bc2 = st.columns(2)
            b_old_basis  = bc1.number_input("Adjusted Basis of Relinquished Asset ($)", min_value=0.0, step=1_000.0, format="%.2f", key="b_1031_old")
            b_boot_recv  = bc1.number_input("Boot Received ($, if any)",                min_value=0.0, step=100.0,   format="%.2f", key="b_1031_boot")
            b_gain_recog = bc2.number_input("Gain Recognized on Boot ($)",              min_value=0.0, step=100.0,   format="%.2f", key="b_1031_gain")
            basis = b_old_basis - b_boot_recv + b_gain_recog
            st.metric("Tax Basis of Replacement Asset", f"${basis:,.0f}")
            st.caption("Substituted basis = old basis − boot received + gain recognized. Deferred gain is embedded in the lower basis of the new asset.")
    # MACRS rate tables (200DB switching to SL, half-year convention)
    MACRS_RATES = {
        5:  [0.2000, 0.3200, 0.1920, 0.1152, 0.1152, 0.0576],
        7:  [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446],
        15: [0.0500, 0.0950, 0.0855, 0.0770, 0.0693, 0.0623, 0.0590, 0.0590,
             0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0295],
        39: None,  # straight-line mid-month, handled separately
    }
    ASSET_LABELS = {
        5:  "5-yr — Vehicles, Computers (200DB)",
        7:  "7-yr — Furniture, Fixtures, Equipment (200DB)",
        15: "15-yr — Land Improvements (150DB)",
        39: "39-yr — Commercial Real Property (SL, Mid-Month)",
    }

    def tooltip(text):
        return f'<span title="{text}" style="cursor:help; font-size:14px; color:#4A7AC7; margin-left:4px;">ℹ️</span>'

    dep_method = st.radio("Depreciation Method", ["MACRS", "§179 Expensing", "Bonus Depreciation", "Cost Segregation"],
                          horizontal=True, key="dep_method")
    c1, c2 = st.columns(2)
    asset_cost   = c1.number_input(L("20a", "Asset Tax Basis ($)"), min_value=0.0, step=10_000.0, format="%.2f", key="asset_cost")
    year_placed  = c2.number_input(L("20b", "Year Placed in Service", "year"), min_value=2010, max_value=2040, key="year_placed")
    book_dep     = c1.number_input(L("20c", "Book Depreciation — for M-1 only"), min_value=0.0, step=1_000.0, format="%.2f", key="book_depreciation")

    if dep_method == "MACRS":
        d1, d2, d3 = st.columns(3)
        macrs_life   = d1.selectbox("Asset Class", list(ASSET_LABELS.keys()),
                                    format_func=lambda x: ASSET_LABELS[x], key="macrs_life")
        placed_month = d2.number_input("Month Placed in Service (1–12)", min_value=1, max_value=12, step=1, key="macrs_month")

        # Mid-quarter test inputs (personal property only)
        tax_dep_auto = 0.0
        if macrs_life in (5, 7, 15):
            total_tpp    = d3.number_input("Total TPP placed in service this year ($)", min_value=0.0, step=10_000.0, format="%.2f", key="total_placed_in_service")
            q4_tpp       = d3.number_input("TPP placed in service in Q4 ($)", min_value=0.0, step=10_000.0, format="%.2f", key="q4_tpp")
            mq_pct       = (q4_tpp / total_tpp) if total_tpp > 0 else 0.0
            use_mq       = mq_pct > 0.40

            # Convention factor: half-year vs mid-quarter
            if use_mq:
                quarter = (placed_month - 1) // 3 + 1
                # Mid-quarter: fraction = (quarter - 0.5) / 4 quarters
                conv_factor_y1 = (quarter - 0.5) / 4
                conv_label = f"Mid-Quarter (Q{quarter} placed) — Q4={mq_pct:.0%} > 40%"
            else:
                conv_factor_y1 = 0.5   # half-year: always 50% in year 1
                conv_label = "Half-Year (default)"

            rates = MACRS_RATES[macrs_life]
            tax_year_int = int(TAX_YEAR)
            recovery_year = tax_year_int - int(year_placed) + 1

            if 1 <= recovery_year <= len(rates):
                rate = rates[recovery_year - 1]
                if recovery_year == 1:
                    rate = rate * (conv_factor_y1 / 0.5)  # adjust year-1 rate for convention
                tax_dep_auto = asset_cost * rate
            elif recovery_year == len(rates) + 1:
                # Disposal year — apply convention
                if use_mq:
                    quarter = (placed_month - 1) // 3 + 1
                    disp_factor = (quarter - 0.5) / 4
                else:
                    disp_factor = 0.5
                full_yr_rate = rates[-1]
                tax_dep_auto = asset_cost * full_yr_rate * disp_factor

            st.markdown(
                f'**Convention:** {conv_label} {tooltip("Half-year: all personal property treated as placed in service mid-year. Mid-quarter required if >40% of all TPP cost basis placed in service in Q4 — applied to ALL TPP that year.")}',
                unsafe_allow_html=True
            )

        else:  # 39-yr real property, mid-month convention
            total_tpp = 0.0
            annual_rate = 1 / 39
            tax_year_int = int(TAX_YEAR)
            recovery_year = tax_year_int - int(year_placed) + 1
            if recovery_year == 1:
                months_remaining = 12 - placed_month + 0.5  # mid-month
                tax_dep_auto = asset_cost * annual_rate * (months_remaining / 12)
            elif 2 <= recovery_year <= 39:
                tax_dep_auto = asset_cost * annual_rate
            elif recovery_year == 40:
                months_held = placed_month - 0.5
                tax_dep_auto = asset_cost * annual_rate * (months_held / 12)
            st.markdown(
                f'**Convention:** Mid-Month (real property always) {tooltip("Real property is treated as placed in service / disposed at the midpoint of the month. Year 1 deduction = annual rate × (months remaining including 0.5 for placed month) / 12.")}',
                unsafe_allow_html=True
            )

        m1, m2, m3 = st.columns(3)
        m1.metric("Recovery Year", f"Year {int(TAX_YEAR) - int(year_placed) + 1}")
        m2.metric("Tax Depreciation (auto)", f"${tax_dep_auto:,.0f}")
        m3.metric("Book vs Tax Difference", f"${book_dep - tax_dep_auto:,.0f}")
        st.markdown(
            f'ℹ️ Asset lives: Vehicles/Computers = 5yr · Furniture/Equipment = 7yr · Land Improvements = 15yr · Commercial Building = 39yr · Residential Rental = 27.5yr {tooltip("Source: IRS Pub 946. Know 5yr (vehicles, computers), 7yr (furniture/fixtures), 27.5yr (residential rental — people live there), 39yr (commercial — people work there).")}',
            unsafe_allow_html=True
        )

    elif dep_method == "§179 Expensing":
        total_tpp = st.number_input(L("20d", "Total §179 Property Placed in Service This Year"), min_value=0.0,
                        step=10_000.0, format="%.2f", key="total_placed_in_service")
        _ = 0  # macrs_month / q4_tpp not needed for §179
        limit_179 = 1_285_000
        phase_out  = max(0, total_tpp - 3_220_000)
        allowed    = max(0, min(asset_cost, limit_179 - phase_out))
        tax_dep_auto = allowed
        m1, m2 = st.columns(2)
        m1.metric("§179 Deduction (auto)", f"${tax_dep_auto:,.0f}")
        m2.metric("Phase-out reduction", f"${phase_out:,.0f}")
        st.markdown(
            f'ℹ️ §179 rules {tooltip("2025: $1,285,000 limit; phases out $1-for-$1 above $3,220,000 total placed in service. Cannot create a loss. Personal property (§1245) only — not buildings.")}',
            unsafe_allow_html=True
        )

    elif dep_method == "Bonus Depreciation":
        rates_bonus = {2023: 0.80, 2024: 0.60, 2025: 0.40, 2026: 0.20, 2027: 0.0}
        rate_b      = rates_bonus.get(int(TAX_YEAR), 0.0)
        tax_dep_auto = asset_cost * rate_b
        total_tpp    = 0.0
        m1, m2 = st.columns(2)
        m1.metric(f"Bonus Rate ({int(TAX_YEAR)})", f"{rate_b:.0%}")
        m2.metric("Bonus Deduction (auto)", f"${tax_dep_auto:,.0f}")
        st.markdown(
            f'ℹ️ §168(k) phase-out {tooltip("TCJA phase-out: 80% (2023) → 60% (2024) → 40% (2025) → 20% (2026) → 0% (2027+). Applies to MACRS property with recovery period ≤ 20 years only.")}',
            unsafe_allow_html=True
        )

    elif dep_method == "Cost Segregation":
        tax_dep_auto = 0.0
        total_tpp    = 0.0
        irc([
            "Cost Segregation: 5-yr (17.5%), 7-yr (22.5%), 15-yr land improvements (12.5%), 39-yr structure (47.5%). Reclassified components qualify for bonus depreciation.",
        ])

    st.markdown("## Organizational & Start-Up Costs — §248 / §195")
    with st.expander("📚 §248 / §195 — Org & Start-Up Cost Rules"):
        irc([
            "<b>Organizational Expenditures (§248)</b>: costs incident to the <i>creation</i> of the corporation — legal fees for drafting charter/bylaws, temporary directors, fees paid to the state of incorporation. <b>NOT</b> costs of issuing stock.",
            "<b>Start-Up Costs (§195)</b>: costs incurred <i>before the first day of business</i> — marketing surveys, pre-operating advertising, rent before generating income, salaries paid before business opens.",
            "<b>Immediate deduction</b>: elect to deduct up to <b>$5,000</b> in the year business begins. Reduced dollar-for-dollar by the amount total costs exceed <b>$50,000</b>. If total ≥ $55,000 → $0 immediate deduction.",
            "<b>Amortization</b>: remaining balance amortized ratably over <b>180 months</b> (15 years) beginning with the month business begins. Uses <b>full-month convention</b> (first month counts in full).",
            "Election is <b>automatic</b> — deemed to have been made unless the taxpayer affirmatively opts out. Both §248 and §195 follow the same rules and same dollar limits.",
        ])

    with st.expander("🧮 Org & Start-Up Cost Calculator", expanded=False):
        st.caption("Applies to the tax year the corporation begins business.")
        oc1, oc2 = st.columns(2)
        org_costs    = oc1.number_input("Total Organizational Costs (§248) ($)",  min_value=0.0, step=1_000.0, format="%.2f", key="org_costs")
        su_costs     = oc2.number_input("Total Start-Up Costs (§195) ($)",         min_value=0.0, step=1_000.0, format="%.2f", key="su_costs")
        biz_month    = oc1.number_input("Month Business Began (1–12)", min_value=1, max_value=12, step=1, key="biz_start_month")
        first_year   = oc2.checkbox("This is the corporation's first year of business", value=True, key="org_first_year")

        for label, total in [("Organizational Costs (§248)", org_costs), ("Start-Up Costs (§195)", su_costs)]:
            if total <= 0:
                continue
            st.markdown(f"**{label}**")
            immediate = max(0.0, min(5_000.0, 5_000.0 - max(0.0, total - 50_000.0)))
            balance   = total - immediate
            monthly   = balance / 180 if balance > 0 else 0.0
            months_y1 = (12 - biz_month + 1) if first_year else 12
            amort_y1  = monthly * months_y1

            r1, r2, r3 = st.columns(3)
            r1.metric("Immediate Deduction", f"${immediate:,.0f}",
                      "Full \\$5K" if total <= 50_000 else (f"Phased out \\${total-50_000:,.0f}" if total < 55_000 else "Fully phased out"))
            r2.metric("Amortizable Balance", f"${balance:,.0f}", f"÷ 180 months = ${monthly:,.2f}/mo")
            r3.metric(f"Year 1 Amortization ({months_y1} mo)", f"${amort_y1:,.0f}",
                      f"Full year = ${monthly*12:,.0f}" if not first_year else f"Month {biz_month}–12")

            total_yr1 = immediate + amort_y1
            st.info(f"**Total deduction year 1: \\${total_yr1:,.0f}** (immediate \\${immediate:,.0f} + amortization \\${amort_y1:,.0f})")
            if total >= 55_000:
                st.warning(f"Total costs ≥ \\$55,000 → immediate deduction fully phased out. Entire \\${total:,.0f} amortized over 180 months.")

    st.markdown("## Book-vs-Tax Timing Items")
    st.markdown(
        "<div style='background:#EBF4FF;border-left:4px solid #2C5282;padding:10px 14px;margin:8px 0;"
        "color:#2C5282;-webkit-text-fill-color:#2C5282;'>"
        "These four are the differences that dominate a real filer's deferred tax note, and "
        "the ones a textbook Form 1120 problem never mentions. Enter the book charge and the "
        "tax deduction; the gap flows to Schedule M-1 lines 5 and 8 and to its own Schedule "
        "M-3 line. All four are <b>temporary</b> — they reverse, they do not disappear."
        "</div>", unsafe_allow_html=True)

    _m1, _m2 = st.columns(2)
    with _m1:
        st.markdown("**§174 — Research and experimental**")
        st.number_input("Book R&D expense for the year ($)", min_value=0.0, step=10_000.0,
                        format="%.2f", key="s174_book")
        st.number_input("§174 amortisation from prior-year pools ($)", min_value=0.0,
                        step=10_000.0, format="%.2f", key="s174_prior_amort")
        st.caption(f"Tax deduction {'$'}{MODERN['s174_tax']:,.0f} "
                   f"— 10% of this year's spend (5-year straight line, mid-year "
                   f"convention) plus prior pools.")

        st.markdown("**Stock-based compensation**")
        st.number_input("Book expense — ASC 718 ($)", min_value=0.0, step=10_000.0,
                        format="%.2f", key="sbc_book")
        st.number_input("Tax deduction on vesting / exercise ($)", min_value=0.0,
                        step=10_000.0, format="%.2f", key="sbc_tax")
    with _m2:
        st.markdown("**§197 — Intangibles**")
        st.number_input("Book amortisation and impairment ($)", min_value=0.0, step=10_000.0,
                        format="%.2f", key="intang_book")
        st.number_input("§197 amortisation — basis ÷ 15 ($)", min_value=0.0, step=10_000.0,
                        format="%.2f", key="intang_tax")

        st.markdown("**Leases — ASC 842**")
        st.number_input("Book lease cost ($)", min_value=0.0, step=10_000.0,
                        format="%.2f", key="lease_book")
        st.number_input("Rent actually deducted for tax ($)", min_value=0.0, step=10_000.0,
                        format="%.2f", key="lease_tax")

    irc([
        "<b>§174 (as amended by the TCJA, effective 2022):</b> domestic research must be "
        "<b>capitalised</b> and amortised over 5 years; foreign research over 15. A mid-year "
        "convention applies, so the first year gives only <b>10%</b> of the spend. This "
        "reversed decades of immediate expensing and is now one of the largest deferred tax "
        "assets on many balance sheets.",
        "<b>§197:</b> acquired intangibles — goodwill, customer lists, covenants not to compete — "
        "amortise straight-line over <b>15 years</b> whatever the book life. A book impairment "
        "is never a tax event, so it is added back in full and released only as the §197 "
        "amortisation runs.",
        "<b>Stock compensation:</b> book expense accrues over the vesting period under ASC 718; "
        "the tax deduction arrives on vesting (RSUs) or exercise (NQSOs) and is measured by the "
        "value <i>then</i>. The excess or shortfall against the book charge is a permanent "
        "item — enter it separately on the M-3 line 38 manual box.",
        "<b>Leases:</b> ASC 842 puts a right-of-use asset and a lease liability on the balance "
        "sheet and splits the cost; tax simply deducts the rent paid under §162(a)(3). The "
        "difference unwinds over the lease term.",
    ])

    st.markdown("## Other Deductions")
    col_headers("deduction")
    _, _, pen_tax   = tax_row("26",  "Pension & Profit-Sharing Plans",    "pension_book",     mode="deduction")
    _, _, ben_tax   = tax_row("27",  "Employee Benefit Programs",          "benefits_book",    mode="deduction")
    _, _, adv_tax   = tax_row("26b", "Advertising",                        "advertising_book", mode="deduction")
    _, _, trv_tax   = tax_row("—",   "Travel & Transportation — §274(d) (enter deductible business portion only)", "travel_book", mode="deduction")
    irc([
        "§274(d) Travel — deductible only if away from home <b>overnight</b> for business: lodging and incidentals fully deductible for business days; meals limited to 50% (§274(n)).",
        "Transportation (domestic): commuting home↔office is <b>never</b> deductible. Business travel (client visits, job sites) deductible at actual cost (depreciation, gas, maintenance) or standard mileage rate (70¢/mile for 2025).",
        "Primary purpose test: if primary reason is <b>business</b>, transportation is fully deductible; if primarily <b>personal</b>, transportation is not deductible (allocate meals/lodging to business days only).",
        "International travel: must <b>allocate</b> transportation costs between personal vs. business days — transportation not deductible when primary purpose is personal.",
    ])

    with st.expander("🧮 Travel Deduction Calculator (§274(d))", expanded=False):
        st.caption("Compute the deductible portion of a trip. Results are reference only — enter totals into the travel row above.")
        tc1, tc2 = st.columns(2)
        trip_type  = tc1.radio("Trip Type", ["Domestic", "International"], horizontal=True, key="trip_type")
        airfare    = tc1.number_input("Airfare / Transportation ($)", min_value=0.0, step=100.0, format="%.2f", key="t_airfare")
        hotel_pd   = tc1.number_input("Hotel per night ($)", min_value=0.0, step=50.0, format="%.2f", key="t_hotel_pd")
        meals_pd   = tc1.number_input("Meals per day ($)", min_value=0.0, step=10.0, format="%.2f", key="t_meals_pd")
        total_days = tc2.number_input("Total trip days", min_value=1, step=1, key="t_total_days")
        biz_days   = tc2.number_input("Business days", min_value=0, max_value=int(total_days), step=1, key="t_biz_days")
        nights     = tc2.number_input("Hotel nights", min_value=0, step=1, key="t_nights")

        pct_biz    = biz_days / total_days if total_days > 0 else 0.0
        primary_biz = pct_biz > 0.5

        ded_airfare = (airfare if primary_biz else 0.0) if trip_type == "Domestic" else airfare * pct_biz
        ded_hotel   = hotel_pd * min(biz_days, nights)
        ded_meals   = meals_pd * biz_days * 0.5
        total_paid  = airfare + hotel_pd * nights + meals_pd * total_days
        total_ded   = ded_airfare + ded_hotel + ded_meals
        non_ded     = total_paid - total_ded

        st.markdown("---")
        r1, r2, r3 = st.columns(3)
        r1.metric("Total Paid", f"${total_paid:,.0f}")
        r2.metric("Tax Deductible", f"${total_ded:,.0f}")
        r3.metric("Non-Deductible", f"${non_ded:,.0f}")

        airfare_note = ("Full — primary biz" if primary_biz else "$0 — primarily personal") if trip_type == "Domestic" else f"{pct_biz:.0%} allocation (intl)"
        st.markdown(f"""
| Item | Total Paid | Deductible | Rule |
|---|---|---|---|
| Airfare | ${airfare:,.0f} | ${ded_airfare:,.0f} | {airfare_note} |
| Hotel | ${hotel_pd*nights:,.0f} | ${ded_hotel:,.0f} | Business nights only |
| Meals | ${meals_pd*total_days:,.0f} | ${ded_meals:,.0f} | Business days × 50% §274(n) |
        """)
        if not primary_biz and trip_type == "Domestic":
            st.warning("Primary purpose is personal — airfare is \\$0. Only business-day hotel and meals qualify.")

    _, _, oth_d_tax = tax_row("28",  "Other Deductions",                   "other_ded_book",    mode="deduction")
    irc([
        "§461: Deduction when (1) all-events test met AND (2) economic performance occurred.",
        "§461(h): Warranty reserves, rebate accruals, environmental cleanup — NOT deductible until service/property received.",
        "Recurring item exception: ≤$0.5M or immaterial + economic performance within 8.5 months → may deduct in accrual year.",
        "§404: Accrued bonuses deductible only if paid within 2.5 months after year-end.",
        "<b>Prepaid expenditures</b> — generally NOT deductible when paid, even under the cash method; must be capitalized and amortized over the life of the contract. <b>12-month rule exception</b>: prepayment deductible when paid if (1) the contract does not last longer than 1 year AND (2) the contract does not extend past the end of the following tax year. ⚠️ Exception does <u>not</u> apply to prepaid interest — always deducted over the life of the loan.",
    ])

    st.markdown("### Non-Deductible Items — Public Policy & Tax-Exempt Income")
    st.caption("Enter the full book/AFS amount. Disallowance is auto-computed at 100%. These flow to M-1 as permanent add-backs.")
    col_headers("deduction")
    _, meals_b, meals_tax   = tax_row("—", "Meals — §274(n) (50% auto-disallowed; exceptions noted in IRC below)",        "meals_book",         auto_adj_pct=0.5, mode="deduction")
    _, ent_b,   ent_tax     = tax_row("—", "Entertainment — §274(a) (100% auto-disallowed; exceptions noted in IRC below)", "entertainment_book", auto_adj_pct=1.0, mode="deduction")
    _, fin_b,   _  = tax_row("—", "Fines & Penalties §162(f) — 100% disallowed",              "fines_book",         auto_adj_pct=1.0, mode="deduction")
    _, lob_b,   _  = tax_row("—", "Lobbying §162(e) — 100% disallowed",                       "lobbying_book",      auto_adj_pct=1.0, mode="deduction")
    _, bri_b,   _  = tax_row("—", "Bribes & Kickbacks §162(c) — 100% disallowed",             "bribes_book",        auto_adj_pct=1.0, mode="deduction")
    _, pol_b,   _  = tax_row("—", "Political Contributions §276 — 100% disallowed",            "political_book",     auto_adj_pct=1.0, mode="deduction")
    _, ins_b,   _  = tax_row("—", "Key Employee Life Insurance Premiums §264 — 100% disallowed","key_ins_book",      auto_adj_pct=1.0, mode="deduction")
    _, oth_perm, _ = tax_row("—", "Other permanently non-deductible expense — 100% disallowed", "other_perm_book", auto_adj_pct=1.0, mode="deduction")
    st.caption("For book charges that never become a deduction and have no dedicated line: "
               "goodwill impairment on stock-acquired basis, non-deductible debt inducement "
               "or extinguishment costs, disallowed transaction costs.")
    irc([
        "§162(f): Fines/penalties to government — non-deductible.",
        "§162(c): Bribes/kickbacks — non-deductible.",
        "§162(e): Lobbying — non-deductible.",
        "§276: Political contributions — non-deductible.",
        "§264(a)(1): Key employee life insurance (corp as beneficiary) — non-deductible.",
        "§274(n): Meals — 50% disallowed generally. <b>Exceptions (100% deductible):</b> (1) included in employee's W-2 compensation; (2) employee recreation/party open to all employees (not restricted to highly compensated). COVID relief: 100% if purchased from a restaurant in 2021–2022.",
        "§274(a): Entertainment (golf, sporting events, concerts) — 100% disallowed post-TCJA (Tax Cuts and Jobs Act, 2017). <b>Exceptions:</b> (1) amounts treated as employee compensation (included in W-2); (2) primarily for benefit of all employees (e.g., company-wide holiday party)."
        "<br><span style='color:#C53030'>If meals and entertainment are bundled together, meals must be invoiced separately to preserve 50% deductibility.</span>",
    ])

    st.markdown("## NOL Deduction")
    st.markdown(
        "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
        "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
        "<b>Why there is no carryback grid here.</b> Unlike a capital loss, a 2018-or-later NOL has "
        "<b>no carryback at all</b> (§172(b)(1)(A), farming and certain insurance companies excepted) — "
        "it only goes forward, and forever. So the only thing worth tracking is the <b>vintage</b> of each "
        "tranche, because that is what decides the offset limit and whether the tranche can still expire."
        "</div>", unsafe_allow_html=True)
    st.markdown("### Carryforward tranches by vintage")
    st.number_input("Number of NOL vintages to track", min_value=0, max_value=8, step=1, key="nol_n")

    _cy_nol = int(st.session_state.get("tax_year", 2025))
    for _i in range(int(st.session_state.get("nol_n", 1))):
        _c1, _c2, _c3 = st.columns([1, 1.4, 2])
        with _c1:
            st.number_input("Loss year", min_value=1998, max_value=_cy_nol - 1, step=1,
                            key=f"nol_year_{_i}")
        with _c2:
            st.number_input("NOL remaining", min_value=0.0, step=10_000.0, format="%.2f",
                            key=f"nol_amt_{_i}")
        _row = next((r for r in NOL["rows"] if r["i"] == _i), None)
        with _c3:
            if _row is None:
                st.write("")
            elif _row["expired"]:
                st.markdown(
                    f"<div style='background:#FDECEA;border-left:4px solid #C53030;padding:8px 12px;"
                    f"margin-top:28px;color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
                    f"<b>EXPIRED</b> after {_row['expires']} — 20-year carryforward lapsed. Not usable.</div>",
                    unsafe_allow_html=True)
            elif _row["pre2018"]:
                st.markdown(
                    f"<div style='background:#EBF4FF;border-left:4px solid #2C5282;padding:8px 12px;"
                    f"margin-top:28px;color:#2C5282;-webkit-text-fill-color:#2C5282;'>"
                    f"Pre-2018 vintage — <b>100% offset</b>, expires after {_row['expires']}.</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div style='background:#EBF4FF;border-left:4px solid #2C5282;padding:8px 12px;"
                    "margin-top:28px;color:#2C5282;-webkit-text-fill-color:#2C5282;'>"
                    "2018+ vintage — <b>80% limit</b>, never expires.</div>",
                    unsafe_allow_html=True)

    _nc1, _nc2, _nc3 = st.columns(3)
    _nc1.metric("Pre-2018 pool (100% offset)", f"\\${NOL['pre2018_pool']:,.0f}")
    _nc2.metric("2018+ pool (80% limit)", f"\\${NOL['post2017_pool']:,.0f}")
    _nc3.metric("Expired / unusable", f"\\${NOL['expired']:,.0f}")

    _nolr = R1120["taxable_income"]["nol"]
    st.markdown(
        f"<table style='width:100%;border-collapse:collapse'>"
        f"<tr style='background:#EBF4FF'><th style='padding:6px;text-align:left;color:#1B3A6B'>Step</th>"
        f"<th style='padding:6px;text-align:right;color:#1B3A6B'>Amount</th></tr>"
        f"<tr><td style='padding:6px'>Taxable income before NOL (line 28 − 29b)</td>"
        f"<td style='padding:6px;text-align:right'>${_nolr.get('taxable_income', 0) + _nolr.get('nol_used', 0):,.0f}</td></tr>"
        f"<tr><td style='padding:6px'>Pre-2018 NOL applied first (no limit)</td>"
        f"<td style='padding:6px;text-align:right'>({_nolr.get('pre2018_used', 0):,.0f})</td></tr>"
        f"<tr><td style='padding:6px'>2018+ NOL, capped at 80% of what remains</td>"
        f"<td style='padding:6px;text-align:right'>({_nolr.get('post2017_used', _nolr.get('nol_used', 0)):,.0f})</td></tr>"
        f"<tr style='font-weight:700'><td style='padding:6px'>Line 29a — NOL deduction</td>"
        f"<td style='padding:6px;text-align:right'>${_nolr.get('nol_used', 0):,.0f}</td></tr>"
        f"</table>", unsafe_allow_html=True)

    irc([
        "<b>⚠️ Vintage matters — note which year each NOL was generated.</b> Rules follow the year the loss was incurred, not the year it is used.",
        "<b>Pre-2018 NOL (generated before 1/1/2018):</b> Carryback 2 years, carryforward 20 years. Income offset: up to <b>100%</b> (can fully eliminate taxable income). These losses are still being carried forward and their old rules still apply.",
        "<b>2018-and-beyond NOL (generated after 12/31/2017):</b> No carryback (exception: farming losses). Carryforward <b>indefinitely</b>. Income offset: up to <b>80%</b> of taxable income before the NOL deduction — cannot fully eliminate tax.",
        "<b>*Special COVID rules (2018–2020 NOLs):</b> CARES Act temporarily allowed 5-year carryback for losses generated in 2018, 2019, and 2020. These carryback windows have closed, but you may encounter them in workpapers.",
        "<b>Multiple tranches:</b> Stack in FIFO order (oldest vintage first). Each tranche retains its own vintage rules — a pre-2018 loss in the stack still gets 100% offset.",
        "The 80% limit applies per year of use, computed against that year's taxable income <i>before</i> the NOL deduction.",
    ])

    st.markdown("## Lines 28–30 — Taxable Income")
    _l29b = st.session_state.get("sc_line24")
    _l29b_val = _l29b if _l29b is not None else 0.0
    _l28 = SC["line28"]
    _l29a = NOL["line29a"]
    _l29c = _l29a + _l29b_val
    _l30 = max(0.0, _l28 - _l29c)

    st.markdown(
        "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
        "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
        "<b>⚠️ Line 29b has NO input on Form 1120.</b> The figure is carried from <b>Schedule C line 24</b> "
        "(total of column (c)) and cannot be typed in here.<br>You <b>must</b> compute the DRD and any §250 deduction on "
        "the <b>💰 Schedule C — Dividends</b> page. This is where the deduction is actually taken — it is <b>not</b> "
        "netted against income at line 4."
        "</div>", unsafe_allow_html=True)

    st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">28</td><td style="padding:8px 12px;">Taxable income <i>before</i> NOL and special deductions</td><td style="padding:8px 12px;text-align:right;">${_l28:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">29a</td><td style="padding:8px 12px;">NOL deduction — pre-2018 tranches in full, 2018+ tranches capped at 80% of the remainder</td><td style="padding:8px 12px;text-align:right;">(${_l29a:,.0f})</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">29b</td><td style="padding:8px 12px;">Special deductions — Schedule C line 24 (DRD + §250)</td><td style="padding:8px 12px;text-align:right;">(${_l29b_val:,.0f})</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">29c</td><td style="padding:8px 12px;">Add lines 29a and 29b</td><td style="padding:8px 12px;text-align:right;">(${_l29c:,.0f})</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">30</td><td style="padding:8px 12px;font-weight:bold;">Taxable income — line 28 minus line 29c</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${_l30:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

    if _l29b is None:
        st.warning("Schedule C has not been filled in yet — Line 29b is \\$0. Open the **💰 Schedule C — Dividends** page.")

    irc([
        "<b>Why the DRD is a deduction here and not an exclusion at line 4:</b> An <i>exclusion</i> would keep the income "
        "off the return entirely. The DRD is a <b>deduction</b> — the dividend is fully in gross income at line 4, and the "
        "relief is granted lower down at line 29b."
        "<br><span style='color:#C53030'>The distinction is not cosmetic. §246(b) caps the DRD at a percentage of taxable "
        "income measured at <b>line 28</b>. If the dividend were excluded at line 4, line 28 would shrink by the dividend "
        "and the cap would be computed on the wrong base.</span>"
        "<br>Contrast with a true exclusion: §103 muni bond interest never enters income at all — that one <i>is</i> "
        "handled with the Tax Exclusion column on the Income page.",
        "<b>What line 29b contains:</b> the §243 DRD (Dividends Received Deduction), the §245A participation exemption, and "
        "the §250 deduction on NCTI (Net CFC Tested Income) and FDDEI (Foreign-Derived Deduction Eligible Income).",
    ])

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE C — DIVIDENDS
# ─────────────────────────────────────────────────────────────────────────────
elif section == "💰 Schedule C — Dividends":
    st.title("Schedule C — Dividends & Special Deductions")

    st.markdown("## Dividends Received Deduction (DRD)")
    st.caption("Dividends are entered here, not on Page 1 — Page 1 line 4 is carried from Schedule C line 23.")
    c1, c2 = st.columns(2)
    divs = c1.number_input("Dividends received — column (a), lines 1–8 ($)", min_value=0.0,
                           step=1_000.0, format="%.2f", key="dividends_book")
    ownership = c1.slider("Ownership % in Dividend-Paying Corporation (0–100%)", 0, 100, key="ownership_pct")

    # Same computation the shared pass ran before any page rendered — keeps this page
    # and Page 1 line 4 from ever disagreeing.
    _drd = SC["drd"]
    drd_rate, drd_label = _drd["rate"], _drd["label"]
    step1, step2 = _drd["step1"], _drd["step2"]
    taxable_inc_before_drd = SC["line28"]
    nol_if_step1 = taxable_inc_before_drd - step1
    nol_rule_applies = _drd["nol_rule"]
    drd_allowed, drd_note = _drd["allowed"], _drd["note"]

    c2.metric("DRD Rate", f"{drd_rate:.0%}", drd_label)
    c2.metric("§246(b) limit base — line 28", f"${taxable_inc_before_drd:,.0f}",
              "auto — taxable income before NOL & special deductions")

    st.markdown("#### §246(b) Limitation — Three-Step Calculation")
    st.caption("The limit base is Form 1120 line 28, computed from every income and deduction "
               "entered elsewhere in this return. It is not typed in — and it cannot be, because "
               "the DRD is what line 28 is being used to limit.")
    s1, s2, s3 = st.columns(3)
    s1.metric("Step 1 — Dividends × Rate", f"${step1:,.0f}")
    s2.metric("Step 2 — Line 28 × Rate", f"${step2:,.0f}")
    s3.metric("DRD Allowed (lesser, or NOL rule)", f"${drd_allowed:,.0f}", drd_note)

    if nol_rule_applies:
        st.warning(f"NOL rule active: deducting Step 1 (\\${step1:,.0f}) would produce a loss of \\${nol_if_step1:,.0f}. Full Step 1 DRD is allowed under §246(b) NOL exception.")

    irc([
        f"<b>IRC §243(a) — Dividends Received Deduction (DRD):</b> C-corps receiving dividends from a domestic corporation get a deduction to mitigate multiple layers of taxation. Rate depends on ownership: &lt;20% → 50% (§243(a)(1)); 20–79% → 65% (§243(a)(2)); 80%+ affiliated group → 100% (§243(a)(3)).",
        f"Current rate for this return: <b>{drd_label}</b>.",
        "<b>§246(b) Taxable income limitation — 3 steps:</b> (1) Dividends received × deduction %; (2) Taxable income (before DRD) × deduction %; (3) DRD = lesser of Step 1 or Step 2. <b>NOL exception:</b> if using Step 1 creates or increases an NOL, Step 1 is used in full regardless of Step 2.",
        "<b>§246(c) Holding period:</b> Must hold stock &gt;45 days in the 91-day window around ex-dividend date — otherwise DRD is fully disallowed for that dividend.",
    ])

    st.markdown("---")
    st.markdown("## Lines 16a / 16b / 18 / 22 — Foreign Income Inclusions")
    st.caption("Subpart F, NCTI/GILTI, the §78 gross-up and the §250 deduction are Schedule C lines — they are entered and computed here, then flow to line 23 / line 24.")


    with st.expander("🌐 International Tax — Subpart F / GILTI / PTEP / §245A / FTC Baskets"):
        irc([
            "<b>§951 Subpart F Inclusions (CFC deemed dividend):</b> U.S. Shareholders (≥10% vote or value) of a Controlled Foreign Corporation (CFC — foreign corp &gt;50% owned by U.S. Shareholders) must currently include their pro-rata share of the CFC's Subpart F income regardless of actual distribution."
            "<br>Subpart F targets <i>highly mobile income</i>:"
            "<br>&nbsp;&nbsp;(1) <b>FPHCI (Foreign Personal Holding Company Income)</b> — dividends, interest, rents, royalties, gains on property."
            "<br>&nbsp;&nbsp;(2) <b>FBCSI (Foreign Base Company Sales Income)</b> — 3-prong test: (a) manufactured/produced outside the CFC's country, (b) sold for use/consumption outside that country, and (c) purchased from or sold to a related party."
            "<br>&nbsp;&nbsp;(3) <b>FBCSVI (Foreign Base Company Services Income)</b> — services performed for/on behalf of a related party outside the CFC's country."
            "<br><span style='color:#C53030'><b>De minimis rule:</b> If total Subpart F income &lt;5% of gross income (or &lt;$1M) → treat as zero.</span>"
            "<br><span style='color:#C53030'><b>Full inclusion rule:</b> If total Subpart F income &gt;70% of gross income → entire gross income is Subpart F.</span>"
            "<br><span style='color:#C53030'><b>Inclusion formula:</b> pro-rata share × CFC current-year E&amp;P (cannot exceed E&amp;P). Taxed at 21%; FTC (Foreign Tax Credit) available — gross up inclusion by foreign taxes paid.</span>"
            "<br><span style='color:#C53030'><b>High-tax exception:</b> Subpart F income taxed by foreign country at &gt;90% of U.S. 21% rate (i.e., &gt;18.9%) may be excluded by election.</span>"
            "<br>Excess FTCs: carryback 1 yr, carryforward 10 yrs.",

            "<b>§951A GILTI (Global Intangible Low-Taxed Income) / NCTI (Net CFC Tested Income) (2026+):</b> Tested income = all CFC income NOT otherwise Subpart F."
            "<br>Net each U.S. Shareholder's pro-rata share of tested income across all CFCs → NCTI."
            "<br><b>Pre-2026 GILTI:</b> NDTIR (Net Deemed Tangible Income Return) = 10% × QBAI (Qualified Business Asset Investment — tangible depreciable assets); net tested income − NDTIR = GILTI."
            "<br><span style='color:#C53030'><b>Pre-2026 rate:</b> 50% deduction → 10.5% effective rate.</span>"
            "<br><b>2026+ NCTI:</b> QBAI hurdle eliminated."
            "<br><span style='color:#C53030'><b>2026+ rate:</b> 40% deduction → 12.6% effective rate.</span>"
            "<br><span style='color:#C53030'><b>FTC 90% haircut:</b> Only 90% of creditable foreign taxes usable; gross-up is still 100%. NCTI excess FTCs <b>cannot</b> be carried back or forward (use it or lose it).</span>"
            "<br>NCTI is a separate FTC basket.",

            "<b>PTEP (Previously Taxed E&amp;P):</b> Once income is included under Subpart F or NCTI, it is tracked in the CFC's PTEP account."
            "<br>Actual distributions out of PTEP → <b>non-taxable</b> to the U.S. Shareholder (avoids double tax)."
            "<br><span style='color:#C53030'>Distributions in excess of PTEP → taxable under §959 ordering rules.</span>",

            "<b>§962 Election:</b> Individual U.S. Shareholders of CFCs may elect corporate-rate treatment (21%) on Subpart F/NCTI inclusions and claim FTCs."
            "<br>Without election: individuals pay ordinary income rates with no FTC."
            "<br>Election is annual and made on the individual's return.",

            "<b>§245A Participation Exemption (DRD — Dividends Received Deduction):</b> Domestic corporations owning ≥10% of a foreign corporation's stock (by vote and value) for &gt;365 days get a <b>100% DRD</b> on the foreign-source portion of dividends received."
            "<br>Designed to prevent double tax on repatriation of already-taxed foreign earnings."
            "<br><span style='color:#C53030'>Does NOT apply to hybrid instruments or Subpart F/GILTI income already included.</span>",

            "<b>FTC (Foreign Tax Credit) Baskets:</b> General (active foreign business income), Passive (dividends, interest, rents, royalties), Branch, and NCTI (separate basket, no carryover)."
            "<br><span style='color:#C53030'>Cross-crediting within a basket is allowed across countries; cross-basket crediting is prohibited.</span>",
        ])

        st.divider()
        _has_cfc = st.checkbox(
            "This corporation owns one or more CFCs — carry the inclusions below to Schedule C",
            key="has_cfc",
            help="Leave unchecked to use the calculators for practice only. Nothing is carried to "
                 "Schedule C, Line 4, or the tax computation while this is off.")
        if _has_cfc:
            st.markdown(
                "<div style='background:#E7F6EC;border-left:5px solid #1E7A3C;padding:10px 14px;margin:6px 0;"
                "color:#14532D;-webkit-text-fill-color:#14532D;'>"
                "<b>✅ Live — inclusions are being carried.</b> Whatever the calculators below compute now flows to "
                "Schedule C lines 16a / 16b / 18 / 22, and on to Line 4 and the tax computation. "
                "Replace the sample figures with the corporation's real numbers."
                "</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:10px 14px;margin:6px 0;"
                "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
                "<b>⚠️ Practice mode — nothing is being carried.</b> The calculators below are pre-filled with sample "
                "figures for practice. They reach neither Schedule C, Line 4, nor the tax computation until the "
                "checkbox above is ticked."
                "</div>", unsafe_allow_html=True)

        intl_tab1, intl_tab2 = st.tabs(["🧮 Subpart F Calculator", "🧮 GILTI / NCTI Calculator"])

        with intl_tab1:
            st.caption("Computes U.S. Shareholder's §951 Subpart F inclusion and available FTC.")
            sf1, sf2 = st.columns(2)
            sf_owner_pct  = sf1.number_input("U.S. Shareholder ownership % in CFC", min_value=0.0, max_value=100.0, value=60.0, step=1.0, key="sf_owner_pct") / 100
            sf_subf_inc   = sf1.number_input("CFC Subpart F income ($)", min_value=0.0, value=500000.0, step=1000.0, key="sf_subf_inc")
            sf_ep         = sf1.number_input("CFC current-year E&P ($)", min_value=0.0, value=800000.0, step=1000.0, key="sf_ep")
            sf_gross_inc  = sf2.number_input("CFC gross income ($) — for de minimis / full inclusion tests", min_value=0.0, value=1000000.0, step=1000.0, key="sf_gross_inc")
            sf_foreign_tax= sf2.number_input("Foreign taxes paid on Subpart F income ($)", min_value=0.0, value=50000.0, step=1000.0, key="sf_foreign_tax")

            _sf = calc_subpart_f(sf_owner_pct, sf_subf_inc, sf_ep, sf_gross_inc, sf_foreign_tax)
            sf_deminimis = _sf["deminimis"]
            sf_full_incl = _sf["full_inclusion"]
            sf_eff_subf  = _sf["effective"]
            sf_inclusion = _sf["inclusion"]
            sf_grossup   = _sf["grossup"]
            sf_ftc       = sf_grossup

            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Subpart F Income Used", f"${sf_eff_subf:,.0f}",
                      "Full inclusion rule" if sf_full_incl else ("De minimis → $0" if sf_deminimis else "Actual"))
            c2.metric("§951 Inclusion", f"${sf_inclusion:,.0f}", f"{sf_owner_pct:.0%} × min(SubF, E&P)")
            c3.metric("FTC Available (gross-up)", f"${sf_ftc:,.0f}")

            if sf_deminimis:
                st.info("De minimis rule applies — Subpart F income < 5% of gross income and < \\$1M → treated as zero.")
            elif sf_full_incl:
                st.warning("Full inclusion rule — Subpart F income > 70% of gross income → entire gross income is Subpart F.")

            st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">CFC Subpart F income</td><td style="padding:8px 12px;text-align:right;">${sf_subf_inc:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">CFC current-year E&P</td><td style="padding:8px 12px;text-align:right;">${sf_ep:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Effective Subpart F income (after rules)</td><td style="padding:8px 12px;text-align:right;">${sf_eff_subf:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">U.S. shareholder pro-rata share ({sf_owner_pct:.0%})</td><td style="padding:8px 12px;text-align:right;">${sf_owner_pct * sf_eff_subf:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Capped at E&P share ({sf_owner_pct:.0%} × E&P)</td><td style="padding:8px 12px;text-align:right;">${sf_owner_pct * sf_ep:,.0f}</td></tr>
<tr style="background:#2D5A9E;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">§951 Inclusion</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${sf_inclusion:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Foreign tax gross-up ({sf_owner_pct:.0%} × foreign taxes paid)</td><td style="padding:8px 12px;text-align:right;">${sf_grossup:,.0f}</td></tr>
<tr style="background:#eef2f7;"><td style="padding:8px 12px;">FTC available</td><td style="padding:8px 12px;text-align:right;">${sf_ftc:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        with intl_tab2:
            st.caption("Pre-2026 GILTI or 2026+ NCTI inclusion, deduction, and effective rate.")
            regime = st.radio("Regime", ["Pre-2026 GILTI", "2026+ NCTI"], horizontal=True, key="gilti_regime")
            g1, g2 = st.columns(2)
            g_tested_inc  = g1.number_input("Net CFC tested income ($)", min_value=0.0, value=1000000.0, step=1000.0, key="g_tested_inc")
            g_qbai        = g1.number_input("QBAI — tangible depreciable assets net book value ($)", min_value=0.0, value=2000000.0, step=1000.0, key="g_qbai",
                                            help="Pre-2026 only — QBAI hurdle eliminated in 2026+ NCTI")
            g_tested_tax  = g2.number_input("Net tested taxes (CFC-level foreign taxes on tested income) ($)", min_value=0.0, value=80000.0, step=1000.0, key="g_tested_tax")
            g_owner_pct   = g2.number_input("U.S. Shareholder ownership % in CFC", min_value=0.0, max_value=100.0, value=100.0, step=1.0, key="g_owner_pct") / 100

            _gl = calc_gilti_ncti(regime, g_owner_pct, g_tested_inc, g_qbai, g_tested_tax)
            ndtir         = _gl["ndtir"]
            gilti_inc     = _gl["base"]
            inclusion     = _gl["inclusion"]
            deduction_pct = _gl["deduction_pct"]
            deduction     = _gl["deduction"]
            net_inclusion = _gl["net_inclusion"]
            ftc_haircut   = _gl["ftc_haircut"]
            effective_rate= _gl["effective_rate"]

            gross_tax = net_inclusion * 0.21
            avail_ftc = _gl["avail_ftc"]
            net_tax   = max(0.0, gross_tax - avail_ftc)

            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Inclusion", f"${inclusion:,.0f}")
            m2.metric(f"§250 Deduction ({deduction_pct:.0%})", f"${deduction:,.0f}")
            m3.metric("Net Inclusion", f"${net_inclusion:,.0f}")
            m4.metric("U.S. Tax After FTC", f"${net_tax:,.0f}", f"Eff. rate ≈ {effective_rate:.1%}")

            ndtir_str = f"${ndtir:,.0f}" if regime == "Pre-2026 GILTI" else "N/A (eliminated)"
            st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:center;width:40px;">Step</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;text-align:center;">1</td><td style="padding:8px 12px;">Net CFC tested income</td><td style="padding:8px 12px;text-align:right;">${g_tested_inc:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;text-align:center;">2</td><td style="padding:8px 12px;">NDTIR (10% × QBAI)</td><td style="padding:8px 12px;text-align:right;">{ndtir_str}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;text-align:center;">3</td><td style="padding:8px 12px;">GILTI / NCTI inclusion (before deduction)</td><td style="padding:8px 12px;text-align:right;">${inclusion:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;text-align:center;">4</td><td style="padding:8px 12px;">§250 deduction ({deduction_pct:.0%})</td><td style="padding:8px 12px;text-align:right;">(${deduction:,.0f})</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;text-align:center;">5</td><td style="padding:8px 12px;">Net inclusion</td><td style="padding:8px 12px;text-align:right;">${net_inclusion:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;text-align:center;">6</td><td style="padding:8px 12px;">Gross U.S. tax @ 21%</td><td style="padding:8px 12px;text-align:right;">${gross_tax:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;text-align:center;">7</td><td style="padding:8px 12px;">FTC available ({ftc_haircut:.0%} of tested taxes)</td><td style="padding:8px 12px;text-align:right;">(${avail_ftc:,.0f})</td></tr>
<tr style="background:#2D5A9E;color:#ffffff;"><td style="padding:8px 12px;text-align:center;font-weight:bold;">8</td><td style="padding:8px 12px;font-weight:bold;">Net U.S. tax</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${net_tax:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)
            if regime == "2026+ NCTI":
                st.warning("NCTI excess FTCs cannot be carried back or forward — use it or lose it. NCTI is a separate FTC basket.")

    irc([
        "<b>§951A NCTI (Net CFC Tested Income, formerly GILTI) — 2026+:</b> QBAI (Qualified Business Asset Investment) hurdle eliminated; NCTI = full net CFC tested income."
        "<br><span style='color:#C53030'><b>2026+ rate:</b> §250 deduction = 40% → effective rate 12.6%.</span>"
        "<br><span style='color:#C53030'><b>Pre-2026 GILTI rate:</b> NCTI = tested income − 10% × QBAI; 50% deduction → 10.5% effective rate.</span>"
        "<br>Reported on Form 8992 (NCTI computation) and Form 8993 (§250 deduction)."
        "<br><span style='color:#C53030'>FTC (Foreign Tax Credit) on NCTI subject to 90% haircut; excess FTCs are use-it-or-lose-it (no carryover).</span>",

        "<b>FDDEI (Foreign-Derived Deduction Eligible Income, formerly FDII) — §250 Export Deduction, 2026+:</b> Domestic corps selling products or services directly into foreign markets (not through a CFC or branch) can deduct 33.34% of FDDEI."
        "<br><span style='color:#C53030'><b>Effective rate: ~14%.</b> FDDEI = foreign-derived portion of DEI (Deduction Eligible Income).</span>"
        "<br>OBBBA (One Big Beautiful Bill Act, 2026) eliminated the FDII 10% QBAI hurdle.",

        "<b>§250 is a DEDUCTION, not an exclusion — this trips people up.</b> The phrase “40% deduction → 12.6% effective "
        "rate” makes it sound as if only part of the NCTI is included. Mechanically it is the opposite:"
        "<br>&nbsp;&nbsp;<b>100%</b> of the NCTI inclusion enters gross income — Schedule C line 16b, column (a) → line 23 → page 1 line 4;"
        "<br>&nbsp;&nbsp;the §250 relief is a separate <b>deduction</b> — Schedule C line 22, column (c) → line 24 → page 1 line 29b."
        "<br><span style='color:#C53030'>Net result 60% × 21% = 12.6%, but the gross inclusion is still sitting in income. "
        "That matters: it inflates line 28, which is the base for the §246(b) DRD limit and for the §250 limit itself.</span>"
        "<br>Contrast a real exclusion — §103 muni interest — which never enters income at all.",

        "<b>§250(a)(2) Limitation:</b> The FDDEI + NCTI amounts the deduction is computed on cannot exceed <b>taxable income "
        "determined without regard to §250</b>."
        "<br><span style='color:#C53030'>Any excess is permanently lost — there is <b>no carryforward</b>, unlike the §246(b) "
        "DRD which has the NOL exception.</span>",
        "<b>IC-DISC (Interest Charge Domestic International Sales Corporation):</b> Export incentive — operating company pays deductible commission to IC-DISC shell; IC-DISC pays no corporate tax and distributes qualified dividends to owners.",
    ])

    st.markdown("---")
    st.markdown("## Schedule C — Lines 23 & 24 Summary")

    irc([
        "<b>Schedule C is a three-column form — and the two totals go to two different places:</b>"
        "<br>&nbsp;&nbsp;<b>Column (a)</b> Dividends and inclusions &nbsp;·&nbsp; <b>Column (b)</b> % &nbsp;·&nbsp; "
        "<b>Column (c)</b> Special deductions = (a) × (b)"
        "<br>&nbsp;&nbsp;<b>Line 23</b> = total of column (a) → Form 1120 page 1 <b>line 4</b>"
        "<br>&nbsp;&nbsp;<b>Line 24</b> = total of column (c) → Form 1120 page 1 <b>line 29b</b>"
        "<br><span style='color:#C53030'>The DRD is <b>never</b> netted against line 4. Line 4 carries the <b>gross</b> "
        "dividends and inclusions; the deduction is taken far lower down at line 29b, <i>below</i> line 28 "
        "(taxable income before NOL and special deductions).</span>",

        "<b>Why the placement matters:</b> §246(b) caps the DRD at a percentage of <b>taxable income</b>. That limit base "
        "is line 28, which is computed <i>after</i> line 4."
        "<br><span style='color:#C53030'>If the DRD were subtracted at line 4 it would shrink its own limit base — circular "
        "and wrong. Keeping it at line 29b is what makes the §246(b) computation well-defined.</span>",

        "<b>§78 gross-up:</b> Schedule C line 18, column (a). When a US shareholder claims an indirect FTC (Foreign Tax "
        "Credit) on a Subpart F inclusion, it must <b>add back</b> the deemed-paid foreign taxes as income."
        "<br>Rationale: the credit is claimed on a pre-tax amount, so the income must be grossed up to match.",
    ])

    # All figures come from the shared pass so this page and Page 1 line 4 agree.
    sc_divs    = SC["dividends"]
    sc_subf    = SC["subpart_f"]
    sc_gilti   = SC["gilti"]
    sc_gross78 = SC["grossup78"]
    sc_250     = SC["sec250"]
    sc_drd     = SC["drd"]["allowed"]
    sc_line23  = SC["line23"]   # column (a) — gross
    sc_line24  = SC["line24"]   # column (c) — special deductions

    if SC["sec250_limited"]:
        st.warning(
            f"**§250(a)(2) limitation applies.** The uncapped §250 deduction would be "
            f"\\${SC['sec250_uncapped']:,.0f}, but the NCTI amount it is computed on cannot exceed taxable income "
            f"determined without §250 (\\${SC['sec250_base']:,.0f} = line 28 − DRD). Deduction reduced to "
            f"**\\${sc_250:,.0f}** — the unused portion is lost, there is no carryforward.")

    st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">(a) Dividends &amp; inclusions</th>
<th style="padding:8px 12px;text-align:right;">(c) Special deductions</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">1–8</td><td style="padding:8px 12px;">Dividends received from domestic and foreign corporations</td><td style="padding:8px 12px;text-align:right;">${sc_divs:,.0f}</td><td style="padding:8px 12px;text-align:right;">${sc_drd:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">16a</td><td style="padding:8px 12px;">§951(a)(1) Subpart F inclusions from CFCs</td><td style="padding:8px 12px;text-align:right;">${sc_subf:,.0f}</td><td style="padding:8px 12px;text-align:right;">—</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">16b</td><td style="padding:8px 12px;">§951A NCTI / GILTI inclusions</td><td style="padding:8px 12px;text-align:right;">${sc_gilti:,.0f}</td><td style="padding:8px 12px;text-align:right;">—</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">18</td><td style="padding:8px 12px;">§78 gross-up — deemed-paid foreign taxes added back</td><td style="padding:8px 12px;text-align:right;">${sc_gross78:,.0f}</td><td style="padding:8px 12px;text-align:right;">—</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">22</td><td style="padding:8px 12px;">§250 deduction (NCTI / FDDEI)</td><td style="padding:8px 12px;text-align:right;">—</td><td style="padding:8px 12px;text-align:right;">${sc_250:,.0f}</td></tr>
<tr style="background:#2D5A9E;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">23</td><td style="padding:8px 12px;font-weight:bold;">Total column (a) → page 1, <b>line 4</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${sc_line23:,.0f}</td><td style="padding:8px 12px;text-align:right;">—</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">24</td><td style="padding:8px 12px;font-weight:bold;">Total column (c) → page 1, <b>line 29b</b></td><td style="padding:8px 12px;text-align:right;">—</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${sc_line24:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    sc1.metric("Line 23 → Page 1 Line 4", f"${sc_line23:,.0f}", "gross — no DRD netted")
    sc2.metric("Line 24 → Page 1 Line 29b", f"${sc_line24:,.0f}", "special deductions")

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE D — CAPITAL GAINS AND LOSSES
# ─────────────────────────────────────────────────────────────────────────────
elif section == "📉 Schedule D — Capital Gains":
    st.title("Schedule D (Form 1120) — Capital Gains and Losses")
    st.caption("Part I short-term · Part II long-term · Part III summary. Line 18 carries to Form 1120, page 1, line 8.")

    _cy = int(TAX_YEAR)
    sd_tab_law, sd_tab_sched, sd_tab_cf = st.tabs(
        ["📖 Law & Concepts", "🧮 Schedule D", "🔁 Capital Loss Carryover"])
    # Line 11 arrives from Form 4797 Part I line 9 (post §1231(c) look-back).
    sd_1231_ltcg = F4797["schedule_d_ltcg"]

    with sd_tab_law:
        irc([
            "<b>§1221 Capital asset:</b> Property held by the taxpayer, <i>excluding</i> five main categories —"
            "<br>&nbsp;&nbsp;(1) Inventory and property held primarily for sale to customers;"
            "<br>&nbsp;&nbsp;(2) Depreciable property and real property used in a trade or business (this is §1231 property, not a capital asset);"
            "<br>&nbsp;&nbsp;(3) Self-created copyrights, literary and artistic compositions;"
            "<br>&nbsp;&nbsp;(4) Accounts receivable acquired in the ordinary course of business;"
            "<br>&nbsp;&nbsp;(5) US government publications received below cost.",

            "<b>Holding period determines character:</b> Held <b>more than 1 year</b> → LTCG (Long-Term Capital Gain), reported in Part II. Held <b>1 year or less</b> → STCG (Short-Term Capital Gain), reported in Part I."
            "<br><span style='color:#C53030'>The holding period starts the <b>day after</b> acquisition and includes the day of disposition.</span>",

            "<b>§1211(a) — the C corporation rule:</b> A corporation may deduct capital losses <b>only to the extent of capital gains</b>."
            "<br><span style='color:#C53030'>Capital losses can <b>never</b> offset ordinary income for a C corp. This differs from individuals, who may deduct up to $3,000 of net capital loss against ordinary income each year.</span>",

            "<b>§1212(a) — net capital loss carryover:</b> A corporate net capital loss is carried <b>back 3 years</b> and <b>forward 5 years</b>."
            "<br><span style='color:#C53030'>Carryback is applied to the earliest of the 3 prior years first. Any unused amount then carries forward, and it is <b>always treated as a short-term capital loss</b> in the carryover year regardless of its original character.</span>"
            "<br><span style='color:#C53030'>A carryover expires unused at the end of the 5-year window — it does not extend.</span>",

            "<b>§1231 property:</b> Depreciable property and real property used in a trade or business and held more than 1 year. It receives the <b>best of both worlds</b> treatment:"
            "<br>&nbsp;&nbsp;Net §1231 <b>gain</b> → treated as LTCG (Long-Term Capital Gain), taxed favorably;"
            "<br>&nbsp;&nbsp;Net §1231 <b>loss</b> → treated as an <b>ordinary loss</b>, fully deductible against ordinary income.",

            "<b>§1231(c) five-year look-back rule:</b> Current-year net §1231 gain is recharacterized as <b>ordinary income</b> to the extent of <b>non-recaptured net §1231 losses</b> deducted in the 5 preceding tax years."
            "<br><span style='color:#C53030'>Apply the <b>oldest year first</b>. The recharacterized portion goes to Form 4797, Part II → Form 1120 line 9. Only the remainder keeps LTCG treatment and reaches Schedule D line 11 → Form 1120 line 8.</span>"
            "<br>Purpose: prevent a taxpayer from taking ordinary loss deductions in one year and capital gain treatment in the next.",

            "<b>Netting order in Part III:</b>"
            "<br>&nbsp;&nbsp;Line 16 = excess of net STCG (line 7) over net long-term capital <i>loss</i> (line 15);"
            "<br>&nbsp;&nbsp;Line 17 = excess of net LTCG (line 15) over net short-term capital <i>loss</i> (line 7);"
            "<br>&nbsp;&nbsp;<span style='color:#C53030'>Line 18 = line 16 + line 17 → Form 1120, page 1, line 8. If the combined result is a <b>net loss</b>, line 18 is <b>zero</b> — the loss goes to the §1212(a) carryover instead, never to page 1.</span>",
        ])

    # ── §1231 look-back (executes before the schedule tab; feeds line 11) ─────

    # ── Schedule D proper ────────────────────────────────────────────────────
    with sd_tab_sched:
        def _sd_row(num, label, key, allow_neg=True, helptext=None):
            c1, c2 = st.columns([7, 3])
            v = c1.number_input(f"[Line {num}] {label}", min_value=None if allow_neg else 0.0,
                                step=1_000.0, format="%.2f", key=key, help=helptext)
            c2.markdown(f"<div style='padding-top:1.75rem;text-align:right;font-weight:600;color:#1B3A6B;"
                        f"-webkit-text-fill-color:#1B3A6B;'>${v:,.0f}</div>",
                        unsafe_allow_html=True)
            return v

        st.markdown("## Part I — Short-Term Capital Gains and Losses")
        st.caption("Assets held 1 year or less. Enter losses as negative amounts.")
        irc([
            "<b>What belongs in Part I:</b> Gain or loss from selling or exchanging a <b>§1221 capital asset</b> held "
            "<b>1 year or less</b> — corporate stock, bonds, mutual fund shares, land or buildings held for investment, "
            "and cryptocurrency held as an investment."
            "<br><span style='color:#C53030'>Do <b>not</b> enter here: inventory, accounts receivable, or depreciable business "
            "property. Those are ordinary income or §1231 property and belong on Form 4797 → line 9, not Schedule D.</span>",

            "<b>Which line to use — the Form 8949 box system.</b> The split depends on whether your broker reported the "
            "<b>cost basis</b> to the IRS on Form 1099-B (Proceeds From Broker and Barter Exchange Transactions):"
            "<br>&nbsp;&nbsp;<b>Line 1a</b> — basis <b>was</b> reported to the IRS <i>and</i> you have no adjustments. "
            "<span style='color:#C53030'>This is the shortcut line: enter the totals directly and skip Form 8949 entirely.</span>"
            "<br>&nbsp;&nbsp;<b>Line 1b (Box A)</b> — basis <b>was</b> reported to the IRS, but an adjustment is needed "
            "(for example a wash sale under §1091, or a basis correction)."
            "<br>&nbsp;&nbsp;<b>Line 2 (Box B)</b> — the sale appeared on Form 1099-B but the basis was <b>not</b> reported to the IRS."
            "<br>&nbsp;&nbsp;<b>Line 3 (Box C)</b> — the transaction was <b>not reported on any Form 1099-B</b> "
            "(private sales, transactions with no broker involved).",

            "<b>Lines 4–6 — special sources, not ordinary security trades:</b>"
            "<br>&nbsp;&nbsp;<b>Line 4</b> — §453 installment sales (Form 6252). Gain is recognized as each payment is "
            "<i>received</i>, not all in the year of sale."
            "<br>&nbsp;&nbsp;<b>Line 5</b> — §1031 like-kind exchanges (Form 8824). Only the taxable <b>boot</b> "
            "(cash or non-like-kind property received) is entered; the deferred portion is not."
            "<br>&nbsp;&nbsp;<b>Line 6</b> — §1212(a) capital loss carryover. "
            "<span style='color:#C53030'>Always short-term regardless of its original character — computed automatically "
            "from the Capital Loss Carryover tab and entered as a negative amount.</span>",
        ])
        sd_1a = _sd_row("1a", "Totals for all short-term transactions reported on Form 1099-B", "sd_l1a",
                        helptext="Basis WAS reported to the IRS and no adjustment is needed. Enter totals here and skip Form 8949.")
        sd_1b = _sd_row("1b", "Short-term transactions reported on Form 8949 with Box A checked", "sd_l1b",
                        helptext="Box A: basis WAS reported to the IRS, but an adjustment is needed (e.g. §1091 wash sale).")
        sd_2  = _sd_row("2",  "Short-term transactions reported on Form 8949 with Box B checked", "sd_l2",
                        helptext="Box B: reported on Form 1099-B, but basis was NOT reported to the IRS.")
        sd_3  = _sd_row("3",  "Short-term transactions reported on Form 8949 with Box C checked", "sd_l3",
                        helptext="Box C: not reported on any Form 1099-B — private sales, no broker involved.")
        sd_4  = _sd_row("4",  "Short-term capital gain from installment sales (Form 6252)", "sd_l4",
                        helptext="§453: gain recognized as each payment is received, not all in the year of sale.")
        sd_5  = _sd_row("5",  "Short-term capital gain or (loss) from like-kind exchanges (Form 8824)", "sd_l5",
                        helptext="§1031: enter only the taxable boot received. The deferred portion is excluded.")
        _slot_l6 = st.empty()
        _slot_l7 = st.empty()

        st.markdown("## Part II — Long-Term Capital Gains and Losses")
        st.caption("Assets held more than 1 year. Enter losses as negative amounts.")
        irc([
            "<b>What belongs in Part II:</b> The same categories of §1221 capital asset as Part I, but held "
            "<b>more than 1 year</b>. Boxes D / E / F mirror Boxes A / B / C exactly — the only difference is holding period."
            "<br>&nbsp;&nbsp;<b>Line 8a</b> — basis reported to the IRS, no adjustment (shortcut line, no Form 8949 needed)."
            "<br>&nbsp;&nbsp;<b>Line 8b (Box D)</b> — basis reported to the IRS, adjustment needed."
            "<br>&nbsp;&nbsp;<b>Line 9 (Box E)</b> — on Form 1099-B, basis <b>not</b> reported to the IRS."
            "<br>&nbsp;&nbsp;<b>Line 10 (Box F)</b> — not reported on any Form 1099-B.",

            "<b>Line 11 — the §1231 channel (auto-filled here):</b> Net §1231 gain arriving from Form 4797. This is where "
            "gain on <b>depreciable business property and business real property</b> enters Schedule D."
            "<br><span style='color:#C53030'>Only the portion surviving the §1231(c) five-year look-back reaches this line. "
            "The recharacterized portion is ordinary income and goes to Form 4797 Part II → Form 1120 line 9 instead.</span>"
            "<br>Depreciation recapture under §1245 and §291 is stripped out earlier and is never capital gain.",

            "<b>Line 14 — capital gain distributions:</b> Amounts paid out by a RIC (Regulated Investment Company, i.e. a "
            "mutual fund) or a REIT (Real Estate Investment Trust) representing your share of <i>their</i> realized long-term gains."
            "<br><span style='color:#C53030'>Always long-term regardless of how long you held the fund shares, and it can never "
            "be negative.</span>",
        ])
        sd_8a = _sd_row("8a", "Totals for all long-term transactions reported on Form 1099-B", "sd_l8a",
                        helptext="Basis WAS reported to the IRS and no adjustment is needed. Enter totals here and skip Form 8949.")
        sd_8b = _sd_row("8b", "Long-term transactions reported on Form 8949 with Box D checked", "sd_l8b",
                        helptext="Box D: basis WAS reported to the IRS, but an adjustment is needed.")
        sd_9  = _sd_row("9",  "Long-term transactions reported on Form 8949 with Box E checked", "sd_l9",
                        helptext="Box E: reported on Form 1099-B, but basis was NOT reported to the IRS.")
        sd_10 = _sd_row("10", "Long-term transactions reported on Form 8949 with Box F checked", "sd_l10",
                        helptext="Box F: not reported on any Form 1099-B.")

        _l11c1, _l11c2 = st.columns([7, 3])
        _l11c1.markdown(
            "<div style='padding-top:0.4rem;color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>"
            "<b>[Line 11]</b> Enter gain from Form 4797, line 7 or 9"
            "<br><span style='font-size:0.8rem;color:#5a6a85;-webkit-text-fill-color:#5a6a85;'>Auto — net §1231 gain after the §1231(c) look-back recapture</span></div>",
            unsafe_allow_html=True)
        _l11c2.markdown(
            f"<div style='padding-top:0.6rem;text-align:right;font-weight:700;color:#1B3A6B;'>${sd_1231_ltcg:,.0f}</div>",
            unsafe_allow_html=True)
        sd_11 = sd_1231_ltcg

        sd_12 = _sd_row("12", "Long-term capital gain from installment sales (Form 6252)", "sd_l12",
                        helptext="§453: gain recognized as each payment is received, not all in the year of sale.")
        sd_13 = _sd_row("13", "Long-term capital gain or (loss) from like-kind exchanges (Form 8824)", "sd_l13",
                        helptext="§1031: enter only the taxable boot received. The deferred portion is excluded.")
        sd_14 = _sd_row("14", "Capital gain distributions", "sd_l14", allow_neg=False,
                        helptext="Long-term gains distributed by a mutual fund (RIC) or REIT. Always long-term; cannot be negative.")

        sd_15 = SD["l15"]
        st.markdown(
            f"<div style='background:#EBF4FF;border-left:4px solid #2D5A9E;padding:10px 14px;margin:8px 0;"
            f"color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>"
            f"<b>Line 15 — Net long-term capital gain or (loss).</b> Combine lines 8a through 14."
            f"<span style='float:right;font-size:1.2rem;font-weight:700;color:#1B3A6B;"
            f"-webkit-text-fill-color:#1B3A6B;'>${sd_15:,.0f}</span></div>",
            unsafe_allow_html=True)

        _slot_p3 = st.empty()

    # ── Capital loss carryover pool (executes after schedule; fills line 6) ──
    with sd_tab_cf:
        st.markdown("### §1212(a) Capital Loss Carryover")
        st.caption("Corporate net capital losses carry back 3 years and forward 5 years, always as short-term. Oldest year is applied first; anything past the 5-year window expires.")

        _pre_cf_net = SD["pre_cf_net"]
        st.markdown(
            f"**Current-year net capital gain before carryover:** ${_pre_cf_net:,.0f}"
            + ("" if _pre_cf_net > 0 else "  \n_No net gain this year — no carryover can be absorbed._"))

        st.markdown("**Unused net capital losses from prior years**")
        cf_h1, cf_h2, cf_h3, cf_h4 = st.columns([2, 3, 2, 3])
        cf_h1.markdown("**Loss year**")
        cf_h2.markdown("**Unused net capital loss ($)**")
        cf_h3.markdown("**Expires after**")
        cf_h4.markdown("**Applied this year**")

        for _r in SD["cf_rows"]:
            _y, _alive, _use = _r["year"], _r["alive"], _r["used"]
            r1, r2, r3, r4 = st.columns([2, 3, 2, 3])
            r1.markdown(f"<div style='padding-top:0.55rem;font-weight:600;color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>{_y}</div>", unsafe_allow_html=True)
            r2.number_input(f"cf_{_y}", min_value=0.0, step=1_000.0, format="%.2f",
                            key=f"sd_cf_loss_{_y}", label_visibility="collapsed")
            r3.markdown(
                f"<div style='padding-top:0.55rem;{'color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;' if _alive else 'color:#C53030;-webkit-text-fill-color:#C53030;font-weight:600;'}'>{_r['expires_after']}"
                + ("" if _alive else " — expired") + "</div>", unsafe_allow_html=True)
            r4.markdown(
                f"<div style='padding-top:0.55rem;{'color:#C53030;-webkit-text-fill-color:#C53030;font-weight:600;' if _use > 0 else 'color:#5a6a85;-webkit-text-fill-color:#5a6a85;'}'>"
                + (f"${_use:,.0f}" if _use > 0 else "—") + "</div>", unsafe_allow_html=True)

        sd_cf_applied = SD["cf_applied"]
        _cf_expired = SD["cf_expired"]
        _cf_unused = SD["cf_unused"]

        st.divider()
        cfm1, cfm2, cfm3 = st.columns(3)
        cfm1.metric("Applied this year (line 6)", f"${sd_cf_applied:,.0f}")
        cfm2.metric("Still carrying forward", f"${_cf_unused:,.0f}")
        cfm3.metric("Expired unused", f"${_cf_expired:,.0f}",
                    "Permanently lost" if _cf_expired > 0 else None)

        if _cf_expired > 0:
            st.error(f"\\${_cf_expired:,.0f} of capital loss carryover has passed the 5-year window and is permanently lost.")
        if _cf_unused > 0 and _pre_cf_net <= 0:
            st.info("No current-year capital gain to absorb the carryover — the full balance rolls to next year.")

    # ── Fill Part I lines 6–7 and Part III now that carryover is known ───────
    sd_6, sd_7 = SD["l6"], SD["l7"]

    _slot_l6.markdown(
        f"<div style='padding:6px 14px;color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>"
        f"<b>[Line 6]</b> Unused capital loss carryover "
        f"<span style='font-size:0.8rem;color:#5a6a85;-webkit-text-fill-color:#5a6a85;'>(auto — from the Capital Loss Carryover tab)</span>"
        f"<span style='float:right;font-weight:700;color:#C53030;-webkit-text-fill-color:#C53030;'>${sd_6:,.0f}</span></div>",
        unsafe_allow_html=True)
    _slot_l7.markdown(
        f"<div style='background:#EBF4FF;border-left:4px solid #2D5A9E;padding:10px 14px;margin:8px 0;"
        f"color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>"
        f"<b>Line 7 — Net short-term capital gain or (loss).</b> Combine lines 1a through 6."
        f"<span style='float:right;font-size:1.2rem;font-weight:700;color:#1B3A6B;"
        f"-webkit-text-fill-color:#1B3A6B;'>${sd_7:,.0f}</span></div>",
        unsafe_allow_html=True)

    sd_16 = SD["l16"]
    sd_17 = max(0.0, sd_15 + min(0.0, sd_7)) if sd_15 > 0 else 0.0
    sd_18, sd_net_loss = SD["l18"], SD["net_loss"]

    _slot_p3.markdown(f"""
## Part III — Summary of Parts I and II
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">16</td><td style="padding:8px 12px;">Excess of net short-term capital gain (line 7) over net long-term capital loss (line 15)</td><td style="padding:8px 12px;text-align:right;">${sd_16:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">17</td><td style="padding:8px 12px;">Net capital gain. Excess of net long-term capital gain (line 15) over net short-term capital loss (line 7)</td><td style="padding:8px 12px;text-align:right;">${sd_17:,.0f}</td></tr>
<tr style="background:#2D5A9E;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">18</td><td style="padding:8px 12px;font-weight:bold;">Add lines 16 and 17 — carries to Form 1120, page 1, line 8</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${sd_18:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)


    st.divider()
    sdm1, sdm2, sdm3 = st.columns(3)
    sdm1.metric("Line 7 — Net short-term", f"${sd_7:,.0f}")
    sdm2.metric("Line 15 — Net long-term", f"${sd_15:,.0f}")
    sdm3.metric("Line 18 → Page 1 Line 8", f"${sd_18:,.0f}")

    if sd_net_loss > 0:
        st.error(
            f"**Net capital loss of \\${sd_net_loss:,.0f}** — §1211(a) bars a C corporation from deducting it against "
            f"ordinary income, so line 18 is \\$0. Under §1212(a) carry it **back 3 years** (earliest year first), then "
            f"**forward 5 years** as a short-term capital loss.")
    elif sd_18 > 0:
        st.success(f"Net capital gain of \\${sd_18:,.0f} flows to Form 1120, page 1, line 8.")

# ─────────────────────────────────────────────────────────────────────────────
# FORM 4797 — SALES OF BUSINESS PROPERTY
# ─────────────────────────────────────────────────────────────────────────────
elif section == "🏭 Form 4797 — Business Property":
    st.title("Form 4797 — Sales of Business Property")
    st.caption("Part III computes recapture and feeds Parts I and II. Two destinations only: "
               "Part I line 9 → Schedule D line 11 → **Form 1120 line 8** (capital); "
               "Part II line 17 → **Form 1120 line 9** (ordinary). "
               "Note Form 4797's own line 9 and Form 1120's line 9 are different lines.")

    F = F4797
    _cy4 = int(TAX_YEAR)
    f_law, f_how, f_p1, f_p2, f_p3, f_p4 = st.tabs(
        ["📖 Law & Concepts", "📝 How to Fill", "Part I — §1231", "Part II — Ordinary", "Part III — Recapture", "Part IV — §179/§280F"])

    with f_law:
        irc([
            "<b>What Form 4797 covers:</b> disposals of <b>property used in a trade or business</b>. Schedule D covers "
            "§1221 investment assets; Form 4797 covers the operating assets — machinery, vehicles, buildings, land used in "
            "the business."
            "<br><span style='color:#C53030'>The two forms meet in exactly one place: net §1231 gain surviving the look-back "
            "moves from Form 4797 Part I line 9 onto Schedule D line 11.</span>",

            "<b>§1231 — the asymmetry that makes this form matter:</b> Property used in a trade or business and held more "
            "than 1 year."
            "<br>&nbsp;&nbsp;Net §1231 <b>gain</b> → long-term capital gain treatment (favourable)."
            "<br>&nbsp;&nbsp;Net §1231 <b>loss</b> → <b>ordinary</b> loss, fully deductible against ordinary income."
            "<br><span style='color:#C53030'>Best of both worlds — which is why §1231(c) exists to stop taxpayers harvesting "
            "ordinary losses one year and capital gains the next.</span>",

            "<b>Order of operations — the form is computed bottom-up:</b>"
            "<br>&nbsp;&nbsp;<b>Part III</b> first: computes §1245 / §1250 / §291 depreciation recapture per property."
            "<br>&nbsp;&nbsp;Part III line 31 (recapture) → <b>Part II line 13</b> — always ordinary income."
            "<br>&nbsp;&nbsp;Part III line 32 (the remainder) → <b>Part I line 6</b> — the §1231 portion."
            "<br>&nbsp;&nbsp;Part I line 7 nets all §1231 items, then lines 8–9 apply the look-back."
            "<br>&nbsp;&nbsp;<b>Part II line 17</b> → Form 1120 line 9.",

            "<b>§1245 recapture (personal property — equipment, vehicles):</b> Gain is ordinary to the extent of "
            "<b>all depreciation previously allowed</b>."
            "<br><span style='color:#C53030'>Recapture = lesser of (total gain) or (accumulated depreciation). If the gain is "
            "smaller than accumulated depreciation, 100% of it is ordinary and no §1231 gain survives.</span>",

            "<b>§291(a)(1) — the C corporation add-on for real property:</b> For §1250 property a C corp must treat an extra "
            "<b>20%</b> of the excess §1245-style recapture as ordinary income."
            "<br><span style='color:#C53030'>Applies to corporations only — this is a classic exam distinction between a C corp "
            "and an individual selling the same building.</span>",

            "<b>§1231(c) five-year look-back — Part I lines 7 / 8 / 9:</b>"
            "<br>&nbsp;&nbsp;Line 7 = net §1231 result. If it is <b>zero or a loss</b>, it goes to Part II line 11 as an ordinary loss."
            "<br>&nbsp;&nbsp;Line 8 = <b>non-recaptured net §1231 losses</b> from the 5 preceding years."
            "<br>&nbsp;&nbsp;Line 9 = line 7 − line 8, floored at zero."
            "<br><span style='color:#C53030'>If line 9 is zero, the whole gain on line 7 goes to Part II line 12 as ordinary. "
            "If line 9 is positive, line 8 goes to line 12 (ordinary) and only line 9 reaches Schedule D as LTCG.</span>",
        ])

    with f_how:
        st.markdown("### Form 4797 is filled bottom-up — Part III, then Part I, then Part II.")
        st.caption("Part III produces the two numbers Parts I and II depend on, so working top-down leaves Part I line 6 blank when you reach it.")

        st.markdown("### Step 1 — Does the disposal even belong on Form 4797?")
        st.markdown("""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">What was disposed of</th>
<th style="padding:8px 12px;text-align:left;">Where it goes</th>
<th style="padding:8px 12px;text-align:left;">Why</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Stocks, bonds, investment land</td><td style="padding:8px 12px;"><b>Schedule D</b> — never touches Form 4797</td><td style="padding:8px 12px;">§1221 capital asset</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Inventory, accounts receivable</td><td style="padding:8px 12px;">Form 1120 line 1a / ordinary income</td><td style="padding:8px 12px;">Ordinary asset by definition</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>Depreciable</b> business property, held <b>&gt; 1 year</b></td><td style="padding:8px 12px;"><b>Part III → Part I</b></td><td style="padding:8px 12px;">§1231 property with depreciation to recapture</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Business <b>land</b>, held &gt; 1 year</td><td style="padding:8px 12px;"><b>Part I line 2</b> — skip Part III entirely</td><td style="padding:8px 12px;">§1231 but land is not depreciable, so there is nothing to recapture</td></tr>
<tr><td style="padding:8px 12px;">Business property held <b>≤ 1 year</b></td><td style="padding:8px 12px;"><b>Part II line 10</b></td><td style="padding:8px 12px;">Not §1231 — fully ordinary</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        irc([
            "<b>Most common filing error at this step:</b> putting business land into Part III."
            "<br><span style='color:#C53030'>Land has no accumulated depreciation, so Part III has nothing to compute for it. "
            "It skips straight to Part I line 2.</span>",
        ])

        st.markdown("### Step 2 — Fill the form bottom-up, not top-down")
        irc([
            "<b>The order on the page is not the order you work in.</b> Part III produces two numbers that Parts I and II "
            "depend on, and Part II is almost entirely auto-filled from the other two."
            "<br>&nbsp;&nbsp;<b>1st — Part III:</b> compute depreciation recapture per property."
            "<br>&nbsp;&nbsp;<b>2nd — Part I:</b> net the §1231 items, then apply the §1231(c) look-back."
            "<br>&nbsp;&nbsp;<b>3rd — Part II:</b> collect everything ordinary and total to line 17."
            "<br><span style='color:#C53030'>Part III line 31 → Part II line 13 &nbsp;·&nbsp; Part III line 32 → Part I line 6. "
            "Filling top-down means Part I line 6 is still blank when you reach it.</span>",
        ])

        st.markdown("### Step 3 — Part III, property by property")
        st.markdown("""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">What to enter</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">19</td><td style="padding:8px 12px;">Description, date acquired, date sold</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">20</td><td style="padding:8px 12px;">Gross sales price</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">21</td><td style="padding:8px 12px;">Cost or other basis <b>plus expense of sale</b></td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">22</td><td style="padding:8px 12px;">Depreciation <b>allowed <i>or allowable</i></b></td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">23</td><td style="padding:8px 12px;">Adjusted basis = line 21 − line 22</td></tr>
<tr style="background:#eef2f7;"><td style="padding:8px 12px;">24</td><td style="padding:8px 12px;">Total gain = line 20 − line 23</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        irc([
            "<b>Line 22 is the biggest trap on the form — “allowed <i>or allowable</i>”.</b> Depreciation you were entitled "
            "to take but did <b>not</b> claim is still recaptured on sale."
            "<br><span style='color:#C53030'>Skipping depreciation deductions does not avoid recapture — you lose the annual "
            "deduction and still pay ordinary income on the amount when you sell. It is a pure loss.</span>",

            "<b>Then split by property type:</b>"
            "<br>&nbsp;&nbsp;<b>§1245 — line 25</b> (equipment, vehicles, machinery): "
            "<span style='color:#C53030'>25b = min(line 24 total gain, line 22 accumulated depreciation)</span>. "
            "Plain English: all depreciation comes back as ordinary income, capped at the gain."
            "<br>&nbsp;&nbsp;<b>§1250 + §291 — line 26</b> (real property, C corporations): post-1986 real property uses "
            "straight-line, so classic §1250 recapture is usually zero — but a C corp still owes §291(a)(1)."
            "<br><span style='color:#C53030'>§291 recapture = 20% × (what §1245 recapture <i>would</i> have been − actual §1250 "
            "recapture) = 20% × min(gain, depreciation) under straight-line. Corporations only — an individual selling the same "
            "building has no §291.</span>",

            "<b>Part III exits into two places:</b>"
            "<br>&nbsp;&nbsp;<b>Line 31</b> = total recapture → <b>Part II line 13</b> — always ordinary income."
            "<br>&nbsp;&nbsp;<b>Line 32</b> = line 30 − line 31 → <b>Part I line 6</b> — the §1231 portion.",
        ])

        st.markdown("### Step 4 — Part I, then the three-way branch at line 7")
        irc([
            "<b>Enter lines 2 through 5 yourself; line 6 arrives from Part III.</b>"
            "<br>&nbsp;&nbsp;Line 2 — §1231 transactions that never needed Part III (land, non-depreciable property)."
            "<br>&nbsp;&nbsp;Line 3 — Form 4684 casualty and theft gains."
            "<br>&nbsp;&nbsp;Line 4 — §453 installment sales &nbsp;·&nbsp; Line 5 — §1031 like-kind exchanges."
            "<br>&nbsp;&nbsp;Line 7 = combine lines 2 through 6.",

            "<b>Line 7 then branches three ways — this is the heart of the form:</b>"
            "<br>&nbsp;&nbsp;<b>(a) Line 7 is zero or a loss</b> → the whole amount goes to <b>Part II line 11</b> as an "
            "<b>ordinary loss</b>. Schedule D receives nothing."
            "<br><span style='color:#C53030'>&nbsp;&nbsp;&nbsp;&nbsp;It also becomes a non-recaptured §1231 loss that the "
            "look-back will hold against gains for the next 5 years.</span>"
            "<br>&nbsp;&nbsp;<b>(b) Line 7 is a gain and line 9 = 0</b> (the prior-year loss pool absorbs it all) → the whole "
            "gain goes to <b>Part II line 12</b> as ordinary income."
            "<br>&nbsp;&nbsp;<b>(c) Line 7 is a gain and line 9 &gt; 0</b> → <b>line 8</b> goes to Part II line 12 (ordinary) "
            "and only <b>line 9</b> reaches Schedule D line 11 as long-term capital gain.",

            "<b>Why §1231(c) exists:</b> §1231 gives gains capital treatment and losses ordinary treatment — the best of both. "
            "Without the look-back a taxpayer could take ordinary losses in one year and capital gains the next."
            "<br><span style='color:#C53030'>The look-back makes you repay the earlier ordinary benefit as ordinary income "
            "before any capital treatment is allowed. Apply the oldest year first.</span>",
        ])

        st.markdown("### Step 5 — Part II is mostly automatic")
        st.markdown("""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Source</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">10</td><td style="padding:8px 12px;"><b>You enter</b> — business property held 1 year or less</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">11</td><td style="padding:8px 12px;">Auto — line 7 if it is a loss</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">12</td><td style="padding:8px 12px;">Auto — §1231(c) look-back recapture</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">13</td><td style="padding:8px 12px;">Auto — Part III line 31</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">14 / 15 / 16</td><td style="padding:8px 12px;">Form 4684 / Form 6252 / Form 8824</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">17</td><td style="padding:8px 12px;font-weight:bold;">Total → Form 1120 page 1, line 9</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        st.markdown("### Worked example — equipment sold at a gain")
        st.markdown("""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Facts</td><td style="padding:8px 12px;">Sale price 120,000 · original cost 100,000 · accumulated depreciation 60,000 · held 3 years</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Part III line 23</td><td style="padding:8px 12px;">Adjusted basis = 100,000 − 60,000 = <b>40,000</b></td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Part III line 24</td><td style="padding:8px 12px;">Total gain = 120,000 − 40,000 = <b>80,000</b></td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Part III line 25b</td><td style="padding:8px 12px;">§1245 recapture = min(80,000, 60,000) = <b>60,000</b></td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Part III lines 31 / 32</td><td style="padding:8px 12px;">31 = 60,000 → Part II line 13 &nbsp;·&nbsp; 32 = 20,000 → Part I line 6</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Part I lines 7 / 8 / 9</td><td style="padding:8px 12px;">7 = 20,000 · 8 = 0 (no prior losses) · 9 = <b>20,000</b> → Schedule D line 11</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Part II line 17</td><td style="padding:8px 12px;"><b>60,000</b> → Form 1120 line 9</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">Result</td><td style="padding:8px 12px;font-weight:bold;">Form 1120 LINE 8 = 20,000 (capital) · Form 1120 LINE 9 = 60,000 (ordinary)</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        irc([
            "<b>What the split means economically:</b> the company deducted 60,000 of depreciation over three years, but the "
            "asset only really fell in value by 20,000 (120,000 sale price against 100,000 cost means it actually appreciated)."
            "<br><span style='color:#C53030'>The over-deducted 60,000 is clawed back as <b>ordinary</b> income. Only the "
            "20,000 of genuine appreciation above original cost gets capital gain treatment.</span>"
            "<br>That is the whole logic of depreciation recapture: you do not get an ordinary deduction going in and a "
            "capital rate coming out on the same dollars.",
        ])

        st.markdown("### Six mistakes that cost marks")
        irc([
            "<b>1. Filling the form top-down.</b> Part III must be completed first — Parts I and II depend on it.",
            "<b>2. Entering only the depreciation actually claimed on line 22.</b> "
            "<span style='color:#C53030'>The statute says allowed <i>or allowable</i>.</span>",
            "<b>3. Sending a net §1231 loss to Schedule D.</b> "
            "<span style='color:#C53030'>It is an <b>ordinary</b> loss and stays on Part II line 11.</span>",
            "<b>4. Forgetting §291 for a C corporation.</b> Individuals have no §291; corporations owe an extra 20% slice of "
            "ordinary income on real property.",
            "<b>5. Putting business land in Part III.</b> No depreciation means nothing to recapture — it belongs on Part I line 2.",
            "<b>6. Confusing the two “line 9”s.</b> "
            "<span style='color:#C53030'>Form 4797 Part I line 9 is the capital amount heading to Schedule D and ultimately "
            "Form 1120 <b>line 8</b>. Form 1120 line 9 is the ordinary total from Form 4797 Part II line 17. Different lines, "
            "different characters, different destinations.</span>",
        ])

    # ── Part III first — it feeds Parts I and II ─────────────────────────────
    with f_p3:
        st.markdown("### Part III — Gain From Disposition Under §1245 / §1250 / §291")
        st.number_input("Number of properties disposed of (A–D)", min_value=1, max_value=4, value=1,
                        step=1, key="f4797_n_props")
        for i in range(int(st.session_state.get("f4797_n_props", 1))):
            st.markdown(f"**Property {chr(65 + i)}**")
            p1c, p2c, p3c = st.columns([3, 2, 2])
            p1c.text_input("Description (line 19)", value=f"Property {chr(65 + i)}", key=f"f4797_desc_{i}")
            p1c.radio("Property type", ["§1245 — Personal property", "§1250 + §291 — Real property"],
                      key=f"f4797_type_{i}", horizontal=False)
            p2c.number_input("Line 20 — Gross sales price ($)", min_value=0.0, step=1_000.0,
                             format="%.2f", key=f"f4797_price_{i}")
            p2c.number_input("Line 21 — Cost or other basis ($)", min_value=0.0, step=1_000.0,
                             format="%.2f", key=f"f4797_basis_{i}")
            p3c.number_input("Line 22 — Depreciation allowed ($)", min_value=0.0, step=1_000.0,
                             format="%.2f", key=f"f4797_dep_{i}")
            _p = F["props"][i] if i < len(F["props"]) else None
            if _p:
                p3c.markdown(
                    f"<div style='padding-top:0.5rem;color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;font-size:0.85rem;'>"
                    f"Line 23 adjusted basis <b>${_p['adj_basis']:,.0f}</b><br>"
                    f"Line 24 total gain <b>${_p['gain']:,.0f}</b><br>"
                    f"<span style='color:#C53030;-webkit-text-fill-color:#C53030;'>Recapture <b>${_p['recapture']:,.0f}</b></span><br>"
                    f"§1231 portion <b>${_p['sec1231']:,.0f}</b></div>", unsafe_allow_html=True)
            st.divider()

        st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">30</td><td style="padding:8px 12px;">Total gains for all properties (add line 24, columns A–D)</td><td style="padding:8px 12px;text-align:right;">${F['l30']:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">31</td><td style="padding:8px 12px;">Total recapture — <b>carries to Part II line 13</b> (ordinary)</td><td style="padding:8px 12px;text-align:right;">${F['l31']:,.0f}</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">32</td><td style="padding:8px 12px;font-weight:bold;">Line 30 less line 31 — <b>carries to Part I line 6</b> (§1231)</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${F['l32']:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

    with f_p4:
        st.markdown("### Part IV — Recapture Under §179 and §280F(b)(2)")
        st.caption("Applies when business use of the property drops to 50% or less. C corporations rarely hit this; it is "
                   "informational here and does not flow into Parts I–III.")
        q1, q2 = st.columns(2)
        p4_prior = q1.number_input("Line 33 — §179 expense or depreciation allowable in prior years ($)",
                                   min_value=0.0, step=1_000.0, format="%.2f", key="f4797_l33")
        p4_recomp = q2.number_input("Line 34 — Recomputed depreciation ($)", min_value=0.0, step=1_000.0,
                                    format="%.2f", key="f4797_l34")
        st.metric("Line 35 — Recapture amount", f"${max(0.0, p4_prior - p4_recomp):,.0f}",
                  "line 33 minus line 34")
        irc([
            "<b>§179 recapture:</b> If business use falls to <b>50% or less</b> before the end of the property's recovery "
            "period, the §179 deduction previously taken is recaptured as ordinary income."
            "<br><span style='color:#C53030'>Recapture amount = §179 previously deducted − depreciation that <i>would</i> have "
            "been allowed under MACRS without the election.</span>",
        ])

    # ── Part I ────────────────────────────────────────────────────────────────
    with f_p1:
        st.markdown("### Part I — §1231 Property Held More Than 1 Year")
        st.number_input("Line 2 — §1231 gains/(losses) from property held > 1 year (from line 2, column (g)) ($)",
                        step=1_000.0, format="%.2f", key="f4797_l2")
        st.number_input("Line 3 — Gain from Form 4684, line 39 (casualty/theft) ($)",
                        step=1_000.0, format="%.2f", key="f4797_l3")
        st.number_input("Line 4 — §1231 gain from installment sales (Form 6252) ($)",
                        step=1_000.0, format="%.2f", key="f4797_l4")
        st.number_input("Line 5 — §1231 gain or (loss) from like-kind exchanges (Form 8824) ($)",
                        step=1_000.0, format="%.2f", key="f4797_l5")

        _l6c1, _l6c2 = st.columns([7, 3])
        _l6c1.markdown("<div style='padding-top:0.4rem;color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>"
                       "<b>[Line 6]</b> Gain from Part III line 32"
                       "<br><span style='font-size:0.8rem;color:#5a6a85;-webkit-text-fill-color:#5a6a85;'>Auto — the §1231 portion left after recapture</span></div>",
                       unsafe_allow_html=True)
        _l6c2.markdown(f"<div style='padding-top:0.6rem;text-align:right;font-weight:700;color:#1B3A6B;"
                       f"-webkit-text-fill-color:#1B3A6B;'>${F['l6']:,.0f}</div>", unsafe_allow_html=True)

        st.markdown(
            f"<div style='background:#EBF4FF;border-left:4px solid #2D5A9E;padding:10px 14px;margin:8px 0;"
            f"color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>"
            f"<b>Line 7 — Combine lines 2 through 6.</b>"
            f"<span style='float:right;font-size:1.2rem;font-weight:700;color:#1B3A6B;"
            f"-webkit-text-fill-color:#1B3A6B;'>${F['l7']:,.0f}</span></div>", unsafe_allow_html=True)

        st.markdown("#### Line 8 — Non-recaptured net §1231 losses from the prior 5 years")
        lb1, lb2, lb3, lb4 = st.columns([2, 3, 3, 3])
        lb1.markdown("**Year**"); lb2.markdown("**Net §1231 loss deducted ($)**")
        lb3.markdown("**Already recaptured ($)**"); lb4.markdown("**Still available**")
        for r in F["lb_rows"]:
            c1, c2, c3, c4 = st.columns([2, 3, 3, 3])
            c1.markdown(f"<div style='padding-top:0.55rem;font-weight:600;color:#1a1a2e;"
                        f"-webkit-text-fill-color:#1a1a2e;'>{r['year']}</div>", unsafe_allow_html=True)
            c2.number_input(f"loss_{r['year']}", min_value=0.0, step=1_000.0, format="%.2f",
                            key=f"f4797_lb_loss_{r['year']}", label_visibility="collapsed")
            c3.number_input(f"recap_{r['year']}", min_value=0.0, step=1_000.0, format="%.2f",
                            key=f"f4797_lb_recap_{r['year']}", label_visibility="collapsed")
            c4.markdown(
                f"<div style='padding-top:0.55rem;color:#1a1a2e;-webkit-text-fill-color:#1a1a2e;'>${r['avail']:,.0f}"
                + (f" <span style='color:#C53030;-webkit-text-fill-color:#C53030;font-weight:600;'>→ ${r['used']:,.0f} used</span>"
                   if r.get('used', 0) > 0 else "") + "</div>", unsafe_allow_html=True)

        st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;margin-top:10px;">
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">8</td><td style="padding:8px 12px;">Non-recaptured net §1231 losses from prior years</td><td style="padding:8px 12px;text-align:right;">${F['l8']:,.0f}</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">9</td><td style="padding:8px 12px;font-weight:bold;">Line 7 less line 8 (not below zero) — <b>→ Schedule D line 11 → Form 1120 LINE 8</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${F['l9']:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        if F["l7"] <= 0:
            st.error(f"Line 7 is a **net §1231 loss of \\${abs(F['l7']):,.0f}** → the entire amount goes to "
                     f"**Part II line 11 as an ordinary loss**. Nothing reaches Schedule D. It also becomes a "
                     f"non-recaptured §1231 loss that the look-back will use against gains in the next 5 years.")
        elif F["l9"] == 0:
            st.warning(f"Line 9 is zero — the prior-year loss pool (\\${F['l8']:,.0f}) fully absorbs the gain. "
                       f"The whole \\${F['l7']:,.0f} goes to **Part II line 12 as ordinary income**; Schedule D gets nothing.")
        else:
            st.success(f"\\${F['l12']:,.0f} recharacterized as ordinary (Part II line 12); "
                       f"\\${F['l9']:,.0f} keeps long-term capital gain treatment → Schedule D line 11.")

    # ── Part II ───────────────────────────────────────────────────────────────
    with f_p2:
        st.markdown("### Part II — Ordinary Gains and Losses")
        st.number_input("Line 10 — Ordinary gains/(losses) not on lines 11–16 — property held ≤ 1 year ($)",
                        step=1_000.0, format="%.2f", key="f4797_l10")
        st.number_input("Line 14 — Net gain or (loss) from Form 4684 (casualty/theft) ($)",
                        step=1_000.0, format="%.2f", key="f4797_l14")
        st.number_input("Line 15 — Ordinary gain from installment sales (Form 6252) ($)",
                        step=1_000.0, format="%.2f", key="f4797_l15")
        st.number_input("Line 16 — Ordinary gain or (loss) from like-kind exchanges (Form 8824) ($)",
                        step=1_000.0, format="%.2f", key="f4797_l16")

        st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">10</td><td style="padding:8px 12px;">Ordinary gains and losses — held ≤ 1 year</td><td style="padding:8px 12px;text-align:right;">${F['l10']:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">11</td><td style="padding:8px 12px;">Loss, if any, from line 7 <i>(auto)</i></td><td style="padding:8px 12px;text-align:right;">${F['l11']:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">12</td><td style="padding:8px 12px;">Gain from line 7, or amount from line 8 <i>(auto — §1231(c) recapture)</i></td><td style="padding:8px 12px;text-align:right;">${F['l12']:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">13</td><td style="padding:8px 12px;">Gain from Part III line 31 <i>(auto — depreciation recapture)</i></td><td style="padding:8px 12px;text-align:right;">${F['l13']:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">14</td><td style="padding:8px 12px;">Form 4684 casualty/theft</td><td style="padding:8px 12px;text-align:right;">${F['l14']:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">15</td><td style="padding:8px 12px;">Installment sales (Form 6252)</td><td style="padding:8px 12px;text-align:right;">${F['l15']:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">16</td><td style="padding:8px 12px;">Like-kind exchanges (Form 8824)</td><td style="padding:8px 12px;text-align:right;">${F['l16']:,.0f}</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">17</td><td style="padding:8px 12px;font-weight:bold;">Combine lines 10 through 16 — <b>→ Form 1120 page 1, line 9</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${F['l17']:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### Where each piece lands on Form 1120")
    st.caption("Form 4797 has its own line 9 and Form 1120 has a different line 9 — these are not the same line. "
               "The two columns below are the only two destinations.")

    st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Route</th>
<th style="padding:8px 12px;text-align:left;">Path through the forms</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>Capital</b></td><td style="padding:8px 12px;">Part III line 32 → Part I line 6 → line 7 → <i>look-back</i> → <b>Part I line 9</b> → Schedule D line 11 → Schedule D line 18</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${F['l9']:,.0f}</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">→</td><td style="padding:8px 12px;font-weight:bold;">Form 1120, page 1, <b>LINE 8</b> — Capital gain net income</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${F['l9']:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>Ordinary</b></td><td style="padding:8px 12px;">Part III line 31 (recapture) → Part II line 13; §1231(c) recapture → Part II line 12; net §1231 loss → Part II line 11 → <b>Part II line 17</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${F['l17']:,.0f}</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">→</td><td style="padding:8px 12px;font-weight:bold;">Form 1120, page 1, <b>LINE 9</b> — Net gain from Form 4797</td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${F['l17']:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

    fm1, fm2, fm3 = st.columns(3)
    fm1.metric("Part III line 31 — depreciation recapture", f"${F['l31']:,.0f}",
               "ordinary → Part II line 13")
    fm2.metric("→ Form 1120 LINE 8 (capital gain)", f"${F['l9']:,.0f}",
               "via Part I line 9 → Schedule D line 11")
    fm3.metric("→ Form 1120 LINE 9 (ordinary income)", f"${F['l17']:,.0f}",
               "Form 4797 Part II line 17")

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE J — TAX COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────
elif section == "🧮 Schedule J — Tax Computation":
    st.title("Schedule J — Tax Computation and Payment")
    st.caption("Part I line 11 → Form 1120 page 1, line 31 (total tax). "
               "Part II line 22 → Form 1120 page 1, line 33 (total payments and credits).")

    _sj_l30 = R1120["taxable_income"]["taxable_income"]
    _sj_l2_regular = R1120["tax"]["regular_tax"]
    _sj_camt = R1120["tax"]["camt"]["camt"]
    _sj_l2 = _sj_l2_regular + _sj_camt
    _sj_l3 = R1120["tax"]["beat"]["beat"]
    _sj_l4 = _sj_l2 + _sj_l3
    _sj_l5a = st.session_state.get("ftc", 0.0)
    _sj_l5c = (R1120["tax"]["credits"]["rd_credit_used"]
               + st.session_state.get("other_credits", 0.0))
    _sj_l5d = st.session_state.get("camt_credit_prior", 0.0)
    _sj_l6 = _sj_l5a + _sj_l5c + _sj_l5d
    _sj_l7 = max(0.0, _sj_l4 - _sj_l6)
    _sj_l8 = st.session_state.get("sj_phc_tax", 0.0)
    _sj_l10 = st.session_state.get("sj_other_taxes", 0.0)
    _sj_l11 = _sj_l7 + _sj_l8 + _sj_l10

    sj_tab_calc, sj_tab_pay, sj_tab_credits = st.tabs(
        ["🧮 Part I — Tax Computation", "💵 Part II — Payments", "📖 Credit & Minimum-Tax Detail"])

    with sj_tab_calc:
        st.markdown("### Part I — Tax Computation")
        j1, j2 = st.columns(2)
        j1.number_input("Line 8 — Personal holding company tax (Schedule PH) ($)", min_value=0.0,
                        step=1_000.0, format="%.2f", key="sj_phc_tax")
        j2.number_input("Lines 9a–9g — Recapture and other taxes, total ($)", min_value=0.0,
                        step=1_000.0, format="%.2f", key="sj_other_taxes",
                        help="Form 4255 investment credit recapture, Form 8611 low-income housing recapture, "
                             "Form 8697/8866 look-back interest, §453A(c) interest, Form 8902 shipping.")

        st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">—</td><td style="padding:8px 12px;">Taxable income (page 1, line 30)</td><td style="padding:8px 12px;text-align:right;">${_sj_l30:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">2</td><td style="padding:8px 12px;">Income tax — 21% flat, plus CAMT (Form 4626) where applicable</td><td style="padding:8px 12px;text-align:right;">${_sj_l2:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">3</td><td style="padding:8px 12px;">Base erosion minimum tax — BEAT (Form 8991)</td><td style="padding:8px 12px;text-align:right;">${_sj_l3:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>4</b></td><td style="padding:8px 12px;"><b>Add lines 2 and 3</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${_sj_l4:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">5a</td><td style="padding:8px 12px;">Foreign tax credit (Form 1118)</td><td style="padding:8px 12px;text-align:right;">(${_sj_l5a:,.0f})</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">5c</td><td style="padding:8px 12px;">General business credit (Form 3800) — includes the §41 R&amp;D credit</td><td style="padding:8px 12px;text-align:right;">(${_sj_l5c:,.0f})</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">5d</td><td style="padding:8px 12px;">Credit for prior year minimum tax (Form 8827) — CAMT credit carryforward</td><td style="padding:8px 12px;text-align:right;">(${_sj_l5d:,.0f})</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>6</b></td><td style="padding:8px 12px;"><b>Total credits — add lines 5a through 5e</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">(${_sj_l6:,.0f})</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>7</b></td><td style="padding:8px 12px;"><b>Subtract line 6 from line 4</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${_sj_l7:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">8</td><td style="padding:8px 12px;">Personal holding company tax (Schedule PH)</td><td style="padding:8px 12px;text-align:right;">${_sj_l8:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">10</td><td style="padding:8px 12px;">Total of lines 9a through 9g — recapture and other taxes</td><td style="padding:8px 12px;text-align:right;">${_sj_l10:,.0f}</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">11</td><td style="padding:8px 12px;font-weight:bold;">Total tax — add lines 7, 8 and 10 → <b>page 1, line 31</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${_sj_l11:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        irc([
            "<b>Credits reduce tax; deductions reduce income.</b> Everything on Schedule J lines 5a–5e is a "
            "<b>credit</b> — a dollar of credit removes a dollar of tax, so it is worth roughly five times a dollar of "
            "deduction at the 21% rate."
            "<br><span style='color:#C53030'>This is why the §41 R&amp;D credit is worth chasing even though the underlying "
            "wages were already deductible.</span>",

            "<b>Ordering matters on this schedule:</b> BEAT is added at line 3 <i>before</i> credits, and the FTC (Foreign "
            "Tax Credit) at line 5a comes off the combined figure."
            "<br><span style='color:#C53030'>But §59A(b) computes BEAT itself by reference to regular tax <i>after</i> "
            "credits — which is exactly why the FTC cannot shelter BEAT. Claiming more FTC lowers regular tax and "
            "mechanically raises the BEAT top-up.</span>",

            "<b>Line 9a–9g are add-backs, not credits.</b> Investment credit recapture (Form 4255), low-income housing "
            "recapture (Form 8611), look-back interest on long-term contracts (Form 8697) and §453A(c) interest all "
            "<i>increase</i> total tax at line 10.",
        ])

    with sj_tab_pay:
        st.markdown("### Part II — Payments and Refundable Credits")
        st.caption("Quarterly estimates are entered on the 📅 Estimated Tax & Safe Harbor page and carried here.")

        _sj_l12 = st.session_state.get("prior_overpayment", 0.0)
        _sj_l13 = sum(st.session_state.get(k, 0.0) for k in ("q1", "q2", "q3", "q4"))
        p1, p2 = st.columns(2)
        _sj_l14 = p1.number_input("Line 14 — Refund applied for on Form 4466 ($)", min_value=0.0,
                                  step=1_000.0, format="%.2f", key="sj_l14")
        _sj_l16 = p2.number_input("Line 16 — Tax deposited with Form 7004 (extension) ($)", min_value=0.0,
                                  step=1_000.0, format="%.2f", key="sj_l16")
        _sj_l17 = p1.number_input("Line 17 — Withholding ($)", min_value=0.0,
                                  step=1_000.0, format="%.2f", key="sj_l17")
        _sj_l20 = p2.number_input("Lines 19a–19d — Refundable credits, total ($)", min_value=0.0,
                                  step=1_000.0, format="%.2f", key="sj_l20",
                                  help="Form 2439 undistributed capital gains, Form 4136 fuel tax credit, "
                                       "Form 8827 line 5c refundable minimum tax.")

        _sj_l15 = _sj_l12 + _sj_l13 - _sj_l14
        _sj_l18 = _sj_l15 + _sj_l16 + _sj_l17
        _sj_l22 = _sj_l18 + _sj_l20
        _sj_balance = _sj_l11 - _sj_l22

        st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Line</th>
<th style="padding:8px 12px;text-align:left;">Item</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">12</td><td style="padding:8px 12px;">Preceding year's overpayment credited to this year</td><td style="padding:8px 12px;text-align:right;">${_sj_l12:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">13</td><td style="padding:8px 12px;">Current year's estimated tax payments (Q1–Q4)</td><td style="padding:8px 12px;text-align:right;">${_sj_l13:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">14</td><td style="padding:8px 12px;">Less: refund applied for on Form 4466</td><td style="padding:8px 12px;text-align:right;">(${_sj_l14:,.0f})</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>15</b></td><td style="padding:8px 12px;"><b>Combine lines 12, 13 and 14</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${_sj_l15:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">16</td><td style="padding:8px 12px;">Tax deposited with Form 7004</td><td style="padding:8px 12px;text-align:right;">${_sj_l16:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">17</td><td style="padding:8px 12px;">Withholding</td><td style="padding:8px 12px;text-align:right;">${_sj_l17:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;"><b>18</b></td><td style="padding:8px 12px;"><b>Total payments — add lines 15, 16 and 17</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${_sj_l18:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">20</td><td style="padding:8px 12px;">Total refundable credits (lines 19a–19d)</td><td style="padding:8px 12px;text-align:right;">${_sj_l20:,.0f}</td></tr>
<tr style="background:#1B3A6B;color:#ffffff;"><td style="padding:8px 12px;font-weight:bold;">22</td><td style="padding:8px 12px;font-weight:bold;">Total payments and credits → <b>page 1, line 33</b></td><td style="padding:8px 12px;text-align:right;font-weight:bold;">${_sj_l22:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

        b1, b2, b3 = st.columns(3)
        b1.metric("Line 11 — Total tax", f"${_sj_l11:,.0f}", "→ page 1 line 31")
        b2.metric("Line 22 — Total payments", f"${_sj_l22:,.0f}", "→ page 1 line 33")
        b3.metric("Balance due / (overpayment)", f"${_sj_balance:,.0f}",
                  "page 1 line 34" if _sj_balance > 0 else "page 1 line 35")

        if _sj_balance > 0:
            st.error(f"**Balance due \\${_sj_balance:,.0f}** — Form 1120 page 1 line 34.")
        elif _sj_balance < 0:
            st.success(f"**Overpayment \\${abs(_sj_balance):,.0f}** — Form 1120 page 1 line 35. "
                       f"Elect on line 36 to refund it or credit it to next year's estimated tax.")

        irc([
            "<b>Refundable vs non-refundable:</b> lines 5a–5e are <b>non-refundable</b> — they can reduce tax to zero but "
            "no further. Lines 19a–19d are <b>refundable</b> — they are treated like payments and can generate a refund."
            "<br><span style='color:#C53030'>That is why they sit in Part II with the cash, not in Part I with the credits.</span>",
            "<b>Form 4466 (line 14) is a subtraction, not an addition.</b> It is a <i>quick refund</i> of overpaid estimated "
            "tax claimed before the return is filed, so the amount already returned must come back out of the payments total.",
        ])

    with sj_tab_credits:
        st.markdown("## §41 R&D Credit — Form 6765")
        c1, c2 = st.columns(2)
        c1.number_input(L("—", "Current Year QRE — wages + supplies + 65% contract research"), min_value=0.0, step=1_000.0, format="%.2f", key="current_qre")
        c2.number_input(L("—", "Avg Prior 3-Year QRE — enter 0 if startup"), min_value=0.0, step=1_000.0, format="%.2f", key="avg_prior_3yr_qre")
        c1.slider("Fixed Base % — Regular Method only (3–16%)", 3, 16, key="fixed_base_pct")
        c2.number_input(L("—", "Avg Gross Receipts — Regular Method only"), min_value=0.0, step=10_000.0, format="%.2f", key="avg_gross_receipts_rd")
        irc([
            "§41 R&D Credit: QRE (Qualified Research Expenditure) = wages for research personnel + supplies + 65% of contract research.",
            "Four tests for a QRE: (1) technological uncertainty, (2) process of experimentation, (3) technological in nature, (4) qualified purpose.",
            "<span style='color:#C53030'><b>ASC (Alternative Simplified Credit) method:</b> 14% × (current QRE − 50% × avg prior 3-yr QRE). Available only if regular method not previously elected.</span>",
            "<span style='color:#C53030'><b>Regular method:</b> 20% × (current QRE − fixed base % × avg gross receipts). Fixed base % = historical QRE/gross receipts ratio (3–16%).</span>",
            "§280C(c): Claiming the §41 credit reduces the QRE deduction by the credit amount. An election to take a reduced credit instead is available on Form 6765.",
        ])

        st.markdown("## Foreign Tax Credit & Other Credits")
        c1, c2 = st.columns(2)
        c1.number_input(L("5a", "Foreign Tax Credit — Form 1118"), min_value=0.0, step=1_000.0, format="%.2f", key="ftc")
        c2.number_input(L("5c", "Other General Business Credits — Form 3800"), min_value=0.0, step=1_000.0, format="%.2f", key="other_credits")
        irc([
            "§901/§904 FTC (Foreign Tax Credit): Reduces U.S. tax on foreign-source income dollar-for-dollar, up to the U.S. tax on that income.",
            "<b>§904 Basket system:</b> FTC separated by income type — General basket, Passive basket, Foreign Branch basket, NCTI (Net CFC Tested Income) basket."
            "<br><span style='color:#C53030'>Carryback 1 year, carryforward 10 years. Exception: NCTI basket has <b>no carryover</b> (use it or lose it).</span>",
            "<span style='color:#C53030'>FTC cannot offset BEAT (Base Erosion Anti-Abuse Tax, §59A) liability.</span>",
        ])

        st.markdown("## CAMT — §55 / Form 4626")
        c1, c2 = st.columns(2)
        c1.number_input(L("—", "Adjusted Financial Statement Income (AFSI) — current year"), min_value=0.0, step=100_000.0, format="%.2f", key="afsi")
        c2.number_input(L("—", "3-Year Average AFSI — threshold test"), min_value=0.0, step=100_000.0, format="%.2f", key="avg_afsi_3yr")
        irc([
            "§55 CAMT (Corporate Alternative Minimum Tax): 15% × AFSI (Adjusted Financial Statement Income), reported on Form 4626.",
            "<span style='color:#C53030'><b>Threshold:</b> Applies only to corporations with 3-yr average AFSI &gt; $1 billion.</span>",
            "<b>AFSI</b> = GAAP net income adjusted for: (1) tax depreciation replaces book depreciation; (2) §168(k) bonus depreciation reduces AFSI; (3) equity method income replaced by NCTI inclusion.",
            "<span style='color:#C53030'><b>CAMT formula:</b> max(0, tentative minimum tax − regular tax after credits). Corporation pays only the excess above regular tax.</span>",
        ])

        st.markdown("## BEAT — §59A / Form 8991")
        c1, c2 = st.columns(2)
        c1.number_input(L("—", "3-Year Avg Gross Receipts — threshold test (must exceed $500M)"), min_value=0.0, step=100_000.0, format="%.2f", key="avg_gross_receipts_3yr")
        c2.number_input(L("—", "Base Erosion Payments to Foreign Related Parties"), min_value=0.0, step=10_000.0, format="%.2f", key="base_erosion_payments")
        c1.number_input(L("—", "Modified Taxable Income — add back base erosion deductions"), min_value=0.0, step=10_000.0, format="%.2f", key="modified_ti")
        irc([
            "§59A BEAT (Base Erosion Anti-Abuse Tax): Minimum tax on deductible payments made to foreign related parties, reported on Form 8991.",
            "Rate: 10% (2019–2025), 12.5% (2026+).",
            "Two-part threshold — BOTH must be met: (1) 3-yr avg gross receipts > $500M AND (2) base erosion payments > 3% of total deductions.",
            "Base erosion payments: deductible payments to foreign related parties — interest, royalties, management fees, rents. COGS excluded.",
            "BEAT = max(0, modified taxable income × rate − regular tax after credits). FTC cannot reduce BEAT.",
        ])

# ─────────────────────────────────────────────────────────────────────────────
# ESTIMATED TAX & SAFE HARBOR
# ─────────────────────────────────────────────────────────────────────────────
elif section == "📅 Estimated Tax & Safe Harbor":
    st.title("Estimated Tax & Safe Harbor")

    st.markdown("## Safe Harbor Rules")
    prior_tax = st.number_input(L("—", "Prior Year Total Tax Liability"), min_value=0.0, step=1_000.0, format="%.2f", key="prior_year_tax")
    large_corp = st.checkbox("Large Corporation (taxable income > $1M in any of prior 3 years)", key="large_corp")

    if large_corp:
        st.markdown('<div class="safe-harbor">⚠️ <strong>Large Corporation Rule:</strong> Safe harbor requires paying 100% of <em>current year</em> tax liability. Prior year tax may only be used for Q1. §6655(d)(2).</div>', unsafe_allow_html=True)
    else:
        sh_each = prior_tax / 4 if prior_tax > 0 else 0
        st.markdown(f'<div class="safe-harbor">✅ <strong>Safe Harbor:</strong> Pay the <em>lesser</em> of (a) 100% of prior year tax = <strong>${prior_tax:,.0f}</strong> or (b) 100% of current year tax — in 4 equal installments of <strong>${sh_each:,.0f}</strong> each. No underpayment penalty if met. §6655(d)(1).</div>', unsafe_allow_html=True)

    irc([
        "§6655: Corporations must make estimated tax payments by 4/15, 6/15, 9/15, 12/15 of the tax year.",
        "Underpayment penalty = federal short-term rate + 3% (applied to the shortfall per day).",
        "Safe harbor: pay the lesser of (a) 100% of prior year tax or (b) 100% of current year tax, in 4 equal installments.",
        "Large corp (taxable income > $1M in any of 3 prior years): prior year safe harbor only applies to Q1; Q2–Q4 must be based on current year.",
        "Alternative methods: annualized income installment (for uneven income) or adjusted seasonal installment method.",
    ])

    st.markdown("## Installment Payments")
    c1, c2, c3, c4 = st.columns(4)
    c1.number_input(L("—", "Q1 Payment — due April 15"), min_value=0.0, step=1_000.0, format="%.2f", key="q1")
    c2.number_input(L("—", "Q2 Payment — due June 15"), min_value=0.0, step=1_000.0, format="%.2f", key="q2")
    c3.number_input(L("—", "Q3 Payment — due September 15"), min_value=0.0, step=1_000.0, format="%.2f", key="q3")
    c4.number_input(L("—", "Q4 Payment — due December 15"), min_value=0.0, step=1_000.0, format="%.2f", key="q4")
    st.number_input(L("—", "Prior Year Overpayment Applied to Current Year"), min_value=0.0, step=1_000.0, format="%.2f", key="prior_overpayment")

    total_paid = sum([st.session_state.q1, st.session_state.q2,
                      st.session_state.q3, st.session_state.q4,
                      st.session_state.prior_overpayment])
    st.metric("Total Payments to Date", f"${total_paid:,.0f}")

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE M-1
# ─────────────────────────────────────────────────────────────────────────────
elif section == "📚 Schedule M-1":
    st.title("Schedule M-1 — Book-Tax Reconciliation")
    st.caption("Required for corporations with total assets < $10M. Reconciles net income per books to Form 1120 line 28 — taxable income *before* the NOL deduction and special deductions.")

    tab_law, tab_calc = st.tabs(["📖 Law & Concepts", "🧮 Calculator"])

    with tab_law:
        irc([
            "<b>What is Schedule M-1?</b> Filed by C corporations with total assets <b>under $10 million</b>. Reconciles net income per books (GAAP) to the return, because book income and taxable income differ due to permanent and temporary differences."
            "<br><span style='color:#C53030'><b>Line 10 must equal Form 1120 line 28</b> — taxable income <i>before</i> the NOL deduction (line 29a) and special deductions (line 29b). M-1 does <b>not</b> reconcile to final taxable income at line 30.</span>"
            "<br>Consequence: the DRD (Dividends Received Deduction) and the §250 deduction are <b>never</b> M-1 adjustments. They are not book-tax differences at all — they are statutory deductions taken below line 28.",
            "<b>Permanent differences</b> — items that are recognized for book but never for tax (or vice versa). They never reverse. Examples: 50% meals disallowance, tax-exempt interest income, non-deductible fines and penalties, dividends received deduction.",
            "<b>Temporary differences</b> — timing differences that reverse over time. Most common: MACRS (Modified Accelerated Cost Recovery System) accelerated depreciation (tax) vs. straight-line (book); deferred revenue recognized for tax when received but for book when earned.",
            "<b>M-1 formula:</b>"
            "<br>&nbsp;&nbsp;Start with <b>net income per books</b>"
            "<br>&nbsp;&nbsp;+ Items expensed on books but <b>not deductible</b> on return (e.g., fines, 50% meals disallowance)"
            "<br>&nbsp;&nbsp;+ Income on return <b>not on books</b> (e.g., prepaid income taxable when received)"
            "<br>&nbsp;&nbsp;− Income on books <b>not on return</b> (e.g., tax-exempt interest)"
            "<br>&nbsp;&nbsp;− Deductions on return <b>not on books</b> (e.g., excess MACRS over book depreciation)"
            "<br>&nbsp;&nbsp;= <b>Line 10 — equals Form 1120 line 28</b>"
            "<br><span style='color:#C53030'>Not final taxable income. Line 30 is reached only after subtracting the NOL "
            "deduction (29a) and the special deductions (29b), neither of which is an M-1 item.</span>",
        ])
        st.markdown("""
| Difference Type | Definition | Example |
|---|---|---|
| Permanent | Never reverses | Fines, tax-exempt interest |
| Temporary | Timing only — reverses over time | MACRS vs. straight-line depreciation |
""")

        st.markdown("### Common Permanent Differences")
        st.markdown("""
| Item | Treatment |
|---|---|
| Meals & Entertainment (50%) | Add back 50% — permanently disallowed |
| Fines & Penalties | Add back — §162(f) |
| §162(m) excess compensation | Add back — public corps only |
| Lobbying expense | Add back — §162(e) |
| Tax-exempt interest income | Subtract — not taxable |
| Life insurance proceeds | Subtract — §101 |
""")

        st.markdown("### Common Temporary Differences")
        st.markdown("""
| Item | Direction | Reverses When |
|---|---|---|
| Tax depreciation > book | Subtract from book income | Asset fully depreciated |
| Bad debt reserve (book) vs. specific charge-off (tax) | Add back reserve | Debt actually written off |
| §163(j) interest carryforward | Add back | Deducted in future year |
| Warranty reserve (book accrual) | Add back | Warranty costs incurred |
| Deferred revenue (book) vs. §451(c) advance payment | Subtract | Earned in future year |
""")

    with tab_calc:
        st.markdown(
            "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
            "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
            "<b>⚠️ Schedule M-1 line 10 ties to Form 1120 line 28 — not to final taxable income.</b><br>"
            "M-1 stops <i>above</i> the NOL deduction (line 29a) and the special deductions (line 29b). "
            "The DRD and the §250 deduction are therefore <b>not</b> M-1 adjustments — they sit below M-1's endpoint. "
            "Do not compute tax from line 10."
            "</div>", unsafe_allow_html=True)

        st.markdown(
            "<div style='background:#EBF4FF;border-left:4px solid #2C5282;padding:10px 14px;margin:8px 0;"
            "color:#2C5282;-webkit-text-fill-color:#2C5282;'>"
            "Every line below is <b>derived from the Book / AFS and disallowance columns you already filled in</b>. "
            "The only figure the ledger cannot give the return is the federal tax accrual, so that is the one input. "
            "Use the \u201cother\u201d boxes for anything this app does not model."
            "</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.number_input("Line 2 — Federal income tax expense per books ($)",
                            min_value=0.0, step=1000.0, key="m1_fed_tax",
                            help="§275 — never deductible, so it is always an add-back.")
        with c2:
            st.number_input("Override — net income (loss) per books ($)",
                            step=1000.0, key="m1_book_override",
                            help="Leave at 0 to use the derived figure.")

        _bk = M1["book"]
        st.markdown(
            f"<div style='background:#E7F6EC;border-left:4px solid #1E7A3C;padding:10px 14px;margin:4px 0 12px 0;"
            f"color:#14532D;-webkit-text-fill-color:#14532D;'>"
            f"<b>Line 1 — net income (loss) per books: ${M1['l1']:,.0f}</b>"
            f"{' (override)' if M1['override'] else ' — derived'}<br>"
            f"Book revenue ${_bk['revenue']:,.0f} \u2212 book expenses ${_bk['expenses']:,.0f} "
            f"\u2212 federal tax per books ${M1['fed_tax']:,.0f}"
            f"</div>", unsafe_allow_html=True)

        def _breakdown(title, items):
            rows = [(n, v) for n, v in items if abs(v) >= 0.5]
            with st.expander(f"{title} — {len(rows)} item(s)"):
                if not rows:
                    st.caption("Nothing on this line yet.")
                else:
                    st.markdown(
                        "<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
                        + "".join(f"<tr><td style='padding:5px 8px'>{n}</td>"
                                  f"<td style='padding:5px 8px;text-align:right'>{v:,.0f}</td></tr>"
                                  for n, v in rows)
                        + "</table></div>", unsafe_allow_html=True)

        _breakdown("Line 4 — income on the return not recorded on books", M1["l4_items"])
        _breakdown("Line 5 — expenses on books not deducted on this return", M1["l5_items"])
        _breakdown("Line 7 — income on books not included on this return", M1["l7_items"])
        _breakdown("Line 8 — deductions on this return not charged against book income", M1["l8_items"])

        mo1, mo2, mo3, mo4 = st.columns(4)
        mo1.number_input("Line 4 other ($)", step=1000.0, key="m1_l4_other")
        mo2.number_input("Line 5 other ($)", step=1000.0, key="m1_l5_other")
        mo3.number_input("Line 7 other ($)", step=1000.0, key="m1_l7_other")
        mo4.number_input("Line 8 other ($)", step=1000.0, key="m1_l8_other")

        book_income, fed_tax_books, cap_loss_excess = M1["l1"], M1["fed_tax"], M1["l3"]
        m1_l4, m1_l5, m1_l6 = M1["l4"], M1["l5"], M1["l6"]
        m1_l7, m1_l8, m1_l9, m1_l10 = M1["l7"], M1["l8"], M1["l9"], M1["l10"]

        st.divider()
        st.markdown(f"""
| Line | Item | Amount |
|---|---|---|
| 1 | Net income (loss) per books | ${book_income:,.0f} |
| 2 | Federal income tax per books | ${fed_tax_books:,.0f} |
| 3 | Excess of capital losses over capital gains | ${cap_loss_excess:,.0f} |
| 4 | Income subject to tax not recorded on books | ${m1_l4:,.0f} |
| 5 | Expenses on books not deducted on this return | ${m1_l5:,.0f} |
| **6** | **Add lines 1 through 5** | **${m1_l6:,.0f}** |
| 7 | Income on books not included on this return | ${m1_l7:,.0f} |
| 8 | Deductions on this return not charged against book income | ${m1_l8:,.0f} |
| **9** | **Add lines 7 and 8** | **${m1_l9:,.0f}** |
| **10** | **Income (loss) — line 6 less line 9** | **${m1_l10:,.0f}** |
""")

        _l28 = SC["line28"]
        _diff = m1_l10 - _l28
        t1, t2, t3 = st.columns(3)
        t1.metric("M-1 line 10", f"${m1_l10:,.0f}")
        t2.metric("Form 1120 line 28", f"${_l28:,.0f}")
        t3.metric("Difference", f"${_diff:,.0f}", "must be zero" if abs(_diff) >= 1 else "reconciled")

        if abs(_diff) < 1:
            st.success("Reconciled — M-1 line 10 equals Form 1120 line 28.")
        else:
            st.error(
                f"**Out of balance by \\${_diff:,.0f}.** M-1 line 10 must equal Form 1120 line 28. "
                f"Either a book-tax difference is missing above, or the income/deduction pages do not yet reflect "
                f"the same fact pattern as the book income entered here.")

        st.markdown("#### Below M-1 — where the return continues")
        _l29b_m1 = SC["line24"]
        _l29a_m1 = NOL["line29a"]
        _l30_m1 = max(0.0, _l28 - _l29a_m1 - _l29b_m1)
        st.markdown(f"""
| Line | Item | Amount |
|---|---|---|
| 28 | Taxable income before NOL and special deductions — **M-1 stops here** | ${_l28:,.0f} |
| 29a | NOL deduction | (${_l29a_m1:,.0f}) |
| 29b | Special deductions — DRD + §250 (Schedule C line 24) | (${_l29b_m1:,.0f}) |
| **30** | **Taxable income** | **${_l30_m1:,.0f}** |
| — | Federal income tax @ 21% | ${_l30_m1 * 0.21:,.0f} |
""")
        st.info("The DRD and §250 deduction never appear on Schedule M-1. They are neither permanent nor temporary "
                "book-tax differences — they are statutory deductions taken after line 28.")

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE M-3
# ─────────────────────────────────────────────────────────────────────────────
elif section == "📊 Schedule M-3":
    st.title("Schedule M-3 — Net Income Reconciliation")
    st.caption("Required for corporations with total assets ≥ $10M.")

    tab_law, tab_calc = st.tabs(["📖 Law & Concepts", "🧮 Calculator"])

    with tab_law:
        irc([
            "<b>Who must file M-3?</b> C corporations with total assets of <b>$10 million or more</b> at year-end must file Schedule M-3 instead of M-1. Corporations with assets between $10M–$50M may use an abbreviated version.",
            "<b>Structure:</b> M-3 has three parts. Part I reconciles worldwide consolidated net income to the income of the US tax group. Part II details income/loss items. Part III does the same for expense/deduction items, then totals into Part II."
            "<br><span style='color:#C53030'><b>Part II line 30, column (d) must equal Form 1120 line 28</b> — the same endpoint as M-1 line 10, i.e. before the NOL deduction and special deductions.</span>"
            "<br>So the DRD and §250 deduction appear nowhere in Part II or Part III.",
            "<b>Three-column format:</b> For every line item — (1) book amount, (2) temporary difference, (3) permanent difference. Tax amount = book ± temp ± perm. Allows the IRS to pinpoint exactly where book and tax diverge.",
            "<b>Key difference from M-1:</b> M-1 is a single net reconciliation. M-3 requires line-by-line disclosure of every significant book-tax difference categorized as permanent or temporary.",
            "<b>Deferred Tax:</b> Temporary differences create DTAs or DTLs on the balance sheet."
            "<br><span style='color:#C53030'>Favorable temp diff (e.g. accelerated depreciation now) → DTL (Deferred Tax Liability — pay more tax later).</span>"
            "<br><span style='color:#C53030'>Unfavorable temp diff (e.g. warranty reserve on books, not yet deductible for tax) → DTA (Deferred Tax Asset — pay less tax later).</span>",
        ])
        st.markdown("""
| Column | Meaning |
|---|---|
| Book amount | Per audited financial statements (GAAP) |
| Temporary difference | Timing — will reverse in future years |
| Permanent difference | Never reverses (e.g. fines, tax-exempt income) |
| Tax amount | Book ± temp ± perm |
""")

        st.markdown("### Part I — Financial Information")
        irc([
            "Part I: Start from worldwide consolidated FS (Financial Statement) income.",
            "Adjustments: eliminate non-US operations, minority interest (NCI — Noncontrolling Interest), and intercompany items.",
            "Result: income of the US consolidated tax group — the starting point for Parts II and III.",
        ])

        st.markdown("### Part II — Temporary Differences")
        st.markdown("""
| Category | Examples |
|---|---|
| Income included on return, not on books | Advance payments (§451(c)), prepaid income |
| Income on books, not on return | Tax-exempt interest, life insurance proceeds |
| Expense on return, not on books | Accelerated tax depreciation, §179, bonus dep. |
| Expense on books, not on return | Book depreciation > tax, warranty reserve, bad debt reserve |
""")

        st.markdown("### Part III — Permanent Differences")
        st.markdown("""
| Category | Examples |
|---|---|
| Income on books not on return (permanent) | Municipal bond interest, life insurance proceeds |
| Non-deductible expenses | Fines/penalties, §162(m) excess, 50% meals, lobbying |
| DRD | Reduces book dividend income for tax |
| §199A / §250 deductions | GILTI deduction, FDII deduction |
""")

    with tab_calc:
        total_assets = st.number_input("Total Assets at Year-End ($)", min_value=0.0, step=100_000.0, format="%.2f", key="total_assets")
        if total_assets < 10_000_000:
            st.markdown('<div class="warn-box">⚠️ Schedule M-3 is required only when total assets ≥ $10,000,000. Current total assets below threshold — M-1 is sufficient.</div>', unsafe_allow_html=True)
        else:
            st.success("✅ Total assets ≥ \\$10M — Schedule M-3 required.")
            st.markdown(
                "<div style='background:#EBF4FF;border-left:4px solid #2C5282;padding:10px 14px;margin:8px 0;"
                "color:#2C5282;-webkit-text-fill-color:#2C5282;'>"
                "Every difference below is <b>derived from the pages you have already filled in</b> — "
                "Form 1125-A, Schedule C, Schedule D, Form 4797 and the Deductions page. "
                "Column (a) is the book amount, column (d) is the tax amount, and "
                "<b>(a) + (b) + (c) = (d)</b> on every line. Only the two \u201cother\u201d lines are typed by hand."
                "</div>", unsafe_allow_html=True)

            bc1, bc2 = st.columns(2)
            with bc1:
                st.number_input("Federal income tax expense per books ($)",
                                min_value=0.0, step=1000.0, key="m3_fed_tax",
                                help="§275 — never deductible. Drives Part III line 1.")
            with bc2:
                st.number_input("Override — net income per income statement ($)",
                                step=1000.0, key="m3_book_override",
                                help="Leave at 0 to use the figure derived from the Book / AFS columns.")

            _bk = M3["book"]
            m3_fed_tax, book_income_m3 = M3["fed_tax"], M3["l1"]
            st.markdown(
                f"<div style='background:#E7F6EC;border-left:4px solid #1E7A3C;padding:10px 14px;margin:4px 0 12px 0;"
                f"color:#14532D;-webkit-text-fill-color:#14532D;'>"
                f"<b>Part I line 11 — net income per books: ${book_income_m3:,.0f}</b>"
                f"{' (override)' if M3['override'] else ' — derived from the Book / AFS columns you already filled in'}<br>"
                f"Book revenue ${_bk['revenue']:,.0f} − book expenses ${_bk['expenses']:,.0f} "
                f"− federal tax per books ${m3_fed_tax:,.0f}"
                f"</div>", unsafe_allow_html=True)

            def _n(v):
                return 0.0 if abs(v) < 0.5 else v      # kill "-0" from float noise

            part2, part3, _o38 = M3["part2"], M3["part3"], M3["o38"]

            def _tbl(rows, title):
                st.markdown(f"#### {title}")
                body = "".join(
                    f"<tr><td style='padding:5px 8px'>{r['line']}</td>"
                    f"<td style='padding:5px 8px'>{r['label']}</td>"
                    f"<td style='padding:5px 8px;text-align:right'>{_n(r['a']):,.0f}</td>"
                    f"<td style='padding:5px 8px;text-align:right'>{_n(r['b']):,.0f}</td>"
                    f"<td style='padding:5px 8px;text-align:right'>{_n(r['c']):,.0f}</td>"
                    f"<td style='padding:5px 8px;text-align:right;font-weight:600'>{_n(r['d']):,.0f}</td></tr>"
                    for r in rows)
                st.markdown(
                    "<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
                    "<tr style='background:#EBF4FF;color:#1B3A6B'>"
                    "<th style='padding:6px 8px;text-align:left'>Line</th>"
                    "<th style='padding:6px 8px;text-align:left'>Item</th>"
                    "<th style='padding:6px 8px;text-align:right'>(a) Per income statement</th>"
                    "<th style='padding:6px 8px;text-align:right'>(b) Temporary difference</th>"
                    "<th style='padding:6px 8px;text-align:right'>(c) Permanent difference</th>"
                    "<th style='padding:6px 8px;text-align:right'>(d) Per tax return</th></tr>"
                    + body + "</table></div>", unsafe_allow_html=True)
                with st.expander("Why each difference is temporary or permanent"):
                    for r in rows:
                        if r["note"]:
                            st.markdown(f"- **Line {r['line']} — {r['label']}:** {r['note']}")

            _tbl(part2, "Part II — Income (loss) items")

            oc1, oc2 = st.columns(2)
            oc1.number_input("Part II line 25 — other temporary ($)", step=1000.0, key="m3_other_ii_temp")
            oc2.number_input("Part II line 25 — other permanent ($)", step=1000.0, key="m3_other_ii_perm")

            _tbl(part3, "Part III — Expense/deduction items")

            with st.expander("Part III line 38 breakdown"):
                st.markdown(
                    "<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
                    "<tr style='background:#EBF4FF;color:#1B3A6B'>"
                    "<th style='padding:6px 8px;text-align:left'>Item</th>"
                    "<th style='padding:6px 8px;text-align:right'>(a) Book</th>"
                    "<th style='padding:6px 8px;text-align:right'>(d) Tax</th>"
                    "<th style='padding:6px 8px;text-align:right'>of which permanent</th></tr>"
                    + "".join(
                        f"<tr><td style='padding:5px 8px'>{n}</td>"
                        f"<td style='padding:5px 8px;text-align:right'>{_n(a):,.0f}</td>"
                        f"<td style='padding:5px 8px;text-align:right'>{_n(d):,.0f}</td>"
                        f"<td style='padding:5px 8px;text-align:right'>{_n(c):,.0f}</td></tr>"
                        for n, a, d, c in _o38)
                    + "</table></div>", unsafe_allow_html=True)

            oc3, oc4 = st.columns(2)
            oc3.number_input("Part III line 38 — other temporary ($)", step=1000.0, key="m3_other_iii_temp")
            oc4.number_input("Part III line 38 — other permanent ($)", step=1000.0, key="m3_other_iii_perm")

            total_temp, total_perm, m3_part2_l30 = M3["temp"], M3["perm"], M3["l30"]

            st.divider()
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Total temporary differences", f"\\${_n(total_temp):+,.0f}")
            mc2.metric("Total permanent differences", f"\\${_n(total_perm):+,.0f}")
            mc3.metric("Part II line 30 col (d)", f"\\${m3_part2_l30:,.0f}",
                       delta=f"{m3_part2_l30 - book_income_m3:+,.0f} vs book")

            _l28_m3 = SC["line28"]
            _diff_m3 = m3_part2_l30 - _l28_m3
            u1, u2, u3 = st.columns(3)
            u1.metric("M-3 Part II line 30 col (d)", f"\\${m3_part2_l30:,.0f}")
            u2.metric("Form 1120 line 28", f"\\${_l28_m3:,.0f}")
            u3.metric("Difference", f"\\${_diff_m3:,.0f}",
                      "must be zero" if abs(_diff_m3) >= 1 else "reconciled")

            if abs(_diff_m3) < 1:
                st.success("Reconciled — M-3 Part II line 30 column (d) equals Form 1120 line 28.")
            else:
                st.error(f"**Out of balance by \\${_diff_m3:,.0f}.** Part II line 30 column (d) must equal "
                         f"Form 1120 line 28.")
                st.caption(f"Book income of \\${_l28_m3 - total_temp - total_perm:,.0f} would tie exactly — "
                           f"if your books really do show \\${book_income_m3:,.0f}, the gap is an item the "
                           f"return does not yet model. Put it on line 25 or line 38.")

            st.markdown("#### Below M-3 — where the return continues")
            _l29b_m3 = SC["line24"]
            _l29a_m3 = NOL["line29a"]
            _l30_m3 = max(0.0, _l28_m3 - _l29a_m3 - _l29b_m3)
            st.markdown(f"""
| Line | Item | Amount |
|---|---|---|
| 28 | Taxable income before NOL and special deductions — **M-3 stops here** | ${_l28_m3:,.0f} |
| 29a | NOL deduction | (${_l29a_m3:,.0f}) |
| 29b | Special deductions — DRD + §250 (Schedule C line 24) | (${_l29b_m3:,.0f}) |
| **30** | **Taxable income** | **${_l30_m3:,.0f}** |
| — | Federal income tax @ 21% | ${_l30_m3 * 0.21:,.0f} |
""")
            st.info("Like M-1, Schedule M-3 reconciles only down to line 28. The DRD and §250 deduction are not "
                    "book-tax differences and never appear in Part II or Part III — they are statutory deductions "
                    "taken below line 28.")

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
elif section == "📈 Results Summary":
    st.title("Results Summary")

    s = st.session_state

    st.markdown("## ✅ Return Integrity Check")
    st.caption("Book income, the book-tax differences and taxable income must all carry "
               "figures, and the reconciliation schedule must land on Form 1120 line 28. "
               "Anything else means the return does not hang together.")
    render_checks()
    st.markdown("---")

    # Same result the shared pass computed — Schedule J reads the identical object.
    inputs = build_1120_inputs(SC["line23"], SC["line24"], NOL["post2017_pool"], NOL["pre2018_pool"])
    r = R1120

    # KPI Row
    gross_rev = inputs["gross_revenue"]
    fed_tax = r["tax"]["total_federal_tax"]
    bal = r["payments"]["balance_due"]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Gross Revenue", f"${gross_rev:,.0f}")
    k2.metric("Taxable Income", f"${r['taxable_income']['taxable_income']:,.0f}")
    k3.metric("Federal Tax", f"${fed_tax:,.0f}",
              f"{r['tax']['effective_rate']:.1%} effective rate")
    k4.metric("Total Credits", f"(${r['tax']['credits']['total_credits']:,.0f})")
    color = "normal" if bal <= 0 else "inverse"
    k5.metric("Balance Due / (Refund)", f"${bal:,.0f}", delta_color=color)

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("### 📥 Income")
        inc = r["income"]
        st.markdown(f"""
| | |
|---|---:|
| Gross Revenue (net of returns) | ${gross_rev:,.0f} |
| Net Capital Gain | ${inc['capital_gains']['net_capital_gain']:,.0f} |
| Other Income | ${inc['other_income']:,.0f} |
| **Total Income** | **${inc['total_income']:,.0f}** |
""")
        if inc['capital_gains']['capital_loss_carryforward'] > 0:
            st.caption(f"⚠️ Capital loss carryforward: ${inc['capital_gains']['capital_loss_carryforward']:,.0f}")

        st.markdown("### 📤 Deductions")
        ded = r["deductions"]
        st.markdown(f"""
| | |
|---|---:|
| COGS (after §263A) | ${ded['cogs']:,.0f} |
| §263A UNICAP Adjustment | ${ded['unicap_adjustment']:,.0f} |
| Operating Expenses | ${ded['operating_expenses']:,.0f} |
| Officer Comp (deductible) | ${ded['officer_compensation']:,.0f} |
| §162(m) Disallowed | ${ded['section_162m_disallowed']:,.0f} |
| Depreciation | ${ded['depreciation']:,.0f} |
| Interest (§163(j) limited) | ${ded['interest']['deductible']:,.0f} |
| §163(j) Carryforward | ${ded['interest']['excess_carryforward']:,.0f} |
| Charitable (limited to 10%) | ${ded['charitable']['deductible']:,.0f} |
| Charitable Carryforward | ${ded['charitable']['carryforward_5yr']:,.0f} |
| DRD ({ded['drd']['label']}) | ${ded['drd']['deduction']:,.0f} |
| Bad Debt | ${ded['bad_debt']:,.0f} |
| **Total Deductions** | **${ded['total_deductions']:,.0f}** |
""")

        if ded.get("cost_seg_detail"):
            cs = ded["cost_seg_detail"]
            st.markdown("**Cost Segregation Breakdown:**")
            for k, v in cs["splits"].items():
                st.markdown(f"- {k}: ${v['amount']:,.0f} → dep. ${v['depreciation']:,.0f}")
            st.success(f"💡 Tax savings vs. straight 39-yr: **\\${cs['tax_savings_vs_no_seg']:,.0f}**")

    with col_r:
        st.markdown("### 🧮 Tax Computation")
        tx = r["tax"]
        cr = tx["credits"]
        ti = r["taxable_income"]
        st.markdown(f"""
| | |
|---|---:|
| Income Before NOL | ${ti['before_nol']:,.0f} |
| NOL Deduction (§172, by vintage) | (${ti['nol']['nol_used']:,.0f}) |
| NOL Remaining Carryforward | ${ti['nol']['remaining_carryforward']:,.0f} |
| **Taxable Income** | **${ti['taxable_income']:,.0f}** |
| Income Tax @ 21% | ${tx['regular_tax']:,.0f} |
| §41 R&D Credit — ASC | (${cr['rd_asc']['credit']:,.0f}) |
| §41 R&D Credit — Regular | (${cr['rd_regular']['credit']:,.0f}) |
| R&D Credit Applied (higher) | (${cr['rd_credit_used']:,.0f}) |
| Foreign Tax Credit | (${cr['foreign_tax_credit']:,.0f}) |
| Other Credits | (${inputs['other_credits']:,.0f}) |
| Tax After Credits | ${tx['tax_after_credits']:,.0f} |
| CAMT | ${tx['camt']['camt']:,.0f} |
| BEAT | ${tx['beat']['beat']:,.0f} |
| **Total Federal Tax** | **${tx['total_federal_tax']:,.0f}** |
""")
        if not tx["camt"]["applies"]:
            st.caption(f"CAMT: {tx['camt']['note']}")
        if not tx["beat"]["applies"]:
            st.caption(f"BEAT: {tx['beat']['note']}")

        st.markdown("### 📅 Payments")
        pay = r["payments"]
        sh_amount = s.prior_year_tax
        underpaid = max(0, fed_tax - sh_amount)
        st.markdown(f"""
| | |
|---|---:|
| Q1 (4/15) | ${s.q1:,.0f} |
| Q2 (6/15) | ${s.q2:,.0f} |
| Q3 (9/15) | ${s.q3:,.0f} |
| Q4 (12/15) | ${s.q4:,.0f} |
| Prior Year Overpayment | ${s.prior_overpayment:,.0f} |
| **Total Payments** | **${pay['total_payments']:,.0f}** |
| Total Federal Tax | ${fed_tax:,.0f} |
| **Balance Due / (Refund)** | **${bal:,.0f}** |
""")
        if bal > 0:
            st.markdown(f'<div class="warn-box">⚠️ Balance due ${bal:,.0f}. Safe harbor based on prior year: ${sh_amount:,.0f} / 4 = ${sh_amount/4:,.0f} per quarter.</div>', unsafe_allow_html=True)
        else:
            st.success(f"✅ Overpayment / Refund: \\${abs(bal):,.0f}")

        st.markdown("### 📚 Schedule M-1")
        m1 = r["m1_reconciliation"]
        perm = m1["permanent_differences"]
        temp = m1["temporary_differences"]
        st.markdown(f"""
| | |
|---|---:|
| Net Income per Books | ${m1['book_income']:,.0f} |
| + Meals 50% disallowed | ${perm['meals_50pct_disallowed']:,.0f} |
| + Fines & Penalties (§162(f)) | ${perm['fines_penalties']:,.0f} |
| + §162(m) disallowed compensation | ${perm['162m_disallowed']:,.0f} |
| + Lobbying (§162(e)) | ${perm['lobbying']:,.0f} |
| + Bribes & Kickbacks (§162(c)) | ${s.bribes_book:,.0f} |
| + Political Contributions (§276) | ${s.political_book:,.0f} |
| + Key Employee Insurance (§264) | ${s.key_ins_book:,.0f} |
| ± Depreciation (book vs tax) | ${temp['depreciation_book_vs_tax']:,.0f} |
| ± Bad Debt (reserve vs charge-off) | ${temp['bad_debt_reserve']:,.0f} |
| ± §163(j) interest carryforward | ${temp['interest_163j_carryforward']:,.0f} |
| **Computed Taxable Income** | **${m1['computed_taxable_income']:,.0f}** |
""")

    # ── Year-end rollforward ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 🔄 Close the Year and Roll Forward")

    _done = st.session_state.pop("_roll_done", None)
    if _done:
        st.success(_done)

    with st.expander("📖 How the annual cycle works — read this first"):
        st.markdown("""
**Run this once a year, after the current year's figures are final.**

##### The three steps

1. **Check the preview table below.** It lists exactly what will be written into next
   year's carryforward positions — capital loss carryover, non-recaptured §1231 losses,
   NOL, §163(j) interest, charitable excess, and the §6655 safe-harbour base. Sanity-check
   these before going further.
2. **Decide what happens to any overpayment.** If the year overpaid, a checkbox appears:
   tick it to credit the amount against next year's estimated tax (Form 1120 line 36),
   leave it clear to treat the overpayment as refunded.
3. **Tick the confirmation, then press the close button.** The button stays locked until
   the confirmation is ticked.

##### What closing the year does

| | |
|---|---|
| Writes | the carryforwards shown in the preview |
| Clears | every current-year amount — income, deductions, Schedule D, Form 4797, M-1 and M-3 entries, estimated tax payments |
| Keeps | ownership %, public-company status, depreciation method and life, CFC election, 3-year averages, and all carryforward balances |
| Advances | the tax year by one |
| Records | the year as closed, so it can never be closed twice |

##### Then save

Everything lives in the browser session. **Closing the browser loses it all**, including the
record of which years have been closed.

Use **💾 Save / Load** in the sidebar → *Save return as JSON* after each close. The filename
carries the year (`form1120_2026.json`), so saving after each close leaves a year-by-year
trail. Next session, *Load a saved return* picks up exactly where you left off.
""")

    _cy_roll = int(s.tax_year)
    _next_y = _cy_roll + 1

    _closed = st.session_state.get("_closed_years", [])
    _already_closed = _cy_roll in _closed

    if _already_closed:
        st.markdown(
            "<div style='background:#E7F6EC;border-left:5px solid #1E7A3C;padding:12px 16px;margin:8px 0;"
            "color:#14532D;-webkit-text-fill-color:#14532D;'>"
            f"<b>✅ {_cy_roll} is already closed.</b> Its carryforwards have been written and cannot be written again — "
            "running the close twice would double-count them.<br>"
            f"Closed years so far: {', '.join(str(y) for y in _closed)}."
            "</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#FDECEA;border-left:5px solid #C53030;padding:12px 16px;margin:8px 0;"
            "color:#7A1C1C;-webkit-text-fill-color:#7A1C1C;'>"
            "<b>⚠️ Carryforwards do NOT roll automatically.</b> Changing the Tax Year in the sidebar only re-labels the "
            "carryover tables — it moves no data.<br>Closing the year writes this year's results into the "
            f"<b>{_next_y}</b> carryforward positions, <b>clears every current-year amount</b>, and advances the tax year. "
            "It can only be run once per year."
            "</div>", unsafe_allow_html=True)

    _roll_cap_new = SD["net_loss"]
    _roll_cap_used = [(r["year"], r["used"]) for r in SD["cf_rows"] if r["used"] > 0]
    _roll_1231_new = abs(F4797["l7"]) if F4797["l7"] < 0 else 0.0
    _roll_1231_used = [(r["year"], r["used"]) for r in F4797["lb_rows"] if r.get("used", 0) > 0]
    _roll_nol = r["taxable_income"]["nol"]["remaining_carryforward"] + r["taxable_income"]["nol"]["new_nol_generated"]
    _roll_nol_used = [(v["year"], v["used"]) for v in NOL["rows"] if v.get("used", 0) > 0]
    _roll_nol_new = r["taxable_income"]["nol"]["new_nol_generated"]
    _roll_163j = r["deductions"]["interest"]["excess_carryforward"]
    _roll_char = r["deductions"]["charitable"]["carryforward_5yr"]
    _roll_total_tax = r["tax"]["total_federal_tax"]
    _roll_payments = sum(s.get(k, 0.0) for k in ("q1", "q2", "q3", "q4")) + s.get("prior_overpayment", 0.0)
    _roll_overpay = max(0.0, _roll_payments - _roll_total_tax)

    _credit_fwd = st.checkbox(
        f"Credit this year's overpayment of ${_roll_overpay:,.0f} to {_next_y} estimated tax "
        f"(Form 1120 line 36) instead of refunding it",
        key="roll_credit_overpay", disabled=_roll_overpay <= 0)
    _roll_overpay_credit = _roll_overpay if (_credit_fwd and _roll_overpay > 0) else 0.0

    st.markdown(f"""
<table style="width:100%;border-collapse:collapse;background:#f8f9fa;color:#1a1a2e;font-size:14px;">
<thead><tr style="background:#2D5A9E;color:#ffffff;">
<th style="padding:8px 12px;text-align:left;">Carryforward</th>
<th style="padding:8px 12px;text-align:left;">What will be written</th>
<th style="padding:8px 12px;text-align:right;">Amount</th>
</tr></thead>
<tbody>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">§1212(a) capital loss</td><td style="padding:8px 12px;">New {_cy_roll} loss row in the Schedule D carryover table</td><td style="padding:8px 12px;text-align:right;">${_roll_cap_new:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">§1212(a) amounts used</td><td style="padding:8px 12px;">Reduce the source years drawn on this year: {', '.join(f'{y} −${u:,.0f}' for y, u in _roll_cap_used) or '—'}</td><td style="padding:8px 12px;text-align:right;">${sum(u for _, u in _roll_cap_used):,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">§1231(c) new loss</td><td style="padding:8px 12px;">New {_cy_roll} non-recaptured §1231 loss row on Form 4797</td><td style="padding:8px 12px;text-align:right;">${_roll_1231_new:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">§1231(c) recaptured</td><td style="padding:8px 12px;">Add to the “already recaptured” column: {', '.join(f'{y} +${u:,.0f}' for y, u in _roll_1231_used) or '—'}</td><td style="padding:8px 12px;text-align:right;">${sum(u for _, u in _roll_1231_used):,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">NOL (§172) used</td><td style="padding:8px 12px;">Reduce the vintages drawn on this year: {', '.join(f'{y} −${u:,.0f}' for y, u in _roll_nol_used) or '—'}</td><td style="padding:8px 12px;text-align:right;">${sum(u for _, u in _roll_nol_used):,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">NOL (§172) new</td><td style="padding:8px 12px;">New {_cy_roll} vintage if this year ran a loss — no carryback, 80% limit, never expires</td><td style="padding:8px 12px;text-align:right;">${_roll_nol_new:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">§163(j) interest</td><td style="padding:8px 12px;">Disallowed business interest carried forward indefinitely</td><td style="padding:8px 12px;text-align:right;">${_roll_163j:,.0f}</td></tr>
<tr style="background:#eef2f7;border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Charitable (§170)</td><td style="padding:8px 12px;">Excess over the 10% limit — 5-year carryforward</td><td style="padding:8px 12px;text-align:right;">${_roll_char:,.0f}</td></tr>
<tr style="border-bottom:1px solid #dee2e6;"><td style="padding:8px 12px;">Prior year tax (§6655)</td><td style="padding:8px 12px;">This year's total tax becomes the {_next_y} estimated-tax safe harbour base</td><td style="padding:8px 12px;text-align:right;">${_roll_total_tax:,.0f}</td></tr>
<tr><td style="padding:8px 12px;">Overpayment credited</td><td style="padding:8px 12px;">Applied against {_next_y} estimated tax (Form 1120 line 36)</td><td style="padding:8px 12px;text-align:right;">${_roll_overpay_credit:,.0f}</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

    irc([
        "<b>What closing the year does:</b>"
        "<br>&nbsp;&nbsp;(1) writes the carryforwards above;"
        "<br>&nbsp;&nbsp;(2) <b>zeroes every current-year amount</b> — income, deductions, Schedule D and Form 4797 "
        "transactions, M-1 and M-3 entries, estimated tax payments;"
        "<br>&nbsp;&nbsp;(3) advances the Tax Year;"
        "<br>&nbsp;&nbsp;(4) records the year as closed so it cannot be run again."
        "<br><span style='color:#C53030'>Standing settings are kept: ownership %, public-company status, depreciation "
        "method and asset life, CFC election, 3-year averages, and every carryforward balance.</span>",

        "<b>Why this is a button and not automatic:</b> a silent rollforward would overwrite figures you may have entered by "
        "hand, and an error would be almost impossible to spot after the fact."
        "<br>Making it explicit means the numbers only move when you say so — and the closed-year record means pressing it "
        "twice is impossible rather than merely discouraged.",
    ])

    _roll_confirm = st.checkbox(f"I have reviewed the {_cy_roll} results above and want to close the year",
                               key="roll_confirm", disabled=_already_closed)
    if st.button(f"🔄 Close {_cy_roll} and roll forward to {_next_y}",
                 key="roll_forward_btn", disabled=(not _roll_confirm) or _already_closed):
        st.session_state["_roll_payload"] = {
            "cy": _cy_roll, "next_y": _next_y,
            "cap_new": _roll_cap_new, "cap_used": _roll_cap_used,
            "s1231_new": _roll_1231_new, "s1231_used": _roll_1231_used,
            "nol": _roll_nol, "nol_used": _roll_nol_used, "nol_new": _roll_nol_new,
            "i163j": _roll_163j, "char": _roll_char,
            "total_tax": _roll_total_tax, "overpay_credit": _roll_overpay_credit,
        }
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TOPIC — CORPORATE FORMATION §351
# ─────────────────────────────────────────────────────────────────────────────
elif topic == "📐 Corporate Formation — §351":
    st.title("Corporate Formation — §351")
    st.markdown("Analysis of non-recognition treatment when property is transferred to a corporation in exchange for stock.")

    with st.expander("📚 §351 Law & Concepts — Property, Boot, Control, Basis, Holding Period"):
        st.markdown("### Tax Consequences — Corporation (§1032)")
        irc([
            "<b>§1032(a) — Corporation side:</b> <b>No gain or loss</b> is recognized by the corporation on the receipt of money or other property in exchange for its own stock. This applies regardless of whether §351 is satisfied — the corporation <i>never</i> recognizes gain or loss on a stock issuance.",
        ])

        st.markdown("### Tax Consequences — Shareholder (§351)")
        irc([
            "<b>§351(a) — Shareholder non-recognition:</b> No gain or loss is recognized if (1) <b>property</b> is transferred to a corporation, (2) <i>solely</i> in exchange for <b>stock</b>, and (3) immediately after the exchange the transferors are in <b>control</b> of the corporation.",
            "<b>If §351 is NOT met</b> (e.g., control test fails, services transferred instead of property): the shareholder <b>recognizes the full realized gain</b>. Character depends on the asset: ordinary for inventory/recapture, capital for capital assets, §1231 for business property.",
        ])

        st.markdown("#### Issue #1 — Property")
        irc([
            "<b>Property is defined broadly</b> — includes cash, capital assets, inventory, accounts receivable, patents, and other intangibles.",
            "<b>Property does NOT include services</b> (§351(d)(1)). Stock received in exchange for services is <b>taxable compensation</b> under §61 — ordinary income to the recipient, and a deductible compensation expense (or capitalizable cost) to the corporation. The services portion does not qualify for §351 non-recognition.",
        ])

        st.markdown("#### Issue #2 — Solely in Exchange for Stock (Boot)")
        irc([
            "<b>Qualifying stock</b> = common stock + most types of preferred stock.",
            "<b>Boot</b> = anything received <i>other than</i> qualifying stock — cash, notes, other property. Boot <b>does not disqualify</b> a transaction from §351 despite the 'solely' language.",
            "<b>Gain recognized when boot received</b> = <b>lesser of</b>: (a) gain realized, or (b) boot received. <b>Losses are never recognized</b> even if boot is received.",
        ])

        st.markdown("#### Issue #3 — Control (§§351(a); 368(c))")
        irc([
            "<b>Control</b> requires <b>both</b> tests to be met <i>immediately after</i> the exchange:",
            "(1) Ownership of at least <b>80% of total combined voting power</b> of all classes of stock entitled to vote; <b>AND</b>",
            "(2) Ownership of at least <b>80% of the total number of shares</b> of each class of non-voting stock (every class separately — Rev. Rul. 59-259).",
        ])

        st.markdown("#### Transferor Group")
        irc([
            "§351(a) says '<i>one or more persons</i>' — multiple transferors can qualify as a <b>transferor group</b> and aggregate their ownership to meet the 80% control test together.",
            "<b>Services transferors are excluded from the group.</b> A person who transfers only services (not property) to the corporation cannot be counted as part of the transferor group for the control test. If removing services-only transferors causes the remaining group to fall below 80%, §351 fails for <i>everyone</i>.",
            "<b>Example:</b> Benjamin (property, 50%) + Katie (services only, 50%) → Katie excluded from group → Benjamin alone holds only 50% → control test fails → Benjamin recognizes his full gain.",
            "<b>Mixed transfers (property + services):</b> If a person transfers <i>both</i> property and services, they <i>can</i> be included in the transferor group, but only to the extent of the property portion. The services portion is still ordinary income — but they are not fully excluded from the group.",
        ])

        st.markdown("#### Accommodation Transferor Problem (Treas. Reg. §1.351-1(a)(1)(ii))")
        irc([
            "<b>The abuse:</b> A majority shareholder makes a <i>de minimis</i> token transfer of property to bring a services-only person into the transferor group and manufacture §351 qualification.",
            "<b>Treasury Reg. §1.351-1(a)(1)(ii):</b> Stock issued for property of <i>relatively small value</i> compared to stock already owned (or received for services) by that person shall <b>NOT</b> be treated as issued for property, if the <b>primary purpose</b> of the transfer is to qualify the exchange for other persons under §351.",
            "<b>IRS de minimis safe harbor:</b> A transfer will <b>not</b> be treated as relatively small value if the FMV of the property transferred is <b>at least 10%</b> of the FMV of the stock already owned (or to be received for services) by that person.",
            "<b>Example:</b> Katie transfers $3,699,990 of services + $10 cash to receive 50% stock. The $10 property transfer is de minimis relative to her $3.7M stock position — primary purpose is accommodation. Katie is still excluded from the group under the reg.",
        ])

        st.markdown("#### Basis Rules — Shareholder's Stock (§358)")
        irc([
            "<b>§351 transaction — Substituted basis [IRC 358(a)(1)(A)&(B)]:</b><br>"
            "Basis in stock received =<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Basis of property contributed<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>+ Gain recognized</b> on the transfer<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>− FMV of boot received</b><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>− Liabilities assumed by the corporation</b><br>"
            "Called a '<b>substituted basis</b>' because the shareholder's original property basis carries over into the stock.",
            "<b>Non-§351 transaction:</b> No non-recognition. Basis in stock = <b>FMV</b> of the property transferred (cost basis).",
            "<b>Corporation's asset basis (§362):</b> Carryover basis = transferor's adjusted basis in property transferred <b>+ gain recognized</b> by the transferor. Corp steps up basis only to the extent gain was recognized.",
            "<b>Liabilities assumed — general rule [§357(a)(2)]:</b> In tax generally, a liability assumed by another party = amount realized (triggers gain). However, in a <b>§351 transaction</b>, assumption of a liability will: (1) <b>NOT</b> be considered boot, and (2) <b>NOT</b> prevent §351 treatment. But it <b>will require a downward adjustment to the shareholder's stock basis</b> under §358 (see formula above — liabilities reduce basis dollar-for-dollar).",
            "<b>Exception — §357(c):</b> If the <b>total liabilities assumed exceed the total adjusted basis</b> of all properties transferred, the excess is treated as <b>recognized gain</b>. This prevents the shareholder from walking away with a negative stock basis.",
        ])

        st.markdown("#### Holding Period — Shareholder's Stock (§1223(1))")
        irc([
            "<b>§351 exchange — Capital or §1231 asset transferred:</b> Holding period of the stock received is <b>'tacked on'</b> — it includes the holding period of the transferred property. The clock doesn't reset.",
            "<b>§351 exchange — Ordinary asset transferred</b> (inventory, accounts receivable, short-term trade/business assets): Holding period of the stock begins <b>at the time of exchange</b>. No tacking.",
            "<b>Non-§351 exchange:</b> Regardless of asset type, holding period always begins <b>at the time of the exchange</b> (technically the day after).",
            "<b>Mixed transfer — allocate proportionally by FMV:</b> When different asset types are transferred together (like Benjamin: cash + inventory + §1231 land), the stock holding period is split by FMV weight. "
            "<b>Example (Benjamin):</b> Total FMV $3.7M — Cash $100K (3%, ordinary → fresh start), Robot Parts $600K (16%, inventory → fresh start), Land & Building $3M (81%, §1231 → <b>tacked on</b> from when Benjamin bought the land, say 3 years ago). "
            "If §351 had failed, 100% of the holding period would begin at exchange.",
        ])

        st.markdown("#### Holding Period — Corporation's Assets (§362)")
        irc([
            "<b>§351 qualified exchange:</b> Corporation's holding period in each asset received is <b>tacked on</b> — it includes the shareholder's holding period for that specific asset, regardless of the asset type.",
            "<b>Non-§351 exchange:</b> Corporation's basis in each asset = <b>FMV</b> at the time of transfer, and the holding period begins <b>at the time of the exchange</b> (fresh start).",
            "<b>§362 basis recap:</b> §351 qualified → carryover basis (transferor's basis + gain recognized). Non-§351 → FMV basis. The holding period rule mirrors the basis rule: carryover basis = tacked period; FMV basis = fresh start.",
        ])

    st.markdown("---")
    st.markdown("## §351 Transaction Analyzer")
    st.caption("Complete the qualification checklist first, then enter the asset details.")

    # ── Step 1: Qualification Checklist ──────────────────────────────────────
    st.markdown("### Step 1 — Qualification Checklist")

    st.markdown("**Issue #1: What did the transferor(s) transfer?**")
    q_property = st.radio("Transfer type", [
        "Property only (cash, assets, IP, receivables — all qualify)",
        "Services only (does NOT qualify as property under §351(d)(1))",
        "Mixed — property AND services",
    ], key="f351_q_property", label_visibility="collapsed")

    accom_flag = False
    if q_property == "Mixed — property AND services":
        st.markdown("**Accommodation transferor check (Treas. Reg. §1.351-1(a)(1)(ii))**")
        qa1, qa2 = st.columns(2)
        prop_fmv_mixed  = qa1.number_input("FMV of property portion ($)",        min_value=0.0, step=1_000.0, format="%.2f", key="f351_prop_fmv_mixed")
        stock_fmv_mixed = qa2.number_input("FMV of stock already owned / to be received for services ($)", min_value=0.0, step=1_000.0, format="%.2f", key="f351_stock_fmv_mixed")
        if stock_fmv_mixed > 0:
            ratio = prop_fmv_mixed / stock_fmv_mixed
            if ratio < 0.10:
                accom_flag = True
                st.error(f"⚠️ Property FMV (\\${prop_fmv_mixed:,.0f}) is only {ratio:.1%} of stock FMV (\\${stock_fmv_mixed:,.0f}) — below the 10% de minimis threshold. This transfer will likely be treated as an accommodation transfer and excluded from the group.")
            else:
                st.success(f"✅ Property FMV is {ratio:.1%} of stock FMV — meets the 10% safe harbor. This transferor may be counted in the group.")

    st.markdown("**Issue #2: What did the transferor(s) receive?**")
    q_boot = st.radio("Consideration received", [
        "Stock only (common or most preferred) — purely §351",
        "Stock + boot (cash or other property) — §351 still qualifies, but gain recognized to extent of boot",
    ], key="f351_q_boot", label_visibility="collapsed")

    st.markdown("**Issue #3: Does the transferor group have control immediately after?**")
    q_control = st.radio("Control test (§368(c))", [
        "Yes — transferors (property-only) own ≥80% voting power AND ≥80% of each non-voting class",
        "No — control test fails (services-only transferors excluded; remaining group < 80%)",
    ], key="f351_q_control", label_visibility="collapsed")

    # ── Verdict ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Step 2 — §351 Qualification Verdict")

    services_only   = q_property == "Services only (does NOT qualify as property under §351(d)(1))"
    control_fails   = "No —" in q_control
    boot_received   = "boot" in q_boot

    qualifies_351 = not services_only and not control_fails and not accom_flag

    if services_only:
        st.error("❌ §351 does NOT qualify — transferor transferred services, not property. Full gain recognized as ordinary income (§61).")
    elif accom_flag:
        st.error("❌ §351 does NOT qualify for this transferor — accommodation transferor rule applies. Property transfer is de minimis; transferor excluded from the group.")
    elif control_fails:
        st.error("❌ §351 does NOT qualify — control test fails. Transferor group (property transferors only) does not reach 80%. Full gain recognized.")
    elif boot_received:
        st.warning("⚠️ §351 qualifies — but boot was received. Gain recognized to the extent of boot (lesser of gain realized or boot received). Losses still not recognized.")
    else:
        st.success("✅ §351 qualifies — no gain or loss recognized. Gain fully deferred into substituted stock basis.")

    # ── Step 3: Asset Details & Calculation ──────────────────────────────────
    st.markdown("---")
    st.markdown("### Step 3 — Asset Details & Gain Calculation")

    n_assets = st.number_input("Number of assets transferred", min_value=1, max_value=10, step=1, value=1, key="f351_n")

    rows = []
    for i in range(int(n_assets)):
        st.markdown(f"**Asset {i+1}**")
        a1, a2, a3, a4 = st.columns(4)
        desc  = a1.text_input("Description",        key=f"f351_desc_{i}", value="")
        fmv   = a2.number_input("FMV ($)",           key=f"f351_fmv_{i}",   min_value=0.0, step=1_000.0, format="%.2f")
        basis = a3.number_input("Adj. Basis ($)",    key=f"f351_basis_{i}", min_value=0.0, step=1_000.0, format="%.2f")
        liab  = a4.number_input("Liab. Assumed ($)", key=f"f351_liab_{i}",  min_value=0.0, step=1_000.0, format="%.2f")
        rows.append({"desc": desc or f"Asset {i+1}", "fmv": fmv, "basis": basis, "liab": liab})

    b1, b2 = st.columns(2)
    boot_cash  = b1.number_input("Boot received — Cash ($)",               min_value=0.0, step=1_000.0, format="%.2f", key="f351_boot_cash")
    boot_other = b2.number_input("Boot received — Other property FMV ($)", min_value=0.0, step=1_000.0, format="%.2f", key="f351_boot_other")

    total_fmv   = sum(r["fmv"]   for r in rows)
    total_basis = sum(r["basis"] for r in rows)
    total_liab  = sum(r["liab"]  for r in rows)
    total_boot  = boot_cash + boot_other
    realized_gain = total_fmv - total_basis
    liab_excess   = max(0.0, total_liab - total_basis)

    if not qualifies_351:
        recognized_gain  = max(0.0, realized_gain)
        gain_deferred    = 0.0
        recognized_label = "Full gain (§351 failed)"
    else:
        recognized_gain  = max(0.0, min(realized_gain, total_boot + liab_excess))
        gain_deferred    = max(0.0, realized_gain - recognized_gain)
        recognized_label = "Lesser of gain or boot" if boot_received else "§351 non-recognition"

    stock_basis = total_basis - total_boot - total_liab + recognized_gain
    corp_basis  = total_basis + recognized_gain

    st.markdown("---")
    st.markdown("### Results")
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Realized Gain",   f"${realized_gain:,.0f}",   "FMV − adj. basis")
    rc2.metric("Recognized Gain", f"${recognized_gain:,.0f}", recognized_label)
    rc3.metric("Gain Deferred",   f"${gain_deferred:,.0f}",   "§351 non-recognition" if qualifies_351 else "N/A")

    rb1, rb2 = st.columns(2)
    rb1.metric("Transferor's Stock Basis (§358)", f"${stock_basis:,.0f}",
               "Basis in − boot − liab + gain recognized")
    rb2.metric("Corporation's Asset Basis (§362)", f"${corp_basis:,.0f}",
               "Transferor basis + gain recognized")

    if liab_excess > 0:
        st.error(f"⚠️ §357(c) — Liabilities assumed (\\${total_liab:,.0f}) exceed total basis (\\${total_basis:,.0f}). Excess \\${liab_excess:,.0f} treated as gain recognized.")

    if total_fmv > 0:
        stock_fmv = total_fmv - total_liab - total_boot
        st.markdown(f"""
| | Amount |
|---|---|
| Total FMV of property transferred | ${total_fmv:,.0f} |
| Less: liabilities assumed by corp | (${total_liab:,.0f}) |
| Less: boot received | (${total_boot:,.0f}) |
| **FMV of stock received** | **${stock_fmv:,.0f}** |
| Transferor's adjusted basis in property | ${total_basis:,.0f} |
| Less: boot received | (${total_boot:,.0f}) |
| Less: liabilities assumed | (${total_liab:,.0f}) |
| Plus: gain recognized | ${recognized_gain:,.0f} |
| **Transferor's stock basis (§358)** | **${stock_basis:,.0f}** |
| Corporation's asset basis (§362) | ${corp_basis:,.0f} |
""")

# ─────────────────────────────────────────────────────────────────────────────
# TAX TOPIC: CORPORATE DISTRIBUTIONS
# ─────────────────────────────────────────────────────────────────────────────
elif topic == "💸 Corporate Distributions":
    st.title("Corporate Distributions")

    st.markdown("### Treatment of Distributions — Corporation Side")
    irc([
        "<b>General Rule — Non-deductible:</b> A distribution by a corporation to its shareholders is generally <b>not deductible</b> to the corporation. It is treated as a <b>dividend</b> — a return of earnings, not a business expense.",
        "<b>Exception 1 — Appreciated property distribution [§311(b)]:</b> When a corporation distributes <b>appreciated property</b> (FMV > adjusted basis) to shareholders, the corporation <b>recognizes gain as if it sold the property at FMV</b>. No loss is recognized on non-liquidating distributions of depreciated property [§311(a)].<br>"
        "<b>Rationale:</b> If the corporation sold the asset and distributed cash, it would be taxed on the gain. Distributing the property directly should not allow avoidance of that tax — §311(b) prevents the end-run.<br>"
        "<b>Effect on E&P (property distributions):</b><br>"
        "&nbsp;&nbsp;+ Recognized gain (FMV − adj. basis) → <b>increases E&P</b> (flows through taxable income)<br>"
        "&nbsp;&nbsp;− Distribution reduces E&P at <b>FMV</b> of the property (not basis)<br>"
        "&nbsp;&nbsp;→ <b>Net E&P change = −adjusted basis</b> of the property distributed<br>"
        "<i>Example: Corp distributes land with basis $40K, FMV $100K. Gain of $60K increases E&P; distribution reduces E&P by $100K (FMV). Net E&P change = −$40K (the basis).</i>",
        "<b>Exception 2 — Liquidating distribution:</b> In a <b>complete liquidation</b>, the corporation recognizes <b>both gains and losses</b> on distributed property (treated as a deemed sale at FMV under §336).",
    ])

    st.markdown("### Constructive Dividends")
    irc([
        "<b>Definition:</b> Transactions not formally labeled as distributions but that have the <b>economic effect of a distribution</b> to a shareholder. E&P still determines whether the constructive distribution is a dividend or non-dividend distribution — hence sometimes called 'constructive <i>distributions</i>.' Most common in <b>closely-held corporations</b> where shareholder and management overlap.",

        "<b>Category 1 — Unreasonable payments to shareholders:</b><br>"
        "<ul>"
        "<li><b>Excess compensation:</b> Salary/bonus paid in excess of the value of services actually performed — the excess is recharacterized as a constructive dividend</li>"
        "<li><b>Excess rent:</b> Rent paid by the corporation to a shareholder-landlord above fair market rental value</li>"
        "<li><b>Loans from shareholders at excessive interest:</b> Interest paid above market rate — excess interest = constructive dividend to the shareholder-lender</li>"
        "<li><b>Payment of shareholder's personal expenses:</b> Corp pays personal costs (personal credit cards, home expenses, vacations) — treated as a distribution</li>"
        "<li><b>Below-market loans to shareholders:</b> Corp lends money to shareholder at below-AFR interest — the foregone interest is a constructive dividend [§7872]</li>"
        "<li><b>Loans with no expectation of repayment:</b> Advances treated as loans on paper but with no real intent to collect — recharacterized as a distribution</li>"
        "</ul>",

        "<b>Category 2 — Bargain sales of corporate property to shareholders:</b> Corp sells property to a shareholder at below FMV. The <b>spread (FMV − sale price) = constructive dividend</b>. The corp is treated as if it sold at FMV — recognizes gain under §311(b) on the appreciation, and the shareholder's basis = FMV.",

        "<b>Category 3 — Personal use of corporate property:</b> Shareholder uses corporate assets for personal purposes (boats, cars, aircraft, vacation homes). The <b>fair rental value of the personal use period = constructive dividend</b>. Common audit target for closely-held corps.",

        "<b>Tax treatment:</b> Constructive dividend → flows through the §301(c) waterfall just like a formal distribution: dividend to extent of E&P, then return of capital, then capital gain. The corporation gets no deduction for amounts recharacterized as constructive dividends.",
    ])

    st.markdown("### Stock Distributions — IRC §305")
    irc([
        "<b>General rule [§305(a)] — Non-taxable:</b> A stock dividend paid <b>pro-rata on common stock</b> (proportional to all shareholders' ownership) is <b>not taxable</b> to the shareholder. No economic change — everyone's ownership % stays the same, so no real income has been received.<br>"
        "<ul>"
        "<li><b>Basis:</b> Allocated from old shares to new shares based on relative FMV. Old basis is spread across a larger share count — basis per share decreases.</li>"
        "<li><b>Holding period:</b> Tacked — new shares inherit the holding period of the old shares.</li>"
        "<li><b>E&P:</b> Corporation does <b>not reduce E&P</b> on a non-taxable stock dividend. No economic distribution occurred.</li>"
        "</ul>",

        "<b>Exception [§305(b)] — Taxable:</b> Stock distribution is <b>taxable</b> if it is <b>non-pro-rata</b> (some shareholders receive stock, others receive cash or property) <b>OR</b> distributed on <b>preferred stock</b>. Taxable because these create a real shift in economic interest.<br>"
        "<ul>"
        "<li><b>Income to shareholder:</b> FMV of the shares received = taxable income (flows through §301(c) waterfall — dividend to extent of E&P, then ROC, then capital gain).</li>"
        "<li><b>Basis in new shares:</b> FMV at date of issuance (cost basis — not allocated from old shares).</li>"
        "<li><b>Holding period:</b> Begins on the <b>date issued</b> (fresh start — no tacking).</li>"
        "<li><b>E&P:</b> Corporation reduces E&P by <b>FMV</b> of the shares distributed.</li>"
        "</ul>",

        "<b>Quick reference:</b><br>"
        "<table style='font-size:0.82rem;width:100%;border-collapse:collapse'>"
        "<tr style='background:#1B3A6B;color:white'><th style='padding:4px 8px'></th><th style='padding:4px 8px'>Non-taxable (§305(a))</th><th style='padding:4px 8px'>Taxable (§305(b))</th></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'><b>When</b></td><td style='padding:4px 8px'>Pro-rata on common stock</td><td style='padding:4px 8px'>Non-pro-rata OR on preferred stock</td></tr>"
        "<tr><td style='padding:4px 8px'><b>Income</b></td><td style='padding:4px 8px'>None</td><td style='padding:4px 8px'>FMV of shares = taxable income</td></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'><b>Shareholder basis</b></td><td style='padding:4px 8px'>Allocated from old shares (lower per-share basis)</td><td style='padding:4px 8px'>FMV at date issued</td></tr>"
        "<tr><td style='padding:4px 8px'><b>Holding period</b></td><td style='padding:4px 8px'>Tacked from old shares</td><td style='padding:4px 8px'>Begins date issued (fresh start)</td></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'><b>Corp E&P</b></td><td style='padding:4px 8px'>No reduction</td><td style='padding:4px 8px'>Reduced by FMV</td></tr>"
        "</table>",
    ])

    st.markdown("### Stock Redemptions — IRC §302")
    with st.expander("📚 §302 — Qualifying Redemptions: Rules & Tax Consequences"):
        irc([
        "<b>What is a stock redemption? [§317(b)]:</b> A stock redemption occurs when a corporation acquires its own stock from a shareholder in exchange for <b>property</b> (usually cash). The shareholder sells stock back to the <b>issuing corporation</b>.",
        "<b>The core problem:</b> A redemption can have the <i>economic effect</i> of a distribution rather than a true sale — especially when the shareholder's ownership percentage is unchanged after the redemption. Example: sole shareholder sells 50 of 100 shares back to corp for $200K → still owns 100% of the remaining 50 shares. Same position, but wants capital gain treatment instead of dividend treatment.",
        "<b>General rule [§302(d)]:</b> Unless the redemption <b>qualifies</b> as a sale under §302(b), it is treated as a <b>distribution under §301</b> — going through the E&P waterfall (dividend → return of capital → capital gain). The shareholder gets no offset for stock basis.",
        "<b>Qualifying redemptions [§302(b)] — treated as a sale (must meet one):</b><ul>"
        "<li><b>§302(b)(1) — Not essentially equivalent to a dividend:</b> Fact-sensitive <i>subjective</i> test. Redemption qualifies if it results in a <b>meaningful reduction</b> in the shareholder's interest. Two factors: (1) <b>reduction in voting control</b> — most important; (2) <b>reduction in economic rights</b>. No bright-line numbers; courts weigh the totality.</li>"
        "<li><b>§302(b)(2) — Substantially disproportionate (must satisfy BOTH, partial redemptions only):</b>"
        "<ul><li><b>50% control test:</b> Immediately after redemption, shareholder owns <b>&lt;50%</b> of total combined voting power.</li>"
        "<li><b>80% reduction test:</b> Ownership % immediately after must be <b>&lt;80%</b> of ownership % immediately before (shareholder must give up more than 20% of their original ownership %).</li>"
        "<li><b>Note [Reg. §1.302-3(a)]:</b> Shareholder must still own stock <i>after</i> the redemption — complete terminations (0% after) go to §302(b)(3), not §302(b)(2).</li></ul></li>"
        "<li><b>§302(b)(3) — Complete termination of interest:</b> A complete redemption of <b>all stock</b> owned by a shareholder = sale or exchange. Need not occur simultaneously — a <b>series of redemptions</b> under an integrated plan qualifies. Allows <b>waiver of family attribution rules</b> (§302(c)(2)) with requirements — this distinguishes it from §302(b)(2).</li>"
        "<li><b>§302(b)(4) — Partial liquidation:</b> <b>Non-corporate shareholders only.</b> Sale treatment if: (1) distribution is <i>not essentially equivalent to a dividend</i> from the <i>corporation's perspective</i>; AND (2) there is a <b>genuine contraction</b> of corporate business. Note: sale of investments or sale of excess inventory does NOT qualify — these are not genuine contractions.</li>"
        "<li><b>§303 — Redemption to pay death taxes:</b> Sale/gain treatment allowed if: (1) stock redeemed represents <b>&gt;35%</b> of decedent's gross estate; (2) proceeds are <b>limited to</b> estate taxes + death-related expenses (funeral, admin); (3) <b>attribution rules do NOT apply</b>; (4) generally <b>tax-free</b> because the estate receives a <b>step-up in basis at death</b> — proceeds ≈ stepped-up basis → little or no gain.</li>"
        "</ul>",
        "<b>Non-qualifying result — treated as §301 distribution:</b> Entire redemption proceeds go through the E&P waterfall (dividend → ROC (Return of Capital) → CG (capital gain)). Shareholder's redeemed stock basis is NOT recovered — it transfers to remaining shares or is lost.<br>"
        "<b>Corp side — property distributed in a non-qualifying redemption:</b><ul>"
        "<li><b>Appreciated property:</b> Corp recognizes <b>gain</b> as if sold at FMV [§311(b)]. If property is subject to a liability that exceeds FMV, the <b>liability amount</b> (not FMV) is used to determine the gain.</li>"
        "<li><b>Loss property:</b> Corp recognizes <b>no loss</b> [§311(a)].</li>"
        "<li><b>E&P reduced by:</b> (1) cash distributed; and (2) <b>greater of</b> FMV (appreciated property) <b>or</b> adjusted basis (loss property) of noncash property distributed.</li>"
        "</ul>",
        "<b>Qualifying result — sale/exchange treatment:</b><ul>"
        "<li><b>Shareholder:</b> Amount realized minus <b>adjusted basis of redeemed shares</b> = capital gain or loss.</li>"
        "<li><b>Corp side — property distributed in a qualifying redemption:</b>"
        "<ul><li><b>Appreciated property:</b> Corp still recognizes <b>gain</b> [§311(b)] — same as a non-qualifying redemption.</li>"
        "<li><b>Loss property:</b> Corp still recognizes <b>no loss</b> [§311(a)] — same rule applies regardless of qualifying status.</li></ul></li>"
        "<li><b>E&P reduction:</b> Reduced by the <b>ratable percentage of stock redeemed × E&P</b>, but <b>not more than the FMV</b> of property distributed. Example: redeem 20% of stock → reduce E&P by 20% of E&P (capped at FMV distributed). This differs from non-qualifying treatment where E&P is reduced dollar-for-dollar like a regular distribution.</li>"
        "</ul>",
        "<b>Attribution rules [§318]:</b> For §302(b) tests (other than partial liquidation), shares owned by related parties are <i>attributed</i> to the redeeming shareholder. See §318 section below for the four categories.",
    ])

    st.markdown("### Constructive Ownership of Stock — IRC §318")
    with st.expander("📚 §318 — Constructive Ownership Attribution Rules & Family Example"):
        irc([
        "<b>Purpose [§318]:</b> To qualify for sale treatment under §302(b), there must be a substantial or meaningful reduction in ownership. §318 prevents manipulation — closely related parties could shift ownership on paper without changing the true economic reality. Stock owned by certain related parties is <b>attributed back</b> to the shareholder whose stock is redeemed.",
        "<b>4 categories of attribution:</b><ol>"
        "<li><b>Family attribution [§318(a)(1)]:</b> An individual is deemed to own stock owned by their <b>spouse, children, grandchildren, and parents</b>.<ul>"
        "<li>Siblings and in-laws are <b>NOT</b> included in 'family' for this purpose.</li>"
        "<li>Attribution is <b>upward only</b> for grandparent/grandchild — grandchild's shares attributed to grandparent, but <b>NOT</b> grandparent's shares down to grandchild.</li>"
        "<li><b>No double attribution</b> — cannot chain family attribution (e.g., parent → child → child's spouse does not work).</li>"
        "<li><b>Waivable under §302(c)(2)</b> for complete terminations [§302(b)(3)] only. Three requirements:<ul>"
        "<li>Individual has <b>no interest</b> in the corp after redemption — including as officer, director, or employee. (<i>Can</i> remain a creditor.)</li>"
        "<li>Individual does <b>not acquire</b> any interest in the corp (other than by bequest or inheritance) within <b>10 years</b> after the redemption.</li>"
        "<li>Individual <b>files an agreement</b> with the IRS to notify them of any prohibited acquisition within the 10-year period.</li>"
        "</ul></li>"
        "</ul></li>"
        "<li><b>Entity → owner attribution [§318(a)(2)]:</b>"
        "<ul><li><b>Partnership → partners:</b> Stock owned by a partnership is attributed to each partner <b>proportionally</b> (no ownership threshold). E.g., own 20% of ABC Partnership that owns 70% of XYZ Corp → deemed to own 14% of XYZ.</li>"
        "<li><b>C-corporation → shareholders:</b> Stock owned by a C-corp is attributed to a shareholder only if that shareholder owns (directly or by attribution) <b>≥50%</b> in value of the C-corp's stock. E.g., Me owns 20% of ABC Corp and ABC owns 70% of XYZ → <b>NOT attributed to Me</b> (only 20% of ABC, below threshold).</li>"
        "<li><b>Trust/estate → beneficiaries:</b> Proportionally attributed to beneficiaries.</li>"
        "</ul></li>"
        "<li><b>Owner → entity attribution [§318(a)(3)]:</b>"
        "<ul><li><b>Partners → partnership:</b> <b>ALL</b> stock owned by any partner is attributed to the partnership (no threshold). E.g., I own 20% of ABC and 70% of ABC Partnership → ABC Partnership is deemed to own 100% of my ABC shares.</li>"
        "<li><b>Shareholders → C-corporation:</b> Stock owned by a shareholder is attributed to the C-corp only if that shareholder owns <b>≥50%</b> of the C-corp. E.g., Me owns 20% of ABC Corp and 70% of XYZ Corp → My 20% ABC is <b>attributed to XYZ</b> (I own 70% ≥ 50% of XYZ), but <b>NOT attributed to ABC</b> (I own only 20% of ABC).</li>"
        "<li><b>Beneficiaries → trust/estate:</b> Attributed to the entity.</li>"
        "</ul></li>"
        "<b>Key asymmetry — Partnership vs. Corporation:</b><br>"
        "<table style='border-collapse:collapse;width:100%'>"
        "<tr style='background:#1B3A6B;color:white'><th style='padding:4px 8px'>Direction</th><th style='padding:4px 8px'>Partnership</th><th style='padding:4px 8px'>C-Corporation</th></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'>Entity → Owner</td><td style='padding:4px 8px'>Pro-rata, <b>no threshold</b></td><td style='padding:4px 8px'>Only if shareholder owns <b>≥50%</b> of that corp</td></tr>"
        "<tr><td style='padding:4px 8px'>Owner → Entity</td><td style='padding:4px 8px'>All partners' stock → partnership, <b>no threshold</b></td><td style='padding:4px 8px'>Only if shareholder owns <b>≥50%</b> of that corp</td></tr>"
        "</table><br>",
        "<li><b>Option attribution [§318(a)(4)]:</b> A person who holds an <b>option to acquire stock</b> is deemed to own that stock.</li>"
        "</ol>",
        "<b>MCEWMS family example — how to apply §318:</b><br>"
        "<table style='border-collapse:collapse;width:100%'>"
        "<tr style='background:#1B3A6B;color:white'><th style='padding:4px 8px'>Person</th><th style='padding:4px 8px'>Direct</th><th style='padding:4px 8px'>Attributed from</th><th style='padding:4px 8px'>Total deemed owned</th></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'>Alice (grandma)</td><td style='padding:4px 8px'>50</td><td style='padding:4px 8px'>George (son) 25 + Diane (daughter-in-law, via George's spouse rule? No — Diane is in-law, not direct family of Alice). Charlie &amp; Mary via George: 10+10=20</td><td style='padding:4px 8px'>50 + 25 + 20 = <b>95</b></td></tr>"
        "<tr><td style='padding:4px 8px'>George (father)</td><td style='padding:4px 8px'>25</td><td style='padding:4px 8px'>Alice (parent) 50 + Diane (spouse) 20 + Charlie (child) 10 + Mary (child) 10</td><td style='padding:4px 8px'>25 + 50 + 20 + 10 + 10 = <b>115</b></td></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'>Diane (mother)</td><td style='padding:4px 8px'>20</td><td style='padding:4px 8px'>George (spouse) 25 + Charlie (child) 10 + Mary (child) 10. <i>NOT Alice — Diane is in-law to Alice, not her child/parent/grandchild/spouse.</i></td><td style='padding:4px 8px'>20 + 25 + 10 + 10 = <b>65</b></td></tr>"
        "<tr><td style='padding:4px 8px'>Charlie (son)</td><td style='padding:4px 8px'>10</td><td style='padding:4px 8px'>Diane (parent) 20 + George (parent) 25 + Marie (spouse) 10 + Mary (sibling — <b>NOT attributed</b>, siblings excluded)</td><td style='padding:4px 8px'>10 + 20 + 25 + 10 = <b>65</b></td></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'>Mary (daughter)</td><td style='padding:4px 8px'>10</td><td style='padding:4px 8px'>Diane (parent) 20 + George (parent) 25. <i>NOT Alice — no attribution grandparent → grandchild.</i> Charlie (sibling — excluded). Marie (in-law — excluded).</td><td style='padding:4px 8px'>10 + 20 + 25 = <b>55</b></td></tr>"
        "<tr><td style='padding:4px 8px'>Marie (daughter-in-law)</td><td style='padding:4px 8px'>10</td><td style='padding:4px 8px'>Charlie (spouse) 10. <i>In-laws of Alice/George/Diane are NOT her family for §318.</i></td><td style='padding:4px 8px'>10 + 10 = <b>20</b></td></tr>"
        "</table><br><i>Total actual shares: 50+25+20+10+10+10 = 125</i>",
    ])

    with st.expander("§302 Redemption Analyzer"):
        red_mode = st.radio("Test type", ["§302(b)(2) Substantially Disproportionate", "§302(b)(3) Complete Termination"], horizontal=True, key="red_mode")

        col1, col2 = st.columns(2)
        with col1:
            total_shares_before = st.number_input("Total shares outstanding (before)", min_value=1, value=100, key="red_total_before")
            sh_shares_before = st.number_input("Shareholder shares before redemption", min_value=0, value=60, key="red_sh_before")
            shares_redeemed = st.number_input("Shares redeemed", min_value=0, value=20, key="red_redeemed")
        with col2:
            red_fmv = st.number_input("Redemption proceeds ($)", min_value=0.0, value=200000.0, step=1000.0, key="red_fmv")
            red_basis = st.number_input("Adjusted basis of redeemed shares ($)", min_value=0.0, value=50000.0, step=1000.0, key="red_basis")
            corp_ep = st.number_input("Corp E&P at time of redemption ($)", min_value=0.0, value=500000.0, step=1000.0, key="red_ep")

        total_shares_after = total_shares_before - shares_redeemed
        sh_shares_after = sh_shares_before - shares_redeemed
        pct_before = sh_shares_before / total_shares_before * 100 if total_shares_before > 0 else 0
        pct_after = sh_shares_after / total_shares_after * 100 if total_shares_after > 0 else 0

        st.markdown("**Ownership Analysis**")
        rcol1, rcol2, rcol3 = st.columns(3)
        rcol1.metric("% Before", f"{pct_before:.1f}%")
        rcol2.metric("% After (direct)", f"{pct_after:.1f}%")

        if red_mode == "§302(b)(2) Substantially Disproportionate":
            threshold_80 = pct_before * 0.80
            rcol3.metric("80% Threshold", f"{threshold_80:.1f}%")

            if sh_shares_after <= 0:
                st.warning("§302(b)(2) does not apply — shareholder owns 0 shares after the redemption. Use §302(b)(3) Complete Termination instead. [Reg. §1.302-3(a)]")
                qualifies = False
            else:
                test_80 = pct_after < threshold_80
                test_50 = pct_after < 50.0
                qualifies = test_80 and test_50

                st.markdown(f"- 50% control test: after = {pct_after:.1f}% {'✅ < 50%' if test_50 else '❌ ≥ 50%'}")
                st.markdown(f"- 80% reduction test: after {pct_after:.1f}% vs threshold {threshold_80:.1f}% {'✅ qualifies' if test_80 else '❌ fails'}")

                if qualifies:
                    st.success(f"QUALIFIES §302(b)(2) — Treated as SALE.")
                else:
                    reasons = []
                    if not test_80:
                        reasons.append(f"after % ({pct_after:.1f}%) ≥ 80% threshold ({threshold_80:.1f}%)")
                    if not test_50:
                        reasons.append(f"after % ({pct_after:.1f}%) ≥ 50%")
                    st.error(f"FAILS §302(b)(2) — {'; '.join(reasons)}.")

        else:  # §302(b)(3) Complete Termination
            rcol3.metric("Shares After", f"{sh_shares_after:.0f}")
            attr_shares = st.number_input("Attributed shares (family/entity §318)", min_value=0, value=0, key="red_attr")
            family_waiver = st.checkbox("Family attribution waived under §302(c)(2)?", key="red_waiver")

            effective_after = sh_shares_after + (0 if family_waiver else attr_shares)
            qualifies = effective_after == 0

            st.markdown(f"- Direct shares after: {sh_shares_after:.0f}")
            st.markdown(f"- Attributed shares: {attr_shares} {'(waived)' if family_waiver else ''}")
            st.markdown(f"- Effective ownership after §318: {effective_after:.0f} shares")

            if qualifies:
                st.success("QUALIFIES §302(b)(3) — Complete termination. Treated as SALE.")
            else:
                st.error(f"FAILS §302(b)(3) — Shareholder still has {effective_after:.0f} effective shares (including attributed). Family attribution waiver may be available.")

        assume_qualifying = False
        if not qualifies:
            assume_qualifying = st.checkbox("Problem states this is a qualifying redemption — override test result", key="red_override")

        st.divider()
        gain_loss = red_fmv - red_basis
        ep_ratable = corp_ep * (shares_redeemed / total_shares_before) if total_shares_before > 0 else 0

        if qualifies or assume_qualifying:
            st.markdown("**Sale treatment:**")
            st.markdown(f"Proceeds ${red_fmv:,.0f} − Basis ${red_basis:,.0f} = **{'Gain' if gain_loss >= 0 else 'Loss'} ${abs(gain_loss):,.0f}** (capital gain/loss)")
            ep_capped = min(ep_ratable, red_fmv)
            st.markdown(f"**Corp E&P reduction:** ${ep_capped:,.0f} (lesser of ratable % × E&P = ${ep_ratable:,.0f} or FMV distributed = ${red_fmv:,.0f})")
        else:
            st.markdown("**§301 distribution treatment:**")
            div = min(red_fmv, corp_ep)
            roc = min(red_fmv - div, red_basis)
            cg = max(0.0, red_fmv - div - roc)
            st.markdown(f"Dividend ${div:,.0f} | Return of Capital ${roc:,.0f} | Capital Gain ${cg:,.0f}")
            st.warning(f"Redeemed shares basis (\\${red_basis:,.0f}) is NOT recovered — transfers to remaining shares or is lost.")

    st.markdown("### Liquidating Distributions — IRC §§ 331 & 336")
    irc([
        "<b>What is a complete liquidation?</b> Distribution (or series of distributions) of <b>all corporate assets and liabilities</b> in redemption or cancellation of all outstanding shares. Key points:<ul>"
        "<li>Legal dissolution is <b>not required</b> — corp can retain a nominal amount of assets to pay debts and preserve legal existence.</li>"
        "<li>Formal plan of liquidation is not legally required but <b>should</b> be adopted — prevents earlier distributions from being re-characterized as ordinary operating distributions.</li>"
        "</ul>",
        "<b>General rule:</b> Complete liquidations are treated as fully taxable <b>sales or exchanges</b> for <i>both</i> the corporation and the shareholders. This is the key difference from §311 regular distributions — in liquidation, the corp can recognize <b>both gains AND losses</b>.",
        "<b>Shareholder side [§331]:</b><ul>"
        "<li><b>Amount realized</b> = FMV of property received <i>minus</i> liabilities assumed by the shareholder.</li>"
        "<li><b>Gain or loss</b> = Amount realized − adjusted basis of stock surrendered (capital gain/loss).</li>"
        "<li><b>Basis of property received</b> = FMV at date of distribution. Liabilities assumed do <b>not</b> reduce the shareholder's basis in received property.</li>"
        "</ul>",
        "<b>Corporation side [§336(a)]:</b> '…gain or loss shall be recognized to a liquidating corporation on the distribution of property in complete liquidation <i>as if such property were sold to the distributee at its fair market value.</i>' Both gains and losses recognized — contrast with §311(a) which disallows losses on non-liquidating distributions.<br>"
        "Gain/loss per asset = FMV − adjusted basis of that asset.",
    ])

    with st.expander("§331/§336 Liquidation Calculator"):
        st.markdown("**Shareholder Side [§331]**")
        liq_col1, liq_col2 = st.columns(2)
        with liq_col1:
            liq_fmv = st.number_input("FMV of property received ($)", min_value=0.0, value=500000.0, step=1000.0, key="liq_fmv")
            liq_liab = st.number_input("Liabilities assumed by shareholder ($)", min_value=0.0, value=0.0, step=1000.0, key="liq_liab")
        with liq_col2:
            liq_stock_basis = st.number_input("Adjusted basis of stock surrendered ($)", min_value=0.0, value=200000.0, step=1000.0, key="liq_stock_basis")
            liq_holding = st.radio("Holding period of stock", ["Long-term (>1 year)", "Short-term (≤1 year)"], key="liq_holding")

        liq_amt_realized = liq_fmv - liq_liab
        liq_gain_loss = liq_amt_realized - liq_stock_basis

        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Amount Realized", f"${liq_amt_realized:,.0f}")
        sc2.metric("Stock Basis", f"${liq_stock_basis:,.0f}")
        sc3.metric("Gain / (Loss)", f"${liq_gain_loss:,.0f}", delta_color="normal")

        if liq_gain_loss >= 0:
            st.success(f"Shareholder recognizes **{'long-term' if 'Long' in liq_holding else 'short-term'} capital gain of \\${liq_gain_loss:,.0f}**. Basis in property received = FMV \\${liq_fmv:,.0f} (liabilities assumed do not reduce basis).")
        else:
            st.error(f"Shareholder recognizes **{'long-term' if 'Long' in liq_holding else 'short-term'} capital loss of \\${abs(liq_gain_loss):,.0f}**. Basis in property received = FMV \\${liq_fmv:,.0f}.")

        st.divider()
        st.markdown("**Corporation Side [§336] — Asset-by-Asset**")
        n_assets = st.number_input("Number of assets distributed", min_value=1, max_value=10, value=2, key="liq_n_assets")
        corp_rows = []
        for i in range(int(n_assets)):
            c1, c2, c3 = st.columns(3)
            with c1:
                a_name = st.text_input(f"Asset {i+1} name", value=f"Asset {i+1}", key=f"liq_aname_{i}")
            with c2:
                a_fmv = st.number_input(f"FMV ($)", min_value=0.0, value=100000.0, step=1000.0, key=f"liq_afmv_{i}")
            with c3:
                a_basis = st.number_input(f"Adjusted basis ($)", min_value=0.0, value=60000.0, step=1000.0, key=f"liq_abasis_{i}")
            corp_rows.append({"name": a_name, "fmv": a_fmv, "basis": a_basis, "gl": a_fmv - a_basis})

        total_gl = sum(r["gl"] for r in corp_rows)
        st.markdown("| Asset | FMV | Basis | Gain / (Loss) |")
        st.markdown("|---|---|---|---|")
        for r in corp_rows:
            gl_str = f"({'Loss'} ${abs(r['gl']):,.0f})" if r["gl"] < 0 else f"Gain ${r['gl']:,.0f}"
            st.markdown(f"| {r['name']} | ${r['fmv']:,.0f} | ${r['basis']:,.0f} | {gl_str} |")
        st.markdown(f"| **Total** | | | **${total_gl:,.0f}** |")
        if total_gl >= 0:
            st.success(f"Corp recognizes net gain of \\${total_gl:,.0f} on liquidation (gains AND losses both recognized under §336(a)).")
        else:
            st.error(f"Corp recognizes net loss of \\${abs(total_gl):,.0f} on liquidation.")

    st.markdown("### Treatment of Distributions — Shareholder Side")
    st.markdown("Distributions are applied in this order:")
    irc([
        "<b>Statutory authority — IRC §301(c):</b> 'In the case of a distribution…' (1) the portion which is a <i>dividend</i> shall be <b>included in gross income</b>; (2) the portion which is not a dividend shall be applied against and <b>reduce the adjusted basis of the stock</b>; (3) the portion which is not a dividend, to the extent it <b>exceeds the adjusted basis</b> of the stock, shall be treated as <b>gain from the sale or exchange of property</b> (capital gain).",
        "<b>1st — Dividend (to the extent of E&P):</b> To the extent the corporation has current or accumulated <b>Earnings & Profits (E&P)</b>, the distribution is classified as a <b>dividend</b> and is fully <b>taxable</b> to the shareholder as ordinary income (or qualified dividend income if eligible).",
        "<b>2nd — Return of Capital (to the extent of stock basis):</b> Once E&P is exhausted, any remaining distribution is a <b>non-dividend distribution</b> and is <b>non-taxable</b> to the extent the shareholder has <b>adjusted basis</b> in their stock. The basis is reduced dollar-for-dollar.",
        "<b>3rd — Capital Gain (excess over basis):</b> If the non-dividend distribution exceeds the shareholder's remaining stock basis, the excess is treated as a <b>taxable capital gain</b> (long-term if the stock has been held > 1 year).",
    ])

    st.markdown("### Definition of 'Dividend' — IRC §316(c)")
    irc([
        "<b>§316(c) statutory definition:</b> The term '<b>dividend</b>' means any distribution of property made by a corporation to its shareholders— (1) out of its <b>earnings and profits accumulated</b> after February 28, 1913 (<b>Accumulated E&P</b>); or (2) out of its <b>earnings and profits of the taxable year</b> (<b>Current E&P</b>), without regard to the amount of E&P at the time the distribution was made.",
        "<b>Accumulated E&P:</b> The running total of all prior years' undistributed after-tax earnings since the corporation's inception (post-1913). Think of it as the corporate retained earnings account for tax purposes.",
        "<b>Current E&P:</b> The current tax year's earnings and profits, computed before distributions. A distribution is a dividend to the extent of current E&P <i>even if accumulated E&P is negative</i> — current E&P is tested independently.",
        "<b>Priority rule:</b> Current E&P is used first; accumulated E&P is the backstop. If both are zero or negative, the distribution is a non-dividend distribution (return of capital / capital gain per §301(c)).",
    ])

    st.markdown("### Dividend Tax Rates")
    irc([
        "<b>Corporate shareholder:</b> Dividend income taxed at <b>21% ordinary rate</b>. However, corporate shareholders may claim the <b>Dividends Received Deduction (DRD)</b> under §243 — partially or fully offsetting the dividend income (see Schedule C in Form 1120).",
        "<b>Individual shareholder — Qualified dividend:</b> Taxed at <b>long-term capital gains rates</b> (0% / 15% / 20%) + <b>3.8% Net Investment Income Tax (NIIT)</b> if applicable. Maximum combined rate = <b>23.8%</b> (20% + 3.8%). Assumes stock held > 60 days around ex-dividend date.",
        "<b>Individual shareholder — Nonqualified dividend:</b> Taxed at <b>ordinary income rates</b> (up to 37%) + 3.8% NIIT if applicable. Maximum combined rate = <b>40.8%</b> (37% + 3.8%).",
        "<b>Exam assumption:</b> Unless stated otherwise, assume dividends are <b>qualified</b>.",
    ])

    st.markdown("### Non-Dividend Distributions — Return of Capital")
    irc([
        "<b>Nontaxable return of capital:</b> Once E&P is exhausted, distributions are <b>not taxable</b> but <b>reduce the shareholder's adjusted basis</b> in the stock dollar-for-dollar.",
        "<b>Why nontaxable?</b> E&P represents income that <u>has already been taxed</u> at the corporate level. Once all taxed income has been distributed (E&P reduced to zero through dividends), any additional distributions are simply returning the shareholder's own investment — not new income. No double-tax on what was never earnings.",
        "<b>Basis floor:</b> Once stock basis reaches zero, further non-dividend distributions flip to <b>capital gain</b> (§301(c)(3)) — the shareholder has fully recovered their investment and any additional amount is gain.",
    ])

    st.markdown("### Capital Gain Distributions")
    irc([
        "<b>Treated as sale or exchange of stock:</b> When a shareholder receives a non-dividend distribution and has <b>insufficient basis</b> in the stock, the excess over basis is treated as a <b>sale or exchange of the stock</b> (§301(c)(3)).",
        "<b>Holding period determines character:</b> If the stock has been held <b>&gt; 1 year</b> → <b>Long-Term Capital Gain (LTCG)</b>. If held <b>1 year or less</b> → <b>Short-Term Capital Gain (STCG)</b> taxed at ordinary rates.",
    ])

    st.markdown("---")
    st.markdown("## E&P Reconciliation — Book / Tax / E&P")
    st.caption("Three sets of books. Enter amounts in each column; E&P adjustments are entered separately from tax adjustments.")

    irc([
        "<b>E&P is the third set of books</b> — separate from GAAP (book) and taxable income (tax). It measures the corporation's <b>economic ability to pay a dividend</b>. Calculation begins with taxable income, then +/− certain adjustments.",
        "<b>Rollforward:</b> Beginning Accumulated E&P + Current E&P − Distributions paid from E&P = <b>Ending Accumulated E&P</b>.",
        "<b>Common ADDITIONS to taxable income for E&P:</b> Muni bond interest (§103 exempt but real economic income) · Life insurance proceeds · Federal income tax refunds · DRD (Dividends Received Deduction — added back because corp received the full dividend economically) · NOL (Net Operating Loss) carryovers used · Net capital loss carryover used · Charitable contribution carryovers used.",
        "<b>Common SUBTRACTIONS from taxable income for E&P:</b> Federal taxes paid · Non-deductible charitable contributions (above 10% limit) · Non-deductible meals &amp; entertainment · Non-deductible fines &amp; lobbying costs · Current year net capital loss · Other non-deductible expenses · <b>Excess MACRS (Modified Accelerated Cost Recovery System) over ADS (Alternative Depreciation System) depreciation</b> — E&P <b>cannot use MACRS</b>; must use ADS, which is straight-line over longer ADS lives. The excess of MACRS deduction over ADS deduction is subtracted. In early years MACRS &gt; ADS (MACRS accelerates), so E&P is lower than taxable income; in later years ADS &gt; MACRS, so E&P is higher.",
    ])

    _book_default = float(st.session_state.get("book_income", 0.0))
    _tax_default  = float(st.session_state.get("_taxable_income", 0.0))
    _tax_paid_default = float(st.session_state.get("_federal_tax_paid", 0.0))
    if _book_default or _tax_default:
        st.info("📋 Book and Tax columns auto-populated from your Form 1120 entries. Edit below to override.")

    ep1, ep2, ep3 = st.columns(3)
    ep1.markdown("**📚 Book (GAAP)**")
    ep2.markdown("**📋 Tax (IRC)**")
    ep3.markdown("**💰 E&P Adjustments**")

    book_ni = ep1.number_input("Net Income (GAAP)",  min_value=-1e9, step=1_000.0, format="%.2f",
                                key="ep_book_ni", value=_book_default)
    tax_ti  = ep2.number_input("Taxable Income",     min_value=-1e9, step=1_000.0, format="%.2f",
                                key="ep_tax_ti",  value=_tax_default)

    st.markdown("**Additions to taxable income (+)**")
    ea1, ea2 = st.columns(2)
    ep_muni      = ea1.number_input("+ Muni bond interest",              min_value=0.0, step=1_000.0, format="%.2f", key="ep_muni")
    ep_li        = ea2.number_input("+ Life insurance proceeds",         min_value=0.0, step=1_000.0, format="%.2f", key="ep_li")
    ep_taxrefund = ea1.number_input("+ Federal income tax refunds",      min_value=0.0, step=1_000.0, format="%.2f", key="ep_taxrefund")
    ep_drd       = ea2.number_input("+ DRD add-back",                   min_value=0.0, step=1_000.0, format="%.2f", key="ep_drd")
    ep_nol_used  = ea1.number_input("+ NOL carryover used",             min_value=0.0, step=1_000.0, format="%.2f", key="ep_nol_used")
    ep_cl_used   = ea2.number_input("+ Capital loss carryover used",    min_value=0.0, step=1_000.0, format="%.2f", key="ep_cl_used")
    ep_char_used = ea1.number_input("+ Charitable carryover used",      min_value=0.0, step=1_000.0, format="%.2f", key="ep_char_used")

    st.markdown("**Subtractions from taxable income (−)**")
    es1, es2 = st.columns(2)
    ep_fed_tax   = es1.number_input("− Federal taxes paid",             min_value=0.0, step=1_000.0, format="%.2f", key="ep_fed_tax", value=_tax_paid_default)
    ep_nd_char   = es2.number_input("− Non-deductible charitable",      min_value=0.0, step=1_000.0, format="%.2f", key="ep_nd_char")
    ep_nd_meals  = es1.number_input("− Non-deductible meals & ent.",    min_value=0.0, step=1_000.0, format="%.2f", key="ep_nd_meals")
    ep_nd_fines  = es2.number_input("− Non-deductible fines & lobby",   min_value=0.0, step=1_000.0, format="%.2f", key="ep_nd_fines")
    ep_cur_cl    = es1.number_input("− Current year net capital loss",  min_value=0.0, step=1_000.0, format="%.2f", key="ep_cur_cl")
    ep_depr      = es2.number_input("− Excess MACRS over ADS depreciation", min_value=0.0, step=1_000.0, format="%.2f", key="ep_depr")
    ep_install   = es1.number_input("+ Installment sale gain deferred (add back)", min_value=0.0, step=1_000.0, format="%.2f", key="ep_install")

    ep_additions    = ep_muni + ep_li + ep_taxrefund + ep_drd + ep_nol_used + ep_cl_used + ep_char_used + ep_install
    ep_subtractions = ep_fed_tax + ep_nd_char + ep_nd_meals + ep_nd_fines + ep_cur_cl + ep_depr
    current_ep      = tax_ti + ep_additions - ep_subtractions

    ep_accum_beg = st.number_input("Beginning Accumulated E&P", min_value=-1e9, step=1_000.0, format="%.2f", key="ep_accum_beg")
    ep_dist_paid = st.number_input("Distributions paid this year (from E&P)", min_value=0.0, step=1_000.0, format="%.2f", key="ep_dist_paid")

    ep_accum_end = ep_accum_beg + current_ep - min(ep_dist_paid, max(0.0, ep_accum_beg + current_ep))

    st.markdown("### E&P Summary")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Current E&P",            f"${current_ep:,.0f}")
    s2.metric("Beginning Accum. E&P",   f"${ep_accum_beg:,.0f}")
    s3.metric("Distributions from E&P", f"${min(ep_dist_paid, max(0.0, ep_accum_beg + current_ep)):,.0f}")
    s4.metric("Ending Accum. E&P",      f"${ep_accum_end:,.0f}")

    st.markdown("---")
    st.markdown("## Distribution Analyzer")

    # ── §311(b) Property Distribution Calculator ───────────────────────────────
    with st.expander("🏠 §311(b) Property Distribution Calculator — Appreciated Property", expanded=False):
        st.caption("Use when the corporation distributes non-cash property. Computes corp-level gain, E&P impact, and shareholder's basis in the property received.")
        pc1, pc2 = st.columns(2)
        prop_fmv   = pc1.number_input("FMV of property distributed ($)",      min_value=0.0, step=1_000.0, format="%.0f", key="prop_fmv")
        prop_basis = pc2.number_input("Corp's adjusted basis in property ($)", min_value=0.0, step=1_000.0, format="%.0f", key="prop_basis")
        prop_liab  = pc1.number_input("Liabilities assumed by shareholder ($, if any)", min_value=0.0, step=1_000.0, format="%.0f", key="prop_liab")

        if prop_fmv > 0 or prop_basis > 0:
            is_appreciated = prop_fmv >= prop_basis
            prop_gain      = max(0.0, prop_fmv - prop_basis)
            dist_amt_prop  = max(prop_fmv, prop_liab)  # §301(b)(1): amount to shareholder = FMV

            if is_appreciated:
                # §311(b): gain recognized; §312(b): E&P decreases at FMV
                ep_increase = prop_gain   # gain → taxable income → E&P
                ep_decrease = prop_fmv    # §312(b): distribution reduces E&P at FMV
                ep_net      = ep_increase - ep_decrease  # = −basis
                ep_rule     = "§312(b) — E&P decreases at <b>FMV</b> (appreciated property)"
                ep_decrease_label = f"E&P decrease at FMV [§312(b)]"
            else:
                # §311(a): NO loss recognized; §312(a)(3): E&P decreases at adjusted basis
                ep_increase = 0.0
                ep_decrease = prop_basis  # §312(a)(3): E&P decreases at adjusted basis, NOT FMV
                ep_net      = -ep_decrease
                ep_rule     = "§312(a)(3) — E&P decreases at <b>adjusted basis</b> (loss property — worse than FMV)"
                ep_decrease_label = f"E&P decrease at adjusted basis [§312(a)(3)]"

            pr1, pr2, pr3, pr4 = st.columns(4)
            pr1.metric("Gain / Loss Recognized",   f"${prop_gain:,.0f}" if is_appreciated else "$0",
                       "§311(b) — taxed as sold at FMV" if is_appreciated else "§311(a) — loss disallowed")
            pr2.metric("E&P Increase",             f"+${ep_increase:,.0f}", "From gain recognized" if ep_increase else "No gain → no increase")
            pr3.metric("E&P Decrease",             f"−${ep_decrease:,.0f}", ep_decrease_label)
            pr4.metric("Net E&P Change",            f"${ep_net:,.0f}",      "= −basis (appreciated)" if is_appreciated else "= −basis (loss property, larger hit)")

            if is_appreciated:
                st.markdown(f"""
| | Amount |
|---|---|
| FMV of property | ${prop_fmv:,.0f} |
| − Adjusted basis | (${prop_basis:,.0f}) |
| **§311(b) gain recognized by corp** | **${prop_gain:,.0f}** |
| + E&P increase (gain → taxable income) | +${ep_increase:,.0f} |
| − E&P decrease at FMV [§312(b)] | −${ep_decrease:,.0f} |
| **Net E&P change** | **${ep_net:,.0f}** (= −adjusted basis) |
| Shareholder's basis in property [§301(d)] | ${prop_fmv:,.0f} (FMV) |
| Amount of distribution to shareholder [§301(b)(1)] | ${dist_amt_prop:,.0f} |
""")
            else:
                st.warning("⚠️ **Loss property distribution — not recommended.** Corp gets no loss deduction [§311(a)]. E&P decreases by **adjusted basis** [§312(a)(3)], which is *larger* than the FMV the shareholder receives. The built-in loss is permanently wasted.")
                st.markdown(f"""
| | Amount |
|---|---|
| FMV of property | ${prop_fmv:,.0f} |
| Adjusted basis | ${prop_basis:,.0f} |
| Built-in loss (FMV − basis) | (${prop_basis - prop_fmv:,.0f}) |
| **§311(a) loss recognized by corp** | **$0** (disallowed) |
| + E&P increase | $0 (no gain) |
| − E&P decrease at adjusted basis [§312(a)(3)] | −${ep_decrease:,.0f} |
| **Net E&P change** | **${ep_net:,.0f}** |
| Shareholder's basis in property [§301(d)] | ${prop_fmv:,.0f} (FMV — not basis) |
| Amount of distribution to shareholder [§301(b)(1)] | ${dist_amt_prop:,.0f} |
| ⚠️ E&P cost vs. cash distributed | Corp E&P drops ${ep_decrease:,.0f} but sh only gets ${prop_fmv:,.0f} |
""")

    dist_mode = st.radio("Mode", ["Single Distribution", "Multiple Distributions (same year)"],
                         horizontal=True, key="dist_mode")

    # ── §316 E&P Available at Distribution Date ────────────────────────────────
    st.markdown("### Step 1 — §316 E&P Available at Distribution Date")
    irc([
        "<b>General rules [§316]:</b><br>"
        "(1) <b>Current E&P is used first</b> — always takes priority over accumulated E&P.<br>"
        "(2) <b>Current E&P is pro-rated by distribution size</b> across all distributions in the year (not by date). Each distribution's share = (its amount ÷ total distributions) × current E&P.<br>"
        "(3) <b>Current E&P is measured at year end</b> — regardless of when the distribution happens. The full-year current E&P figure applies to all distributions during the year.<br>"
        "(4) <b>Accumulated E&P is applied chronologically</b> — earliest distribution gets first access.",

        "<b>⭐ 4-Scenario Reference Table:</b><br>"
        "<table style='font-size:0.82rem;width:100%;border-collapse:collapse'>"
        "<tr style='background:#1B3A6B;color:white'><th style='padding:4px 8px'>Current E&P</th><th style='padding:4px 8px'>Accum. E&P</th><th style='padding:4px 8px'>Treatment</th></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'>Positive</td><td style='padding:4px 8px'>Positive</td><td style='padding:4px 8px'>Current first (pro-rata by size) → accumulated second (chronological)</td></tr>"
        "<tr><td style='padding:4px 8px'>Positive</td><td style='padding:4px 8px'>Negative</td><td style='padding:4px 8px'>Current E&P available in full until depleted. Accumulated deficit is <u>NOT netted</u> with positive current before distributions.</td></tr>"
        "<tr style='background:#EBF4FF'><td style='padding:4px 8px'>Negative</td><td style='padding:4px 8px'>Positive</td><td style='padding:4px 8px'>Negative current (pro-rated to distribution date) IS netted with accumulated before distributions. E&P available = accum + (month/12 × current deficit).</td></tr>"
        "<tr><td style='padding:4px 8px'>Negative</td><td style='padding:4px 8px'>Negative</td><td style='padding:4px 8px'>All distributions are non-dividend (return of capital / capital gain). No E&P available.</td></tr>"
        "</table>",
    ])

    p316_c1, p316_c2, p316_c3 = st.columns(3)
    p316_accum   = p316_c1.number_input("Accumulated E&P (start of year) ($)", value=float(ep_accum_beg), step=100.0, format="%.2f", key="p316_accum")
    p316_current = p316_c2.number_input("Current year E&P (can be negative) ($)", value=float(current_ep), step=100.0, format="%.2f", key="p316_current")
    if dist_mode == "Single Distribution":
        p316_month = p316_c3.number_input("Distribution month (1–12)", min_value=1, max_value=12, value=4, step=1, key="p316_month")
    else:
        p316_month = None  # not used in multi-dist mode

    # §316 E&P availability rules:
    # Case A — Current E&P POSITIVE: stands alone; accumulated deficit does NOT reduce it.
    #           Dividend = min(distribution, current E&P) + min(remaining, max(0, accum E&P))
    # ── helpers ────────────────────────────────────────────────────────────────
    def _ep_step3(current, accum, total_div):
        """Return (ep_next_year, div_from_current, div_from_accum)."""
        d_cur  = min(total_div, max(0.0, current))
        d_acc  = total_div - d_cur
        return current + accum - total_div, d_cur, d_acc

    def _waterfall(dist_amt, ep_avail, basis, lt):
        div  = min(dist_amt, ep_avail)
        rem  = dist_amt - div
        roc  = min(rem, basis)
        cg   = max(0.0, rem - roc)
        return div, roc, cg, basis - roc

    dist_lt = st.checkbox("Stock held > 1 year (LTCG if capital gain applies)", value=True, key="dist_lt")
    cg_label = "LTCG" if dist_lt else "STCG"

    # ══════════════════════════════════════════════════════════════════════════
    if dist_mode == "Single Distribution":
    # ══════════════════════════════════════════════════════════════════════════
        if p316_current >= 0:
            current_ep_avail = p316_current
            accum_ep_avail   = max(0.0, p316_accum)
            ep_avail_at_dist = current_ep_avail + accum_ep_avail
            accum_str = f"${accum_ep_avail:,.0f}" if p316_accum >= 0 else f"$0 (accumulated deficit of ${abs(p316_accum):,.0f} not available)"
            st.markdown(f"""
<div class="irc-note">
<b>Current E&P is positive — accumulated deficit does NOT offset [§316(a)]:</b><br>
Current E&P available (full year, single distribution): <b>${current_ep_avail:,.0f}</b><br>
Accumulated E&P available: <b>{accum_str}</b><br>
<b>Total E&P available: ${ep_avail_at_dist:,.0f}</b>
</div>
""", unsafe_allow_html=True)
        else:
            prorata_frac       = p316_month / 12.0
            current_ep_at_dist = prorata_frac * p316_current
            ep_avail_at_dist   = p316_accum + current_ep_at_dist
            sign_str = f"(${abs(current_ep_at_dist):,.2f})"
            ep_sign  = f"(${abs(ep_avail_at_dist):,.2f})" if ep_avail_at_dist < 0 else f"${ep_avail_at_dist:,.2f}"
            verdict  = "✓ E&P positive at distribution date — distribution is a dividend to this extent." if ep_avail_at_dist > 0 else "⚠️ Net E&P is <b>negative</b> at distribution date — distribution is <b>NOT a dividend</b>."
            st.markdown(f"""
<div class="irc-note">
<b>Current E&P deficit — pro-rated to distribution date [Reg. §1.316-2(b)]:</b><br>
{p316_month}/12 × (${abs(p316_current):,.0f}) = <b>{sign_str}</b><br>
Net E&P = ${p316_accum:,.0f} + {sign_str} = <b>{ep_sign}</b><br><br>
{verdict}
</div>
""", unsafe_allow_html=True)

        ep_avail_clamped = max(0.0, ep_avail_at_dist)

        st.markdown("### Step 2 — §301(c) Shareholder Waterfall")
        da1, da2, da3 = st.columns(3)
        dist_amount = da1.number_input("Distribution Amount ($)", min_value=0.0, step=100.0, format="%.2f", key="dist_amount")
        dist_ep     = da2.number_input("E&P Available ($)", min_value=0.0, step=100.0, format="%.2f", key="dist_ep", value=ep_avail_clamped)
        dist_basis  = da3.number_input("Shareholder's Stock Basis ($)", min_value=0.0, step=100.0, format="%.2f", key="dist_basis")

        div_portion, roc_portion, cg_portion, basis_after = _waterfall(dist_amount, dist_ep, dist_basis, dist_lt)
        remaining = dist_amount - div_portion

        st.markdown("### Results")
        if remaining > 0 and dist_basis == 0:
            st.warning("⚠️ Non-dividend portion of **\\${:,.0f}** — enter shareholder's stock basis above to split between Return of Capital and Capital Gain.".format(remaining))
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("Dividend (taxable)",         f"${div_portion:,.0f}",  "To extent of E&P")
        rc2.metric("Return of Capital",          f"${roc_portion:,.0f}",  "Non-taxable, reduces basis")
        rc3.metric(f"Capital Gain ({cg_label})", f"${cg_portion:,.0f}",   "Excess over basis")
        rc4.metric("Stock Basis After",          f"${basis_after:,.0f}",  "Reduced by ROC")
        st.markdown(f"""
| | Amount |
|---|---|
| Total distribution | ${dist_amount:,.0f} |
| Less: dividend (E&P) | (${div_portion:,.0f}) |
| Non-dividend distribution | ${remaining:,.0f} |
| Less: return of capital (basis) | (${roc_portion:,.0f}) |
| **Capital gain ({cg_label})** | **${cg_portion:,.0f}** |
| Stock basis after distribution | ${basis_after:,.0f} |
""")
        st.markdown("### Step 3 — E&P to Start Next Tax Year")
        ep_next_year, d_cur, d_acc = _ep_step3(p316_current, p316_accum, div_portion)
        col_ep1, col_ep2 = st.columns(2)
        col_ep1.markdown(f"""
| | Current E&P | Accumulated E&P |
|---|---|---|
| Beginning of year | ${p316_current:,.0f} | ${p316_accum:,.0f} |
| − Dividends paid | (${d_cur:,.0f}) | (${d_acc:,.0f}) |
| End of year | ${p316_current - d_cur:,.0f} | ${p316_accum - d_acc:,.0f} |
| **Accumulated E&P next year** | | **${ep_next_year:,.0f}** |
""")
        if ep_next_year < 0:
            col_ep2.markdown(f'<div class="warn-box">⚠️ Ending accumulated E&P: <b>(${abs(ep_next_year):,.0f})</b> deficit.</div>', unsafe_allow_html=True)
        else:
            col_ep2.markdown(f'<div class="safe-harbor">✓ Ending accumulated E&P: <b>${ep_next_year:,.0f}</b></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    else:  # Multiple Distributions
    # ══════════════════════════════════════════════════════════════════════════
        st.markdown("### Step 2 — Enter Distributions (chronological order)")
        n_dist = st.number_input("Number of distributions", min_value=2, max_value=6, value=2, step=1, key="n_dist")

        dist_rows = []
        for i in range(int(n_dist)):
            c1, c2, c3 = st.columns(3)
            mo  = c1.number_input(f"Distribution {i+1} — Month (1–12)", min_value=1, max_value=12, value=3 if i==0 else 11, step=1, key=f"md_month_{i}")
            amt = c2.number_input(f"Distribution {i+1} — Amount ($)", min_value=0.0, step=100.0, format="%.2f", key=f"md_amt_{i}")
            bas = c3.number_input(f"Distribution {i+1} — Shareholder Basis ($)", min_value=0.0, step=100.0, format="%.2f", key=f"md_basis_{i}")
            dist_rows.append({"month": mo, "amount": amt, "basis": bas})

        # Sort chronologically
        dist_rows_sorted = sorted(dist_rows, key=lambda r: r["month"])
        total_dist = sum(r["amount"] for r in dist_rows_sorted)

        st.markdown("### Step 3 — Allocation")

        if p316_current >= 0:
            # Current E&P: pro-rata by amount. Accumulated E&P: chronological.
            st.markdown(f"""
<div class="irc-note">
<b>Current E&P positive:</b> Allocated pro-rata by distribution size (not date).<br>
<b>Accumulated E&P:</b> Applied chronologically — earliest distribution gets first access.
</div>
""", unsafe_allow_html=True)
            accum_remaining = p316_accum
            total_div_all   = 0.0
            rows_out = []
            for r in dist_rows_sorted:
                if total_dist > 0:
                    cur_alloc = (r["amount"] / total_dist) * p316_current
                else:
                    cur_alloc = 0.0
                ep_avail = max(0.0, cur_alloc) + max(0.0, accum_remaining)
                div = min(r["amount"], ep_avail)
                rem = r["amount"] - div
                roc = min(rem, r["basis"])
                cg  = max(0.0, rem - roc)
                # accumulated used = div minus current portion
                acc_used = max(0.0, div - max(0.0, cur_alloc))
                accum_remaining -= acc_used
                total_div_all   += div
                rows_out.append({
                    "month": r["month"], "amount": r["amount"],
                    "cur_alloc": cur_alloc, "acc_used": acc_used,
                    "ep_avail": ep_avail, "div": div,
                    "rem": rem, "roc": roc, "cg": cg,
                    "basis_after": r["basis"] - roc,
                })
        else:
            # Current E&P deficit: pro-rate to each distribution date, reduce accumulated
            st.markdown(f"""
<div class="irc-note">
<b>Current E&P deficit:</b> Pro-rated to each distribution date (month/12). Reduces accumulated E&P chronologically.
</div>
""", unsafe_allow_html=True)
            accum_remaining = p316_accum
            total_div_all   = 0.0
            rows_out = []
            for r in dist_rows_sorted:
                cur_at_date    = (r["month"] / 12.0) * p316_current
                ep_at_date     = accum_remaining + cur_at_date
                ep_avail       = max(0.0, ep_at_date)
                div = min(r["amount"], ep_avail)
                rem = r["amount"] - div
                roc = min(rem, r["basis"])
                cg  = max(0.0, rem - roc)
                accum_remaining -= div   # dividend reduces accumulated
                total_div_all   += div
                rows_out.append({
                    "month": r["month"], "amount": r["amount"],
                    "cur_alloc": cur_at_date, "acc_used": div,
                    "ep_avail": ep_avail, "div": div,
                    "rem": rem, "roc": roc, "cg": cg,
                    "basis_after": r["basis"] - roc,
                })

        # Summary table
        header = "| Dist # | Month | Amount | Current E&P | Accum E&P Used | E&P Avail | **Dividend** | ROC | Cap Gain | Basis After |"
        sep    = "|---|---|---|---|---|---|---|---|---|---|"
        lines  = [header, sep]
        for i, r in enumerate(rows_out):
            lines.append(f"| {i+1} | {r['month']} | ${r['amount']:,.0f} | ${r['cur_alloc']:,.0f} | ${r['acc_used']:,.0f} | ${r['ep_avail']:,.0f} | **${r['div']:,.0f}** | ${r['roc']:,.0f} | ${r['cg']:,.0f} | ${r['basis_after']:,.0f} |")
        lines.append(f"| **Total** | | **${total_dist:,.0f}** | | | | **${total_div_all:,.0f}** | | | |")
        st.markdown("\n".join(lines))

        # ── Per-Shareholder Allocation ─────────────────────────────────────────
        st.markdown("### Step 4 — Per-Shareholder Allocation (optional)")
        n_sh = st.number_input("Number of shareholders", min_value=1, max_value=6, value=2, step=1, key="n_shareholders")
        sh_names = []
        sh_pcts  = []
        sh_bases = []
        sh_cols  = st.columns(int(n_sh))
        for i, col in enumerate(sh_cols):
            name = col.text_input(f"Shareholder {i+1} name", value=f"SH{i+1}", key=f"sh_name_{i}")
            pct  = col.number_input(f"Ownership %", min_value=0.0, max_value=100.0, value=round(100/int(n_sh), 1), step=0.1, key=f"sh_pct_{i}")
            bas  = col.number_input(f"Stock basis ($)", min_value=0.0, step=100.0, format="%.0f", key=f"sh_bas_{i}")
            sh_names.append(name)
            sh_pcts.append(pct / 100.0)
            sh_bases.append(bas)

        total_pct = sum(sh_pcts)
        if abs(total_pct - 1.0) > 0.001:
            st.warning(f"⚠️ Ownership percentages sum to {total_pct*100:.1f}% — should equal 100%.")
        else:
            # Build per-shareholder per-distribution table
            sh_header = "| Distribution | " + " | ".join(sh_names) + " | Total |"
            sh_sep    = "|---| " + " | ".join(["---"] * (len(sh_names) + 1)) + "|"
            sh_lines  = [sh_header, sh_sep]

            sh_total_div = [0.0] * len(sh_names)
            sh_total_roc = [0.0] * len(sh_names)
            sh_total_cg  = [0.0] * len(sh_names)
            sh_bases_rem = list(sh_bases)

            for i, r in enumerate(rows_out):
                # Dividend row
                div_cells = []
                for j, pct in enumerate(sh_pcts):
                    sh_div = r["div"] * pct
                    sh_total_div[j] += sh_div
                    div_cells.append(f"${sh_div:,.0f} div")
                sh_lines.append(f"| D{i+1} (Mo {r['month']}) ${r['amount']:,.0f} | " + " | ".join(div_cells) + f" | ${r['div']:,.0f} |")

                # Non-dividend row if any
                if r["rem"] > 0:
                    nd_cells = []
                    for j, pct in enumerate(sh_pcts):
                        sh_nd  = r["rem"] * pct
                        sh_roc = min(sh_nd, sh_bases_rem[j])
                        sh_cg  = max(0.0, sh_nd - sh_roc)
                        sh_bases_rem[j] -= sh_roc
                        sh_total_roc[j] += sh_roc
                        sh_total_cg[j]  += sh_cg
                        parts = []
                        if sh_roc > 0: parts.append(f"${sh_roc:,.0f} ROC")
                        if sh_cg  > 0: parts.append(f"${sh_cg:,.0f} CG")
                        nd_cells.append(" / ".join(parts) if parts else "$0")
                    sh_lines.append(f"| D{i+1} non-div ${r['rem']:,.0f} | " + " | ".join(nd_cells) + f" | ${r['rem']:,.0f} |")

            # Totals
            total_cells = [f"**${sh_total_div[j]:,.0f} div**" + (f" / ${sh_total_roc[j]:,.0f} ROC" if sh_total_roc[j] else "") + (f" / ${sh_total_cg[j]:,.0f} CG" if sh_total_cg[j] else "") for j in range(len(sh_names))]
            sh_lines.append(f"| **Total** | " + " | ".join(total_cells) + f" | ${total_div_all:,.0f} div |")
            st.markdown("\n".join(sh_lines))

        st.markdown("### Step 5 — E&P to Start Next Tax Year")
        ep_next_year, d_cur, d_acc = _ep_step3(p316_current, p316_accum, total_div_all)
        col_ep1, col_ep2 = st.columns(2)
        col_ep1.markdown(f"""
| | Current E&P | Accumulated E&P |
|---|---|---|
| Beginning of year | ${p316_current:,.0f} | ${p316_accum:,.0f} |
| − Total dividends paid | (${d_cur:,.0f}) | (${d_acc:,.0f}) |
| End of year | ${p316_current - d_cur:,.0f} | ${p316_accum - d_acc:,.0f} |
| **Accumulated E&P next year** | | **${ep_next_year:,.0f}** |
""")
        if ep_next_year < 0:
            col_ep2.markdown(f'<div class="warn-box">⚠️ Ending accumulated E&P: <b>(${abs(ep_next_year):,.0f})</b> deficit.</div>', unsafe_allow_html=True)
        else:
            col_ep2.markdown(f'<div class="safe-harbor">✓ Ending accumulated E&P: <b>${ep_next_year:,.0f}</b></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TOPIC — FORM 1120 INCOME TAX
# ─────────────────────────────────────────────────────────────────────────────
elif topic == "🏛️ CAMT & Estimated Tax":
    st.title("Form 1120 — US Corporate Income Tax")

    f1120_section = st.radio("Section", [
        "CAMT — Corporate Alternative Minimum Tax",
        "Estimated Tax Payments",
    ], horizontal=False, key="f1120_section")

    # ── CAMT ─────────────────────────────────────────────────────────────────
    if f1120_section == "CAMT — Corporate Alternative Minimum Tax":
        st.markdown("## CAMT — Corporate Alternative Minimum Tax §55")
        st.caption("Inflation Reduction Act 2022 · Effective for tax years beginning after 12/31/2022")
        tab_law, tab_calc = st.tabs(["📖 Law & Concepts", "🧮 Calculator"])

        with tab_law:
            irc([
                "<b>What is CAMT?</b> Imposes a <b>15% minimum tax on Adjusted Financial Statement Income (AFSI)</b>. Ensures large profitable corporations pay at least some tax regardless of deductions or credits.",
                "<b>Who is subject?</b> C corporations with average annual AFSI exceeding <b>$1 billion</b> over the prior 3 tax years. Foreign-parented multinational groups: <b>$100 million</b> threshold for the US subgroup.",
                "<b>What is AFSI?</b> Starts with audited GAAP net income, then adjusted for consolidated group members, dividends received, depreciation differences, and partnership income. <b>Not the same as book income.</b>",
                "<b>CAMT liability:</b> Pay the <b>greater of</b> regular tax or CAMT. If CAMT > regular tax, the excess becomes a <b>CAMT credit carryforward</b> — usable in future years to offset regular tax (prevents permanent double taxation).",
                "<b>Credits against CAMT:</b> Foreign tax credits and general business credits allowed against CAMT, subject to limitations.",
            ])
            st.markdown("""
| Scenario | Result |
|---|---|
| Regular tax > Tentative CAMT | Pay regular tax only — no CAMT |
| Tentative CAMT > Regular tax | Pay regular tax + excess CAMT; excess becomes credit carryforward |
""")

        with tab_calc:
            col1, col2 = st.columns(2)
            with col1:
                afsi = st.number_input("Adjusted Financial Statement Income (AFSI) ($)", value=2000000000.0, step=1000000.0, key="camt_afsi", format="%.0f")
                regular_tax = st.number_input("Regular income tax liability (after credits) ($)", min_value=0.0, value=300000000.0, step=1000000.0, key="camt_reg", format="%.0f")
            with col2:
                camt_credits = st.number_input("Credits allowable against CAMT ($)", min_value=0.0, value=0.0, step=1000000.0, key="camt_cred", format="%.0f")
                prior_camt_credit = st.number_input("Prior year CAMT credit carryforward ($)", min_value=0.0, value=0.0, step=1000000.0, key="camt_carryforward", format="%.0f")

            tentative_camt = afsi * 0.15
            camt_after_credits = max(0.0, tentative_camt - camt_credits)
            camt_liability = max(0.0, camt_after_credits - regular_tax)
            total_tax = regular_tax + camt_liability
            new_camt_credit = camt_liability
            camt_credit_used = min(prior_camt_credit, max(0.0, regular_tax - tentative_camt))

            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("AFSI", f"${afsi:,.0f}")
            c2.metric("Tentative CAMT (15%)", f"${tentative_camt:,.0f}")
            c3.metric("Regular Tax", f"${regular_tax:,.0f}")
            c4.metric("Total Tax Due", f"${total_tax:,.0f}", delta=f"+{camt_liability:,.0f} CAMT" if camt_liability > 0 else "No CAMT")

            st.markdown(f"""
| Step | Item | Amount |
|---|---|---|
| 1 | AFSI | ${afsi:,.0f} |
| 2 | Tentative CAMT (15% × AFSI) | ${tentative_camt:,.0f} |
| 3 | Less: Credits against CAMT | (${camt_credits:,.0f}) |
| 4 | CAMT after credits | ${camt_after_credits:,.0f} |
| 5 | Regular tax liability | ${regular_tax:,.0f} |
| 6 | CAMT excess (line 4 − line 5) | ${camt_liability:,.0f} |
| **7** | **Total tax due** | **${total_tax:,.0f}** |
| 8 | New CAMT credit carryforward generated | ${new_camt_credit:,.0f} |
| 9 | Prior CAMT credit usable this year | ${camt_credit_used:,.0f} |
""")
            if camt_liability > 0:
                st.warning(f"CAMT applies — \\${camt_liability:,.0f} additional tax. Generates \\${new_camt_credit:,.0f} CAMT credit carryforward.")
            else:
                st.success(f"No CAMT — regular tax (\\${regular_tax:,.0f}) ≥ tentative CAMT (\\${tentative_camt:,.0f}).")
                if prior_camt_credit > 0:
                    st.info(f"Prior CAMT credit: \\${prior_camt_credit:,.0f} available — \\${camt_credit_used:,.0f} usable this year.")

    # ── ESTIMATED TAX ─────────────────────────────────────────────────────────
    elif f1120_section == "Estimated Tax Payments":
        st.markdown("## Estimated Tax Payments — §6655")
        st.caption("Required for C corporations with expected tax liability of $500 or more")
        tab_law, tab_calc = st.tabs(["📖 Law & Concepts", "🧮 Calculator"])

        with tab_law:
            irc([
                "<b>Who must pay?</b> C corporations with expected annual tax liability of <b>$500 or more</b> must make quarterly estimated payments. Failure triggers underpayment penalty under §6655.",
                "<b>Four payment dates (calendar year):</b> April 15 (Q1) · June 15 (Q2) · September 15 (Q3) · December 15 (Q4). Each = 25% of required annual payment.",
                "<b>Safe harbor — three methods:</b> (1) <b>Current year:</b> pay 100% of current year estimated tax. (2) <b>Prior year:</b> pay 100% of prior year actual tax (only if prior year had positive tax). (3) <b>Annualized income installment:</b> annualize actual YTD income each quarter — useful for seasonal businesses.",
                "<b>Large corporations (taxable income ≥ $1M in any prior 3 years):</b> Prior year safe harbor only applies to Q1. Q2–Q4 must use current year estimates — prevents locking in a low prior-year base.",
                "<b>CAMT interaction:</b> Estimated payments must also cover CAMT liability. Underpayment of CAMT triggers the same §6655 penalty.",
            ])
            st.markdown("""
| Method | Basis | Large Corp Restriction |
|---|---|---|
| Current year | 100% of estimated current tax | None |
| Prior year | 100% of prior year actual tax | Q1 only |
| Annualized | YTD income × annualization factor | None |
""")

        with tab_calc:
            col1, col2 = st.columns(2)
            with col1:
                est_method = st.radio("Safe harbor method", [
                    "Current year (100% of estimated current tax)",
                    "Prior year (100% of prior year tax)",
                    "Annualized income installment",
                ], key="est_method")
                current_year_tax = st.number_input("Estimated current year tax liability ($)", min_value=0.0, value=400000.0, step=1000.0, key="est_current")
            with col2:
                prior_year_tax = st.number_input("Prior year actual tax liability ($)", min_value=0.0, value=350000.0, step=1000.0, key="est_prior")
                is_large_corp = st.checkbox("Large corporation (taxable income ≥ $1M in any prior 3 years)", key="est_large")

            if est_method == "Current year (100% of estimated current tax)":
                required_annual = current_year_tax
                method_note = "100% of estimated current year tax"
            elif est_method == "Prior year (100% of prior year tax)":
                required_annual = prior_year_tax
                method_note = "100% of prior year tax liability"
                if prior_year_tax == 0:
                    st.error("Prior year safe harbor not available if prior year tax was \\$0.")
            else:
                st.info("Annualized income installment: enter actual YTD income per quarter below.")
                col_q = st.columns(4)
                q_incomes = []
                for i, col in enumerate(col_q):
                    with col:
                        inc = st.number_input(f"Q{i+1} YTD income ($)", min_value=0.0, value=0.0, step=1000.0, key=f"est_q{i+1}_inc")
                        q_incomes.append(inc)
                required_annual = current_year_tax
                method_note = "Annualized income installment"

            per_installment = required_annual / 4

            if is_large_corp and est_method == "Prior year (100% of prior year tax)":
                q1 = prior_year_tax / 4
                q2 = q3 = q4 = current_year_tax / 4
                st.warning("Large corporation: prior year safe harbor only for Q1. Q2–Q4 use current year estimate.")
            else:
                q1 = q2 = q3 = q4 = per_installment

            st.divider()
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Q1 — Apr 15", f"${q1:,.0f}")
            p2.metric("Q2 — Jun 15", f"${q2:,.0f}")
            p3.metric("Q3 — Sep 15", f"${q3:,.0f}")
            p4.metric("Q4 — Dec 15", f"${q4:,.0f}")

            st.markdown(f"""
| Installment | Due Date | Amount | Cumulative |
|---|---|---|---|
| Q1 | April 15 | ${q1:,.0f} | ${q1:,.0f} |
| Q2 | June 15 | ${q2:,.0f} | ${q1+q2:,.0f} |
| Q3 | September 15 | ${q3:,.0f} | ${q1+q2+q3:,.0f} |
| Q4 | December 15 | ${q4:,.0f} | ${q1+q2+q3+q4:,.0f} |
| **Total** | | **${q1+q2+q3+q4:,.0f}** | |
""")
            st.divider()
            st.markdown("**Underpayment Check**")
            actual_paid = st.number_input("Total estimated tax actually paid ($)", min_value=0.0, value=required_annual, step=1000.0, key="est_paid")
            shortfall = max(0.0, required_annual - actual_paid)
            if shortfall > 0:
                st.error(f"Underpayment: \\${shortfall:,.0f} — §6655 penalty applies.")
            else:
                overpay = actual_paid - required_annual
                st.success(f"Safe harbor met.{f' Overpayment of \\${overpay:,.0f} — refund or apply to next year.' if overpay > 0 else ''}")

# ─────────────────────────────────────────────────────────────────────────────
# TOPIC — PARTNERSHIPS (FORM 1065)
# ─────────────────────────────────────────────────────────────────────────────
elif active_form == "🤝 Form 1065":
    st.title("Partnerships — Form 1065")

    f1065_section = f1065_nav  # routed from sidebar

    if f1065_nav == "📖 Overview":
        st.markdown("### Overview — Pass-Through Entities")
        irc([
            "<b>What is a pass-through entity?</b> Income is <b>not taxed at the entity level</b>. Instead, owners report and pay tax on their share of the entity's income on their own returns. Two main types:<ul>"
            "<li><b>Partnership</b> — files <b>Form 1065</b> (information return only, no tax paid)</li>"
            "<li><b>S Corporation</b> — files <b>Form 1120S</b>. Legally a C corporation that elected to be taxed like a partnership ('checked the box')</li>"
            "</ul>",
            "<b>Form 1065 — U.S. Return of Partnership Income:</b> The partnership files this return to report total income, deductions, gains, and losses. <b>No tax is paid</b> with this return — purely informational.",
            "<b>Schedule K (inside Form 1065, Page 4):</b> Summarizes all <b>distributive share items</b> at the partnership level — the total that will flow through to all partners combined.",
            "<b>Schedule K-1:</b> Each partner receives their own K-1 — their individual slice of Schedule K. <b>Sum of all K-1s = Schedule K.</b> Partners report K-1 items on their own Form 1040 (individuals) or Form 1120 (corporate partners).",
            "<b>Separately stated items:</b> A partnership cannot pass through a single 'taxable income' number because different types of income and expenses require <b>different tax treatments depending on each partner's situation</b>. The <b>character</b> of each item must be preserved so it can be correctly applied at the partner level. Example: charitable contributions are separately stated because some partners itemize while others take the standard deduction.<br>"
            "Common separately stated items: capital gains/losses, §1231 gains/losses, charitable contributions, §179 deductions, tax-exempt interest, rental income, self-employment income, foreign taxes paid.",
        ])

        st.markdown("### Form 1065 vs. Schedule K-1 — Side by Side")
        irc([
            "<b>Quick reference:</b><br>"
            "<table style='border-collapse:collapse;width:100%'>"
            "<tr style='background:#1B3A6B;color:white'><th style='padding:4px 8px'></th><th style='padding:4px 8px'>Form 1065</th><th style='padding:4px 8px'>Schedule K-1</th></tr>"
            "<tr style='background:#EBF4FF'><td style='padding:4px 8px'><b>Filed by</b></td><td style='padding:4px 8px'>The partnership</td><td style='padding:4px 8px'>Issued by partnership to each partner</td></tr>"
            "<tr><td style='padding:4px 8px'><b>Purpose</b></td><td style='padding:4px 8px'>Report total partnership activity</td><td style='padding:4px 8px'>Each partner's allocable share</td></tr>"
            "<tr style='background:#EBF4FF'><td style='padding:4px 8px'><b>Tax paid?</b></td><td style='padding:4px 8px'>No — informational only</td><td style='padding:4px 8px'>Partner pays tax on their own return</td></tr>"
            "<tr><td style='padding:4px 8px'><b>Schedule K</b></td><td style='padding:4px 8px'>Page 4 — total of all distributive items</td><td style='padding:4px 8px'>Sum of all K-1s = Schedule K</td></tr>"
            "<tr style='background:#EBF4FF'><td style='padding:4px 8px'><b>Income items</b></td><td style='padding:4px 8px'>Ordinary business income + separately stated items</td><td style='padding:4px 8px'>Each partner's pro-rata (or allocated) share of each item</td></tr>"
            "<tr><td style='padding:4px 8px'><b>Who uses it</b></td><td style='padding:4px 8px'>IRS, state tax authorities</td><td style='padding:4px 8px'>Each partner for their individual return</td></tr>"
            "</table>",
        ])

    # defaults
    f65_defaults = {
        "f65_gross_receipts": 0.0, "f65_returns": 0.0, "f65_cogs": 0.0,
        "f65_ordinary_other": 0.0, "f65_farm": 0.0, "f65_4797": 0.0, "f65_other_inc": 0.0,
        "f65_salaries": 0.0, "f65_gp_services": 0.0, "f65_gp_capital": 0.0,
        "f65_repairs": 0.0, "f65_bad_debt": 0.0, "f65_rent": 0.0,
        "f65_taxes": 0.0, "f65_interest": 0.0, "f65_dep": 0.0, "f65_dep_elsewhere": 0.0,
        "f65_depletion": 0.0, "f65_retirement": 0.0, "f65_benefits": 0.0, "f65_other_ded": 0.0,
        "f65_k_rental_re": 0.0, "f65_k_other_rental": 0.0,
        "f65_k_interest": 0.0, "f65_k_ord_div": 0.0, "f65_k_qual_div": 0.0,
        "f65_k_royalties": 0.0, "f65_k_stcg": 0.0, "f65_k_ltcg": 0.0,
        "f65_k_1231": 0.0, "f65_k_other_inc": 0.0,
        "f65_k_179": 0.0, "f65_k_charitable": 0.0, "f65_k_other_ded": 0.0,
        "f65_k_taxexempt": 0.0, "f65_k_nonded": 0.0,
        "f65_k_dist_cash": 0.0, "f65_k_dist_prop": 0.0,
        "f65_n_partners": 2,
    }
    for k, v in f65_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    def f65_row(line, label, key, step=1000.0, allow_neg=False):
        min_v = None if allow_neg else 0.0
        return st.number_input(
            f"[Line {line}] {label}", min_value=min_v,
            step=step, format="%.2f", key=key
        )

    def _f65_ord_income():
        gp = st.session_state.get("f65_gp_services", 0.0) + st.session_state.get("f65_gp_capital", 0.0)
        dep_net = st.session_state.get("f65_dep", 0.0) - st.session_state.get("f65_dep_elsewhere", 0.0)
        inc = (st.session_state.get("f65_gross_receipts", 0.0)
               - st.session_state.get("f65_returns", 0.0)
               - st.session_state.get("f65_cogs", 0.0)
               + st.session_state.get("f65_ordinary_other", 0.0)
               + st.session_state.get("f65_farm", 0.0)
               + st.session_state.get("f65_4797", 0.0)
               + st.session_state.get("f65_other_inc", 0.0))
        ded = (st.session_state.get("f65_salaries", 0.0) + gp
               + st.session_state.get("f65_repairs", 0.0)
               + st.session_state.get("f65_bad_debt", 0.0)
               + st.session_state.get("f65_rent", 0.0)
               + st.session_state.get("f65_taxes", 0.0)
               + st.session_state.get("f65_interest", 0.0)
               + dep_net
               + st.session_state.get("f65_depletion", 0.0)
               + st.session_state.get("f65_retirement", 0.0)
               + st.session_state.get("f65_benefits", 0.0)
               + st.session_state.get("f65_other_ded", 0.0))
        return inc - ded

    # PAGE: INCOME
    if f1065_section == "📥 Income (Lines 1–8)":
        st.markdown("## Form 1065 — Income")
        irc([
            "<b>Form 1065 income section:</b> Captures the partnership's gross business activity. Line 22 (ordinary business income) flows to Schedule K line 1 — the non-separately-stated income that has the same character for all partners.",
            "<b>Separately stated items</b> (capital gains, §1231, tax-exempt interest, charitable contributions, §179) are NOT included here — they go directly to Schedule K to preserve their character at the partner level.",
        ])

        gr = f65_row("1a", "Gross receipts or sales", "f65_gross_receipts", step=10000.0)
        ra = f65_row("1b", "Returns and allowances", "f65_returns")
        net_sales = gr - ra
        st.markdown(f"**Line 1c — Net sales: ${net_sales:,.0f}**")
        cogs = f65_row("2", "Cost of goods sold (Form 1125-A)", "f65_cogs", step=10000.0)
        gross_profit = net_sales - cogs
        st.markdown(f"**Line 3 — Gross profit: ${gross_profit:,.0f}**")
        st.divider()
        ord_other = f65_row("4", "Ordinary income from other partnerships/estates/trusts", "f65_ordinary_other", allow_neg=True)
        farm = f65_row("5", "Net farm profit (loss)", "f65_farm", allow_neg=True)
        g4797 = f65_row("6", "Net gain (loss) from Form 4797 Part II", "f65_4797", allow_neg=True)
        other_inc = f65_row("7", "Other income (loss)", "f65_other_inc", allow_neg=True)
        total_inc = gross_profit + ord_other + farm + g4797 + other_inc
        st.markdown(f"### Line 8 — Total Income (Loss): ${total_inc:,.0f}")
        irc([
            "<b>Line 4:</b> Ordinary income from lower-tier partnerships flows here. Capital gains and other separately stated items from the lower tier pass through Schedule K directly.",
            "<b>Line 6 — Form 4797:</b> Ordinary §1245 recapture goes here; net §1231 gain/loss goes to Schedule K line 10.",
        ])

    # PAGE: DEDUCTIONS
    elif f1065_section == "📤 Deductions (Lines 9–22)":
        st.markdown("## Form 1065 — Deductions")
        irc([
            "<b>Non-separately-stated deductions only.</b> §179 expensing and charitable contributions go to Schedule K, not here.",
            "<b>Guaranteed payments [§707(c)]:</b> Payments to partners for services or capital, determined without regard to partnership income. Deductible by the partnership here; ordinary income to the partner on their K-1 (Schedule K line 4).",
            "<b>Salaries (line 9):</b> Employee wages only — not partner draws or guaranteed payments.",
        ])

        f65_row("9", "Salaries & wages (excl. partners, less employment credits)", "f65_salaries", step=10000.0)
        gp_s = f65_row("10a", "Guaranteed payments — services", "f65_gp_services")
        gp_c = f65_row("10b", "Guaranteed payments — capital", "f65_gp_capital")
        st.markdown(f"*Total guaranteed payments: ${gp_s + gp_c:,.0f}*")
        f65_row("11", "Repairs and maintenance", "f65_repairs")
        f65_row("12", "Bad debts", "f65_bad_debt")
        f65_row("13", "Rent", "f65_rent")
        f65_row("14", "Taxes and licenses", "f65_taxes")
        f65_row("15", "Interest", "f65_interest")
        dep = f65_row("16a", "Depreciation (Form 4562)", "f65_dep")
        dep_e = f65_row("16b", "Less: depreciation on Schedule A/elsewhere", "f65_dep_elsewhere")
        st.markdown(f"*Line 16c — Net depreciation: ${dep - dep_e:,.0f}*")
        f65_row("17", "Depletion (not oil and gas)", "f65_depletion")
        f65_row("18", "Retirement plans, etc.", "f65_retirement")
        f65_row("19", "Employee benefit programs", "f65_benefits")
        f65_row("20", "Other deductions", "f65_other_ded")

        ord_income = _f65_ord_income()
        if ord_income >= 0:
            st.success(f"**Line 22 — Ordinary Business Income: \\${ord_income:,.0f}**  ->  flows to Schedule K Line 1")
        else:
            st.error(f"**Line 22 — Ordinary Business Loss: (\\${abs(ord_income):,.0f})**  ->  flows to Schedule K Line 1")

    # PAGE: SCHEDULE K
    elif f1065_section == "📋 Schedule K — Distributive Share Items":
        st.markdown("## Schedule K — Partners' Distributive Share Items (Total)")
        irc([
            "<b>Schedule K</b> aggregates ALL items flowing to partners. Line 1 = ordinary business income from page 1 line 22. All other lines are separately stated items preserving their character at the partner level.",
            "<b>Why separately stated?</b> Each item may be subject to different limitations — §469 passive activity rules, §1211 capital loss limits, charitable deduction floors, AMT adjustments, and self-employment tax — depending on the individual partner.",
        ])

        ord_income = _f65_ord_income()
        st.markdown(f"**Line 1 — Ordinary business income (from line 22): ${ord_income:,.0f}**")
        st.divider()

        st.markdown("#### Income / Loss Items")
        f65_row("2", "Net rental real estate income (loss)", "f65_k_rental_re", allow_neg=True)
        f65_row("3c", "Other net rental income (loss)", "f65_k_other_rental", allow_neg=True)
        gp_total = st.session_state.get("f65_gp_services", 0.0) + st.session_state.get("f65_gp_capital", 0.0)
        st.markdown(f"*Line 4 — Guaranteed payments (carried from deductions): ${gp_total:,.0f}*")
        f65_row("5", "Interest income", "f65_k_interest")
        f65_row("6a", "Ordinary dividends", "f65_k_ord_div")
        f65_row("6b", "Qualified dividends", "f65_k_qual_div")
        f65_row("7", "Royalties", "f65_k_royalties")
        f65_row("8", "Net short-term capital gain (loss)", "f65_k_stcg", allow_neg=True)
        f65_row("9a", "Net long-term capital gain (loss)", "f65_k_ltcg", allow_neg=True)
        f65_row("10", "Net §1231 gain (loss)", "f65_k_1231", allow_neg=True)
        f65_row("11", "Other income (loss)", "f65_k_other_inc", allow_neg=True)

        st.markdown("#### Deduction Items")
        f65_row("12", "§179 deduction", "f65_k_179")
        f65_row("13a", "Charitable contributions", "f65_k_charitable")
        f65_row("13d", "Other deductions", "f65_k_other_ded")

        st.markdown("#### Other Information")
        f65_row("18a", "Tax-exempt income", "f65_k_taxexempt")
        f65_row("18b", "Nondeductible expenses", "f65_k_nonded")
        f65_row("19a", "Distributions — cash & marketable securities", "f65_k_dist_cash")
        f65_row("19b", "Distributions — other property (FMV)", "f65_k_dist_prop")

        st.divider()
        st.markdown("**Schedule K Total Summary**")
        k_items = {
            "Ordinary business income": ord_income,
            "Net rental real estate": st.session_state.get("f65_k_rental_re", 0.0),
            "Other rental": st.session_state.get("f65_k_other_rental", 0.0),
            "Guaranteed payments": gp_total,
            "Interest income": st.session_state.get("f65_k_interest", 0.0),
            "Ordinary dividends": st.session_state.get("f65_k_ord_div", 0.0),
            "Qualified dividends": st.session_state.get("f65_k_qual_div", 0.0),
            "Royalties": st.session_state.get("f65_k_royalties", 0.0),
            "Net STCG (loss)": st.session_state.get("f65_k_stcg", 0.0),
            "Net LTCG (loss)": st.session_state.get("f65_k_ltcg", 0.0),
            "Net §1231 gain (loss)": st.session_state.get("f65_k_1231", 0.0),
            "Other income": st.session_state.get("f65_k_other_inc", 0.0),
            "§179 deduction": -st.session_state.get("f65_k_179", 0.0),
            "Charitable contributions": -st.session_state.get("f65_k_charitable", 0.0),
            "Tax-exempt income": st.session_state.get("f65_k_taxexempt", 0.0),
            "Nondeductible expenses": st.session_state.get("f65_k_nonded", 0.0),
        }
        for label, amt in k_items.items():
            if amt != 0:
                st.markdown(f"- {label}: **${amt:,.0f}**")

    # PAGE: K-1
    elif f1065_section == "🧾 Schedule K-1 — Per Partner Summary":
        st.markdown("## Schedule K-1 — Per Partner Summary")
        irc([
            "<b>Schedule K-1:</b> Each partner receives one K-1 showing their allocable share of every Schedule K item. The sum of all K-1s equals Schedule K. Partners report K-1 amounts on their own Form 1040 or Form 1120.",
            "<b>Sharing ratios:</b> By default, items are allocated by profit/loss sharing %. Special allocations are allowed if they have substantial economic effect under §704(b).",
        ])

        n_partners = int(st.number_input("Number of partners", min_value=1, max_value=10, value=2, key="f65_n_partners"))
        names = []
        ratios = []
        ratio_cols = st.columns(n_partners)
        for i in range(n_partners):
            with ratio_cols[i]:
                name = st.text_input(f"Partner {i+1}", value=f"Partner {chr(65+i)}", key=f"f65_pname_{i}")
                pct = st.number_input("Share %", min_value=0.0, max_value=100.0,
                                      value=round(100.0/n_partners, 1), step=0.1, key=f"f65_pct_{i}")
                names.append(name)
                ratios.append(pct / 100.0)

        total_pct = sum(ratios)
        if abs(total_pct - 1.0) > 0.005:
            st.warning(f"Sharing ratios sum to {total_pct*100:.1f}% — should equal 100%.")

        ord_income = _f65_ord_income()
        gp_total = st.session_state.get("f65_gp_services", 0.0) + st.session_state.get("f65_gp_capital", 0.0)

        k_schedule = {
            "1 — Ordinary business income (loss)": ord_income,
            "2 — Net rental real estate income (loss)": st.session_state.get("f65_k_rental_re", 0.0),
            "3 — Other rental income (loss)": st.session_state.get("f65_k_other_rental", 0.0),
            "4 — Guaranteed payments (total)": gp_total,
            "5 — Interest income": st.session_state.get("f65_k_interest", 0.0),
            "6a — Ordinary dividends": st.session_state.get("f65_k_ord_div", 0.0),
            "6b — Qualified dividends": st.session_state.get("f65_k_qual_div", 0.0),
            "7 — Royalties": st.session_state.get("f65_k_royalties", 0.0),
            "8 — Net STCG (loss)": st.session_state.get("f65_k_stcg", 0.0),
            "9a — Net LTCG (loss)": st.session_state.get("f65_k_ltcg", 0.0),
            "10 — Net §1231 gain (loss)": st.session_state.get("f65_k_1231", 0.0),
            "12 — §179 deduction": st.session_state.get("f65_k_179", 0.0),
            "13a — Charitable contributions": st.session_state.get("f65_k_charitable", 0.0),
            "18a — Tax-exempt income": st.session_state.get("f65_k_taxexempt", 0.0),
            "18b — Nondeductible expenses": st.session_state.get("f65_k_nonded", 0.0),
            "19a — Distributions (cash)": st.session_state.get("f65_k_dist_cash", 0.0),
            "19b — Distributions (property)": st.session_state.get("f65_k_dist_prop", 0.0),
        }

        header = "| K-1 Line |" + "".join(f" {n} |" for n in names)
        sep = "|---|" + "---|" * n_partners
        rows = [header, sep]
        for item, total in k_schedule.items():
            if total != 0:
                cells = "".join(f" ${total * r:,.0f} |" for r in ratios)
                rows.append(f"| {item} |{cells}")
        st.markdown("\n".join(rows))
        st.caption("Each column = one partner Schedule K-1. Character of each item is preserved for the partner own return.")



# ─────────────────────────────────────────────────────────────────────────────
# TOPIC — QBI DEDUCTION §199A
# ─────────────────────────────────────────────────────────────────────────────
elif topic == "✂️ QBI Deduction — §199A":
    st.title("Qualified Business Income Deduction — §199A")

    irc([
        "<b>§199A — Overview:</b> Provides a deduction of up to <b>20% of qualified business income (QBI)</b> for <b>non-corporate taxpayers</b> (individuals, trusts, estates). Applies to income from <b>sole proprietorships, partnerships, and S corporations</b>. Does NOT apply to C corporations or wages/salary income.",
        "<b>Basic deduction:</b> 20% of QBI, limited to 20% of <b>modified taxable income</b> (taxable income minus net capital gains / qualified dividends). The taxable income limit prevents the deduction from exceeding the individual's regular tax base.",
        "<b>W-2 wage / capital limitation</b> applies above the income threshold — the deduction cannot exceed the GREATER of: (1) 50% of W-2 wages paid by the business, OR (2) 25% of W-2 wages + 2.5% of unadjusted basis of qualified property (immediately after acquisition).",
        "<b>SSTB phase-out:</b> Specified Service Trade or Business (SSTB) income phases out above the threshold. SSTBs include: health, law, accounting, actuarial science, performing arts, consulting, athletics, financial services, brokerage. Engineering and architecture are <b>excluded</b> from SSTB.",
        "<b>2024 thresholds:</b> $191,950 (single) / $383,900 (MFJ). Phase-out range: $50,000 (single) / $100,000 (MFJ). Above the top of the phase-out, SSTB income = $0 QBI and wage limitation fully applies to non-SSTBs.",
    ])

    st.markdown("### §199A QBI Deduction Calculator")

    col1, col2 = st.columns(2)
    with col1:
        filing_status = st.radio("Filing status", ["Single", "Married Filing Jointly"], horizontal=True, key="qbi_filing")
        taxable_income = st.number_input("Taxable income (before §199A deduction) ($)", min_value=0.0, value=200000.0, step=1000.0, key="qbi_ti")
        net_cap_gains = st.number_input("Net capital gains + qualified dividends ($)", min_value=0.0, value=0.0, step=1000.0, key="qbi_cg")
    with col2:
        is_sstb = st.checkbox("Is this a Specified Service Trade or Business (SSTB)?", key="qbi_sstb")
        qbi = st.number_input("Qualified Business Income (QBI) from the business ($)", min_value=0.0, value=150000.0, step=1000.0, key="qbi_qbi")
        w2_wages = st.number_input("W-2 wages paid by the business ($)", min_value=0.0, value=50000.0, step=1000.0, key="qbi_w2")
        unadj_basis = st.number_input("Unadjusted basis of qualified property ($)", min_value=0.0, value=0.0, step=1000.0, key="qbi_basis")

    # Thresholds
    if filing_status == "Single":
        threshold_low = 191950.0
        phase_range = 50000.0
    else:
        threshold_low = 383900.0
        phase_range = 100000.0
    threshold_high = threshold_low + phase_range

    modified_ti = max(0.0, taxable_income - net_cap_gains)

    # Phase-in fraction for limitations
    if taxable_income <= threshold_low:
        phase_frac = 0.0        # no limitation applies
    elif taxable_income >= threshold_high:
        phase_frac = 1.0        # full limitation applies
    else:
        phase_frac = (taxable_income - threshold_low) / phase_range

    # SSTB: phase out QBI above threshold
    if is_sstb:
        if taxable_income >= threshold_high:
            sstb_qbi = 0.0
        elif taxable_income > threshold_low:
            sstb_qbi = qbi * (1.0 - phase_frac)
        else:
            sstb_qbi = qbi
        effective_qbi = sstb_qbi
        sstb_w2 = w2_wages * (1.0 - phase_frac) if taxable_income > threshold_low else w2_wages
        sstb_basis = unadj_basis * (1.0 - phase_frac) if taxable_income > threshold_low else unadj_basis
    else:
        effective_qbi = qbi
        sstb_w2 = w2_wages
        sstb_basis = unadj_basis

    # Step 1: 20% of QBI
    deduction_before_limits = 0.20 * effective_qbi

    # Step 2: W-2 / property wage limitation
    w2_limit_a = 0.50 * sstb_w2
    w2_limit_b = 0.25 * sstb_w2 + 0.025 * sstb_basis
    wage_cap = max(w2_limit_a, w2_limit_b)

    # Apply wage cap — phase in above threshold
    if phase_frac == 0.0:
        deduction_after_wage = deduction_before_limits
        wage_cap_applied = False
    elif phase_frac == 1.0:
        deduction_after_wage = min(deduction_before_limits, wage_cap)
        wage_cap_applied = True
    else:
        # Phase in the wage limitation
        uncapped = deduction_before_limits
        capped = min(deduction_before_limits, wage_cap)
        deduction_after_wage = uncapped - phase_frac * (uncapped - capped)
        wage_cap_applied = (phase_frac > 0)

    # Step 3: 20% of modified taxable income cap
    ti_cap = 0.20 * modified_ti
    final_deduction = min(deduction_after_wage, ti_cap)

    st.divider()
    st.markdown("### Results")

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Effective QBI", f"${effective_qbi:,.0f}",
               delta=f"SSTB phase-out: ({qbi - effective_qbi:,.0f})" if is_sstb and effective_qbi < qbi else None)
    mc2.metric("20% of QBI", f"${deduction_before_limits:,.0f}")
    mc3.metric("§199A Deduction", f"${final_deduction:,.0f}")

    st.markdown("**Step-by-step:**")
    st.markdown(f"1. Taxable income: ${taxable_income:,.0f} | Threshold: ${threshold_low:,.0f}–${threshold_high:,.0f} | Phase fraction: {phase_frac:.1%}")
    if is_sstb:
        if taxable_income >= threshold_high:
            st.error("SSTB fully phased out — QBI = \\$0. No §199A deduction available.")
        elif phase_frac > 0:
            st.warning(f"SSTB partial phase-out: effective QBI reduced to \\${effective_qbi:,.0f} ({(1-phase_frac):.1%} of \\${qbi:,.0f})")
    st.markdown(f"2. 20% × effective QBI ${effective_qbi:,.0f} = **${deduction_before_limits:,.0f}**")
    if wage_cap_applied:
        st.markdown(f"3. W-2 wage limitation: 50% of W-2 = ${w2_limit_a:,.0f} | 25% W-2 + 2.5% basis = ${w2_limit_b:,.0f} → cap = **${wage_cap:,.0f}** (phase-in {phase_frac:.1%})")
        st.markdown(f"   After wage limitation: **${deduction_after_wage:,.0f}**")
    else:
        st.markdown(f"3. W-2 wage limitation: not applicable (taxable income at or below threshold)")
    st.markdown(f"4. 20% × modified taxable income ${modified_ti:,.0f} = **${ti_cap:,.0f}** (overall cap)")
    if final_deduction == ti_cap and ti_cap < deduction_after_wage:
        st.warning(f"Taxable income cap is binding — deduction limited to \\${ti_cap:,.0f}")
    if final_deduction > 0:
        st.success(f"**§199A Deduction: \\${final_deduction:,.0f}** | Taxable income after deduction: \\${taxable_income - final_deduction:,.0f}")
    else:
        st.error("No §199A deduction available.")

    st.divider()
    st.markdown("**SSTB Reference**")
    irc([
        "<b>Specified Service Trades or Businesses (SSTBs):</b> Health, law, accounting, actuarial science, performing arts, consulting, athletics, financial services, brokerage, and any trade/business where the principal asset is the reputation or skill of employees/owners. <b>Engineering and architecture are NOT SSTBs.</b>",
        "<b>Non-SSTB examples:</b> Manufacturing, retail, restaurants, real estate (non-broker), engineering, architecture, technology (product-based). These qualify fully for §199A with no SSTB phase-out.",
    ])
