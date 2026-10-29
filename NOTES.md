# Team Submission & AI Log

> [!IMPORTANT]
> **Challenge Duration**: 45 Minutes | **Total Points**: 100 Points Rubric
> **Evaluation Advisory**: Speed is not the winning criterion. Submissions completed via lazy 1-shot prompts (e.g., "fix this whole file") will be penalized under **Pillar 1: Prompt Quality**. Use this log to paste 3 of your prompt sequences.

---

## 1. Team Information
- **Team Name**: Byte
- **Members**: 1. Avipsa Deb 2. Aditi Nandiraju
- **Working Branch**: `team-solution`

---

## 2. AI Prompting Evidence (Paste your 3 best prompts)
*Show how you guided the AI through iterative reasoning rather than asking it to auto-solve blindly:*

### Prompt 1
- **Defect / Area Investigated**: Backend lifecycle, collision, analytics, pagination, QR, and URL-validation incidents.
- **Exact Prompt Sent to AI**:
  > "The active-tab state and archived-tab state are not behaving correctly. Debug all confirmed variable-state bugs, make all the changes, and do not change endpoints or database structure."
- **Reasoning Sequence**:
  1. Locate each incident from the implementation and public tests.
  2. Confirm the failing state with focused Django tests.
  3. Apply the smallest service/view changes that preserve existing routes and response fields.
  4. Re-run the complete Django test suite.

---

### Prompt 2
- **Defect / Area Investigated**: Duplicate `manage.py` files and project entry-point selection.
- **Exact Prompt Sent to AI**:
  > "There are two files with the same name but in different folders. One may be used somewhere instead of the other. Debug it."
- **Reasoning Sequence**:
  1. Compare both entry-point wrappers and their working-directory assumptions.
  2. Trace Makefile, README, dev-container, and Django settings references.
  3. Verify whether the wrappers resolve the same Django settings module.
  4. Standardize documented commands around the root wrapper where possible.

---

### Prompt 3
- **Defect / Area Investigated**: Variable-state, duplicate-name, reset, empty-value, scope, numeric-slug, and click-telemetry bugs.
- **Exact Prompt Sent to AI**:
  > "Are these problems: variable is right, maybe something at the bottom is overwriting it; two variables have the same name but code is using the wrong one; the value keeps resetting, maybe the function runs twice; the variable is empty, maybe it was declared inside the wrong block. Debug all these and find where these errors are and what changes to make."
- **Reasoning Sequence**:
  1. Search assignments, function definitions, DOM lookups, and state updates across the frontend and backend.
  2. Confirm that application state was not being reset or overwritten by repeated initialization or duplicate DOM IDs.
  3. Identify the inverted active/archived tab flag and corrected its intended archive filter value.
  4. Move unique-click detection into the same transaction as click logging and link-counter updates.
  5. Add ID-first with short-code fallback lookup for numeric custom slugs in detail and QR endpoints.
  6. Replace fragile HTTP error-text matching with explicit validation and slug-conflict exception types.
  7. Verify numeric slug detail/QR behavior and invalid URL responses with focused Django checks.

---

## 3. Final Submission Checklist Before Calling Judge
- [x] All test suites pass 100% (`make test`) — 12 Django tests passed.
- [ ] Web application manually verified in browser (`make run`)
- [x] Code committed to a dedicated branch (`team-solution`, not `main`) — committed as `68246db`.
- [ ] Pull Request opened with clean description
- [x] 3 prompt sequences documented above in Section 2
