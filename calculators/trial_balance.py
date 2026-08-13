"""Read a trial balance out of the file an accountant actually sends.

No two exports look alike. Some give one signed balance column, some give separate debit
and credit columns, some give beginning and ending balances for the balance sheet. The
headers are never spelled the same way twice. So the reader recognises columns by what
they mean rather than by an exact name, and reports what it decided rather than guessing
silently — a misread column is a wrong return.

Everything leaves here debit-positive, which is the convention `tax_lines` expects.
"""

import io
import re

import pandas as pd

ALIASES = {
    "account": ["account", "account no", "account number", "acct", "acct no", "gl",
                "gl account", "code no", "account code"],
    "name":    ["name", "account name", "description", "account description", "title"],
    "code":    ["tax code", "tax line", "tax_code", "taxline", "code", "mapping",
                "mapping code", "tax mapping"],
    "beginning": ["beginning", "beginning balance", "begin", "opening", "opening balance",
                  "prior year", "py", "bop"],
    "ending":  ["ending", "ending balance", "end", "closing", "closing balance", "balance",
                "current year", "cy", "eop", "amount"],
    "debit":   ["debit", "dr", "debits"],
    "credit":  ["credit", "cr", "credits"],
}


def _norm(h):
    return re.sub(r"[^a-z0-9 ]", " ", str(h).strip().lower()).replace("_", " ").strip()


def detect_columns(headers):
    """Match each header to the meaning it carries.

    Aliases are matched whole, not as substrings: "Account Code" is the account number and
    "Tax Code" is the tax line, and a substring match on "code" would confuse the two. A
    header that has already been claimed cannot be claimed again."""
    found, taken = {}, set()
    normed = [(h, _norm(h)) for h in headers]
    for field in ["account", "name", "code", "beginning", "ending", "debit", "credit"]:
        for h, n in normed:
            if h in taken:
                continue
            if n in ALIASES[field]:
                found[field] = h
                taken.add(h)
                break
    return found


def _text(v):
    """An empty spreadsheet cell arrives as NaN, and str(NaN) is the word "nan" — which
    would otherwise become an account named nan carrying a tax code named nan."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _number(v):
    """Accounting exports carry thousands separators, currency symbols, and negatives in
    parentheses. Blank means zero."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(",", "").replace("$", "").replace("(", "-").replace(")", "")
    if not t or t == "-":
        return 0.0
    return float(t)


def read_trial_balance(data, filename):
    """Parse an uploaded CSV or Excel file into trial balance rows.

    Returns the rows, the column assignment that was used, and any warnings. The caller
    shows the assignment back to the user: the reader should be checkable, not trusted."""
    if filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        df = pd.read_excel(io.BytesIO(data))
    else:
        df = pd.read_csv(io.BytesIO(data))
    df.columns = [str(c) for c in df.columns]

    cols = detect_columns(df.columns)
    warnings = []
    if "name" not in cols and "account" not in cols:
        return [], cols, ["No account number or account name column was recognised."]

    has_dc = "debit" in cols and "credit" in cols
    if not has_dc and "ending" not in cols:
        return [], cols, ["No balance column was recognised. Expected either an ending "
                          "balance column, or separate debit and credit columns."]
    if "code" not in cols:
        warnings.append("No tax code column was found — every account will need mapping "
                        "by hand.")

    rows = []
    for _, r in df.iterrows():
        if has_dc:
            ending = _number(r[cols["debit"]]) - _number(r[cols["credit"]])
        else:
            ending = _number(r[cols["ending"]])
        beginning = _number(r[cols["beginning"]]) if "beginning" in cols else 0.0
        account = _text(r[cols["account"]]) if "account" in cols else ""
        name = _text(r[cols["name"]]) if "name" in cols else ""
        if not account and not name:
            continue
        rows.append({"account": account, "name": name,
                     "code": _text(r[cols["code"]]) if "code" in cols else "",
                     "beginning": beginning, "ending": ending})

    if "beginning" not in cols:
        warnings.append("No beginning balance column was found — Schedule L will only "
                        "have an end-of-year column.")
    return rows, cols, warnings
