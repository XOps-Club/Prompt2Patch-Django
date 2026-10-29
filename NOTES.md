# Team Submission & AI Log

> [!IMPORTANT]
> **Challenge Duration**: 45 Minutes | **Total Points**: 100 Points Rubric
> **Evaluation Advisory**: Speed is not the winning criterion. Submissions completed via lazy 1-shot prompts (e.g., "fix this whole file") will be penalized under **Pillar 1: Prompt Quality**. Use this log to paste 3 of your prompt sequences.

---

## 1. Team Information
- **Team Name**: Vector Zero
- **Members**: 1. Aakarshi Dwivedi  2. Michael Shah
- **Working Branch**: `Vecter_Zero-solution`

---

## 2. AI Prompting Evidence (Paste your 3 best prompts)
*Show how you guided the AI through iterative reasoning rather than asking it to auto-solve blindly:*

### Prompt 1
- **Defect / Area Investigated**: Initial repository debugging and test workflow
- **Exact Prompt Sent to AI**:
  > Act as my Django debugging partner for this URL shortener. Help me reproduce and understand one failing behavior at a time; I’ll make the code changes. Start with the existing tests, guide me toward a minimal fix, then help me rerun the tests and write a short summary of the diagnosis, changes, and results.

---

### Prompt 2
- **Defect / Area Investigated**: Six reported LinkSnip regressions
- **Exact Prompt Sent to AI**:
  > Just fix the 6 main critical problem: INC-01 archive lifecycle, INC-02 restore slug collision, INC-03 active-link statistics, INC-04 pagination totals, INC-05 QR generation, and INC-06 strict HTTP/HTTPS target URL validation. Analyze and debug them, then report what was changed and why.

---

### Prompt 3
- **Defect / Area Investigated**: Final local verification and evidence
- **Exact Prompt Sent to AI**:
  > Now test all the fixes, run the project on localhost, check that the core bugs are fixed, find any other required issue, and make it ready for a pull request with a clear test and work summary.

---

## 3. Final Submission Checklist Before Calling Judge
- [x] All links tests pass 100% (`python manage.py test links` — 14 tests)
- [x] Django system check passes (`python manage.py check`)
- [x] Web application manually verified locally (`http://127.0.0.1:8000/`)
- [x] Code committed to a dedicated branch (`Vecter_Zero-solution`, not `main`)
- [x] Pull Request opened with a clean description
- [ ] 3 prompt sequences documented above in Section 2
