import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.schedule_l import (CLOSING_EQUITY, SCHEDULE_L_1065, SCHEDULE_L_1120,
                                    calc_m2_1065, calc_m2_1120, spec, totals)
from calculators.tax_lines import BY_CODE, CONTRA_CODES


# ── The specification ────────────────────────────────────────────────────────

def test_the_two_balance_sheets_share_no_fields():
    """A partnership balance sheet must never land on a corporation's."""
    a = {r[3] for r in SCHEDULE_L_1120}
    b = {r[3] for r in SCHEDULE_L_1065}
    assert a & b == set()


def test_codes_and_keys_are_unique_within_each_form():
    for form in ("1120", "1065"):
        rows = spec(form)
        assert len({r[0] for r in rows}) == len(rows)
        assert len({r[3] for r in rows}) == len(rows)


def test_the_mapping_table_is_generated_from_this_spec():
    """One source of truth — a line added here must appear in the import codes."""
    for form in ("1120", "1065"):
        for code, line, label, key, section, contra in spec(form):
            assert code in BY_CODE
            assert BY_CODE[code][4] == key
            assert (code in CONTRA_CODES) == contra


def test_m2_closes_the_unappropriated_account_specifically():
    """M-2 analyses unappropriated retained earnings. Carrying line 8 into the
    appropriated account instead would still balance and would still be wrong — amounts
    moved to appropriated leave M-2 through line 6."""
    assert CLOSING_EQUITY["1120"] == "sl_retained"
    by_key = {r[3]: r for r in SCHEDULE_L_1120}
    assert by_key["sl_retained"][1] == "25"
    assert "unappropriated" in by_key["sl_retained"][2].lower()
    assert by_key["sl_retained_approp"][1] == "24"


def test_partnership_m2_closes_the_single_capital_line():
    assert CLOSING_EQUITY["1065"] == "f65_sl_capital"
    by_key = {r[3]: r for r in SCHEDULE_L_1065}
    assert by_key["f65_sl_capital"][1] == "21"
    assert by_key["f65_sl_capital"][4] == "equity"


def test_partnerships_have_no_capital_stock_or_treasury_stock():
    labels = " ".join(r[2] for r in SCHEDULE_L_1065).lower()
    assert "capital stock" not in labels
    assert "treasury" not in labels


def test_the_two_forms_number_their_totals_differently():
    """Form 1065 has no capital stock or treasury stock, so its balance sheet runs four
    lines shorter and the totals land in different places."""
    from calculators.schedule_l import TOTAL_LINES
    assert TOTAL_LINES["1120"] == ("15", "28")
    assert TOTAL_LINES["1065"] == ("14", "22")
    for form in ("1120", "1065"):
        printed = {r[1] for r in spec(form)}
        assert TOTAL_LINES[form][0] not in printed
        assert TOTAL_LINES[form][1] not in printed


def test_nonrecourse_debt_has_its_own_line_on_the_partnership_sheet():
    """§752 basis turns on the recourse split, so the balance sheet reports it."""
    assert any("nonrecourse" in r[2].lower() for r in SCHEDULE_L_1065)


# ── Totals ───────────────────────────────────────────────────────────────────

def test_contra_lines_are_subtracted_not_added():
    v = {"sl_ppe": 4_000_000, "sl_accum_dep": 1_500_000}
    assert totals("1120", v)["asset"] == 2_500_000


def test_a_balanced_sheet_is_reported_balanced():
    v = {"sl_cash": 1_000_000, "sl_ap": 400_000, "sl_retained": 600_000}
    t = totals("1120", v)
    assert t["balanced"] and t["difference"] == 0


def test_an_unbalanced_sheet_reports_the_gap_with_its_sign():
    v = {"sl_cash": 1_000_000, "sl_ap": 400_000, "sl_retained": 550_000}
    t = totals("1120", v)
    assert not t["balanced"]
    assert t["difference"] == 50_000


def test_missing_lines_are_nil_not_an_error():
    assert totals("1120", {})["total_assets"] == 0.0


def test_treasury_stock_reduces_equity():
    v = {"sl_capital_stock": 100_000, "sl_treasury": 30_000}
    assert totals("1120", v)["equity"] == 70_000


# ── Schedule M-2, Form 1120 ──────────────────────────────────────────────────

def test_m2_rolls_beginning_equity_to_ending():
    r = calc_m2_1120(beginning=1_000_000, net_income_per_books=580_000,
                     dist_cash=200_000)
    assert r["line4"] == 1_580_000
    assert r["line7"] == 200_000
    assert r["line8"] == 1_380_000


def test_m2_takes_book_income_so_a_book_tax_difference_does_not_move_it():
    """M-2 tracks the book equity account. Feeding it taxable income would still add up
    and would still be wrong, which is why the caller passes M-1 line 1."""
    book = calc_m2_1120(beginning=0.0, net_income_per_books=580_000)
    taxable = calc_m2_1120(beginning=0.0, net_income_per_books=963_000)
    assert book["line8"] != taxable["line8"]


def test_every_kind_of_distribution_reduces_retained_earnings():
    r = calc_m2_1120(beginning=1_000_000, net_income_per_books=0.0,
                     dist_cash=10_000, dist_stock=20_000, dist_property=30_000,
                     other_decreases=40_000)
    assert r["line7"] == 100_000
    assert r["line8"] == 900_000


def test_a_book_loss_reduces_retained_earnings():
    r = calc_m2_1120(beginning=500_000, net_income_per_books=-200_000)
    assert r["line8"] == 300_000


# ── Schedule M-2, Form 1065 ──────────────────────────────────────────────────

def test_partnership_m2_separates_contributions_from_income():
    """A partner can put capital in without any of it passing through income, so the two
    cannot share a line."""
    r = calc_m2_1065(beginning=200_000, contributed=100_000, net_income=450_000,
                     dist_cash=500_000)
    assert r["line5"] == 750_000
    assert r["line9"] == 250_000


def test_partnership_distributions_of_property_reduce_capital():
    r = calc_m2_1065(beginning=100_000, contributed=0.0, net_income=0.0,
                     dist_property=40_000)
    assert r["line9"] == 60_000


# ── The tie between the two schedules ────────────────────────────────────────

def test_closing_equity_is_the_m2_result_and_makes_the_sheet_balance():
    """The whole point of carrying line 8 rather than typing it: get the book income
    right and the balance sheet closes; get it wrong and it does not."""
    m2 = calc_m2_1120(beginning=1_135_000, net_income_per_books=580_000,
                      dist_cash=325_000)
    v = {"sl_cash": 1_240_000, "sl_inventory": 1_100_000,
         "sl_ppe": 4_000_000, "sl_accum_dep": 1_500_000,
         "sl_ap": 800_000, "sl_debt_long": 1_500_000,
         "sl_capital_stock": 100_000, "sl_apic": 1_050_000,
         CLOSING_EQUITY["1120"]: m2["line8"]}
    assert totals("1120", v)["balanced"]


def test_wrong_book_income_breaks_the_balance_sheet_by_exactly_that_amount():
    base = dict(beginning=1_135_000, dist_cash=325_000)
    right = calc_m2_1120(net_income_per_books=580_000, **base)
    wrong = calc_m2_1120(net_income_per_books=530_000, **base)
    v = {"sl_cash": 1_240_000, "sl_inventory": 1_100_000,
         "sl_ppe": 4_000_000, "sl_accum_dep": 1_500_000,
         "sl_ap": 800_000, "sl_debt_long": 1_500_000,
         "sl_capital_stock": 100_000, "sl_apic": 1_050_000}
    assert totals("1120", {**v, CLOSING_EQUITY["1120"]: right["line8"]})["balanced"]
    off = totals("1120", {**v, CLOSING_EQUITY["1120"]: wrong["line8"]})
    assert not off["balanced"]
    assert off["difference"] == pytest.approx(50_000)


def test_a_stock_distribution_leaves_total_equity_unchanged():
    """5b moves retained earnings into capital stock. No asset moves, so the balance sheet
    must still balance once the offsetting credit is recorded."""
    m2 = calc_m2_1120(beginning=1_000_000, net_income_per_books=0.0, dist_stock=100_000)
    v = {"sl_cash": 1_100_000, "sl_capital_stock": 100_000, "sl_apic": 100_000,
         CLOSING_EQUITY["1120"]: m2["line8"]}
    assert totals("1120", v)["balanced"]
