"""How far is a real corporation's federal tax from 21% of its book income?

The whole reason Schedules M-1 and M-3 exist is that book income and taxable income are
different numbers. This measures how different, across every public filer that reported
both figures for CY2024, using the SEC's XBRL frames API.

    python analysis/effective_federal_rate.py

The SEC asks for a contact address in the User-Agent; set SEC_CONTACT to yours.
Nothing here is secret, but it is read from the environment rather than hard-coded.

Two caveats worth stating, because the number is easy to over-read:

  * The numerator is the *current* federal provision. It excludes the deferred piece, so
    the gap it shows is permanent and temporary differences together, not permanent
    alone. That is the right choice here — current tax is what approximates the return.
  * The denominator is consolidated worldwide pretax income, while the numerator is
    federal only. Filers with large foreign operations therefore read low for a reason
    that has nothing to do with book-tax differences.
"""

import json
import os
import statistics
import urllib.request

FRAMES = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{period}.json"
TAX_TAG = "CurrentFederalTaxExpenseBenefit"
PRETAX_TAG = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxes"
              "ExtraordinaryItemsNoncontrollingInterest")
PERIOD = "CY2024"
CACHE = ".data"


def fetch(tag, period=PERIOD):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{period}_{tag}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    contact = os.environ.get("SEC_CONTACT", "research@example.com")
    req = urllib.request.Request(
        FRAMES.format(tag=tag, period=period),
        headers={"User-Agent": f"form-1120-modeller {contact}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return data


def main():
    tax = {r["cik"]: r for r in fetch(TAX_TAG)["data"]}
    pretax = {r["cik"]: r for r in fetch(PRETAX_TAG)["data"]}

    # Profitable, non-trivial, and actually paying federal tax. A loss-year or refund
    # filer has a meaningless ratio, and tiny denominators produce meaningless outliers.
    rows = []
    for cik in tax.keys() & pretax.keys():
        t, p = tax[cik]["val"], pretax[cik]["val"]
        if p > 1_000_000 and t > 0:
            rows.append((tax[cik]["entityName"], t, p, t / p))

    ratios = sorted(r[3] for r in rows)
    pct = lambda f: ratios[int(len(ratios) * f)]
    near_21 = sum(1 for r in ratios if 0.19 <= r <= 0.23) / len(ratios)

    print(f"{PERIOD}: {len(tax)} filers report current federal tax, "
          f"{len(pretax)} report pretax income")
    print(f"Usable overlap (pretax > $1M, federal tax > 0): {len(rows)}\n")
    print("Current federal tax as a share of pretax book income")
    for label, f in [("10th pct", 0.10), ("25th pct", 0.25), ("median", 0.50),
                     ("75th pct", 0.75), ("90th pct", 0.90)]:
        print(f"  {label:>9}  {pct(f):6.1%}")
    print(f"\n  mean     {statistics.fmean(ratios):6.1%}")
    print(f"  within 21% +/- 2pp: {near_21:.1%} of filers")
    print("\nThe statutory rate is 21%. If book income were taxable income, this "
          "distribution\nwould be a spike at 21%. It is not — which is the entire "
          "subject of Schedules M-1\nand M-3, and the reason this project models the "
          "differences rather than the rate.")


if __name__ == "__main__":
    main()
