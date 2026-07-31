"""How much of a real rate reconciliation can this model's vocabulary express?

The Winnebago walk-through in the README proves the model is internally consistent, but
it cannot prove more: the inputs were derived from the answer by grossing the disclosed
rate lines up at 21%, so re-applying 21% only inverts that arithmetic.

This asks a question that is not circular. Every filer's tax provision differs from 21%
of its pretax income, and the rate reconciliation is the list of reasons why. So:

    gap to explain  =  total provision  -  21% x pretax income
    explained       =  sum of the reconciling items this model implements
    residual        =  whatever is left, tagged by the filer but outside the model

The residual measures what the model cannot say. It is a coverage measure, not a
correctness one: a large residual means a filer's tax position turns on something the
model has no line for, which is exactly the list worth knowing.

Two decisions that matter for reading the output:

  * The reconciliation runs to the *total* provision — federal, state and foreign — so
    the state and foreign-rate-differential lines belong on the explained side even
    though neither is a Form 1120 concept. Excluding them instead makes every filer with
    material foreign operations look broken, which says nothing about the model.
  * The residual is scaled by the statutory 21% tax, not by the gap. A filer whose
    provision happens to land near 21% has a gap near zero, and dividing by it
    manufactures enormous residuals out of rounding.

    SEC_CONTACT=you@example.com python analysis/reconcile_provision.py
"""

import json
import os
import sys
import urllib.request

PERIOD = "CY2024"
CACHE = ".data"

PRETAX = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxes"
          "ExtraordinaryItemsNoncontrollingInterest")
TOTAL = "IncomeTaxExpenseBenefit"
STATUTORY = ("IncomeTaxReconciliationIncomeTaxExpenseBenefitAt"
             "FederalStatutoryIncomeTaxRate")
FOREIGN = "IncomeTaxReconciliationForeignIncomeTaxRateDifferential"
VA = "IncomeTaxReconciliationChangeInDeferredTaxAssetsValuationAllowance"

KNOWN = {
    "IncomeTaxReconciliationStateAndLocalIncomeTaxes": "state and local",
    FOREIGN: "foreign rate differential",
    "IncomeTaxReconciliationNondeductibleExpense": "non-deductible expense",
    "IncomeTaxReconciliationNondeductibleExpenseShareBasedCompensationCost":
        "non-deductible stock compensation",
    "IncomeTaxReconciliationTaxExemptIncome": "tax-exempt income (s103, s243)",
    "IncomeTaxReconciliationTaxCredits": "tax credits",
    "IncomeTaxReconciliationTaxCreditsResearch": "s41 research credit",
    VA: "valuation allowance (ASC 740 only)",
    "IncomeTaxReconciliationTaxSettlements": "uncertain positions (ASC 740 only)",
    "IncomeTaxReconciliationOtherAdjustments": "other",
}
ALL_TAGS = [PRETAX, TOTAL, STATUTORY] + list(KNOWN)


def fetch(tag):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{PERIOD}_{tag}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    url = f"https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{PERIOD}.json"
    req = urllib.request.Request(url, headers={
        "User-Agent": "form-1120-modeller "
                      + os.environ.get("SEC_CONTACT", "research@example.com")})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read().decode())
    json.dump(data, open(path, "w", encoding="utf-8"))
    return data


def clean(name):
    """Filer names carry non-breaking spaces a cp950 console cannot print."""
    return "".join(ch if ord(ch) < 128 else " " for ch in name).strip()


def main():
    frames = {t: {r["cik"]: r["val"] for r in fetch(t).get("data", [])} for t in ALL_TAGS}
    names = {r["cik"]: clean(r["entityName"]) for r in fetch(PRETAX)["data"]}
    g = lambda t, c: frames[t].get(c, 0.0)

    core = [c for c in frames[PRETAX] if c in frames[STATUTORY]
            and abs(frames[PRETAX][c]) > 1_000_000]
    ok = sum(1 for c in core
             if abs(g(STATUTORY, c) - 0.21 * g(PRETAX, c)) <= 0.005 * abs(g(PRETAX, c)))
    print("Check 1 - the disclosed statutory line is 21% of pretax income")
    print(f"  {ok:,} of {len(core):,} filers ({ok / len(core):.1%}) within half a point")
    print("  a failure here would mean the join or the tags are wrong")
    print("")

    rows = []
    for c in core:
        if c not in frames[TOTAL]:
            continue
        stat = g(STATUTORY, c)
        if abs(stat) < 1_000_000:
            continue
        gap = g(TOTAL, c) - stat
        explained = sum(g(t, c) for t in KNOWN)
        rows.append({"name": names.get(c, str(c)), "gap": gap, "explained": explained,
                     "residual": abs(gap - explained) / abs(stat),
                     "foreign": c in frames[FOREIGN], "va": c in frames[VA]})

    def report(label, subset):
        r = sorted(x["residual"] for x in subset)
        if not r:
            print(f"  {label:<46} none")
            return
        within = sum(1 for x in r if x <= 0.05) / len(r)
        print(f"  {label:<46} n={len(r):>5}   median {r[len(r) // 2]:>6.1%}"
              f"   within 5%: {within:>5.1%}")

    print("Check 2 - unexplained residual as a share of the statutory 21% tax")
    print("")
    report("all filers", rows)
    report("no foreign rate differential", [x for x in rows if not x["foreign"]])
    domestic = [x for x in rows if not x["foreign"] and not x["va"]]
    report("no foreign differential, no valuation allowance", domestic)

    print("")
    print("  Filers disclosing each modelled item")
    for tag, label in KNOWN.items():
        print(f"    {sum(1 for c in core if c in frames[tag]):>5}  {label}")

    print("")
    print("  Fully explained, domestic, no valuation allowance")
    for x in sorted(domestic, key=lambda r: r["residual"])[:6]:
        print(f"    {x['name'][:34]:<34} gap {x['gap'] / 1e6:>9,.1f}M"
              f"  explained {x['explained'] / 1e6:>9,.1f}M"
              f"  residual {x['residual']:>6.2%}")

    print("")
    print("  Largest residuals in that group - what the model has no line for")
    for x in sorted(domestic, key=lambda r: -r["residual"])[:6]:
        print(f"    {x['name'][:34]:<34} gap {x['gap'] / 1e6:>9,.1f}M"
              f"  explained {x['explained'] / 1e6:>9,.1f}M"
              f"  residual {x['residual']:>6.0%}")


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    main()
