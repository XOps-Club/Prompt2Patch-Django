# Team Submission & AI Log

> [!IMPORTANT]
> **Challenge Duration**: 45 Minutes | **Total Points**: 100 Points Rubric
> **Evaluation Advisory**: Speed is not the winning criterion. Submissions completed via lazy 1-shot prompts (e.g., "fix this whole file") will be penalized under **Pillar 1: Prompt Quality**. Use this log to paste 3 of your prompt sequences.

---

## 1. Team Information
- **Team Name**: The Mosaic
- **Members**: 1. Arpit Kumar Shah  2. Kunal Verma  3. Nittin Kumar Pandey
- **Working Branch**: `team-solution`

---

## 2. AI Prompting Evidence (Paste your 3 best prompts)
*Show how you guided the AI through iterative reasoning rather than asking it to auto-solve blindly:*

### Prompt 1
- **Defect / Area Investigated**: Six reported link lifecycle, telemetry, QR, pagination, and URL-validation defects
- **Exact Prompt Sent to AI**:
  > Read the README.md file, it contains 6 bugs "## 🛠️ Incident Report: Reported Defects & Mission Brief": ... Go through the code and fix them.
  >
  > The AI inspected the README, service layer, views, frontend helper, and tests; it then implemented the six focused fixes and ran the Django test suite.

---

### Prompt 2
- **Defect / Area Investigated**: Django server startup and homepage failure
- **Exact Prompt Sent to AI**:
  > Running "python manage.py runserver" gives a bunch of errors. Fix them.
  >
  > The AI reproduced the request-time failure, identified the missing `links_link` table, applied migrations, and verified system checks and an HTTP 200 homepage response.

---

### Prompt 3
- **Defect / Area Investigated**: URL scope clarification and broken in-page navigation
- **Exact Prompt Sent to AI**:
  > Is the link shortener supposed to accept only github links and nothing else? Also, #about, analytics, and docs doesn't work in the server.
  >
  > The AI verified that the service accepts valid HTTP(S) URLs rather than GitHub-only URLs, added matching `about`, `analytics`, and `docs` anchors, and verified the rendered homepage.

---

## 3. Final Submission Checklist Before Calling Judge
- [ ] All test suites pass 100% (`make test`; `make` is unavailable in the Windows environment)
- [x] Web application manually verified with a `runserver` smoke test and HTTP 200 response
- [x] Code is on the dedicated `team-solution` branch
- [ ] Pull Request opened with clean description (requires repository hosting access)
- [x] 3 prompt sequences documented above in Section 2
