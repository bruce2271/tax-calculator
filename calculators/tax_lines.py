"""Chart of accounts to tax return line mapping.

Real preparers do not type a return line by line. They import a trial balance and give
every account a tax line assignment — the same idea QuickBooks calls Tax Line Mapping and
professional packages call a tax code. This is that table.

Two decisions worth stating.

**Codes are anchored to the form.** `C-12` is Form 1120 page 1 line 12, `P-9` is Form 1065
line 9, `L-2a` is Schedule L accounts receivable. The code documents itself, and there is
no second taxonomy to keep in step with the forms.

**Every code names the field it feeds.** Mapping an account to `C-12` writes to the same
place the Deductions page writes to, so an imported figure and a typed one are the same
figure — there is no parallel set of imported values that can drift.

**Sections.** `income`, `cogs` and `deduction` are the income statement; `asset`,
`liability` and `equity` are the balance sheet; `distribution` is neither — it moves equity
without passing through the result for the year.

**Signs.** A trial balance is debits and credits; a return wants positive numbers in both
the income and the deduction columns. `sign` is the multiplier that turns a debit-positive
balance into the figure the form expects: +1 for accounts that normally carry a debit
(expenses, assets), -1 for those that normally carry a credit (revenue, liabilities,
equity). Getting this wrong is the most common import error, so the import shows the
balance and the converted figure side by side.
"""

from . import schedule_l

# code, form, line, label, session key, sign, section
TAX_LINES = [
    # ── Form 1120, page 1 — income ───────────────────────────────────────────
    ("C-1a",  "1120", "1a",  "Gross receipts or sales",        "gross_receipts_book",   -1, "income"),
    ("C-1b",  "1120", "1b",  "Returns and allowances",         "returns_allowances_book", 1, "income"),
    ("C-4",   "1120", "4",   "Dividends",                      "dividends_book",        -1, "income"),
    ("C-5",   "1120", "5",   "Interest income",                "interest_income_book",  -1, "income"),
    ("C-6",   "1120", "6",   "Gross rents",                    "gross_rents_book",      -1, "income"),
    ("C-7",   "1120", "7",   "Gross royalties",                "gross_royalties_book",  -1, "income"),
    ("C-10",  "1120", "10",  "Other income",                   "other_income_book",     -1, "income"),

    # ── Form 1125-A — cost of goods sold ─────────────────────────────────────
    ("A-1",   "1125-A", "1", "Beginning inventory",            "f1125a_beg_inv",         1, "cogs"),
    ("A-2",   "1125-A", "2", "Purchases",                      "f1125a_purchases",       1, "cogs"),
    ("A-3",   "1125-A", "3", "Cost of labor",                  "f1125a_labor",           1, "cogs"),
    ("A-5",   "1125-A", "5", "Other costs",                    "f1125a_other",           1, "cogs"),
    # Ending inventory relieves cost of goods sold, so it sits in the ledger as a credit
    # while Form 1125-A line 7 prints it positive and subtracts it there.
    ("A-7",   "1125-A", "7", "Ending inventory",               "f1125a_end_inv",        -1, "cogs"),

    # ── Form 1120, page 1 — deductions ───────────────────────────────────────
    ("C-12",  "1120", "12",  "Compensation of officers",       "comp_officers_book",     1, "deduction"),
    ("C-13",  "1120", "13",  "Salaries and wages",             "salaries_book",          1, "deduction"),
    ("C-14",  "1120", "14",  "Repairs and maintenance",        "repairs_book",           1, "deduction"),
    ("C-15",  "1120", "15",  "Bad debts — book reserve",       "bad_debt_book_reserve",  1, "deduction"),
    ("C-16",  "1120", "16",  "Rents",                          "rents_book",             1, "deduction"),
    ("C-17",  "1120", "17",  "Taxes and licenses",             "taxes_book",             1, "deduction"),
    ("C-18",  "1120", "18",  "Interest expense",               "interest_book",          1, "deduction"),
    ("C-19",  "1120", "19",  "Charitable contributions",       "charitable_book",        1, "deduction"),
    ("C-20",  "1120", "20",  "Depreciation — book",            "book_depreciation",      1, "deduction"),
    ("C-22",  "1120", "22",  "Advertising",                    "advertising_book",       1, "deduction"),
    ("C-23",  "1120", "23",  "Pension and profit-sharing",     "pension_book",           1, "deduction"),
    ("C-24",  "1120", "24",  "Employee benefit programs",      "benefits_book",          1, "deduction"),
    ("C-26",  "1120", "26",  "Other deductions",               "other_ded_book",         1, "deduction"),
    # Line 26 breaks out further, because each piece meets a different rule.
    ("C-26t", "1120", "26",  "Travel — §274(d)",               "travel_book",            1, "deduction"),
    ("C-26m", "1120", "26",  "Meals — §274(n), 50% allowed",   "meals_book",             1, "deduction"),
    ("C-26e", "1120", "26",  "Entertainment — §274(a), none",  "entertainment_book",     1, "deduction"),
    ("C-26f", "1120", "26",  "Fines and penalties — §162(f)",  "fines_book",             1, "deduction"),
    ("C-26l", "1120", "26",  "Lobbying — §162(e)",             "lobbying_book",          1, "deduction"),
    ("C-26b", "1120", "26",  "Bribes and kickbacks — §162(c)", "bribes_book",            1, "deduction"),
    ("C-26p", "1120", "26",  "Political contributions — §276", "political_book",         1, "deduction"),
    ("C-26k", "1120", "26",  "Key employee insurance — §264",  "key_ins_book",           1, "deduction"),
    ("C-26x", "1120", "26",  "Other permanently non-deductible", "other_perm_book",      1, "deduction"),
    ("C-26r", "1120", "26",  "Research — §174",                "s174_book",              1, "deduction"),
    ("C-26a", "1120", "26",  "Amortisation — §197 and impairment", "intang_book",        1, "deduction"),
    ("C-26s", "1120", "26",  "Stock compensation — ASC 718",   "sbc_book",               1, "deduction"),
    ("C-26z", "1120", "26",  "Lease cost — ASC 842",           "lease_book",             1, "deduction"),

    # ── Form 1120, Schedule M-2 — distributions ──────────────────────────────
    # A ledger usually carries dividends declared in its own account rather than debiting
    # retained earnings directly. It closes to equity, so it belongs on neither the income
    # statement nor the balance sheet.
    ("M-5a",  "Sch M-2", "5a", "Distributions — cash",          "m2_dist_cash",           1, "distribution"),
    ("M-5b",  "Sch M-2", "5b", "Distributions — stock",         "m2_dist_stock",          1, "distribution"),
    ("M-5c",  "Sch M-2", "5c", "Distributions — property",      "m2_dist_prop",           1, "distribution"),

    # ── Form 1065, page 1 ────────────────────────────────────────────────────
    ("P-1a",  "1065", "1a",  "Gross receipts or sales",        "f65_gross_receipts",    -1, "income"),
    ("P-1b",  "1065", "1b",  "Returns and allowances",         "f65_returns",            1, "income"),
    ("P-2",   "1065", "2",   "Cost of goods sold",             "f65_cogs",               1, "income"),
    ("P-4",   "1065", "4",   "Income from other partnerships", "f65_ordinary_other",    -1, "income"),
    ("P-5",   "1065", "5",   "Net farm profit (loss)",         "f65_farm",              -1, "income"),
    ("P-7",   "1065", "7",   "Other income (loss)",            "f65_other_inc",         -1, "income"),
    ("P-9",   "1065", "9",   "Salaries and wages",             "f65_salaries",           1, "deduction"),
    ("P-10a", "1065", "10a", "Guaranteed payments — services", "f65_gp_services",        1, "deduction"),
    ("P-10b", "1065", "10b", "Guaranteed payments — capital",  "f65_gp_capital",         1, "deduction"),
    ("P-11",  "1065", "11",  "Repairs and maintenance",        "f65_repairs",            1, "deduction"),
    ("P-12",  "1065", "12",  "Bad debts",                      "f65_bad_debt",           1, "deduction"),
    ("P-13",  "1065", "13",  "Rent",                           "f65_rent",               1, "deduction"),
    ("P-14",  "1065", "14",  "Taxes and licenses",             "f65_taxes",              1, "deduction"),
    ("P-15",  "1065", "15",  "Interest",                       "f65_interest",           1, "deduction"),
    ("P-16a", "1065", "16a", "Depreciation",                   "f65_dep",                1, "deduction"),
    ("P-17",  "1065", "17",  "Depletion",                      "f65_depletion",          1, "deduction"),
    ("P-18",  "1065", "18",  "Retirement plans",               "f65_retirement",         1, "deduction"),
    ("P-19",  "1065", "19",  "Employee benefit programs",      "f65_benefits",           1, "deduction"),
    ("P-20",  "1065", "20",  "Other deductions",               "f65_other_ded",          1, "deduction"),

    # ── Schedule K (Form 1065) — separately stated ───────────────────────────
    ("K-5",   "Sch K", "5",   "Interest income",               "f65_k_interest",        -1, "income"),
    ("K-6a",  "Sch K", "6a",  "Ordinary dividends",            "f65_k_ord_div",         -1, "income"),
    ("K-7",   "Sch K", "7",   "Royalties",                     "f65_k_royalties",       -1, "income"),
    ("K-13a", "Sch K", "13a", "Contributions",                 "f65_k_charitable",       1, "deduction"),
    ("K-18a", "Sch K", "18a", "Tax-exempt interest income",    "f65_k_taxexempt",       -1, "income"),
    ("K-18c", "Sch K", "18c", "Nondeductible expenses",        "f65_k_nonded",           1, "deduction"),
    # A distribution moves equity; it is not an expense. Section "distribution" keeps it
    # out of book income — coding it as a deduction understated the year's result by the
    # whole distribution and left the balance sheet unable to close.
    ("K-19a", "Sch K", "19a", "Distributions — cash",          "f65_k_dist_cash",        1, "distribution"),
    ("K-19b", "Sch K", "19b", "Distributions — property",      "f65_k_dist_prop",        1, "distribution"),
]

# The balance sheet rows are generated from the Schedule L specification rather than
# retyped here. One source of truth: a line added to the form appears in the mapping table
# automatically, and the two can never drift apart. Assets carry a debit balance, and
# everything on the other side carries a credit; the contra lines are the exception, and
# they flip because the form prints them positive and subtracts them.
for _form, _label in (("1120", "Sch L"), ("1065", "Sch L (1065)")):
    for _c, _ln, _lab, _key, _sec, _contra in schedule_l.spec(_form):
        _sign = 1 if _sec == "asset" else -1
        if _contra:
            _sign = -_sign
        TAX_LINES.append((_c, _label, _ln, _lab, _key, _sign, _sec))

BY_CODE = {row[0]: row for row in TAX_LINES}
BALANCE_SHEET_SECTIONS = {"asset", "liability", "equity"}

# Lines the form prints positive and then subtracts. They belong to their section but
# reduce it, so a section total has to know about them — summing the column would
# double the contra instead of removing it.
CONTRA_CODES = ({"A-7", "C-1b", "P-1b"}
                | {r[0] for f in ("1120", "1065") for r in schedule_l.spec(f) if r[5]})


def lookup(code):
    """Return the mapping row for a code, or None. Codes are matched case-insensitively
    and tolerate surrounding whitespace, because they arrive from spreadsheets."""
    if code is None:
        return None
    row = BY_CODE.get(str(code).strip().upper())
    if row:
        return row
    # Spreadsheets lowercase suffixes freely — C-26M and C-26m are the same line.
    for k, v in BY_CODE.items():
        if k.upper() == str(code).strip().upper():
            return v
    return None


def split_code(cell):
    """One account often feeds several lines. A single ledger account called Travel &
    Entertainment has to reach three different rules — travel is deductible, meals are
    halved by §274(n), entertainment is disallowed outright — so the code cell accepts a
    split: `C-26t:60,C-26m:30,C-26e:10`. Percentages are normalised, so 60/30/10 and
    6/3/1 mean the same thing.

    A plain code is the whole account."""
    text = str(cell).strip()
    if ":" not in text:
        return [(text, 1.0)]
    parts = []
    for piece in text.replace(";", ",").split(","):
        if not piece.strip():
            continue
        code, _, pct = piece.partition(":")
        parts.append([code.strip(), float(pct or 0)])
    total = sum(p[1] for p in parts)
    if total <= 0:
        return [(text, 1.0)]
    return [(c, w / total) for c, w in parts]


def map_trial_balance(rows, column="ending"):
    """Turn trial balance rows into the figures the return expects.

    Each row is a dict with `account`, `name`, `code` and debit-positive balances.
    `column` selects which balance to read: Schedule L wants both the beginning and the
    ending column, while the income statement lines only want the ending one.

    Several accounts may carry the same code — a chart of accounts usually has more
    detail than a return line — so amounts accumulate.

    Returns the mapped figures keyed by the session field they feed, the rows that could
    not be mapped, and the codes that were not recognised. Nothing is silently dropped:
    an unmapped account is reported, never ignored."""
    mapped, detail, unmapped, bad_codes = {}, {}, [], []
    bal = lambda r: float(r.get(column, r.get("balance")) or 0.0)

    for r in rows:
        code = r.get("code")
        if not code or not str(code).strip():
            unmapped.append(r)
            continue

        parts = split_code(code)
        if any(lookup(c) is None for c, _ in parts):
            bad_codes.append(r)
            continue

        for c, share in parts:
            _, _, _, label, key, sign, section = lookup(c)
            amount = bal(r) * share * sign
            mapped[key] = mapped.get(key, 0.0) + amount
            detail.setdefault(key, {"code": c, "label": label, "section": section,
                                    "accounts": []})
            detail[key]["accounts"].append(
                {"account": r.get("account"), "name": r.get("name"),
                 "balance": bal(r) * share, "converted": amount,
                 "share": share})

    return {"mapped": mapped, "detail": detail,
            "unmapped": unmapped, "unknown_codes": bad_codes}


def check_trial_balance(rows, column="ending"):
    """A trial balance must balance. Debit-positive balances sum to zero when they do.

    This runs before anything is mapped: an out-of-balance import means the extract is
    wrong, and mapping it would only spread the error across the return."""
    bal = lambda r: float(r.get(column, r.get("balance")) or 0.0)
    total = sum(bal(r) for r in rows)
    debits = sum(bal(r) for r in rows if bal(r) > 0)
    credits = -sum(bal(r) for r in rows if bal(r) < 0)
    return {"balanced": abs(total) < 0.01, "difference": total,
            "debits": debits, "credits": credits}
