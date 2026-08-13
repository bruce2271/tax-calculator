# U.S. Tax Return Modeller — Forms 1120 and 1065

**▶ [Try it live](https://us-tax-calculator.streamlit.app/)** — runs in the browser, nothing to install.

Form 1120 (corporate) is complete. Form 1065 (partnership) is **in progress** —
the partnership lifecycle calculators are built and tested; see
[Form 1065](#form-1065--partnership-in-progress) below for what is and is not there yet.

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
| **Page 1 lines 31–37** | Total tax, payments, the §6655 penalty and the amount owed or overpaid — all carried, none typed |
| **§1062** | Qualified farmland sale deferral: the return is recomputed without the gain to size the liability, then paid in four annual instalments |
| **§6655** | Quarterly underpayment interest, tested instalment by instalment |
| **Schedule M-1 / M-3** | Both fully derived — see [The reconciliations](#the-reconciliations) |
| **NOL (§172)** | Vintage-aware: pre-2018 tranches offset 100% and expire after 20 years; 2018+ tranches never expire but are capped at 80% |
| **§263A UNICAP** | Percentage allocation across lines 12, 13, 14, 16, 17 and 20 into the inventory pool |
| **§163(j)** | 30%-of-ATI limitation with indefinite carryforward and the §448(c) small-business exemption |
| **§162(m), §274(n), §162(f)/(e)/(c), §276, §264, §267(a)(2), §170** | Disallowances and deferrals wired into both reconciliations |
| **Credits** | §41 research computed both ways with the §41(c)(2) base floor, the §280C(c) reduced-credit election, the §38(c) ceiling and §39 twenty-year carryforwards |
| **§174, §197, ASC 718, ASC 842** | The timing items that dominate real filings: research capitalised and amortised over 5 years, 15-year intangible amortisation, stock compensation, and leases |
| **Year-end close** | Explicit rollforward that writes every carryforward, clears current-year amounts, advances the tax year, and refuses to run twice |
| **Persistence** | Save / load the whole return as JSON, carryforwards and closed-year history included |

Plus topic calculators for §351 formations, corporate distributions and §302 redemptions,
CAMT, Subpart F / GILTI / NCTI, and §199A.

---

## Form 1065 — Partnership (in progress)

> **Status: under construction.** The calculators below are implemented and covered by
> tests. The surrounding return is not finished, and the sections marked *not yet* are
> the honest gaps.

Where Form 1120 asks how income becomes tax, a partnership return asks a harder question:
**whose income is it, and what is each partner's basis in it afterwards?** Almost every
rule below exists because those two answers move independently.

| Area | Implemented |
|---|---|
| **Partner basis mechanics** | §752 liability shares, outside basis, capital account, and the loss limitation stack |
| **Formation** | §721 non-recognition, §724 character taint, disguised sale, holding period, Item N, interests received for services |
| **Current distributions** | §704(c)(1)(B), §735 character on later disposition, §751(b) disproportionate distribution flag |
| **Liquidating distributions** | §736(a) / §736(b) split and the character of §736(a) payments |
| **Sale of an interest** | Amount realised, §751(a) hot assets split, §704(c) on transfer, §743(b) adjustment, resulting buyer basis |
| **§754 election** | §734(b) and §743(b) adjustments, §755 allocation between capital and ordinary classes, previously taxed capital, substantial basis reduction, substantial built-in loss |

Each area has its own test module. A worked §754 scenario is included under `examples/`.

**Not yet:** the return pages and schedules that wrap these calculators are still being
built out, and the edge cases each provision carries are not all covered. Treat this half
as working machinery, not as a finished return.

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

**The mechanics that are easy to get wrong.** §1245 recapture stops at the depreciation
actually taken, so gain above original cost keeps §1231 character. §291(a)(1) recaptures
20% of that figure on corporate real property — a corporate-only rule an individual
selling the same building never meets. The §1231(c) look-back turns a net gain ordinary
to the extent of unrecaptured losses from the last five years, oldest first, while a net
loss stays fully ordinary and does not touch the pool. §263A absorbs the indirect-cost
pool in the ratio of goods sold, so a pure inventory-build year absorbs nothing.

**The suite is checked by mutation.** Deleting the §246(b) NOL exception, removing the
§1245 cap, dropping the §291 20% rate, or reversing the look-back order each make it
fail. That exercise has already earned its keep: it exposed a blind spot where the §172
vintage test used a pre-2018 pool smaller than 80% of taxable income, so capping the pool
changed nothing and the mutant survived. The test now uses a pool large enough to prove a
pre-2018 loss can take taxable income to zero, which is the entire reason vintage is
tracked.

Tests reach the module rather than the Streamlit layer, so anything worth testing has to
be a pure function taking explicit arguments. Pulling `calc_drd_246b`, `calc_4797_recapture`
and `calc_1231_lookback` out of the page code to test them is why they now live in
`calculators/`.

## Checked against a real filer

A corporation's Form 1120 is confidential under §6103, so no public filing can validate
the return itself. What *is* public is the ASC 740 tax footnote — and the effective tax
rate reconciliation in it is, structurally, a schedule of permanent differences. That
makes it something this model can be pointed at.

Winnebago Industries, FY2024 (year ended 31 August 2024). Their disclosed reconciliation
runs from the 21% statutory rate to a 66.2% effective rate, driven by a non-deductible
goodwill impairment and a non-deductible debt inducement charge. Grossing each rate line
up at 21% gives the underlying dollar difference; those were the only inputs:

| Input | From their disclosure |
|---|---|
| Taxable revenue | $114.20M |
| Tax-exempt interest and dividend income | $2.01M (−1.1% rate line) |
| Permanently non-deductible charges | $77.84M (§162(m) 6.6%, debt inducement 19.4%, goodwill 16.6%) |
| General business credits | $3.42M (−8.9%) |

| Result | Model | Winnebago |
|---|---|---|
| Net income per books | **$38,370,000** | $38.37M — their provision of $25.4M ÷ 66.2% |
| Federal tax at 21% | **$23,982,000** | 21.0% + permanents = $23.98M |
| After credits | **$20,562,000** | — |
| Federal provision | $20.56M + valuation allowance $1.92M − uncertain positions $0.65M + other $0.35M = **$22.18M** | $25.40M total − $3.22M state = **$22.18M** |

Book income is the figure worth noticing: nothing told the model what it was. It was
derived from the ledger accounts, and it landed on their pretax income independently.

The last three reconciling items are the honest boundary. A valuation allowance and an
uncertain tax position are ASC 740 constructs about *recognising* tax in financial
statements; neither exists anywhere on a tax return, so a return model should not produce
them.

The scenario is saved at [`examples/winnebago-fy2024.json`](examples/winnebago-fy2024.json)
— load it from the sidebar under **Save / Load** to reproduce the table above. The file
carries the derivation of each figure from the published rate lines in a comment.

Keying these figures in is also what surfaced the §170 loss-year bug now pinned in the
test suite.

## Why the differences are the whole job

`analysis/effective_federal_rate.py` pulls every public filer that reported both a
current federal tax provision and pretax book income for CY2024 from the SEC's XBRL
frames API — 1,710 profitable filers after filtering — and asks how close their federal
tax is to 21% of book income.

```
   10th pct    1.7%
   25th pct    6.8%
     median   15.7%
     75th pct 20.9%
   90th pct   30.1%

  within 21% +/- 2pp: 16.0% of filers
```

If book income were taxable income this would be a spike at 21%. Five filers in six sit
somewhere else. That is the case for modelling the differences rather than the rate.

Read it carefully, though: the numerator is the *current* provision, so the gap reflects
permanent and temporary differences together, and it is federal-only against worldwide
pretax income, so heavy foreign operations read low for reasons that have nothing to do
with book-tax differences.

## A test case built to be run somewhere else

[`examples/acme-2024.md`](examples/acme-2024.md) is a fictional calendar-2024 C
corporation specified precisely enough to key into commercial tax software and compare
line by line. Differential testing against an independent implementation is the only
validation here that is not circular, and the fact pattern is designed to remove
disagreements that would say nothing about the tax logic — the asset was placed in
service two years earlier so no bonus election is in play, the dividends come from a
corporation under 20% owned so the DRD rate is unambiguous, and gross receipts sit under
the §448(c) threshold so §163(j) does not apply.

The model produces taxable income of $378,590 and tax of $79,504 on those facts, with
every intermediate line tabulated for comparison.

Constructing it found two bugs before it was run anywhere else. The §170(b)(2) base was
omitting bad debts, inflating the charitable limit by $4,000. And book income was using
Schedule D line 18, which §1211(a) has already floored at zero, so the disallowed capital
loss was excluded from book income and then added back again on Schedule M-1 — the
integrity check caught that one, landing M-1 $30,000 above line 28.

## What the model cannot say

The Winnebago walk-through above proves internal consistency and nothing more — the
inputs were derived from the answer by grossing the disclosed rate lines up at 21%, so
re-applying 21% only inverts that arithmetic. Saying otherwise would be overclaiming.

`analysis/reconcile_provision.py` asks a question that is not circular. Every filer's
provision differs from 21% of pretax income, and the rate reconciliation lists the
reasons. How much of that gap can this model's vocabulary account for?

```
  all filers                                       n=2379   median 24.2%  within 5%: 18.5%
  no foreign rate differential                     n=1286   median 22.2%  within 5%: 19.6%
  no foreign differential, no valuation allowance   n=584   median 20.9%  within 5%: 20.4%
```

About one filer in five is fully explained, and they are exactly the profile the model
targets — Cal-Maine, Lowe's, CSX, Nobility Homes: US operating companies with ordinary
tax positions. Narrowing to domestic filers with no valuation allowance barely improves
the median, which is the honest result rather than the flattering one.

The residual mixes two different things, and only the first is a real gap:

- **Positions the model has no line for.** The largest residuals name them precisely —
  Ascend Wellness (§280E, which denies cannabis businesses ordinary deductions), Northern
  States Power (regulated-utility excess deferred tax amortisation), Summit Midstream and
  PotlatchDeltic (pass-through and REIT structures where income is not taxed at entity
  level at all).
- **Custom XBRL extension tags.** Filers routinely tag their own reconciling lines rather
  than using the standard element, and no enumeration of standard tags can capture those.

A first check in the same script guards the whole exercise: the disclosed statutory line
equals 21% of pretax income for 83.8% of filers, so the join and the tag names are sound.

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
