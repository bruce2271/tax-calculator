# Form 1120 — U.S. Corporate Income Tax Return Modeller

An interactive model of the U.S. corporate income tax return, built to study how the
mechanics actually fit together — not a rate table, but the machinery: how §263A pulls
labour and overhead out of period expense and into inventory, why the dividends-received
deduction sits *below* line 28 instead of netting against income, and how a 2016 net
operating loss and a 2024 one are governed by entirely different rules in the same year.

> **Educational tool. Not tax advice.** Not prepared or reviewed by a CPA. Does not
> produce a filable return. See [Disclaimer](#disclaimer).

---

## What it does

Enter book figures and the disallowance rules in one place; every schedule, the two
book-tax reconciliations, and the return itself are derived from them.

| Area | Implemented |
|---|---|
| **Page 1** | Lines 1a–30 with the real IRS line numbering, Book / Tax-Exclusion / Taxable columns |
| **Schedule C** | Dividends and inclusions in real column (a)/(c) form, §243 DRD with the §246(b) limit, §250(a)(2) cap on the GILTI deduction, §78 gross-up |
| **Schedule D** | Parts I–III, §1211(a) limitation, §1212(a) carryback/carryforward by vintage year |
| **Form 4797** | Parts I–IV, §1245 / §1250 / §291 recapture, §1231(c) five-year look-back |
| **Form 1125-A** | Cost of goods sold feeding page 1 line 2 as a read-only carried figure |
| **Schedule J** | Tax computation aligned to the real line numbers |
| **Schedule M-1 / M-3** | Both fully derived — see [The reconciliations](#the-reconciliations) |
| **NOL (§172)** | Vintage-aware: pre-2018 tranches offset 100% and expire after 20 years; 2018+ tranches never expire but are capped at 80% |
| **§263A UNICAP** | Percentage allocation across lines 12, 13, 14, 16, 17 and 20 into the inventory pool |
| **§163(j)** | 30%-of-ATI limitation with indefinite carryforward and the §448(c) small-business exemption |
| **§162(m), §274(n), §162(f)/(e)/(c), §276, §264, §267(a)(2), §170** | Disallowances and deferrals wired into both reconciliations |
| **§174, §197, ASC 718, ASC 842** | The timing items that dominate real filings: research capitalised and amortised over 5 years, 15-year intangible amortisation, stock compensation, and leases |
| **Year-end close** | Explicit rollforward that writes every carryforward, clears current-year amounts, advances the tax year, and refuses to run twice |
| **Persistence** | Save / load the whole return as JSON, carryforwards and closed-year history included |

Plus topic calculators for §351 formations, corporate distributions and §302 redemptions,
CAMT, Subpart F / GILTI / NCTI, and §199A.

---

## Two ideas worth pointing at

### The reconciliations

Schedule M-1 and M-3 are usually the tedious part of a tax return — you compute the
return, then type the differences in again by hand. Here they are **fully derived**.

The insight is that the figures entered on the income and deduction pages are not tax
numbers; they are *book* numbers plus *disallowance rules*. Subtract one from the other
and you already have every book-tax difference. So the schedules populate themselves —
including net income per books, which is reconstructed from the same ledger accounts:

```
book income = book revenue − book expenses − federal tax per books
```

The only figure the ledger cannot supply is the federal tax accrual, so that is the one
manual input. Every M-3 row fixes column (a), column (d) and the permanent slice (c),
then derives the temporary slice (b) as the residual — so `(a) + (b) + (c) = (d)` cannot
drift on any line.

### The integrity check

Real tax software runs diagnostics before it lets you e-file. This does the same: a
pass/fail gate that asserts the return hangs together before you trust any number on it.

```
✓ Book income is populated
✓ Taxable income is populated
✓ Book-tax differences are computed
✓ Schedule M-3 Part II line 30 (d) = Form 1120 line 28
✓ M-1 and M-3 agree with each other
✓ Schedule C line 23 = page 1 line 4
✓ Schedule D = page 1 line 8
✓ Form 4797 line 17 = page 1 line 9
✓ §263A costs removed from lines 12–20 reach cost of goods sold
✓ Line 28 − 29a − 29b = line 30
```

Each row shows the two figures and how far apart they are, so a break points at its own
cause. An empty return does not pass — with nothing entered every check succeeds
trivially, which proves nothing, so that state reports "nothing entered yet" instead.

The `§263A` row exists because of a real bug: capitalised costs were correctly stripped
out of lines 12–20 but never reached cost of goods sold, and $1.6M silently left the
return. The check is that bug's signature, kept as a permanent tripwire.

---

## Architecture

```
app.py                      Streamlit UI and the shared computation layer
calculators/form_1120.py    Pure tax functions — no Streamlit imports, no I/O
```

**The shared computation layer** is the one structural decision worth explaining.
Streamlit renders exactly one page per run, so any figure computed inside a page branch
is invisible to every other page — which produced a recurring class of bug where
Schedule C, Schedule D and the NOL carryforward each went stale when edited from
elsewhere. Everything cross-cutting is therefore computed *before* any page branch runs:

```python
F1125A = form_1125a_base()
S263A  = sec263a_status()
F4797  = form_4797_totals()
SD     = schedule_d_totals(F4797["schedule_d_ltcg"])
SC     = schedule_c_totals()
NOL    = nol_vintages()
R1120  = calculate_1120(build_1120_inputs(...))
M1, M3 = m1_lines(), m3_lines()
```

Two dependency cycles are broken with a probe-then-solve pass rather than iteration:
depreciation is computed once to size the §263A pool, and line 28 is computed once to
give §246(b) its limitation base.

Figures that a real form carries rather than collects — page 1 lines 2, 4, 8, 9 and 29b —
are rendered read-only, so there is exactly one place any number can be entered.

---

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

The Streamlit version is pinned on purpose. The app injects CSS targeting Streamlit's
internal DOM in roughly 68 places, so a minor release can change the markup and break the
styling silently. Upgrade deliberately, then re-check the theming and the schedule tabs.

### Secrets

There are none — the app makes no network calls and reads no environment variables. If
that ever changes, load credentials from the environment and never from source:

```bash
export SOME_API_KEY="..."     # shell only; .env and .streamlit/secrets.toml are gitignored
```

Saved returns (`form1120_*.json`) contain taxpayer figures and are gitignored too.

---

## Tests

```bash
pip install pytest && python -m pytest tests/ -q
```

Two kinds of test, and the difference is the point:

**Reproductions of IRS worked examples.** The expected figures come from Publication 542,
not from this code, so they can fail. The §246(b) pair is the one worth reading: with a
$75,000 operating loss and $100,000 of dividends, the *limited* deduction would be
$16,250 — but because the full $65,000 deduction creates a net operating loss,
§246(b)(2) switches the limit off and the whole $65,000 is allowed. Getting that
backwards is the classic error, so it is pinned.

**Regressions for bugs that actually shipped here.** Each names what went wrong: the
§1211 double-count that reported taxable income of $40,000 instead of $70,000; the
dividends that were deducted via the DRD but never added to total income; the `ati=None`
crash that took out the whole results page; the §263A pool that evaporated because
`calc_unicap` received a zero inventory base.

The suite was checked by mutation: deleting the §246(b) NOL exception makes it fail. That
exercise also exposed a blind spot — the original §172 vintage test used a pre-2018 pool
smaller than 80% of taxable income, so capping it changed nothing and the mutant
survived. The test now uses a pool large enough to prove a pre-2018 loss can take taxable
income to zero, which is the entire reason vintage is tracked.

## Known limits

- **Coverage was checked against a real filer.** Winnebago's FY2024 deferred tax footnote
  was used to find gaps; §174, §197, leases and stock compensation came from that
  exercise. Warranty and self-insurance reserves and convertible debt are still absent.
- **`app.py` is one large file.** Splitting it into Streamlit's `pages/` layout is the
  obvious next refactor; the tests exist partly to make that safe.
- Simplifications throughout: the §263A absorption ratio is the simplified method,
  state tax is Texas franchise only, CAMT and BEAT are threshold checks rather than full
  computations, and consolidated-return mechanics are out of scope.
- §280C, the line 14 repair safe harbours and §461 economic performance are documented in
  the app's law notes but not modelled.

---

## Disclaimer

This project is for education and demonstration. It is **not** tax advice and **not**
prepared or reviewed by a CPA or enrolled agent. It does not produce a filable return and
it simplifies or omits rules that apply to real taxpayers. Do not rely on it to compute an
actual tax liability — verify against the current IRS forms and instructions and consult a
qualified professional.

Do not enter real taxpayer data into the hosted demo. Figures live in server memory for
the session and are never stored, but it is a public service you do not control.

Released under the [MIT License](LICENSE), without warranty of any kind.
