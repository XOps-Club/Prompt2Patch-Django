# Team Submission & AI Log

> [!IMPORTANT]
> **Challenge Duration**: 45 Minutes | **Total Points**: 100 Points Rubric
> **Evaluation Advisory**: Speed is not the winning criterion. Submissions completed via lazy 1-shot prompts (e.g., "fix this whole file") will be penalized under **Pillar 1: Prompt Quality**. Use this log to paste 3 of your prompt sequences.

---

## 1. Team Information
- **Team Name**: Delta
- **Members**: 1. ______________________  2. ______________________  3. ______________________
- **Working Branch**: `Delta`

---

## 2. AI Prompting Evidence (Paste your 3 best prompts)
*Show how you guided the AI through iterative reasoning rather than asking it to auto-solve blindly:*

### Prompt 1
- **Defect / Area Investigated**: Reproduce and classify LinkSnip regressions
- **Exact Prompt Sent to AI**:
  > Clone the challenge repository into a new workspace folder, create the
  > Team Delta branch, run the baseline suite unchanged, and report all failing
  > test names and assertions without changing application code.

---

### Prompt 2
- **Defect / Area Investigated**: Lifecycle, analytics, pagination, and collision root causes
- **Exact Prompt Sent to AI**:
  > Trace each failing lifecycle and query test from the public suite to the
  > service implementation. Form three falsifiable hypotheses, prove the
  > wrong assignments and aggregate boundaries, and propose one minimal fix per
  > verified root cause.

---

### Prompt 3
- **Defect / Area Investigated**: QR and protocol contracts plus verification
- **Exact Prompt Sent to AI**:
  > Implement the backend and frontend QR contracts, centralize strict HTTP/HTTPS
  > URL validation, run every links test, check the Django configuration, migrate
  > the database, and verify the application through its local server.

---

## 3. Final Submission Checklist Before Calling Judge
- [ ] All test suites pass 100% (`make test`)
- [ ] Web application manually verified in browser (`make run`)
- [ ] Code committed to a dedicated branch (`team-solution`, not `main`)
- [ ] Pull Request opened with clean description
- [ ] 3 prompt sequences documented above in Section 2
