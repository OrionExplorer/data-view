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
   - [⚙️ Using the `mode` Parameter](#️-using-the-mode-parameter)
   - [📧 `/api/v1/email-to-pdf/` – Email to PDF Conversion](#-apiv1email-to-pdf--email-to-pdf-conversion)
     - [✅ 1. Use Case: Converting EML Files to PDF](#️-1-use-case-converting-eml-files-to-pdf)
     - [✅ 2. Use Case: Sending Email Data as JSON](#️-2-use-case-sending-email-data-as-json)
   - [📎 `/api/v1/attachment-to-pdf/` – Attachment to PDF Conversion](#-apiv1attachment-to-pdf--attachment-to-pdf-conversion)
     - [✅ 1. Use Case: Converting Uploaded Files](#️-1-use-case-converting-uploaded-files)
     - [✅ 2. Use Case: Sending Attachment as Base64](#️-2-use-case-sending-attachment-as-base64)
   - [📥 `/api/v1/download/` – Download Converted PDFs](#-apiv1download--download-converted-pdfs)
2. [🚨 Error Handling](#-error-handling)
   - [❌ 1. Insufficient Credits](#-1-insufficient-credits)
   - [❌ 2. Invalid API Key](#-2-invalid-api-key)
   - [❌ 3. File Not Found (Download Endpoint)](#-3-file-not-found-download-endpoint)
3. [🔑 Authentication](#-authentication)
4. [💡 Final Notes](#-final-notes)
5. [📊 Usage](#-usage)
   - [🔑 API Key Management](#-api-key-management)
   - [📌 API Versioning](#-api-versioning)
     - [🚀 Current Version](#-current-version)
     - [📊 Versioning Strategy](#-versioning-strategy)
     - [⚙️ How to Use Versions](#-how-to-use-versions)
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
- **`/api/v1/email-to-pdf/`** – Convert emails to PDF  
- **`/api/v1/attachment-to-pdf/`** – Convert attachments to PDF  
- **`/api/v1/download/`** – Download converted PDF files  

These endpoints support both simple and advanced workflows, making DataView flexible for different business scenarios.

### ⚙️ Using the `mode` Parameter

The `mode` parameter allows you to control the format of the API response. It can be passed as a **GET** parameter in the URL:

- **`mode=file_id`** (default) – Returns a `file_id` for downloading the PDF later.
- **`mode=inline_pdf`** – Returns the PDF directly in the response.
- **`mode=base64_pdf`** – Returns the PDF as a Base64-encoded string in JSON.

Example:
```bash
POST /api/v1/email-to-pdf/?mode=inline_pdf
```

**Security Note:** When using `mode=inline_pdf` or `mode=base64_pdf`, the generated PDF is **not stored on the server**. The file is processed in memory and deleted immediately after the response is sent. This approach helps meet data protection regulations such as **GDPR**, **HIPAA**, and **ISO/IEC 27001**, ensuring that sensitive data is not retained unnecessarily.

---

## 📧 `/api/v1/email-to-pdf/` – Email to PDF Conversion

This endpoint converts an entire email into a PDF file, preserving key metadata (subject, sender, recipient, date) and the body content.

### ✅ **1. Use Case: Converting EML Files to PDF**

**Request:**
```bash
POST /api/v1/email-to-pdf/?mode=file_id
Content-Type: multipart/form-data
X-API-KEY: your_api_key

--boundary
Content-Disposition: form-data; name="file"; filename="email.eml"
Content-Type: message/rfc822

<email content>
--boundary--
```

**Response:**
```json
{
  "file_id": "abc123xyz"
}
```

### ✅ **2. Use Case: Sending Email Data as JSON**

**Request:**
```bash
POST /api/v1/email-to-pdf/?mode=inline_pdf
Content-Type: application/json
X-API-KEY: your_api_key

{
  "subject": "Project Update",
  "sender": "alice@example.com",
  "recipient": "bob@example.com",
  "body": "Hello Bob, here is the project update."
}
```

**Response:**
- Returns the PDF directly with `Content-Type: application/pdf`.

---

## 📎 `/api/v1/attachment-to-pdf/` – Attachment to PDF Conversion

This endpoint is designed to convert document attachments (e.g., DOCX, XLSX, CSV) into PDF files for secure viewing.

### ✅ **1. Use Case: Converting Uploaded Files**

**Request:**
```bash
POST /api/v1/attachment-to-pdf/?mode=file_id
Content-Type: multipart/form-data
X-API-KEY: your_api_key

--boundary
Content-Disposition: form-data; name="file"; filename="document.docx"
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document

<binary file content>
--boundary--
```

**Response:**
```json
{
  "file_id": "def456uvw"
}
```

### ✅ **2. Use Case: Sending Attachment as Base64**

**Request:**
```bash
POST /api/v1/attachment-to-pdf/?mode=base64_pdf
Content-Type: application/json
X-API-KEY: your_api_key

{
  "filename": "report.docx",
  "content": "BASE64_ENCODED_CONTENT"
}
```

**Response:**
```json
{
  "pdf_base64": "JVBERi0xLjQKJ... (truncated)"
}
```

---

## 📥 `/api/v1/download/` – Download Converted PDFs

This endpoint allows users to download previously converted PDF files using the unique `file_id` received after conversion.

**Request:**
```bash
GET /download/abc123xyz
X-API-KEY: your_api_key
```

**Response:**
- Returns the converted PDF file.

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
- **`billing_credit_cost`** – Defines the cost (in credits) for each data chunk processed.
- **`billing_chunk_kb`** – Specifies the size of each data chunk (in KB) used for billing.
- **`billing_min_chunk_kb`** – Defines the minimum data size (in KB) that will be billed, even if the actual data is smaller.

### 📌 API Versioning

DataView API uses versioning to ensure backward compatibility while allowing for continuous improvements and feature updates.

#### 🚀 **Current Version:** `v1`

All API endpoints are prefixed with the version number:

```
/api/v1/email-to-pdf/
/api/v1/attachment-to-pdf/
/api/v1/download/<file_id>/
```

#### 📊 **Versioning Strategy:**

- **Major Versions (v1, v2, ...):** Introduced when backward-incompatible changes are made.
- **Minor Versions (v1.1, v1.2, ...):** For adding new features in a backward-compatible manner.
- **Patch Versions (v1.1.1, v1.1.2, ...):** Bug fixes and security updates without affecting functionality.

#### ⚙️ **How to Use Versions:**

Simply include the version number in the API URL:

```bash
curl -X POST "http://data-view.local/api/v1/email-to-pdf/" \
     -H "x-api-key: YOUR_API_KEY" \
     -F "file=@/path/to/email.eml"
```

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

* **Chunk Size (KB)**: 10.
> Credits are charged for every 10 KB of data transferred.

* **Credit Cost per Chunk**: 0.1.
> Each 10 KB chunk costs **0.1 credit**.

* **Minimum Chunk Size (KB)**: 10.
> The minimum data size charged is 10 KB, even for smaller files.

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
