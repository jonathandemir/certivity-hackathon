"""certreq: Produktspezifikation → Anforderungen nach UN-Regelungen (Certivity-Challenge).

Pipeline (jede Stufe austauschbar, siehe docs/PLAN.md):
    case.load_case → select.select_regulations → extract.extract_requirements → submission.write_submission
Bewertung: evaluate.evaluate (validate.py + score_local.py + F2) und evaluate.record (Beleg nach experiments/runs/).
"""
