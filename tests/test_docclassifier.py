from datetime import date

import pytest
from docx import Document
from openpyxl import Workbook

from docclassifier import KeywordClassifier, NamingConvention, RenamePipeline, default_registry
from docclassifier.pipeline import undo


def make_docx(path, *lines):
    d = Document()
    for ln in lines:
        d.add_paragraph(ln)
    d.save(path)


def make_xlsx(path, title, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = title
    for r in rows:
        ws.append(r)
    wb.save(path)


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "sub" / "deep").mkdir(parents=True)
    make_docx(tmp_path / "scan001.docx", "Acme Invoice", "Invoice number 42", "Amount due: $100", "Bill to: Bob")
    make_xlsx(tmp_path / "sub" / "book1.xlsx", "Q3 Budget", [["Revenue", 10], ["Expenses", 5], ["Forecast", 7]])
    make_docx(tmp_path / "sub" / "deep" / "x.docx", "Zebra", "nothing special here")
    (tmp_path / "sub" / "deep" / "bad.docx").write_text("not a real docx")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    return tmp_path


def pipeline(template="{category}_{title}"):
    return RenamePipeline(default_registry(), KeywordClassifier(), NamingConvention(template))


def test_plan_recurses_classifies_and_skips(tree):
    plan = pipeline().plan(tree)
    names = {a.source.name: a.target.name for a in plan.actions}
    assert names["scan001.docx"] == "invoice_acme-invoice.docx"
    assert names["book1.xlsx"] == "budget_q3-budget.xlsx"
    assert names["x.docx"] == "other_zebra.docx"
    skipped = {s.path.name for s in plan.skipped}
    assert {"bad.docx", "image.png"} <= skipped


def test_dry_run_changes_nothing_and_apply_then_undo(tree):
    before = sorted(p.name for p in tree.rglob("*"))
    p = pipeline()
    plan = p.plan(tree)
    assert sorted(x.name for x in tree.rglob("*")) == before
    log = tree / "log.json"
    assert p.apply(plan, log) == 3
    assert (tree / "invoice_acme-invoice.docx").exists()
    assert undo(log) == 3
    assert sorted(x.name for x in tree.rglob("*") if x.name != "log.json") == before


def test_collisions_get_numeric_suffix(tmp_path):
    for n in ("a", "b"):
        make_docx(tmp_path / f"{n}.docx", "Same Title", "meeting agenda", "attendees", "minutes")
    plan = pipeline().plan(tmp_path)
    assert sorted(a.target.name for a in plan.actions) == [
        "meeting-notes_same-title.docx", "meeting-notes_same-title_2.docx"]


def test_rerun_is_idempotent(tree):
    p = pipeline()
    p.apply(p.plan(tree))
    assert p.plan(tree).actions == []


def test_date_template_uses_document_metadata(tmp_path):
    make_docx(tmp_path / "a.docx", "Hello")
    plan = pipeline("{date}_{title}").plan(tmp_path)
    assert plan.actions[0].target.name.startswith(str(date.today().year)[:2])


def test_unknown_template_field_rejected():
    with pytest.raises(ValueError):
        NamingConvention("{nope}")
