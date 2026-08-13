"""Schedule L — Balance Sheets per Books, and the M-2 analysis that closes it.

The balance sheet is the only part of a return that can be wrong in a way arithmetic
catches. Everything else — a deduction limit, a credit carryforward — is right or wrong
against the Code, and a return can be internally consistent while being wrong. Schedule L
either balances or it does not.

That is why retained earnings is not typed here. Line 25 for a corporation, line 21 for a
partnership, is carried from the M-2 analysis, and M-2 in turn starts from the Schedule L
beginning column. The loop closes: book income, distributions and last year's equity all
feed the ending balance, so if any of them is wrong the balance sheet stops balancing.
Typing the ending equity instead would let the return hide the error.

Each line is (code, line, label, key, section, contra). `contra` marks the lines the form
prints positive and then subtracts — accumulated depreciation, the bad debt allowance,
treasury stock. Adding those into a section total instead of removing them is the classic
way to end up with a balance sheet that is out by exactly twice the contra.
"""

SCHEDULE_L_1120 = [
    ("L-1",   "1",   "Cash",                                      "sl_cash",              "asset",     False),
    ("L-2a",  "2a",  "Trade notes and accounts receivable",       "sl_ar",                "asset",     False),
    ("L-2b",  "2b",  "Less allowance for bad debts",              "sl_ar_allow",          "asset",     True),
    ("L-3",   "3",   "Inventories",                               "sl_inventory",         "asset",     False),
    ("L-4",   "4",   "U.S. government obligations",               "sl_govt",              "asset",     False),
    ("L-5",   "5",   "Tax-exempt securities",                     "sl_taxexempt_sec",     "asset",     False),
    ("L-6",   "6",   "Other current assets",                      "sl_other_current",     "asset",     False),
    ("L-7",   "7",   "Loans to shareholders",                     "sl_loans_to_sh",       "asset",     False),
    ("L-8",   "8",   "Mortgage and real estate loans",            "sl_mortgage_loans",    "asset",     False),
    ("L-9",   "9",   "Other investments",                         "sl_investments",       "asset",     False),
    ("L-10a", "10a", "Buildings and other depreciable assets",    "sl_ppe",               "asset",     False),
    ("L-10b", "10b", "Less accumulated depreciation",             "sl_accum_dep",         "asset",     True),
    ("L-11a", "11a", "Depletable assets",                         "sl_depletable",        "asset",     False),
    ("L-11b", "11b", "Less accumulated depletion",                "sl_accum_depl",        "asset",     True),
    ("L-12",  "12",  "Land (net of any amortisation)",            "sl_land",              "asset",     False),
    ("L-13a", "13a", "Intangible assets (amortisable only)",      "sl_intangibles",       "asset",     False),
    ("L-13b", "13b", "Less accumulated amortisation",             "sl_accum_amort",       "asset",     True),
    ("L-14",  "14",  "Other assets",                              "sl_other_assets",      "asset",     False),
    ("L-16",  "16",  "Accounts payable",                          "sl_ap",                "liability", False),
    ("L-17",  "17",  "Mortgages, notes, bonds payable in less than 1 year", "sl_debt_current", "liability", False),
    ("L-18",  "18",  "Other current liabilities",                 "sl_other_current_liab", "liability", False),
    ("L-19",  "19",  "Loans from shareholders",                   "sl_loans_from_sh",     "liability", False),
    ("L-20",  "20",  "Mortgages, notes, bonds payable in 1 year or more", "sl_debt_long", "liability", False),
    ("L-21",  "21",  "Other liabilities",                         "sl_other_liab",        "liability", False),
    ("L-22",  "22",  "Capital stock",                             "sl_capital_stock",     "equity",    False),
    ("L-23",  "23",  "Additional paid-in capital",                "sl_apic",              "equity",    False),
    ("L-24",  "24",  "Retained earnings — appropriated",          "sl_retained_approp",   "equity",    False),
    ("L-25",  "25",  "Retained earnings — unappropriated",        "sl_retained",          "equity",    False),
    ("L-26",  "26",  "Adjustments to shareholders' equity",       "sl_equity_adj",        "equity",    False),
    ("L-27",  "27",  "Less cost of treasury stock",               "sl_treasury",          "equity",    True),
]

# Form 1065 numbers the same balance sheet differently — there is no capital stock or
# treasury stock, partners' capital is a single line, and nonrecourse debt gets a line of
# its own because it drives §752 basis. Separate codes keep a partnership trial balance
# from landing on a corporation's balance sheet.
SCHEDULE_L_1065 = [
    ("B-1",   "1",   "Cash",                                      "f65_sl_cash",           "asset",     False),
    ("B-2a",  "2a",  "Trade notes and accounts receivable",       "f65_sl_ar",             "asset",     False),
    ("B-2b",  "2b",  "Less allowance for bad debts",              "f65_sl_ar_allow",       "asset",     True),
    ("B-3",   "3",   "Inventories",                               "f65_sl_inventory",      "asset",     False),
    ("B-4",   "4",   "U.S. government obligations",               "f65_sl_govt",           "asset",     False),
    ("B-5",   "5",   "Tax-exempt securities",                     "f65_sl_taxexempt_sec",  "asset",     False),
    ("B-6",   "6",   "Other current assets",                      "f65_sl_other_current",  "asset",     False),
    ("B-7a",  "7a",  "Loans to partners",                         "f65_sl_loans_to_p",     "asset",     False),
    ("B-7b",  "7b",  "Mortgage and real estate loans",            "f65_sl_mortgage_loans", "asset",     False),
    ("B-8",   "8",   "Other investments",                         "f65_sl_investments",    "asset",     False),
    ("B-9a",  "9a",  "Buildings and other depreciable assets",    "f65_sl_ppe",            "asset",     False),
    ("B-9b",  "9b",  "Less accumulated depreciation",             "f65_sl_accum_dep",      "asset",     True),
    ("B-10a", "10a", "Depletable assets",                         "f65_sl_depletable",     "asset",     False),
    ("B-10b", "10b", "Less accumulated depletion",                "f65_sl_accum_depl",     "asset",     True),
    ("B-11",  "11",  "Land (net of any amortisation)",            "f65_sl_land",           "asset",     False),
    ("B-12a", "12a", "Intangible assets (amortisable only)",      "f65_sl_intangibles",    "asset",     False),
    ("B-12b", "12b", "Less accumulated amortisation",             "f65_sl_accum_amort",    "asset",     True),
    ("B-13",  "13",  "Other assets",                              "f65_sl_other_assets",   "asset",     False),
    ("B-15",  "15",  "Accounts payable",                          "f65_sl_ap",             "liability", False),
    ("B-16",  "16",  "Mortgages, notes, bonds payable in less than 1 year", "f65_sl_debt_current", "liability", False),
    ("B-17",  "17",  "Other current liabilities",                 "f65_sl_other_current_liab", "liability", False),
    ("B-18",  "18",  "All nonrecourse loans",                     "f65_sl_nonrecourse",    "liability", False),
    ("B-19a", "19a", "Loans from partners",                       "f65_sl_loans_from_p",   "liability", False),
    ("B-19b", "19b", "Mortgages, notes, bonds payable in 1 year or more", "f65_sl_debt_long", "liability", False),
    ("B-20",  "20",  "Other liabilities",                         "f65_sl_other_liab",     "liability", False),
    ("B-21",  "21",  "Partners' capital accounts",                "f65_sl_capital",        "equity",    False),
]

# The equity line the M-2 analysis produces. It is computed, never typed.
CLOSING_EQUITY = {"1120": "sl_retained", "1065": "f65_sl_capital"}

TOTAL_LINES = {"1120": ("15", "28"), "1065": ("14", "22")}


def spec(form):
    return SCHEDULE_L_1120 if form == "1120" else SCHEDULE_L_1065


def totals(form, values):
    """Section totals for one column, contra lines subtracted.

    `values` maps the field key to the amount. A missing key is nil — a balance sheet with
    only half its lines filled is normal in this app, since the user may only be looking
    at one part of it."""
    out = {"asset": 0.0, "liability": 0.0, "equity": 0.0}
    for code, line, label, key, section, contra in spec(form):
        out[section] += float(values.get(key, 0.0) or 0.0) * (-1 if contra else 1)
    out["total_assets"] = out["asset"]
    out["total_liab_equity"] = out["liability"] + out["equity"]
    out["difference"] = out["total_assets"] - out["total_liab_equity"]
    out["balanced"] = abs(out["difference"]) < 0.5
    return out


def calc_m2_1120(beginning, net_income_per_books, other_increases=0.0,
                 dist_cash=0.0, dist_stock=0.0, dist_property=0.0, other_decreases=0.0):
    """Schedule M-2 — Analysis of Unappropriated Retained Earnings per Books.

    Note what feeds line 2: net income *per books*, not taxable income. M-2 tracks the
    book equity account, so the book-tax differences reconciled on M-1 have no place
    here. A return that puts taxable income on line 2 will still add up and will still be
    wrong."""
    line4 = beginning + net_income_per_books + other_increases
    line7 = dist_cash + dist_stock + dist_property + other_decreases
    return {"line1": beginning, "line2": net_income_per_books,
            "line3": other_increases, "line4": line4,
            "line5a": dist_cash, "line5b": dist_stock, "line5c": dist_property,
            "line6": other_decreases, "line7": line7, "line8": line4 - line7}


def calc_m2_1065(beginning, contributed, net_income, other_increases=0.0,
                 dist_cash=0.0, dist_property=0.0, other_decreases=0.0):
    """Schedule M-2 — Analysis of Partners' Capital Accounts.

    Line 3 is the Analysis of Net Income figure, which already carries the separately
    stated items. Contributions get their own line because a partner can put capital in
    without any of it passing through income."""
    line5 = beginning + contributed + net_income + other_increases
    line8 = dist_cash + dist_property + other_decreases
    return {"line1": beginning, "line2": contributed, "line3": net_income,
            "line4": other_increases, "line5": line5,
            "line6a": dist_cash, "line6b": dist_property,
            "line7": other_decreases, "line8": line8, "line9": line5 - line8}
