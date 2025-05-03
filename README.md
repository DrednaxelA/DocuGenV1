# DocuGenV1

DocuGenV1 is a Flask-based web application for generating professional PDF documents such as invoices, supplier statements, and POS receipts. It features a dynamic frontend form, real-time PDF generation, and optional invoice linking within supplier statements.

## 🔧 Features

- ✅ Generate invoices, supplier statements, and POS receipts
- ✅ Split totals across dynamic line items
- ✅ Localized date formatting based on currency
- ✅ PDF generation with auto-cleanup of old files
- ✅ Linked invoice generation from within statements
- ✅ Currency and tax rate support

## 🧪 Live Testing

This app is deployed on [Render](https://render.com/) for testing. Push to the main branch will auto-deploy.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Pip

### Installation
```bash
git clone https://github.com/yourusername/DocuGenV1.git
cd DocuGenV1
pip install -r requirements.txt
```
### Run Locally
```bash
python main.py
```
Visit http://localhost:5000 in your browser.

## 🗂️ Project Structure

```bash
DocuGenV1/
├── main.py                 # Core Flask app logic
├── requirements.txt        # Dependencies
├── files/                  # Generated PDFs (auto-cleaned after 30 mins)
└── templates/
    └── index.html          # UI for form inputs
```

## 🛠️ Environment Variables

| Variable | Default | Description           |
| -------- | ------- | --------------------- |
| `PORT`   | 5000    | Port Flask listens on |

## 🔮 Planned Features
- User authentication
- Support for Bank Statements and Sales documents
- Editable line items before PDF generation
- Customizable PDF templates
- Email sending of generated documents
- Persistent storage and document history

## 📄 License
MIT License. Use freely, contribute openly.

  _This README reflects the current state of an evolving project. Contributions and ideas are welcome!
_


