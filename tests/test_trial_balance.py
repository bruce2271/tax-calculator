import io
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.tax_lines import (BY_CODE, TAX_LINES, check_trial_balance, lookup,
                                   map_trial_balance, split_code)
from calculators.trial_balance import detect_columns, read_trial_balance


def csv_bytes(text):
    return text.encode("utf-8")


# ── The mapping table itself ─────────────────────────────────────────────────

def test_codes_are_unique():
    codes = [r[0] for r in TAX_LINES]
    assert len(codes) == len(set(codes))


def test_signs_are_only_plus_or_minus_one():
    assert {r[5] for r in TAX_LINES} == {1, -1}


def test_lookup_tolerates_spreadsheet_formatting():
    assert lookup("  c-12  ") == BY_CODE["C-12"]
    assert lookup("C-26M") == BY_CODE["C-26m"]
    assert lookup("Z-99") is None
    assert lookup(None) is None


# ── Sign conversion ──────────────────────────────────────────────────────────

def test_revenue_credit_balance_becomes_positive_income():
    rows = [{"account": "4000", "name": "Sales", "code": "C-1a", "ending": -5_000_000}]
    out = map_trial_balance(rows)
    assert out["mapped"]["gross_receipts_book"] == 5_000_000


def test_expense_debit_balance_stays_positive():
    rows = [{"account": "6100", "name": "Wages", "code": "C-13", "ending": 800_000}]
    assert map_trial_balance(rows)["mapped"]["salaries_book"] == 800_000


def test_contra_asset_arrives_as_a_positive_deduction():
    """Schedule L line 10b prints accumulated depreciation as a positive figure in the
    left-hand column and subtracts it there, so the credit balance has to be flipped."""
    rows = [{"account": "1590", "name": "A/D", "code": "L-10b", "ending": -1_200_000}]
    assert map_trial_balance(rows)["mapped"]["sl_accum_dep"] == 1_200_000


def test_ending_inventory_credit_becomes_a_positive_form_1125a_line_7():
    """Beginning inventory is charged to cost of goods sold and ending inventory relieves
    it, so the two sit on opposite sides of the ledger but both print positive."""
    rows = [{"account": "5900", "name": "Beg inv", "code": "A-1", "ending": 900_000},
            {"account": "5910", "name": "End inv", "code": "A-7", "ending": -1_100_000}]
    m = map_trial_balance(rows)["mapped"]
    assert m["f1125a_beg_inv"] == 900_000
    assert m["f1125a_end_inv"] == 1_100_000


def test_distributions_are_not_an_income_statement_item():
    """A partner distribution moves equity; it is not an expense. Classifying it as a
    deduction understated book income by the whole distribution, which then left the
    partnership balance sheet unable to close."""
    for code in ("K-19a", "K-19b"):
        assert BY_CODE[code][6] == "distribution"
    income_statement = {"income", "cogs", "deduction"}
    assert BY_CODE["K-19a"][6] not in income_statement


def test_liability_credit_balance_becomes_positive():
    rows = [{"account": "2000", "name": "AP", "code": "L-16", "ending": -300_000}]
    assert map_trial_balance(rows)["mapped"]["sl_ap"] == 300_000


# ── Aggregation, splits, and gaps ────────────────────────────────────────────

def test_many_accounts_accumulate_into_one_line():
    rows = [{"account": "6100", "name": "Wages", "code": "C-13", "ending": 500_000},
            {"account": "6110", "name": "Overtime", "code": "C-13", "ending": 75_000},
            {"account": "6120", "name": "Bonus", "code": "C-13", "ending": 125_000}]
    out = map_trial_balance(rows)
    assert out["mapped"]["salaries_book"] == 700_000
    assert len(out["detail"]["salaries_book"]["accounts"]) == 3


def test_split_sends_one_account_to_three_rules():
    rows = [{"account": "6800", "name": "Travel & Ent",
             "code": "C-26t:60,C-26m:30,C-26e:10", "ending": 100_000}]
    m = map_trial_balance(rows)["mapped"]
    assert m["travel_book"] == 60_000
    assert m["meals_book"] == 30_000
    assert m["entertainment_book"] == 10_000


def test_split_weights_need_not_sum_to_one_hundred():
    rows = [{"account": "6800", "name": "T&E", "code": "C-26t:6,C-26m:3,C-26e:1",
             "ending": 100_000}]
    m = map_trial_balance(rows)["mapped"]
    assert m["travel_book"] == pytest.approx(60_000)
    assert m["meals_book"] == pytest.approx(30_000)


def test_unmapped_and_unknown_are_reported_never_dropped():
    rows = [{"account": "9999", "name": "Suspense", "code": "", "ending": 1_000},
            {"account": "9998", "name": "Mystery", "code": "X-1", "ending": 2_000},
            {"account": "6100", "name": "Wages", "code": "C-13", "ending": 3_000}]
    out = map_trial_balance(rows)
    assert len(out["unmapped"]) == 1
    assert len(out["unknown_codes"]) == 1
    assert out["mapped"] == {"salaries_book": 3_000}


def test_a_split_with_one_bad_code_is_rejected_whole():
    """Half-applying a split would silently understate the line."""
    rows = [{"account": "6800", "name": "T&E", "code": "C-26t:50,X-9:50", "ending": 100}]
    out = map_trial_balance(rows)
    assert out["mapped"] == {}
    assert len(out["unknown_codes"]) == 1


def test_column_choice_selects_beginning_or_ending():
    rows = [{"account": "1000", "name": "Cash", "code": "L-1",
             "beginning": 100_000, "ending": 250_000}]
    assert map_trial_balance(rows, "beginning")["mapped"]["sl_cash"] == 100_000
    assert map_trial_balance(rows, "ending")["mapped"]["sl_cash"] == 250_000


# ── The balance check ────────────────────────────────────────────────────────

def test_balanced_trial_balance_passes():
    rows = [{"ending": 500_000}, {"ending": -200_000}, {"ending": -300_000}]
    r = check_trial_balance(rows)
    assert r["balanced"]
    assert r["debits"] == 500_000 and r["credits"] == 500_000


def test_out_of_balance_is_caught_with_the_difference():
    rows = [{"ending": 500_000}, {"ending": -499_000}]
    r = check_trial_balance(rows)
    assert not r["balanced"]
    assert r["difference"] == 1_000


# ── File reading ─────────────────────────────────────────────────────────────

def test_account_code_and_tax_code_are_not_confused():
    cols = detect_columns(["Account Code", "Description", "Tax Code", "Balance"])
    assert cols["account"] == "Account Code"
    assert cols["code"] == "Tax Code"
    assert cols["ending"] == "Balance"


def test_a_header_is_claimed_by_only_one_field():
    """"Balance" is an alias of ending. Nothing else may also take it."""
    cols = detect_columns(["Acct", "Name", "Balance"])
    assert cols["ending"] == "Balance"
    assert len([f for f, h in cols.items() if h == "Balance"]) == 1


def test_reads_csv_with_a_signed_balance_column():
    data = csv_bytes("Account,Account Name,Tax Code,Ending Balance\n"
                     "4000,Sales,C-1a,\"(5,000,000)\"\n"
                     "6100,Wages,C-13,\"800,000\"\n")
    rows, cols, warn = read_trial_balance(data, "tb.csv")
    assert len(rows) == 2
    assert rows[0]["ending"] == -5_000_000
    assert map_trial_balance(rows)["mapped"]["gross_receipts_book"] == 5_000_000


def test_reads_separate_debit_and_credit_columns():
    data = csv_bytes("Acct,Name,Tax Code,Debit,Credit\n"
                     "4000,Sales,C-1a,0,5000000\n"
                     "6100,Wages,C-13,800000,0\n")
    rows, cols, warn = read_trial_balance(data, "tb.csv")
    assert rows[0]["ending"] == -5_000_000
    assert rows[1]["ending"] == 800_000


def test_reads_excel_with_beginning_and_ending():
    buf = io.BytesIO()
    pd.DataFrame({"Account": ["1000"], "Name": ["Cash"], "Tax Code": ["L-1"],
                  "Opening Balance": [100_000], "Closing Balance": [250_000]}
                 ).to_excel(buf, index=False)
    rows, cols, warn = read_trial_balance(buf.getvalue(), "tb.xlsx")
    assert rows[0]["beginning"] == 100_000 and rows[0]["ending"] == 250_000


def test_missing_balance_column_is_refused_not_guessed():
    rows, cols, warn = read_trial_balance(csv_bytes("Account,Name\n1000,Cash\n"), "tb.csv")
    assert rows == []
    assert "balance column" in warn[0]


def test_missing_tax_code_column_warns_but_still_reads():
    rows, cols, warn = read_trial_balance(
        csv_bytes("Account,Name,Balance\n1000,Cash,5000\n"), "tb.csv")
    assert len(rows) == 1 and rows[0]["code"] == ""
    assert any("tax code" in w for w in warn)


def test_blank_cells_do_not_become_the_word_nan():
    data = csv_bytes("Account,Name,Tax Code,Balance\n"
                     "1000,Cash,L-1,5000\n"
                     "1010,Petty Cash,,\n")
    rows, cols, warn = read_trial_balance(data, "tb.csv")
    assert rows[1]["code"] == ""
    assert rows[1]["ending"] == 0.0
    assert map_trial_balance(rows)["unmapped"][0]["account"] == "1010"
