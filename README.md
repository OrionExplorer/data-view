# 📄 DataView API [![data-view](https://github.com/OrionExplorer/data-view/actions/workflows/data-view-django.yml/badge.svg)](https://github.com/OrionExplorer/data-view/actions/workflows/data-view-django.yml) [![CodeQL Advanced](https://github.com/OrionExplorer/data-view/actions/workflows/codeql.yml/badge.svg)](https://github.com/OrionExplorer/data-view/actions/workflows/codeql.yml)

**DataView** is an API-based platform designed for secure and efficient conversion of emails and attachments to PDF files.  
It focuses on **data security**, **seamless integration**, and a flexible **credit-based billing system** tailored to each user.

The system provides endpoints for:  
- Converting raw email content to PDF with embedded security features  
- Converting various document attachments to PDF for secure viewing  
- Managing API usage through a credit-based billing model  

---

## 📚 Table of Contents

1. [📊 Use Cases for DataView API](#-use-cases-for-dataview-api)
   - [📧 `/api/email-to-pdf/` – Email to PDF Conversion](#-apiemail-to-pdf--email-to-pdf-conversion)
     - [✅ 1. Use Case: Converting EML Files to PDF](#-1-use-case-converting-eml-files-to-pdf)
     - [✅ 2. Use Case: Sending Email Data as JSON](#-2-use-case-sending-email-data-as-json)
   - [📎 `/api/attachment-to-pdf/` – Attachment to PDF Conversion](#-apiattachment-to-pdf--attachment-to-pdf-conversion)
     - [✅ 1. Use Case: Converting Uploaded Files](#-1-use-case-converting-uploaded-files)
     - [✅ 2. Use Case: Sending Attachment as Base64](#-2-use-case-sending-attachment-as-base64)
   - [📥 `/api/download/` – Download Converted PDFs](#-apidownload--download-converted-pdfs)
     - [✅ 1. Use Case: Downloading a Converted Email PDF](#-1-use-case-downloading-a-converted-email-pdf)
     - [✅ 2. Use Case: Downloading a Converted Attachment PDF](#-2-use-case-downloading-a-converted-attachment-pdf)
2. [🚨 Error Handling](#-error-handling)
   - [❌ 1. Insufficient Credits](#-1-insufficient-credits)
   - [❌ 2. Invalid API Key](#-2-invalid-api-key)
   - [❌ 3. File Not Found (Download Endpoint)](#-3-file-not-found-download-endpoint)
3. [🔑 Authentication](#-authentication)
4. [💡 Final Notes](#-final-notes)
5. [📊 Usage](#-usage)
   - [🔑 API Key Management](#-api-key-management)
6. [💳 Billing System](#-billing-system)
   - [💡 Billing Example](#-billing-example)
     - [📤 Upload Calculation (5 MB file)](#-upload-calculation-5-mb-file)
     - [📥 Download Calculation (12-mb-file)](#-download-calculation-12-mb-file)
     - [✅ Total Credits Charged](#-total-credits-charged)
     - [⚠️ Important Notes](#-important-notes)
     - [🚨 Example Error (Insufficient Credits)](#-example-error-insufficient-credits)
   - [📈 API Request Billing History](#-api-request-billing-history)
   - [💳 Top-up Credits](#-top-up-credits)
7. [🚀 Technologies Used](#-technologies-used)
   - [Core Technologies](#core-technologies)
   - [Document Conversion & Processing](#document-conversion--processing)
   - [Database & Storage](#database--storage)
   - [Containerization & Orchestration](#containerization--orchestration)
   - [Security & API Management](#security--api-management)
8. [📦 Deployment Architecture](#-deployment-architecture)
9. [⚙️ Deployment Instructions](#-deployment-instructions)
10. [📜 License](#-license)

---

# 📊 Use Cases for DataView API

This section describes common use cases for interacting with the DataView API, focusing on the following endpoints:  
- **`/api/email-to-pdf/`** – Convert emails to PDF  
- **`/api/attachment-to-pdf/`** – Convert attachments to PDF  
- **`/api/download/`** – Download converted PDF files  

These endpoints support both simple and advanced workflows, making DataView flexible for different business scenarios.

---

## 📧 `/api/email-to-pdf/` – Email to PDF Conversion

This endpoint converts an entire email into a PDF file, preserving key metadata (subject, sender, recipient, date) and the body content.

### ✅ **1. Use Case: Converting EML Files to PDF**

- **Scenario:** A user has received an email in `.eml` format and wants to archive it as a PDF for legal compliance.  
- **Request Format:** `multipart/form-data`

#### **Example Request:**

```bash
curl -X POST "http://data-view.local/api/email-to-pdf/" \
     -H "x-api-key: YOUR_API_KEY" \
     -F "file=@/path/to/email.eml"
```

#### **Response:**

```json
{
  "status": "success",
  "file_id": "abc123xyz",
  "file_size": 204800
}
```

---

### ✅ **2. Use Case: Sending Email Data as JSON**

- **Scenario:** An external system automatically forwards emails as JSON (without `.eml` files) to convert them into PDFs for quick previews.  
- **Request Format:** `application/json`

#### **Example Request:**

```bash
curl -X POST "http://data-view.local/api/email-to-pdf/" \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "subject": "Project Update",
           "sender": "alice@example.com",
           "recipient": "bob@example.com",
           "body": "Hello Bob, here is the project update.",
           "attachments": [
               {
                   "filename": "report.docx",
                   "content": "BASE64_ENCODED_CONTENT"
               }
           ]
         }'
```

---

## 📎 `/api/attachment-to-pdf/` – Attachment to PDF Conversion

This endpoint is designed to convert document attachments (e.g., DOCX, XLSX, CSV) into PDF files for secure viewing.

### ✅ **1. Use Case: Converting Uploaded Files**

- **Scenario:** A user uploads a Microsoft Word document to convert it into a PDF for secure sharing.  
- **Request Format:** `multipart/form-data`

#### **Example Request:**

```bash
curl -X POST "http://data-view.local/api/attachment-to-pdf/" \
     -H "x-api-key: YOUR_API_KEY" \
     -F "file=@/path/to/document.docx"
```

#### **Response:**

```json
{
  "status": "success",
  "file_id": "def456uvw",
  "file_size": 102400
}
```

---

### ✅ **2. Use Case: Sending Attachment as Base64**

- **Scenario:** An automated system sends a document (encoded in Base64) directly to the API for conversion without storing it locally.  
- **Request Format:** `application/json`

#### **Example Request:**

```bash
curl -X POST "http://data-view.local/api/attachment-to-pdf/" \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "filename": "invoice.xlsx",
           "content": "BASE64_ENCODED_CONTENT"
         }'
```

---

## 📥 `/api/download/` – Download Converted PDFs

This endpoint allows users to download previously converted PDF files using the unique `file_id` received after conversion.

### ✅ **1. Use Case: Downloading a Converted Email PDF**

- **Scenario:** A user wants to download the PDF generated from an email conversion.

#### **Example Request:**

```bash
curl -X GET "http://data-view.local/api/download/abc123xyz/" \
     -H "x-api-key: YOUR_API_KEY" \
     -o "email_converted.pdf"
```

---

### ✅ **2. Use Case: Downloading a Converted Attachment PDF**

- **Scenario:** A PDF generated from an attachment conversion needs to be retrieved for record-keeping.

#### **Example Request:**

```bash
curl -X GET "http://data-view.local/api/download/def456uvw/" \
     -H "x-api-key: YOUR_API_KEY" \
     -o "attachment_converted.pdf"
```

---

## 🚨 Error Handling

### ❌ **1. Insufficient Credits**

If the user's account does not have enough credits to process the request:

```json
{
  "error": "Insufficient credits. Please top up your account.",
  "required_credits": 10,
  "available_credits": 5
}
```

---

### ❌ **2. Invalid API Key**

When an incorrect or missing API key is provided:

```json
{
  "error": "Invalid API key."
}
```

---

### ❌ **3. File Not Found (Download Endpoint)**

If the provided `file_id` does not exist or the user lacks permission:

```json
{
  "error": "File does not exist or you do not have access."
}
```

---

## 🔑 **Authentication**

All API requests require an `x-api-key` header for authentication.

```bash
-H "x-api-key: YOUR_API_KEY"
```

Ensure that the API key has sufficient credits for both uploads and downloads, as DataView uses a **credit-based billing system**.

---

## 💡 Final Notes

- **Efficient Data Flow:** DataView supports both direct file uploads and JSON-based automation for seamless integrations.  
- **Flexible Formats:** Compatible with common file types, ensuring smooth document conversions.  
- **Secure Access:** API key authentication and credit-based billing for controlled usage.

---

## 📊 Usage

### 🔑 API Key Management

The core model for authentication and billing is the **`ApiKey`** model, which is linked to a specific **`User`**.  
Each `ApiKey` includes the following properties:
- **`api_key`** – Auto-generated key used for authenticating API requests via the custom header `x-api-key`.  
- **`credits`** – A virtual currency used to track API usage. Credits are consumed based on data transfers during both uploads and downloads.

---

## 💳 Billing System

DataView uses a **credit-based billing system** to track API usage:  
- **Credits** are consumed for both **uploading data** (e.g., emails, attachments) and **downloading converted PDFs**.  
- **Billing is user-specific**, based on the API key associated with each account.  
- Credit consumption is proportional to data size and processing demands.  

If there are insufficient credits, API requests will return an error with status code **402 (Payment Required)**.

---

### 💡 **Billing Example**

Consider the following scenario where a user uploads a document and later downloads the converted PDF file.

#### **Scenario:**
- **Upload:** A document with a size of **5 MB (5120 KB)** is uploaded for conversion.  
- **Download:** The converted PDF file has a size of **1.2 MB (1229 KB)** and is downloaded.

#### **Billing Configuration:**

```python
billing = {
    'chunk_KB': 10,
    'credits': 0.1,
    'min_chunk_KB': 10
}
```

- **`chunk_KB = 10`** – Credits are charged for every 10 KB of data transferred.  
- **`credits = 0.1`** – Each 10 KB chunk costs **0.1 credit**.  
- **`min_chunk_KB = 10`** – The minimum data size charged is 10 KB, even for smaller files.

---

#### **📤 Upload Calculation (5 MB file):**

1. **File Size:** 5120 KB  
2. **Chunks:** 5120 KB ÷ 10 KB = **512 chunks**  
3. **Credits Charged:** 512 × 0.1 = **51.2 credits**

---

#### **📥 Download Calculation (1.2 MB file):**

1. **File Size:** 1229 KB  
2. **Chunks:** 1229 KB ÷ 10 KB = **123 chunks** (rounded up)  
3. **Credits Charged:** 123 × 0.1 = **12.3 credits**

---

### ✅ **Total Credits Charged**

- **Upload:** 51.2 credits  
- **Download:** 12.3 credits  

**Total Credits Used:** **63.5 credits**

---

### ⚠️ **Important Notes:**
- **Credits are calculated before processing the request.**  
- If the user does not have enough credits, the API will return an error **before** uploading or downloading starts.  
- **Minimum chunk size applies:** Even files smaller than 10 KB will be charged as 1 full chunk (0.1 credit).  

---

### 🚨 **Example Error (Insufficient Credits):**

```json
{
  "error": "Insufficient credits. Please top up your account.",
  "required_credits": 63.5,
  "available_credits": 40.0
}
```
- **`required_credits`** – Number of credits needed to process the request.  
- **`available_credits`** – Current credit balance of the API key.

In this case, the user had **40 credits**, which is insufficient for the total cost of **63.5 credits**.  
The request will be rejected until the user tops up their credits.

---

### 📈 API Request Billing History

Every API request is logged using the **`ApiKeyCreditHistory`** model. This provides detailed tracking of API usage for billing purposes.

#### **Tracked Information:**
- **API Key** used for the request  
- **Date and Time** of the request  
- **Requested Endpoint** with query parameters  
- **Response Size** (in KB)  
- **Chunk Size** (from the model’s `billing` property at the time of the request)  
- **Number of Chunks** generated  
- **Credit Cost per Chunk** (from the model’s `billing` property)  
- **Total Credits Charged** for the request  
- **Credit Balance Before Charge**  
- **IP Address** of the requester  
- **Unique Request Identifier** (as stored in system logs)  

---

### 💳 Top-up Credits

To add credits to an API key, the system uses the **`ApiKeyCreditTopUp`** model.

#### **Top-up Details Tracked:**
- **API Key** to which the credits are applied  
- **Credits Added** to the API key’s current balance  
- **Date and Time** of the top-up transaction  

Credits are immediately available after a successful top-up, allowing uninterrupted API usage.

---

## 🚀 Technologies Used

### **Core Technologies**
- **Django 5.1.5** – Backend framework for API management
- **Gunicorn** – WSGI HTTP server for running the Django application
- **Nginx** – Reverse proxy for handling incoming HTTP(S) requests

### **Document Conversion & Processing**
- **LibreOffice (headless mode)** – For converting document formats to PDF
- **soffice** – Command-line interface for LibreOffice
- **WeasyPrint 64.0** – HTML/CSS to PDF converter for rendering email content
- **BeautifulSoup4 4.12.3** – HTML parsing and data extraction from email content

### **Database & Storage**
- **PostgreSQL 17.2** – Relational database for managing user data and billing
- **Volumes:**  
  - `postgres_data` – Persistent data storage for PostgreSQL  
  - `shared_files` – Shared volume between containers for file management

### **Containerization & Orchestration**
- **Docker** – For containerizing and orchestrating services
- **Bridge Network** – Custom Docker network `app-network` to facilitate inter-container communication

### **Security & API Management**
- **API Key Authentication** – Secure access to API endpoints
- **.env Files** – Environment variable management for secure configuration (`.env.data-view.prod`, `.env.data-view-db.prod`)
- **HTTPS** (via Nginx reverse proxy) – Secure data transmission (configurable)

---

## 📦 Deployment Architecture

The system is composed of multiple Docker containers:

- **`core`** – Runs the Django application using Gunicorn  
  - Exposes port `8888` internally  
  - Depends on **PostgreSQL** and **LibreOffice** services  
- **`libreoffice`** – Headless LibreOffice for document conversion  
  - Exposes port `5000` for internal communication  
- **`db`** – PostgreSQL 17.2 database for data storage  
  - Mapped to port `5455` for database management  
- **`nginx`** – Reverse proxy for handling incoming HTTP(S) requests  
  - Exposes external port `9393` for public API access  

The containers communicate via the **`app-network`** (bridge network).

---

## ⚙️ Deployment Instructions

1. **Build and run the containers:**

```bash
docker-compose up --build -d
```

2. **Access the API via Nginx:**

```bash
http://data-view.local:9393/
```

3. **Check running containers:**

```bash
docker-compose ps
```

## 📜 License

This project is licensed under the **Elastic License 2.0 (ELv2)**.  
- **Usage:** Free for personal, internal, and non-commercial use.  
- **Commercial SaaS Use:** Requires a separate commercial license.  
- **Restrictions:** You may not offer the DataView project as a SaaS or hosted service without explicit permission.  

See [LICENSE](LICENSE.md) for full details.
