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
    # Common fields
    count = int(data.get("count", 1))
    currency = data.get("currency", "USD")
    supplier = data.get("supplier_name", "Acme Corp")
    customer = data.get("customer_name", "Beta LLC")
    total_amount = data.get("total_amount", "")        
    
    # Supplier Statement
    number_of_lines = int(data.get("number_of_lines", 0))
    generate_invoices = data.get("generate_invoices", False)
    date = data.get("date", "2025-04-30")

    # Dispatch for Supplier Statement
    if doc_type == "Supplier Statement":
        return generate_supplier_statement(data)

    filenames = []
    for i in range(count):
        filename = f"{doc_type.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(FILES_DIR, filename)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"{doc_type}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Document Reference: {data.get('document_ref', '')}", ln=True)
        pdf.cell(0, 10, f"Supplier: {supplier}", ln=True)
        pdf.cell(0, 10, f"Customer: {customer}", ln=True)
        pdf.cell(0, 10, f"Date: {date}", ln=True)
        due_date = data.get("due_date")
        if due_date:
            pdf.cell(0, 10, f"Due Date: {due_date}", ln=True)
        pdf.ln(10)

        # Add line items
        line_items_count = int(data.get("line_items_count", 3))
        total_float = 0
        pdf.set_font("Arial", "B", 12)
        pdf.cell(80, 10, "Description", 1)
        pdf.cell(30, 10, "Quantity", 1)
        pdf.cell(40, 10, "Unit Price", 1)
        pdf.cell(40, 10, "Amount", 1, ln=True)
        pdf.set_font("Arial", "", 12)
        for _ in range(line_items_count):
            quantity = float(data.get("quantity", round(random.uniform(1, 10))))
            unit_price = float(data.get("unit_price", round(random.uniform(10, 1000), 2)))
            amount = quantity * unit_price
            total_float += amount
            pdf.cell(80, 10, f"{random.choice(product_descriptions)}", 1)
            pdf.cell(30, 10, f"{quantity:.0f}", 1)
            pdf.cell(40, 10, f"{currency} {unit_price:.2f}", 1)
            pdf.cell(40, 10, f"{currency} {amount:.2f}", 1, ln=True)
        pdf.ln(10)

        tax_rate = float(data.get("tax_rate", 20))
        tax_amount = total_float * (tax_rate / 100)
        grand_total = total_float + tax_amount
        pdf.cell(0, 10, f"Subtotal: {currency} {total_float:.2f}", ln=True)
        pdf.cell(0, 10, f"Tax Rate: {tax_rate}%", ln=True)
        pdf.cell(0, 10, f"Tax Amount: {currency} {tax_amount:.2f}", ln=True)
        pdf.cell(0, 10, f"Total: {currency} {grand_total:.2f}", ln=True)
        pdf.output(filepath)
        filenames.append({"name": filename, "url": f"/files/{filename}"})

    return jsonify({"file": filenames[0] if count == 1 else filenames})

@app.route("/files/<filename>")
def serve_file(filename):
    if '..' in filename or filename.startswith('/'):
        return {"error": "Invalid filename"}, 400
    if not os.path.exists(os.path.join(FILES_DIR, filename)):
        return {"error": "File not found"}, 404
    return send_from_directory(FILES_DIR, filename, as_attachment=True)


def generate_supplier_statement(data):
    # Extract Supplier Statement fields
    supplier = data.get("supplier_name", "Acme Corp")
    date = data.get("date", "2025-04-30")
    total = data.get("total_amount", "")
    lines = int(data.get("number_of_lines", 0))
    make_invs = data.get("generate_invoices", False)

    # Build PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Supplier Statement", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Supplier: {supplier}", ln=True)
    pdf.cell(0, 10, f"Date: {date}", ln=True)
    pdf.cell(0, 10, f"Total Amount: {total}", ln=True)
    pdf.cell(0, 10, f"Number of Lines: {lines}", ln=True)

    # TODO: If make_invs, generate separate invoices here

    filename = f"Supplier_Statement_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(FILES_DIR, filename)
    pdf.output(filepath)
    return jsonify({"file": {"name": filename, "url": f"/files/{filename}"}})


def cleanup_old_files():
    """Cleanup files older than 1 hour"""
    current_time = time.time()
    for filename in os.listdir(FILES_DIR):
        filepath = os.path.join(FILES_DIR, filename)
        if current_time - os.path.getmtime(filepath) > 1800:
            try:
                os.remove(filepath)
            except OSError:
                pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
