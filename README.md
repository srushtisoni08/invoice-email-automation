# 📧 Invoice Email Automation

A Python automation tool that **monitors a Gmail inbox, extracts invoice information from emails and attachments (PDF/Excel), and stores structured data into an Excel report automatically.**

The system runs continuously and checks the inbox every **5 minutes**, ensuring new invoices are processed without manual intervention.

---

# 🚀 Features

* 📥 Automatically monitors Gmail inbox using **IMAP**
* 📎 Processes **PDF and Excel invoice attachments**
* 🧾 Extracts invoice data from **email body + attachments**
* 🔄 **Merge strategy** ensures missing fields are filled from email body
* 📊 Saves all invoice records to a structured **Excel report**
* ⏱ Runs automatically every **5 minutes**
* 📂 Automatically organizes downloaded attachments

---

# 🗂 Project Structure

```
invoice-email-automation
│
├── main.py
├── config.py
├── requirements.txt
├── .env
│
├── email_service
│   ├── email_client.py
│   └── attachment_handler.py
│
├── extractors
│   ├── body_extractor.py
│   ├── pdf_extractor.py
│   └── excel_extractor.py
│
├── storage
│   └── excel_writer.py
│
├── utils
│   └── helpers.py
│
└── attachments
```

---

# 📊 Extracted Invoice Fields

| Field          | Description                       |
| -------------- | --------------------------------- |
| Vendor Name    | Supplier company name             |
| Client Name    | Company or person billed          |
| Invoice Number | Unique invoice identifier         |
| Invoice Date   | Invoice issue date                |
| Due Date       | Payment due date                  |
| GST Number     | Indian GSTIN                      |
| Total Amount   | Total payable amount              |
| Due Amount     | Remaining outstanding amount      |
| Currency       | INR / USD / EUR / GBP             |
| Source File    | Attachment filename or email body |
| Processed At   | Timestamp of processing           |

---

# ⚙️ Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/invoice-email-automation.git
cd invoice-email-automation
```

---

## 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3️⃣ Configure Environment Variables

Create a `.env` file in the project root:

```
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
```

⚠️ Use a **Gmail App Password**, not your normal Gmail password.

Generate it here:

https://myaccount.google.com/apppasswords

---

## 4️⃣ Enable Gmail IMAP

Go to:

```
Gmail Settings → Forwarding and POP/IMAP → Enable IMAP
```

---

# ▶️ Running the Project

```bash
python main.py
```

The system will:

1. Check unread emails immediately
2. Download invoice attachments
3. Extract invoice fields
4. Save structured records into `invoices.xlsx`
5. Repeat the process **every 5 minutes**

---

# 🧠 Extraction Strategy

The system uses a **hybrid extraction approach**:

### Email Body Extraction

Regex-based parsing identifies invoice fields written in the email text.

### Attachment Extraction

Supported formats:

* **PDF invoices** → processed using `pdfplumber`
* **Excel invoices** → parsed using `pandas`

### Merge Logic

If a field is missing in the attachment, the system **fills it using email body data**.

This prevents missing values for fields like:

* Client Name
* GSTIN
* Due Date

---

# 📄 Output Report

All extracted data is stored in:

```
invoices.xlsx
```

Features of the generated report:

* Styled header row
* Alternating row colors
* Frozen header for easier navigation
* Auto-updated **Grand Total** calculation

---

# 📦 Dependencies

| Package       | Purpose                        |
| ------------- | ------------------------------ |
| pdfplumber    | Extract text from PDF invoices |
| pandas        | Parse Excel attachments        |
| openpyxl      | Write Excel output file        |
| python-dotenv | Load environment variables     |
| schedule      | Run automated inbox checks     |

---

# 🧪 Example Email

```
Subject: Invoice #INV-2024-0089

Vendor Name: TechSoft Solutions Pvt Ltd
Client Name: Rajesh Enterprises
Invoice No: INV-2024-0089
Invoice Date: 05/03/2024
Due Date: 20/03/2024
GSTIN: 27AAPFU0939F1ZV
Total Amount: ₹118000
Due Amount: ₹118000
```

---

# ⚠️ Limitations

* Regex extraction may fail on **heavily formatted invoices**
* Password-protected PDFs are not supported
* Only `.pdf`, `.xls`, `.xlsx` attachments are processed

For higher accuracy, services like **AWS Textract or Google Document AI** can be integrated.

---

# 📜 License

MIT License — free to use, modify, and distribute.
