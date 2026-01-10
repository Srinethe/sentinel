# Test Denial PDF - Ready to Use!

## 📄 Generated PDF

**Location:** `backend/app/data/sample_denials/denial_bluecross_hyperkalemia.pdf`

**Size:** ~4.1 KB

## 📋 PDF Contents

This is a realistic denial notice from Blue Cross Shield of California with:

- **Patient:** DOE, JONATHAN (Account #AH-88291-00)
- **Denial Reason:** Serum potassium 5.4 mmol/L (below 6.0 threshold)
- **ICD-10 Code:** E87.5 (Hyperkalemia)
- **P2P Deadline:** 24 hours from notice (01/11/2026 17:00 PST)
- **Visual Features:** Fax-like artifacts (noise, smudges, scan lines)

## 🧪 How to Test

### Option 1: Via Frontend UI

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000
4. Click "Upload Denial" button
5. Select: `backend/app/data/sample_denials/denial_bluecross_hyperkalemia.pdf`
6. Watch the Intake agent extract the denial information!

### Option 2: Via API (curl)

```bash
curl -X POST http://localhost:8000/api/denial/process \
  -F "file=@backend/app/data/sample_denials/denial_bluecross_hyperkalemia.pdf" \
  -F "patient_name=Jonathan Doe"
```

### Option 3: Via Python

```python
import requests

with open('backend/app/data/sample_denials/denial_bluecross_hyperkalemia.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/denial/process',
        files={'file': f},
        data={'patient_name': 'Jonathan Doe'}
    )
    print(response.json())
```

## 🔄 Regenerate PDF

If you want to regenerate the PDF (with different random artifacts):

```bash
cd backend
python generate_test_denial.py
```

## ✅ Expected Results

When processed by the Intake agent, it should extract:

- **Document Type:** DENIAL
- **Patient Name:** DOE, JONATHAN or Jonathan Doe
- **Denial Reason:** "Serum potassium 5.4 mmol/L does not meet threshold of ≥ 6.0 mmol/L"
- **Appeal Deadline:** 24 hours (calculated from notice date)
- **Urgency:** P0_CRITICAL or P1_HIGH
- **Key Missing Criteria:** ["EKG documentation", "Potassium threshold"]

The Rebuttal agent will then generate an appeal letter citing the EKG changes (if documented) and policy exceptions.
