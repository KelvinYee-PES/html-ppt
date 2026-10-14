"""Automated tests for Phase 3 API endpoints."""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from htmlppt.api.app import app

client = TestClient(app)
FIXTURE_HTML = Path(__file__).parent / "fixtures" / "html" / "deck_slides.html"


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_presets_and_palettes():
    res_presets = client.get("/api/presets")
    assert res_presets.status_code == 200
    assert len(res_presets.json()) >= 5

    res_palettes = client.get("/api/palettes")
    assert res_palettes.status_code == 200
    assert len(res_palettes.json()) >= 5


def test_brand_api_flow(tmp_path):
    # 1. Create a brand
    brand_data = {
        "id": "api_test_brand",
        "organization": "API Org",
        "name": "API Brand",
        "colors": {"accent1": "1E40AF"},
        "roles": {"primary": "1E40AF"},
    }
    res = client.post("/api/brands", json=brand_data)
    assert res.status_code == 200
    assert res.json()["id"] == "api_test_brand"

    # 2. Get the brand
    res_get = client.get("/api/brands/api_test_brand")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "API Brand"

    # 3. List brands
    res_list = client.get("/api/brands")
    assert res_list.status_code == 200
    assert any(b["id"] == "api_test_brand" for b in res_list.json())

    # 4. Delete brand
    res_del = client.delete("/api/brands/api_test_brand")
    assert res_del.status_code == 200


def test_conversion_job_flow():
    html_text = FIXTURE_HTML.read_text(encoding="utf-8")

    # 1. Create Job
    res = client.post(
        "/api/jobs",
        data={"html_content": html_text, "preset": "corporate", "palette": "ocean"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    job_id = data["job_id"]
    assert data["slide_count"] == 7
    assert "deck_model" in data

    # 2. Get Job
    res_job = client.get(f"/api/jobs/{job_id}")
    assert res_job.status_code == 200
    assert res_job.json()["slide_count"] == 7

    # 3. Update slides (reorder or delete)
    res_patch = client.patch(
        f"/api/jobs/{job_id}/slides",
        json={"delete_indices": [6]},  # delete last quote slide
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["slide_count"] == 6

    # 4. Download PPTX
    res_pptx = client.get(f"/api/jobs/{job_id}/pptx")
    assert res_pptx.status_code == 200
    assert res_pptx.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert len(res_pptx.content) > 10000


SPLIT_HTML = """<!DOCTYPE html><html><head><title>Strategie für 2027 – €</title></head><body>
<section class="slide"><h1>Opening</h1><p>Intro</p></section>
<section class="slide"><h2>Long list</h2><ul>
""" + "".join(f"<li>Point number {i} with a little bit of text</li>" for i in range(14)) + """
</ul></section>
<section class="slide"><h2>Last</h2><p>Final words here.</p></section>
</body></html>"""


def test_slide_ops_address_split_slides():
    """Overflow-split slides must be individually addressable by preview index and id."""
    res = client.post("/api/jobs", data={"html_content": SPLIT_HTML, "preset": "corporate"})
    assert res.status_code == 200, res.text
    data = res.json()
    job_id = data["job_id"]
    slides = data["deck_model"]["slides"]
    ids = [s["id"] for s in slides]
    assert len(ids) == len(set(ids)), "continuation slides must have unique ids"

    titles = [_title(s) for s in slides]
    last_idx = len(slides) - 1
    assert "Last" in titles[last_idx]

    # Delete the final slide by its preview index; the split list must survive intact.
    res_del = client.patch(f"/api/jobs/{job_id}/slides", json={"delete_indices": [last_idx]})
    assert res_del.status_code == 200, res_del.text
    after = [_title(s) for s in res_del.json()["deck_model"]["slides"]]
    assert after == titles[:last_idx]

    # Reorder must be a strict permutation.
    bad = client.patch(f"/api/jobs/{job_id}/slides", json={"reorder_indices": [0]})
    assert bad.status_code == 422

    # Download with a non-Latin-1 title must not crash header encoding.
    res_pptx = client.get(f"/api/jobs/{job_id}/pptx")
    assert res_pptx.status_code == 200
    assert "filename*=UTF-8''" in res_pptx.headers["content-disposition"]


def test_cannot_delete_every_slide():
    res = client.post("/api/jobs", data={"html_content": SPLIT_HTML})
    data = res.json()
    count = len(data["deck_model"]["slides"])
    res_del = client.patch(
        f"/api/jobs/{data['job_id']}/slides", json={"delete_indices": list(range(count))}
    )
    assert res_del.status_code == 422


def _title(slide: dict) -> str:
    return " ".join(
        r["text"]
        for el in slide["elements"]
        if el["kind"] == "text"
        for p in el["paras"]
        for r in p["runs"]
    )
