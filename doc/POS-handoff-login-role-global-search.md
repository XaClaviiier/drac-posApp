# POS Handoff: Login, Roles, WO Estimates, Global Search, and Hover

## 1. Purpose and current status

Continue the automotive AC workshop POS design in **FigCraft first**.
This handoff records the original delegation brief. **UI-04 has since been applied
to the project documents and FigCraft prototype.** Before continuing, read current
`doc/IPD/ipd.md` UI-04 and `doc/DBD/prototype/README.md`, plus
`doc/DBD/prototype/verification-ui04.json`. Do not reimplement this historical brief
or regenerate over the completed artifact without inspecting the current state.

- Project: `C:\Project-Opencode\POS`.
- Handoff created: 2026-10-31.
- User-facing explanations and UI copy: Indonesian.
- Execution brief: English, as requested by the user.
- No production authentication, database, or search backend is included in this slice.
- The user requested this Markdown handoff for delegation to the next session.
  Current implementation evidence is maintained in IPD and the prototype README.

## 2. Read first

Follow applicable AGENTS.md instructions, then read relevant sections of:

1. `doc/CONTEXT.md`: user decisions; newer decisions in this handoff supersede the
   older role policy once recorded there.
2. `doc/PRD/prd.md`: roles, feature scope, and business behavior.
3. `doc/AFD/afd.md`: login, diagnosis, WO, payment, invoice, and status journeys.
4. `doc/TRD/trd.md`: eventual server-side authorization and online/offline boundaries.
5. `doc/BSD/bsd.md`: schema/API source of truth; currently mostly an unfilled template.
6. `doc/DBD/dbd.md` and `doc/DBD/DESIGN_POS_Extend.md`: visual reference lock, tokens,
   and existing prototype motion.
7. `doc/IPD/ipd.md`: record one coherent design slice and acceptance criteria before execution.
8. `doc/DBD/prototype/README.md`: artifact instructions, verification history, limitations.
9. `C:\Project-Opencode\workflow\DESIGN.md`: applicable UI workflow.

Keep each fact in its designated source document. Do not copy table schemas or
visual tokens into multiple documents. Do not populate unrelated `ISI:` fields.

## 3. Existing artifacts and preservation requirements

- Main editable prototype: `doc/DBD/prototype/pos-ui.figcraft`.
- Manual no-motion alternative: `doc/DBD/prototype/pos-ui-no-motion.figcraft`.
- Invoice exports: `doc/DBD/prototype/invoice-template-a4.pdf` and
  `doc/DBD/prototype/screenshot/invoice-template-a4.png`.
- All screenshots and PNG previews belong in `doc/DBD/prototype/screenshot/`.
- Existing pages: `Desktop · Light`, `Mobile · Light`, `Desktop · Dark`,
  `Mobile · Dark`, and `Invoice · Cetak`.
- Prior session reported 11,279 layers and a 489,013-byte animated native file.
  These are historical observations: inspect current artifacts before relying on them.
- Prior work added 112 transition configurations for sidebar, mobile menu, themes,
  payment, and technician-status demos. Hover coverage was not implemented.
- Existing prototype generators, JSON baseline, manifests, and verification scripts
  may predate the added invoice and motion. Do not regenerate/import the old baseline
  over the latest native file and lose those changes. Inspect their coverage first.
- `index.html` is an older standalone browser prototype, not the FigCraft source of truth.
  Do not change it or its local-storage data in this slice.
- FigCraft in the previous session was headless. Metadata and static renders were
  inspected; animated playback and full keyboard interaction were not observed.

## 4. Confirmed user decisions

### 4.1 Roles and branch

- Exactly **Owner, Teknisi, Kasir**.
- Rename Mekanik to **Teknisi** in the active design and requirements.
- Remove Supervisor. Kepala Cabang is not an additional role.
- Transfer Supervisor's operational responsibilities to Teknisi, subject to the
  explicit financial restrictions below; do not blindly inherit unrestricted access.
- One branch only. Multi-branch is a possible future development, not current scope.
- Shared login design uses **username and password**, with role-specific demo journeys.

### 4.2 Financial access and payments

- HPP/purchase-cost information is restricted to **Owner**.
- Teknisi may see customer-facing selling prices in WO and invoices.
- Teknisi must not see purchase prices or restricted expenditure amounts.
- Only **Kasir and Owner** receive/confirm payments. The user explicitly accepted this.
- Do not infer that Teknisi may view profit reports merely because Supervisor formerly could.
- The conversation treated the audit-log "admin side" as Owner, not a fourth role.
  Preserve the three-role model; state this interpretation when presenting the design.

### 4.3 Transaction-local prices

- Teknisi may edit selling unit prices in WO, draft invoices, and other specifically
  authorized transaction modules that require price entry.
- Each edit applies only to that document's line item. It must **not** update the
  Owner's master price or unrelated documents.
- New line items start from a snapshot of the applicable master price.
- User accepted logging every price change, with complete log access restricted to Owner.
- Preserve old and new prices, actor, time, document/item identity, and change reason.
  Mandatory reason and detailed log fields were proposed by the assistant as the
  implementation design, not separately specified field-by-field by the user.
- Editing a transaction price must not be implemented as editing the master record.

### 4.4 Final invoices and money records

- User explicitly confirmed: **only Owner may correct a finalized invoice**.
- Finalized means locked even if it is unpaid; Teknisi and Kasir cannot correct it.
- User explicitly accepted the explanation that correcting the invoice does not
  rewrite money already received.
- Decreasing a paid invoice can create an overpayment; increasing it can create a
  remaining balance. An actual refund is a separate recorded money movement.
- Recommended correction design: reason, actor/time, before/after values, and preserved
  revision history. Do not silently overwrite the original invoice/payment trail.
- No automatic refund, payment cancellation, or external money transfer is authorized.

### 4.5 WO estimates

- User requested an **estimasi harga** field/summary in WO.
- Teknisi enters the services and parts needed after diagnosis.
- Show itemized service/part prices, not only one combined amount.
- Proposed presentation: type, service/part, quantity, unit, selling unit price,
  line subtotal; service subtotal, parts subtotal, total estimate.
- Recommended formula: line subtotal = quantity × unit price; estimate total = sum
  of service and part subtotals. Avoid a disconnected manually entered grand total.
- Recommended WO-to-invoice behavior: copy the WO's transaction prices into the draft
  invoice rather than re-fetching master prices; later invoice edits do not silently
  change the original WO. Distinguish estimated charges from final charges.

### 4.6 Global search and hover

- User wants sidebar search to search globally, not just license plates.
- Approved visual reference: `@shadcnuikit/command1`.
- Proposed groups: pages, customers/vehicles, WO, invoices, services/parts.
  Only include approved/existing entities and role-permitted results.
- Do not leak restricted amounts through search snippets, totals, links, reports,
  or exports. For Teknisi, show permitted selling prices only in authorized contexts.
- User requested hover animation for all; interpret this as all **enabled interactive
  controls**, not static text, documents, or disabled elements.
- Cover buttons/icons, navigation, tabs, clickable cards/rows, login controls, search
  trigger, and result rows. Include focus and pressed equivalents; do not depend on
  hover for touch devices. Preserve the printable invoice as static content.

## 5. Diagnosis versus WO: explanation already given

- Diagnosis answers: **what is wrong, what was found, and what is recommended?**
- WO answers: **what services/parts will be performed/used, by whom, at what estimate,
  and with what progress?**
- Recommended UX: show linked diagnosis summary within WO instead of requiring duplicate entry.
- This is a functional distinction, not an already implemented database relationship.
  `doc/BSD/bsd.md` does not yet define those tables.

## 6. Unresolved policies: do not invent approval

1. **Price limits/approval:** the assistant recommended an Owner-defined edit range
   with approval outside that range. The user has **not approved this policy**.
   Do not add mandatory approval or invent discount percentages as settled behavior.
2. **Stock versus expenditure:** Owner-only HPP is clear. The exact meaning of
   "pengeluaran barang" and whether Teknisi sees stock quantities/usage remains
   incompletely confirmed. Allowing nonfinancial quantities was a recommendation.
   Clarify only if needed to design those screens; do not expand into stock-policy design.
3. **Other price-entry modules:** not enumerated. Implement explicit WO/invoice needs;
   do not grant generic price-edit permission everywhere.
4. **Corrections with completed payments:** the separation of invoice/payment records
   is approved, but exact refund workflow, correction document type, and accounting
   treatment are not specified. Prototype the distinction without inventing settlement policy.

## 7. Verified external reference

The previous session retrieved the public component JSON and documentation:

- Source: https://shadcnuikit.com/r/command1.json
- Documentation/demo: https://shadcnuikit.com/components/command
- Requested CLI: `npx shadcn@latest add @shadcnuikit/command1`

Observed source is a React component using shadcn Command primitives, an input,
icon rows, a selectable list, and an empty state. It is not a complete POS search engine.
The command has **not** been executed. Do not install it into FigCraft or introduce
React dependencies just to reproduce a visual reference.

Adapt its structure to current POS tokens. Global search still requires application
data, destinations, and eventual server-side authorization. FigCraft can simulate
representative states; do not promise unrestricted live typing/database search.

Prior Refero MCP research failed with `NO_SUBSCRIPTION`. Report current access honestly;
use the explicit user reference and incumbent design rather than pretending research succeeded.

## 8. Research behind recommendations, not additional user requirements

- NIST least privilege supports giving each role only the access needed for its tasks:
  https://csrc.nist.gov/glossary/term/least_privilege
- OpenStax contribution margin explains why selling above part purchase cost does
  not alone establish profitability:
  https://openstax.org/books/principles-managerial-accounting/pages/3-1-explain-contribution-margin-and-calculate-contribution-margin-per-unit-contribution-margin-ratio-and-total-contribution-margin
- OpenStax job-order costing is relevant to costing individual repair jobs:
  https://openstax.org/books/principles-managerial-accounting/pages/4-1-distinguish-between-job-order-costing-and-process-costing
- GAO Green Book 2025 discusses preventive/detective controls and separation of duties:
  https://www.gao.gov/assets/gao-25-107721.pdf

These support recommendations, not a claim that Owner-only HPP is mandatory or that
a universal margin/discount percentage exists. GAO is not a legal requirement for this workshop.

## 9. Suggested skills

Load only those needed for the phase, following current project instructions:

- `refero-design`: research/reference lock for the user-selected search design and login.
- `impeccable`: UI implementation; relevant animate/operate guidance for feedback.
- `change-sop`: if required for the nontrivial existing-design/policy change.
- `security-review`: evaluate the proposed role/privacy boundaries while explicitly
  distinguishing design review from server-enforced security.
- Use the required planner/review roles when the applicable workflow requires them.
- Browser-testing skills only if a browser implementation is separately authorized.

User enabled Caveman, RTK, and Ponytail in the previous session. A genuinely new
session must follow the session-choice SOP; do not assume activation carries over.
Use concise Indonesian chat and normal prose in persistent documents.

## 10. Compact execution prompt

> Method: Context → Decisions → Tasks → Constraints → Acceptance → Evidence.
> Read sources by reference; avoid repeating whole documents. Clarify only decisions
> that change authorization or scope. Reuse components and representative states.

```text
Act as a senior product designer extending the existing POS FigCraft prototype.
Read this handoff and applicable project instructions. Use confirmed decisions in
section 4; treat sections 5-8 recommendations and unresolved items according to
their labels. Do not promote a recommendation into an approved policy.

Work in one coherent prototype slice:
1. Inspect current native artifact, then reconcile new decisions in CONTEXT/PRD/AFD
   and relevant technical/design docs. Record acceptance criteria in IPD first.
2. Create username/password login and Owner/Teknisi/Kasir demo journeys.
3. Rename active Mekanik UI to Teknisi and remove Supervisor role usage.
   Apply the confirmed restrictions, not blanket inherited financial access.
4. Link diagnosis to WO, add itemized services/parts and reconciled estimate totals.
   Demonstrate local selling-price edits without changing master prices.
5. Show draft/final invoice states, Owner-only corrections and Owner-only audit log.
   Preserve payment history; represent overpayment or remaining balance separately.
6. Add role-aware global search based on command1, adapted to current tokens.
   Include initial, results, no-results, loading/error, selected-result states.
7. Add reusable hover/focus/pressed/disabled coverage to interactive families.
   Preserve existing motion and a manually selectable no-motion alternative.

Constraints:
- FigCraft only; no backend, dependency installation, schema migration, real
  credentials, actual payment/refund, index.html changes, or branch features.
- Preserve unrelated screens, current invoice template, and existing navigation.
- Reuse variants/components; avoid duplicating every full screen for every hover.
- Do not regenerate from an outdated baseline and overwrite newer native changes.
- Clearly label sample data, simulated calculations/search/login, and unsupported
  interactions. Never claim UI visibility equals secure server authorization.
- Do not invent price-approval thresholds or grant unspecified module permissions.

Acceptance:
- All three role journeys have correct allowed destinations.
- Teknisi/Kasir cannot reach Owner-only HPP, audit, or final-correction views through
  their demo navigation/search. Owner can demonstrate those views.
- Estimate rows/totals reconcile; a local price edit leaves master and other
  transactions unchanged in the demonstrated states.
- Final invoice is locked except for Owner correction; recorded receipts stay intact.
- Global-search examples cover more than plates and open relevant destinations.
- Interactive families have consistent state feedback across relevant themes/devices.
- Inspect rendered variants and interaction targets; save, close, and reopen.
- Verify the updated no-motion alternative does not regress content to an old version.
- Report observed evidence separately from unverified playback, keyboard, live
  filtering/calculation, backend authorization, and OS reduced-motion behavior.

Deliver concise Indonesian summary, updated artifact paths, demo starting points,
verification evidence, and remaining limitations. Update README for any generator
or manifest limitations introduced or inherited by the new design.
```

## 11. First action for the next session

Inspect current artifact/documents and resolve only policy questions that block the
requested views. Do not restart all discovery or ask the user to repeat confirmed
role, login, branch, transaction-price, payment, or finalized-invoice decisions.
