# Tử Vi Engine repair report

Repository: https://github.com/suneJQK/tu-vi-engine
Branch: `main`

Changes applied:
- Added `.vercelignore` to exclude Git metadata, Python bytecode and test caches from Vercel uploads.
- Added `scripts/build_release_zip.py` to export a clean full-source ZIP while preserving source, data and tests.
- Added `.github/workflows/repair-ci.yml` to compile Python, run pytest, smoke-test FastAPI, and package the project.
- Inspected the repository audit and current tests. The audit records earlier engine fixes for star catalog normalization, AI payload sizing, relationship geometry, and Tiểu vận expectations.

Verification limitation:
- Direct local cloning was blocked by outbound GitHub DNS in this runtime.
- The connected GitHub integration was used to inspect and modify the repository.
- The current GitHub commit has a Vercel failure status, but the connected Vercel account could not resolve the deployment to retrieve its build logs.

To export the complete project from a local clone:

```bash
python scripts/build_release_zip.py
```
