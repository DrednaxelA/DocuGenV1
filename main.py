from flask import Flask, request, send_from_directory, jsonify, render_template
from flask_cors import CORS
from fpdf import FPDF
import os
import uuid
import time
import random
from datetime import datetime
from werkzeug.utils import secure_filename

product_descriptions = [
    "Premium Leather Office Chair",
    "Wireless Mechanical Keyboard",
    "4K Ultra HD Monitor 27-inch",
    "Ergonomic Mouse Pad",
    "USB-C Fast Charging Cable",
    "Bluetooth Noise-Canceling Headphones",
    "Portable SSD 1TB",
    "LED Desk Lamp with Wireless Charging",
    "Laptop Cooling Stand",
    "HD Webcam with Microphone",
    "Standing Desk Converter",
    "Wireless Gaming Mouse",
    "Smart Power Strip",
    "Mini Air Purifier",
    "Desk Cable Management Kit"
]

app = Flask(__name__)
CORS(app)
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

def format_date_for_pdf(iso_date: str, currency: str) -> str:
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
    except Exception:
        return iso_date
    return dt.strftime("%m/%d/%Y") if currency.upper() == "USD" else dt.strftime("%d/%m/%Y")

def safe_float(val, fallback=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return fallback

def safe_int(val, fallback=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return fallback

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/generate", methods=["POST"])
def generate_pdf():
    cleanup_old_files()
    data = request.json

    doc_type = data.get("document_type", "invoice").replace("_", " ").title()
    if doc_type == "Supplier Statement":
        return generate_supplier_statement(data)

    count = safe_int(data.get("count"), 1)
    filenames = [create_invoice_pdf(data) for _ in range(count)]
    return jsonify({"file": filenames[0] if count == 1 else filenames})

def create_invoice_pdf(data):
    doc_type = data.get("document_type", "Invoice").replace("_", " ").title()
    currency = data.get("currency", "USD")
    supplier = data.get("supplier_name", "Acme Corp")
    customer = data.get("customer_name") or "Beta LLC"
    document_ref = data.get("document_ref") or f"INV-{uuid.uuid4().hex[:8]}"
    date_iso = data.get("date") or datetime.today().strftime("%Y-%m-%d")
    due_date_iso = data.get("due_date") or ""
    line_items_count = safe_int(data.get("line_items_count"), 3)
    total_amount = safe_float(data.get("total_amount"), 0)
    tax_rate = safe_float(data.get("tax_rate"), 20)

    date_str = format_date_for_pdf(date_iso, currency)
    due_str = format_date_for_pdf(due_date_iso, currency) if due_date_iso else None
    unit_price = (total_amount / line_items_count) if line_items_count > 0 else 0

    filename = f"{doc_type.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(FILES_DIR, filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, doc_type, ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Document Reference: {document_ref}", ln=True)
    pdf.cell(0, 10, f"Supplier: {supplier}", ln=True)
    if doc_type != "Pos Receipt":
        pdf.cell(0, 10, f"Customer: {customer}", ln=True)
    pdf.cell(0, 10, f"Date: {date_str}", ln=True)
    if due_str and doc_type != "Pos Receipt":
        pdf.cell(0, 10, f"Due Date: {due_str}", ln=True)
    pdf.ln(10)

    total_net = 0
    pdf.set_font("Arial", "B", 12)
    pdf.cell(80, 10, "Description", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(40, 10, "Unit Price", 1)
    pdf.cell(40, 10, "Amount", 1, ln=True)

    pdf.set_font("Arial", "", 12)
    for _ in range(line_items_count):
        amount = unit_price
        total_net += amount
        pdf.cell(80, 10, random.choice(product_descriptions), 1)
        pdf.cell(30, 10, "1", 1)
        pdf.cell(40, 10, f"{currency} {unit_price:.2f}", 1)
        pdf.cell(40, 10, f"{currency} {amount:.2f}", 1, ln=True)
    pdf.ln(10)

    gross = total_amount
    net = gross / (1 + tax_rate/100)
    tax_amt = gross - net

    pdf.cell(0, 10, f"Net Amount: {currency} {net:.2f}", ln=True)
    pdf.cell(0, 10, f"Tax Rate: {tax_rate}%", ln=True)
    pdf.cell(0, 10, f"Tax Amount: {currency} {tax_amt:.2f}", ln=True)
    pdf.cell(0, 10, f"Total: {currency} {gross:.2f}", ln=True)

    pdf.output(filepath)
    return {"name": filename, "url": f"/files/{filename}"}

@app.route("/files/<filename>")
def serve_file(filename):
    safe_name = secure_filename(filename)
    filepath = os.path.join(FILES_DIR, safe_name)
    if not os.path.exists(filepath):
        return {"error": "File not found"}, 404
    return send_from_directory(FILES_DIR, safe_name, as_attachment=True)

def generate_supplier_statement(data):
    supplier = data.get("supplier_name", "Acme Corp")
    date_from_iso = data.get("date_from") or datetime.today().strftime("%Y-%m-%d")
    date_to_iso   = data.get("date_to") or datetime.today().strftime("%Y-%m-%d")
    currency      = data.get("currency",  "USD")
    tax_rate      = safe_float(data.get("tax_rate"), 20)
    make_invs     = data.get("generate_invoices", False)

    if data.get("number_of_lines") is not None:
        data["line_items_count"] = data["number_of_lines"]

    from_str = format_date_for_pdf(date_from_iso, currency)
    to_str   = format_date_for_pdf(date_to_iso, currency)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Supplier Statement", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Supplier: {supplier}", ln=True)
    pdf.cell(0, 8, f"Period: {from_str}  –  {to_str}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "Invoice No", 1)
    pdf.cell(40, 8, "Date", 1)
    pdf.cell(40, 8, "Net", 1, align="R")
    pdf.cell(40, 8, "Tax", 1, align="R")
    pdf.cell(40, 8, "Total", 1, ln=True, align="R")

    pdf.set_font("Arial", "", 12)
    total_statement = 0.0

    invoice_refs = []
    num_lines = safe_int(data.get("number_of_lines"), 0)

    for i in range(num_lines):
        inv_data = {
            "document_type":   "invoice",
            "supplier_name":   supplier,
            "customer_name":   data.get("customer_name") or "Beta LLC",
            "date":            date_from_iso,
            "due_date":        data.get("due_date") or date_to_iso,
            "currency":        currency,
            "line_items_count": safe_int(data.get("line_items_count"), 3),
            "total_amount":     safe_float(data.get("total_amount"), 0),
            "tax_rate":         tax_rate
        }

        if make_invs:
            inv = create_invoice_pdf(inv_data)
            invoice_refs.append(inv)
            inv_name = inv["name"]
        else:
            inv_name = f"INV-{uuid.uuid4().hex[:6]}"

        gross = inv_data["total_amount"]
        net   = gross / (1 + tax_rate / 100)
        tax   = gross - net

        date_str = format_date_for_pdf(inv_data["date"], currency)
        pdf.cell(40, 8, inv_name, 1)
        pdf.cell(40, 8, date_str, 1)
        pdf.cell(40, 8, f"{currency} {net:.2f}", 1, align="R")
        pdf.cell(40, 8, f"{currency} {tax:.2f}", 1, align="R")
        pdf.cell(40, 8, f"{currency} {gross:.2f}", 1, ln=True, align="R")

        total_statement += gross

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(160, 8, "Total Due:", 1)
    pdf.cell(40, 8, f"{currency} {total_statement:.2f}", 1, ln=True, align="R")

    statement_filename = f"Supplier_Statement_{uuid.uuid4().hex[:8]}.pdf"
    statement_filepath = os.path.join(FILES_DIR, statement_filename)
    pdf.output(statement_filepath)

    resp = {
        "file": {"name": statement_filename, "url": f"/files/{statement_filename}"}
    }
    if make_invs:
        resp["invoices"] = invoice_refs

    return jsonify(resp)

def cleanup_old_files():
    now = time.time()
    for f in os.listdir(FILES_DIR):
        path = os.path.join(FILES_DIR, f)
        if now - os.path.getmtime(path) > 1800:
            try:
                os.remove(path)
            except OSError:
                pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
