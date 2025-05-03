from flask import Flask, request, send_from_directory, jsonify, render_template
from flask_cors import CORS
from fpdf import FPDF
import os
import uuid
import time
import random

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

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/generate", methods=["POST"])
def generate_pdf():
    cleanup_old_files()
    data = request.json

    doc_type = data.get("document_type", "invoice").replace("_", " ").title()
    # route supplier statement separately
    if doc_type == "Supplier Statement":
        return generate_supplier_statement(data)

    # generate one or more invoices/receipts/notes
    count = int(data.get("count", 1))
    results = [create_invoice_pdf(data) for _ in range(count)]
    return jsonify({"file": results[0] if count == 1 else results})


def create_invoice_pdf(data):
    # extract and sanitize inputs
    doc_type = data.get("document_type", "invoice").replace("_", " ").title()
    currency = data.get("currency", "USD")
    supplier = data.get("supplier_name", "Acme Corp")
    customer = data.get("customer_name", "Beta LLC") if doc_type != "Pos Receipt" else None
    # always random ref
    document_ref = f"INV-{uuid.uuid4().hex[:8]}"
    date = data.get("date", "2025-04-30")
    due_date = data.get("due_date", "") if doc_type != "Pos Receipt" else None
    # split total amount across lines
    total_amount = float(data.get("total_amount", 0))
    line_items_count = int(data.get("line_items_count", 3))
    number_of_lines = int(data.get("number_of_lines", 1))
    tax_rate = float(data.get("tax_rate", 20))

    # evenly divide amounts
    net_each = round(total_amount / line_items_count, 2) if line_items_count>0 else 0

    # build PDF
    filename = f"{doc_type.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(FILES_DIR, filename)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, doc_type, ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Document Reference: {document_ref}", ln=True)
    pdf.cell(0, 10, f"Supplier: {supplier}", ln=True)
    if customer:
        pdf.cell(0, 10, f"Customer: {customer}", ln=True)
    pdf.cell(0, 10, f"Date: {date}", ln=True)
    if due_date:
        pdf.cell(0, 10, f"Due Date: {due_date}", ln=True)
    pdf.ln(10)

    # table header
    pdf.set_font("Arial", "B", 12)
    pdf.cell(80, 10, "Description", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(40, 10, "Unit Price", 1)
    pdf.cell(40, 10, "Amount", 1, ln=True)
    pdf.set_font("Arial", "", 12)

    total_net = 0
    for i in range(line_items_count):
        desc = random.choice(product_descriptions)
        qty = 1
        amount = net_each
        total_net += amount
        pdf.cell(80, 10, desc, 1)
        pdf.cell(30, 10, f"{qty}", 1)
        pdf.cell(40, 10, f"{currency} {net_each:.2f}", 1)
        pdf.cell(40, 10, f"{currency} {amount:.2f}", 1, ln=True)
    pdf.ln(5)

    tax_amt = round(total_net * tax_rate/100,2)
    grand = round(total_net + tax_amt,2)
    pdf.cell(0, 10, f"Net Amount: {currency} {total_net:.2f}", ln=True)
    pdf.cell(0, 10, f"Tax Rate: {tax_rate}%", ln=True)
    pdf.cell(0, 10, f"Tax Amount: {currency} {tax_amt:.2f}", ln=True)
    pdf.cell(0, 10, f"Total: {currency} {grand:.2f}", ln=True)
    pdf.output(filepath)

    return {"name": filename, "url": f"/files/{filename}"}

@app.route("/files/<filename>")
def serve_file(filename):
    if '..' in filename or filename.startswith('/'):
        return {"error": "Invalid filename"}, 400
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return {"error": "File not found"}, 404
    return send_from_directory(FILES_DIR, filename, as_attachment=True)


def generate_supplier_statement(data):
    supplier = data.get("supplier_name", "Acme Corp")
    date = data.get("date", "2025-04-30")
    lines = int(data.get("number_of_lines", 0))
    make_invs = data.get("generate_invoices", False)

    # build statement PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0,10,"Supplier Statement",ln=True)
    pdf.set_font("Arial","",12)
    pdf.cell(0,10,f"Supplier: {supplier}",ln=True)
    pdf.cell(0,10,f"Date: {date}",ln=True)
    pdf.ln(5)

    # list each line as invoice reference
    invoice_datas = []
    for i in range(lines):
        pdf.cell(0,10,f"Invoice Line {i+1}",ln=True)
        invoice_datas.append({
            **data,
            "document_type":"supplier_invoice"
        })
    statement_file = create_invoice_pdf({
        **data,
        "document_type":"supplier_statement"
    })  # reuse invoice for statement if needed

    pdf.output(os.path.join(FILES_DIR, statement_file['name']))

    response = {"file": statement_file}
    if make_invs:
        response['invoices'] = [create_invoice_pdf(d) for d in invoice_datas]
    return jsonify(response)


def cleanup_old_files():
    now = time.time()
    for f in os.listdir(FILES_DIR):
        p = os.path.join(FILES_DIR,f)
        if now - os.path.getmtime(p) > 1800:
            try: os.remove(p)
            except: pass

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))