# Phase 1.1 — Workflow Foundation

## Scope

This patch centralizes Order and ProjectRequest state mutations without changing
models, database schema, URLs or API response contracts.

### Added
- `orders/workflow.py`
- `projects/workflow.py`
- `orders/test_workflow_phase1.py`
- `projects/test_workflow_phase1.py`

### Updated
- `orders/views.py`
- `projects/serializers.py`
- `projects/expiration_handler.py`

## Not included in this slice
- payment settlement transition (`payments/settlement_views.py`)
- progress percentages
- stage deadlines
- API timeline envelope

Those are intentionally deferred to Phase 1.2+ so this patch stays small and
regression-friendly.

## Apply on Windows PowerShell

From `D:\projects\retoucher`:

```powershell
git status
git checkout -b phase/01-workflow-foundation
Copy-Item "$HOME\Downloads\retoucher_phase1_1_workflow_foundation_FINAL.patch" .
git apply --check .\retoucher_phase1_1_workflow_foundation_FINAL.patch
git apply .\retoucher_phase1_1_workflow_foundation_FINAL.patch
```

## Validate

```powershell
cd backend
python manage.py test orders.test_workflow_phase1 projects.test_workflow_phase1 --verbosity 2
python manage.py test projects --verbosity 1
python manage.py test orders --verbosity 1
python manage.py test --verbosity 1
python manage.py check
python manage.py makemigrations --check --dry-run
```

Expected migration result: `No changes detected`.

## Rollback before commit

```powershell
cd D:\projects\retoucher
git restore backend/orders/views.py backend/projects/serializers.py backend/projects/expiration_handler.py
git clean -f backend/orders/workflow.py backend/projects/workflow.py backend/orders/test_workflow_phase1.py backend/projects/test_workflow_phase1.py backend/PHASE_1_1_APPLY.md
```
