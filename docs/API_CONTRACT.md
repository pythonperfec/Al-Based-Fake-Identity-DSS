# API Contract Specification

**Version:** `v1.1.0`  
**Base URL:** `/api/v1`

---

## Global Invariants & Conventions

1. **Identifiers:** All IDs are opaque UUIDv4 strings. Document numbers are never used as identifiers.
2. **PII Masking:** Extracted document numbers are masked keeping only the last 4 characters visible (e.g., `*****9821`). Raw OCR text and MRZ lines are never returned or logged.
3. **Audit Identifiers:** In this MVP, `case_id` equals `screening_id`.
4. **Risk Score Semantics:** `risk_score` is a screening signal (floating point `0.0` - `100.0`), **NOT** a fraud probability percentage.
5. **Null Rules:**
   - When `status` is `"queued"` or `"processing"`, `risk_level` and `risk_score` MUST be `null`.
   - When `status` is `"failed"`, `risk_level` is set to `"incomplete"`, `risk_score` is `null`, and `reasons` MUST be non-empty.
6. **Enums & Allowed Types:**
   - **Document Type:** `"passport"` | `"national_id"` (strictly enforced, no other types permitted)
   - **Allowed Upload MIME Types:** `image/jpeg`, `image/png` only (no PDF allowed)
   - **Screening Status:** `"queued"`, `"processing"`, `"completed"`, `"incomplete"`, `"failed"`
   - **Risk Level:** `"low"`, `"review_required"`, `"high"`, `"incomplete"`
   - **Check Name:** `"ocr"`, `"mrz_checksum"`, `"expiry"`, `"date_consistency"`, `"format"`, `"watchlist"`, `"tamper"`, `"face"`
   - **Check State:** `"passed"`, `"flagged"`, `"not_performed"`, `"could_not_verify"`
   - **Allowed Finding Types (Issues ONLY):**
     - `"MRZ_CHECKSUM_MISMATCH"`
     - `"EXPIRED_DOCUMENT"` (severity: `"medium"`; note that document expiry is a validity issue, not proof of forgery)
     - `"DATE_INCONSISTENCY"`
     - `"INVALID_FORMAT"`
     - `"WATCHLIST_MATCH"`
     - `"ELA_REGION_ANOMALY"` (evidence_ref: `bbox:x1,y1,x2,y2`; tamper reasons must state "possible", never "confirmed")
     - `"METADATA_SOFTWARE_TAG"`
     - `"NOISE_INCONSISTENCY"`
   - **Finding Severity:** `"low"`, `"medium"`, `"high"`
   - **Review Decision:** `"confirmed"`, `"overridden"`, `"escalated"`
   - **Audit Actions:** `"SCREENING_SUBMITTED"`, `"INSPECTION_COMPLETED"`, `"IMAGE_VIEWED"`, `"FINDINGS_VIEWED"`, `"HUMAN_REVIEW_RECORDED"`
   - **User Roles:** `"officer"`, `"admin"` (Pre-seeded default users: `"officer"`, `"admin"`)

---

## Standard Error Envelope & Status Codes

All non-2xx responses adhere to the standard JSON error envelope:
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description of the error."
}
```

### HTTP Status Code Reference

| Status Code | Primary Error Codes | Description |
|---|---|---|
| `400 Bad Request` | `BAD_REQUEST`, `IDEMPOTENCY_KEY_REQUIRED`, `INVALID_DOCUMENT_TYPE` | Missing required headers (e.g. Idempotency-Key) or malformed payload |
| `401 Unauthorized` | `UNAUTHORIZED` | Missing, expired, or invalid bearer token |
| `403 Forbidden` | `FORBIDDEN` | Authenticated role lacks permission (e.g. admin attempting review) |
| `404 Not Found` | `NOT_FOUND` | Resource (screening, finding, evidence) does not exist |
| `409 Conflict` | `CONFLICT` | Concurrent state conflict on screening resource |
| `413 Payload Too Large` | `PAYLOAD_TOO_LARGE` | Uploaded document image exceeds maximum size limit (10MB) |
| `415 Unsupported Media Type`| `UNSUPPORTED_MEDIA_TYPE` | Uploaded MIME type is not `image/jpeg` or `image/png` |
| `422 Unprocessable Entity`| `VALIDATION_ERROR` | Schema validation error (e.g. review notes under 10 chars) |
| `429 Too Many Requests`| `RATE_LIMIT_EXCEEDED` | Request rate limit exceeded |

---

## 1. Authentication

### `POST /api/v1/auth/login`
Authenticates a user via `username` and issues a JWT token. Seed users are `"officer"` and `"admin"`. Both roles have read access to all endpoints, but only `"officer"` can post reviews. Login events are logged internally but excluded from the case audit endpoint.

#### Request
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "username": "officer",
  "password": "SecurePassword123!"
}
```

#### Response: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "officer"
}
```

#### Error Response: `401 Unauthorized`
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid username or password"
}
```

---

## 2. Document Screenings

### `POST /api/v1/screenings`
Uploads a document image for asynchronous inspection.
- **Idempotency:** The `Idempotency-Key` header is **strictly required**. Replaying the same key by the same user returns the original screening unchanged without creating a new background job.

#### Request
- **Headers:**
  - `Authorization: Bearer <token>`
  - `Idempotency-Key: 7b9d62d2-8f92-4b21-8280-975da620c354` *(Required)*
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: `[binary image data: image/jpeg or image/png only]`
  - `document_type`: `"passport"` | `"national_id"`

#### Response: `202 Accepted`
```json
{
  "screening_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498",
  "status": "queued",
  "document_type": "passport",
  "created_at": "2026-10-29T19:45:00Z"
}
```

#### Error Response: `400 Bad Request` (Missing Idempotency-Key)
```json
{
  "error": "IDEMPOTENCY_KEY_REQUIRED",
  "message": "Idempotency-Key header is required"
}
```

#### Error Response: `415 Unsupported Media Type` (e.g. PDF Uploaded)
```json
{
  "error": "UNSUPPORTED_MEDIA_TYPE",
  "message": "Allowed upload types are image/jpeg and image/png only"
}
```

---

### `GET /api/v1/screenings`
Retrieves a paginated list of screenings, sorted newest first. Supports optional status and risk_level filtering.

#### Request
- **Headers:** `Authorization: Bearer <token>`
- **Query Parameters:**
  - `limit`: `integer` (default: 20, max: 100)
  - `offset`: `integer` (default: 0)
  - `status`: `string` *(optional)* — `"queued" | "processing" | "completed" | "incomplete" | "failed"`
  - `risk_level`: `string` *(optional)* — `"low" | "review_required" | "high" | "incomplete"`

#### Response: `200 OK`
```json
{
  "total": 3,
  "items": [
    {
      "screening_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498",
      "status": "completed",
      "risk_level": "review_required",
      "risk_score": 68.5,
      "requires_human_review": true,
      "document_type": "passport",
      "created_at": "2026-10-29T19:45:00Z",
      "updated_at": "2026-10-29T19:45:08Z"
    },
    {
      "screening_id": "2d1a33ee-92bf-4632-9ab1-a083b4c10214",
      "status": "processing",
      "risk_level": null,
      "risk_score": null,
      "requires_human_review": false,
      "document_type": "passport",
      "created_at": "2026-10-29T19:44:30Z",
      "updated_at": "2026-10-29T19:44:32Z"
    },
    {
      "screening_id": "3c41a299-1a0e-436f-8012-78d1ef9b7342",
      "status": "completed",
      "risk_level": "low",
      "risk_score": 12.0,
      "requires_human_review": false,
      "document_type": "national_id",
      "created_at": "2026-10-29T19:40:12Z",
      "updated_at": "2026-10-29T19:40:19Z"
    }
  ]
}
```

---

### `GET /api/v1/screenings/{id}`
Fetches full screening details including check states, extracted fields, reasons, and latest review adjudication.

#### Request
- **Headers:** `Authorization: Bearer <token>`
- **Path Parameters:**
  - `id`: `8f830a6c-48c9-4ce4-8e11-3bfb8ce93498` (UUID)

#### Response: `200 OK` (Completed with Findings & Review)
```json
{
  "screening_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498",
  "status": "completed",
  "risk_level": "review_required",
  "risk_score": 68.5,
  "requires_human_review": true,
  "document_type": "passport",
  "extracted_fields": {
    "document_type": "passport",
    "issuing_country": "UTO",
    "document_number": "*****9821",
    "holder_name": "SARAH JANE CONNOR",
    "date_of_birth": "1985-02-28",
    "expiration_date": "2028-11-14",
    "nationality": "UTO"
  },
  "checks": [
    {"name": "ocr", "state": "passed", "detail": "High-confidence text extraction completed"},
    {"name": "mrz_checksum", "state": "flagged", "detail": "Checksum mismatch on expiration date field"},
    {"name": "expiry", "state": "passed", "detail": "Document expiration date is in the future"},
    {"name": "date_consistency", "state": "passed", "detail": "Visual dates match machine-readable zone"},
    {"name": "format", "state": "passed", "detail": "Document layout matches ICAO Doc 9303 standards"},
    {"name": "watchlist", "state": "passed", "detail": "No matching identities in watchlist database"},
    {"name": "tamper", "state": "flagged", "detail": "Error Level Analysis detected anomalous visual region"},
    {"name": "face", "state": "passed", "detail": "Portrait photo meets quality specifications"}
  ],
  "reasons": [
    "MRZ checksum mismatch detected on expiration date field",
    "Possible digital tampering detected: ELA compression anomaly in photo border"
  ],
  "review": {
    "review_id": "782ca5bf-9b92-4914-b52b-439589a19c11",
    "decision": "confirmed",
    "notes": "Confirmed MRZ checksum error against physical security feature. Referred for secondary inspection.",
    "reviewed_by": "officer",
    "reviewed_at": "2026-10-29T19:50:15Z"
  },
  "created_at": "2026-10-29T19:45:00Z",
  "updated_at": "2026-10-29T19:45:08Z"
}
```

#### Response: `200 OK` (Queued / In-Progress — Null Risk Rules)
```json
{
  "screening_id": "7a32194b-1498-4b7f-8230-dc1290bbfa11",
  "status": "queued",
  "risk_level": null,
  "risk_score": null,
  "requires_human_review": false,
  "document_type": "passport",
  "extracted_fields": {},
  "checks": [
    {"name": "ocr", "state": "not_performed", "detail": "Queued for worker execution"},
    {"name": "mrz_checksum", "state": "not_performed", "detail": "Pending OCR output"},
    {"name": "expiry", "state": "not_performed", "detail": "Pending OCR output"},
    {"name": "date_consistency", "state": "not_performed", "detail": "Pending OCR output"},
    {"name": "format", "state": "not_performed", "detail": "Pending inspection"},
    {"name": "watchlist", "state": "not_performed", "detail": "Pending extracted fields"},
    {"name": "tamper", "state": "not_performed", "detail": "Pending inspection"},
    {"name": "face", "state": "not_performed", "detail": "Pending photo extraction"}
  ],
  "reasons": [],
  "review": null,
  "created_at": "2026-10-29T19:47:00Z",
  "updated_at": "2026-10-29T19:47:00Z"
}
```

#### Response: `200 OK` (Degraded / Low-Quality Resolution Example)
```json
{
  "screening_id": "1d8923a1-ef12-4299-a9c1-88b1cc9241b8",
  "status": "incomplete",
  "risk_level": "incomplete",
  "risk_score": null,
  "requires_human_review": true,
  "document_type": "passport",
  "extracted_fields": {},
  "checks": [
    {"name": "ocr", "state": "could_not_verify", "detail": "Resolution too low for reliable OCR"},
    {"name": "mrz_checksum", "state": "could_not_verify", "detail": "MRZ unreadable"},
    {"name": "expiry", "state": "could_not_verify", "detail": "Expiry date unreadable"},
    {"name": "date_consistency", "state": "could_not_verify", "detail": "Date fields unreadable"},
    {"name": "format", "state": "could_not_verify", "detail": "Boundary detection uncertain"},
    {"name": "watchlist", "state": "not_performed", "detail": "Identity details unextracted"},
    {"name": "tamper", "state": "could_not_verify", "detail": "Compression artifacts prevent reliable ELA"},
    {"name": "face", "state": "could_not_verify", "detail": "Facial region below minimum dimensions"}
  ],
  "reasons": [
    "Image width 640px is below the 1000px minimum",
    "Failed to detect machine-readable zone (MRZ)"
  ],
  "review": null,
  "created_at": "2026-10-29T19:46:00Z",
  "updated_at": "2026-10-29T19:46:03Z"
}
```

#### Response: `200 OK` (Failed Example — Pipeline Error)
```json
{
  "screening_id": "993a4b01-8bfe-4c6e-8210-6712ab9901ef",
  "status": "failed",
  "risk_level": "incomplete",
  "risk_score": null,
  "requires_human_review": true,
  "document_type": "national_id",
  "extracted_fields": {},
  "checks": [
    {"name": "ocr", "state": "could_not_verify", "detail": "OCR engine execution timed out after 30s"},
    {"name": "mrz_checksum", "state": "not_performed", "detail": "Preceding step failed"},
    {"name": "expiry", "state": "not_performed", "detail": "Preceding step failed"},
    {"name": "date_consistency", "state": "not_performed", "detail": "Preceding step failed"},
    {"name": "format", "state": "not_performed", "detail": "Preceding step failed"},
    {"name": "watchlist", "state": "not_performed", "detail": "Preceding step failed"},
    {"name": "tamper", "state": "not_performed", "detail": "Preceding step failed"},
    {"name": "face", "state": "not_performed", "detail": "Preceding step failed"}
  ],
  "reasons": [
    "Internal OCR engine timeout during text extraction",
    "Screening job aborted due to processing infrastructure failure"
  ],
  "review": null,
  "created_at": "2026-10-29T19:48:10Z",
  "updated_at": "2026-10-29T19:48:40Z"
}
```

---

### `GET /api/v1/screenings/{id}/findings`
Returns granular automated findings for a screening.
> **Invariant:** Findings contain **ONLY** issues and anomalies. Passing checks appear exclusively in the `checks` array and are never included here.

#### Request
- **Headers:** `Authorization: Bearer <token>`
- **Path Parameters:**
  - `id`: `8f830a6c-48c9-4ce4-8e11-3bfb8ce93498` (UUID)

#### Response: `200 OK`
```json
{
  "screening_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498",
  "findings": [
    {
      "finding_id": "4a1d528b-6f69-4501-8b9a-471249bce3d1",
      "type": "MRZ_CHECKSUM_MISMATCH",
      "severity": "high",
      "reason": "Calculated checksum does not match check digit on line 2 character 20.",
      "source": "validator",
      "evidence_ref": "mrz:line2:char20"
    },
    {
      "finding_id": "b73d9e84-e910-48e2-9f32-6a1078d49a3e",
      "type": "ELA_REGION_ANOMALY",
      "severity": "medium",
      "reason": "Possible digital tampering detected: Error Level Analysis shows anomalous high-frequency compression gradient.",
      "source": "tamper_detector",
      "evidence_ref": "bbox:142,65,410,118"
    },
    {
      "finding_id": "6c2b1841-2a9e-4a65-8b11-d11278ce09bb",
      "type": "EXPIRED_DOCUMENT",
      "severity": "medium",
      "reason": "Document expired on 2024-05-10. Note: Expiration is a validity issue, not proof of forgery.",
      "source": "validator",
      "evidence_ref": null
    }
  ]
}
```

---

### `GET /api/v1/screenings/{id}/findings/{finding_id}/evidence`
Retrieves the cropped or annotated visual evidence image for a specific finding (e.g. highlighted bounding box or ELA difference map).

#### Request
- **Headers:** `Authorization: Bearer <token>`
- **Path Parameters:**
  - `id`: `8f830a6c-48c9-4ce4-8e11-3bfb8ce93498` (UUID)
  - `finding_id`: `b73d9e84-e910-48e2-9f32-6a1078d49a3e` (UUID)

#### Response: `200 OK`
- **Headers:**
  - `Content-Type: image/jpeg` (or `image/png`)
  - `Cache-Control: private, no-store`
- **Body:** `[Binary image payload with visual annotation / ELA heat-map]`

#### Error Response: `404 Not Found`
```json
{
  "error": "NOT_FOUND",
  "message": "Finding or evidence asset not found"
}
```

---

### `GET /api/v1/screenings/{id}/image`
Retrieves the original uploaded document image for authorized officer inspection.

#### Request
- **Headers:** `Authorization: Bearer <token>`
- **Path Parameters:**
  - `id`: `8f830a6c-48c9-4ce4-8e11-3bfb8ce93498` (UUID)

#### Response: `200 OK`
- **Headers:**
  - `Content-Type: image/jpeg` (or `image/png`)
  - `Cache-Control: private, no-store`
- **Body:** `[Raw binary image payload]`

---

### `POST /api/v1/screenings/{id}/review`
Records a screening review adjudication.
- **Role Restriction:** Only users with the `"officer"` role can submit reviews. Users with the `"admin"` role receive `403 Forbidden`.
- **Validation:** `notes` is **required** and must be at least 10 characters long.
- **Append-Only:** Multiple reviews can be recorded over time (e.g. initial officer check followed by secondary inspection); reviews are stored in append-only history, and `GET /screenings/{id}` reflects the latest review.

#### Request
- **Headers:**
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- **Path Parameters:**
  - `id`: `8f830a6c-48c9-4ce4-8e11-3bfb8ce93498` (UUID)
- **Body:**
```json
{
  "decision": "confirmed",
  "notes": "Confirmed MRZ checksum error against physical security feature. Referred for secondary inspection."
}
```

#### Response: `201 Created`
```json
{
  "review_id": "782ca5bf-9b92-4914-b52b-439589a19c11",
  "screening_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498",
  "decision": "confirmed",
  "notes": "Confirmed MRZ checksum error against physical security feature. Referred for secondary inspection.",
  "reviewed_by": "officer",
  "reviewed_at": "2026-10-29T19:50:15Z"
}
```

#### Error Response: `403 Forbidden` (Admin Attempting Review)
```json
{
  "error": "FORBIDDEN",
  "message": "Only screening officers are authorized to submit reviews"
}
```

#### Error Response: `422 Unprocessable Entity` (Notes Too Short)
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Review notes must contain at least 10 characters"
}
```

---

## 3. Case Audit & Health

### `GET /api/v1/cases/{id}/audit`
Retrieves the immutable chronological audit trail for a screening case.
- **Case Mapping:** In this MVP, `case_id` equals `screening_id`.
- **Action Enum:** `"SCREENING_SUBMITTED"`, `"INSPECTION_COMPLETED"`, `"IMAGE_VIEWED"`, `"FINDINGS_VIEWED"`, `"HUMAN_REVIEW_RECORDED"`.
- **Privacy:** Login events are logged internally but excluded from the case audit endpoint. Raw OCR text and MRZ lines are never exposed.

#### Request
- **Headers:** `Authorization: Bearer <token>`
- **Path Parameters:**
  - `id`: `8f830a6c-48c9-4ce4-8e11-3bfb8ce93498` (UUID)

#### Response: `200 OK`
```json
{
  "case_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498",
  "events": [
    {
      "event_id": "118942b0-9812-46fa-bb2a-482a1762e519",
      "timestamp": "2026-10-29T19:45:00Z",
      "actor": "officer",
      "action": "SCREENING_SUBMITTED",
      "details": {
        "document_type": "passport",
        "file_size_bytes": 1429810
      }
    },
    {
      "event_id": "281691a2-4180-4965-a690-309489aa5231",
      "timestamp": "2026-10-29T19:45:08Z",
      "actor": "system",
      "action": "INSPECTION_COMPLETED",
      "details": {
        "status": "completed",
        "risk_level": "review_required",
        "findings_count": 3
      }
    },
    {
      "event_id": "391781fa-2201-419b-8e12-892bb193e110",
      "timestamp": "2026-10-29T19:46:12Z",
      "actor": "officer",
      "action": "IMAGE_VIEWED",
      "details": {
        "screening_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498"
      }
    },
    {
      "event_id": "4a7199ec-3392-491a-98b7-61909a82bbca",
      "timestamp": "2026-10-29T19:46:18Z",
      "actor": "officer",
      "action": "FINDINGS_VIEWED",
      "details": {
        "screening_id": "8f830a6c-48c9-4ce4-8e11-3bfb8ce93498"
      }
    },
    {
      "event_id": "589311dc-62a9-4672-913a-cc5188f4981a",
      "timestamp": "2026-10-29T19:50:15Z",
      "actor": "officer",
      "action": "HUMAN_REVIEW_RECORDED",
      "details": {
        "review_id": "782ca5bf-9b92-4914-b52b-439589a19c11",
        "decision": "confirmed"
      }
    }
  ]
}
```

---

### `GET /health`
Liveness and readiness health probe.

#### Request
`GET /health`

#### Response: `200 OK`
```json
{
  "status": "ok",
  "service": "screening-api",
  "version": "0.1.0",
  "timestamp": "2026-10-29T19:52:00Z"
}
```
