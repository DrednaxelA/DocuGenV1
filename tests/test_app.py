import os
import pytest
import main

app = main.app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Redirect file output to a temp directory
    temp_dir = tmp_path / "files"
    temp_dir.mkdir()
    # Patch main.FILES_DIR so create_invoice_pdf writes into our tmp_path
    monkeypatch.setattr(main, "FILES_DIR", str(temp_dir))
    app.config["TESTING"] = True
    return app.test_client()


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Document Generator" in res.data


def test_generate_invoice_minimal(client):
    payload = {
        "document_type": "supplier_invoice",
        "date": "2025-05-01",
        "due_date": "2025-05-01",
        "supplier_name": "Acme",
        "customer_name": "Beta",
        "document_ref": "TEST-REF",
        "currency": "USD",
        "tax_rate": 10,
        "line_items_count": 1,
        "count": 1,
        "total_amount": 100.0,
        "generate_invoices": False
    }
    res = client.post("/generate", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Should return a single file dict
    assert "file" in data
    file_info = data["file"]

    # File should exist on disk under the patched FILES_DIR
    path = os.path.join(main.FILES_DIR, file_info["name"])
    assert os.path.isfile(path)


def test_generate_supplier_statement(client):
    payload = {
        "document_type": "supplier_statement",
        "date_from": "2025-05-01",
        "date_to": "2025-05-02",
        "supplier_name": "Acme",
        "currency": "USD",
        "tax_rate": 10,
        "total_amount": 200.0,
        "number_of_lines": 2,
        "generate_invoices": False
    }
    res = client.post("/generate", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Should return a statement file dict
    assert "file" in data
    stmt = data["file"]

    # File should exist on disk under the patched FILES_DIR
    path = os.path.join(main.FILES_DIR, stmt["name"])
    assert os.path.isfile(path)
