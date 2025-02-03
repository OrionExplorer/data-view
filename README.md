# 📄 DataView API

**DataView** is an API-based platform designed for secure and efficient conversion of emails and attachments to PDF files.  
It focuses on **data security**, **seamless integration**, and a flexible **credit-based billing system** tailored to each user.

The system provides endpoints for:  
- Converting raw email content to PDF with embedded security features  
- Converting various document attachments to PDF for secure viewing  
- Managing API usage through a credit-based billing model  

---

## 📊 Usage

### 🔑 API Key Management

The core model for authentication and billing is the **`ApiKey`** model, which is linked to a specific **`User`**.  
Each `ApiKey` includes the following properties:
- **`api_key`** – Auto-generated key used for authenticating API requests via the custom header `x-api-key`.  
- **`credits`** – A virtual currency used to track API usage. Credits are consumed based on data transfers during both uploads and downloads.

---

### ⚡ Billing Model

Every model that can be queried via the API must define a **`billing`** property. This determines how many credits are deducted for data processing.

#### **Example of a Billing Property Declaration:**

```python
billing = {
    'chunk_KB': 10,
    'credits': 0.1,
    'min_chunk_KB': 10
}
```

- **`chunk_KB`** – The size of each data chunk (in KB) for which credits will be charged.  
- **`credits`** – The number of credits charged per data chunk of `chunk_KB` size.  
- **`min_chunk_KB`** – The minimum data chunk size (in KB) that will trigger a credit deduction.

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

## 💳 Billing System

DataView uses a **credit-based billing system** to track API usage:  
- **Credits** are consumed for both **uploading data** (e.g., emails, attachments) and **downloading converted PDFs**.  
- **Billing is user-specific**, based on the API key associated with each account.  
- Credit consumption is proportional to data size and processing demands.  

If there are insufficient credits, API requests will return an error with status code **402 (Payment Required)**.

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

---

## 📄 License

MIT License – See [LICENSE](LICENSE) for details.
