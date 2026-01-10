#!/usr/bin/env python3
"""
Setup script to create all demo data files and directories.
Run this before starting the backend for the first time.

Usage: python setup_demo_data.py
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent / "app" / "data"

# Directory structure
DIRECTORIES = [
    "payer_policies",
    "sample_denials", 
    "sample_dictations",
    "synthetic_patients"
]

# ============================================================================
# PAYER POLICIES
# ============================================================================

UNITED_HEALTHCARE_POLICY = '''UNITED HEALTHCARE MEDICAL POLICY BULLETIN 2026-HK-001
Subject: Hyperkalemia Management - Inpatient Admission Criteria

EFFECTIVE DATE: January 1, 2026

MEDICAL NECESSITY CRITERIA FOR INPATIENT ADMISSION:

Inpatient admission for hyperkalemia management is considered medically necessary 
when ONE or MORE of the following criteria are met:

1. LABORATORY CRITERIA:
   - Serum potassium ≥ 5.5 mmol/L on repeat testing, OR
   - Serum potassium ≥ 5.0 mmol/L with rapid rise (>0.5 mmol/L in 24 hours), OR
   - Serum potassium ≥ 5.0 mmol/L with EKG changes

2. ELECTROCARDIOGRAPHIC CRITERIA (any of the following):
   - Peaked T waves
   - Prolonged PR interval (>200ms)
   - Widened QRS complex (>120ms)
   - Sine wave pattern
   - Any arrhythmia attributed to hyperkalemia

3. CLINICAL CRITERIA:
   - Hemodynamic instability requiring monitoring
   - Acute kidney injury with oliguria (<400mL/24hr)
   - Concurrent digitalis toxicity
   - Failure of outpatient management (documented)
   - Need for emergent dialysis
   - Symptoms: muscle weakness, paralysis, palpitations

4. COMORBIDITY CRITERIA:
   - Active cardiac disease with hyperkalemia
   - Post-cardiac surgery within 72 hours
   - Tumor lysis syndrome (confirmed or high risk)
   - Rhabdomyolysis

IMPORTANT: Clinical judgment should be applied. Patients with values slightly 
below thresholds may still qualify if there is documented clinical concern 
or trajectory suggesting imminent deterioration.

DOCUMENTATION REQUIREMENTS:
- Serial potassium levels with timestamps
- 12-lead EKG with physician interpretation
- Clinical assessment documenting symptoms and exam findings
- Treatment plan and rationale for inpatient level of care

APPEAL PROCESS:
Peer-to-peer review available within 48 hours of initial determination.
Contact Medical Director at 1-800-555-0123.
'''

AETNA_POLICY = '''AETNA CLINICAL POLICY BULLETIN
Number: 0847
Subject: Inpatient Admission Criteria - Electrolyte Disorders

EFFECTIVE DATE: January 1, 2026

POLICY:
Aetna considers inpatient admission for electrolyte disorders medically necessary 
when clinical documentation supports the need for continuous monitoring and/or 
interventions that cannot be safely provided in an outpatient setting.

HYPERKALEMIA (ICD-11: 5A40):

Inpatient admission is considered medically necessary when ANY of the following 
are documented:

A. SEVERE HYPERKALEMIA:
   - Serum potassium ≥ 6.0 mmol/L, OR
   - Serum potassium ≥ 5.5 mmol/L with ANY EKG abnormality

B. MODERATE HYPERKALEMIA WITH COMPLICATIONS:
   - Serum potassium 5.0-5.9 mmol/L WITH:
     * EKG changes (peaked T waves, prolonged PR, widened QRS)
     * Acute kidney injury (>50% rise in creatinine)
     * Hemodynamic instability
     * Failure of emergency department management

C. RAPID CORRECTION REQUIRED:
   - Need for IV calcium for cardiac stabilization
   - Need for insulin/glucose infusion
   - Need for emergent hemodialysis

DOCUMENTATION REQUIREMENTS:
1. Timed serum potassium levels (minimum 2 values)
2. 12-lead EKG with interpretation
3. Renal function tests
4. Clinical notes documenting symptoms
5. Treatment administered and response

APPEAL PROCESS:
Peer-to-peer review available within 24 hours.
Standard appeals must be filed within 30 days.
Contact: 1-800-AETNA-MD
'''

CIGNA_POLICY = '''CIGNA MEDICAL COVERAGE POLICY
Policy Number: MM-0492
Subject: Observation vs. Inpatient Admission Criteria

EFFECTIVE: January 2026

INPATIENT ADMISSION CRITERIA:

CARDIAC/ELECTROLYTE CONDITIONS:

1. HYPERKALEMIA:
   Inpatient Level of Care Criteria:
   - K+ ≥ 5.8 mmol/L regardless of symptoms, OR
   - K+ ≥ 5.2 mmol/L with cardiac manifestations, OR
   - K+ ≥ 5.0 mmol/L with rapid rise and AKI
   
   Required Documentation:
   - Serial potassium measurements with times
   - Baseline and repeat EKG
   - Creatinine/BUN
   - Clinical assessment of symptoms
   - Medication reconciliation (ACE-I, ARB, K-sparing diuretics, NSAIDs)

OBSERVATION STATUS APPROPRIATE WHEN:
- Expected to require < 24 hours of treatment
- Low risk for deterioration
- No anticipated need for surgery or invasive procedures

IMPORTANT NOTICE:
Cigna applies clinical judgment in all reviews. Patients with values 
near thresholds may qualify for inpatient admission if:
- Comorbidities increase risk
- Social factors preclude safe discharge
- Clinical trajectory suggests deterioration

PEER-TO-PEER REVIEW:
Available within 48 hours of adverse determination.
Expedited review available for urgent cases.
'''

BLUE_CROSS_POLICY = '''BLUE CROSS BLUE SHIELD
Medical Policy Reference Guide
Section: Inpatient Services
Policy: IP-2026-001

CRITERIA FOR INPATIENT HOSPITAL ADMISSION

HYPERKALEMIA (E87.5):

Tier 1 - Automatic Approval:
- Potassium ≥ 6.5 mmol/L
- Any potassium level with cardiac arrest or life-threatening arrhythmia
- Potassium ≥ 6.0 mmol/L with EKG changes

Tier 2 - Requires Clinical Review:
- Potassium 5.5 - 5.9 mmol/L with risk factors
- Potassium ≥ 5.0 mmol/L with acute kidney injury
- Failed outpatient management

Risk Factors That Support Admission:
- Chronic kidney disease stage 4-5
- Heart failure with reduced EF
- Recent cardiac surgery
- Concurrent use of multiple K+-raising medications
- History of life-threatening hyperkalemia
- Unreliable access to follow-up care

APPEAL INFORMATION:
First-level appeal: Submit within 180 days
Peer-to-peer: Available within 24-48 hours
Expedited appeal: 72 hours for urgent situations
'''

# ============================================================================
# SAMPLE DICTATIONS
# ============================================================================

DICTATION_HYPERKALEMIA = '''This is Dr. Chen dictating on patient John Smith, date of birth March 15, 1958, 
medical record number 8847291, date of service January 5th, 2026.

Chief complaint: Weakness and fatigue for three days.

History of present illness: Mr. Smith is a 67-year-old male with past medical 
history significant for chronic kidney disease stage 3B, hypertension, type 2 
diabetes, and gout who presents with progressive generalized weakness and 
fatigue over the past three days. He reports difficulty climbing stairs and 
getting out of chairs. He denies chest pain, shortness of breath, palpitations, 
syncope, or near-syncope. He does report some mild nausea but no vomiting. 
He has had decreased oral intake over the past few days. No recent medication 
changes. He is compliant with his lisinopril 20 milligrams daily, metformin 
1000 milligrams twice daily, and allopurinol 300 milligrams daily.

Past medical history: CKD stage 3B with baseline creatinine around 2.1, 
hypertension for 15 years, type 2 diabetes for 10 years, gout.

Medications: Lisinopril 20 mg daily, metformin 1000 mg BID, allopurinol 300 mg 
daily, aspirin 81 mg daily.

Physical examination:
Vital signs: Blood pressure 148 over 92, heart rate 76 and regular, 
temperature 98.4 Fahrenheit, respiratory rate 16, oxygen saturation 97 percent 
on room air.

General: Alert, oriented, appears fatigued but in no acute distress.
Cardiovascular: Regular rate and rhythm. Normal S1, S2. No murmurs.
Extremities: No edema. Mild proximal muscle weakness bilateral lower extremities.

Laboratory results from ED:
Sodium 138, potassium 6.1 milliequivalents per liter, chloride 104, bicarb 20, 
BUN 52, creatinine 2.9 up from baseline of 2.1, glucose 142. 
Repeat potassium one hour later was 5.9.
Magnesium 1.8, phosphorus 4.2, calcium 9.1.
Troponin negative.

EKG shows normal sinus rhythm at 74 beats per minute. PR interval normal. 
Notable for peaked T waves in leads V2 through V5, consistent with hyperkalemia. 
No ST segment changes. QRS duration 98 milliseconds.

Assessment:
1. Acute hyperkalemia with EKG changes in setting of acute on chronic kidney injury.
2. Acute kidney injury on CKD stage 3B. Creatinine 2.9 from baseline 2.1.

Plan:
1. Admit to telemetry for continuous cardiac monitoring.
2. IV calcium gluconate 1 gram for cardiac membrane stabilization.
3. Regular insulin 10 units IV with D50 for intracellular potassium shift.
4. Sodium polystyrene sulfonate 30 grams for potassium elimination.
5. IV normal saline for volume resuscitation.
6. Hold lisinopril.
7. Recheck BMP in 4 hours.
8. Nephrology consult if not improving.

Dictated by Dr. Sarah Chen, MD.
End of dictation.
'''

# ============================================================================
# SAMPLE DENIAL LETTERS
# ============================================================================

DENIAL_HYPERKALEMIA = '''================================================================================
                           UNITED HEALTHCARE
                        MEDICAL DETERMINATION NOTICE
================================================================================

DATE OF NOTICE: January 8, 2026
NOTICE TYPE: Adverse Benefit Determination (Denial)

--------------------------------------------------------------------------------
MEMBER INFORMATION
--------------------------------------------------------------------------------
Member Name: John Michael Smith
Member ID: UHC-8847291-01
Date of Birth: March 15, 1958

--------------------------------------------------------------------------------
SERVICE INFORMATION
--------------------------------------------------------------------------------
Date of Service: January 5-7, 2026
Claim Number: CLM-2026-8847592-001
Service Requested: Inpatient Hospital Admission
Diagnosis: Hyperkalemia (ICD-10: E87.5)

--------------------------------------------------------------------------------
                              DETERMINATION: DENIED
--------------------------------------------------------------------------------

After review of the submitted clinical documentation, we have determined that 
the requested inpatient hospital admission does NOT meet medical necessity 
criteria under the member's benefit plan.

REASON FOR DENIAL:

1. LABORATORY VALUES DO NOT MEET THRESHOLD:
   The patient's serum potassium level of 5.3 mmol/L does not meet our 
   established threshold of ≥ 5.5 mmol/L for hyperkalemia requiring 
   inpatient management.

2. INSUFFICIENT DOCUMENTATION OF CARDIAC INVOLVEMENT:
   While the documentation mentions "EKG changes," the specific findings 
   were not clearly documented.

3. ALTERNATIVE LEVEL OF CARE AVAILABLE:
   Based on the clinical presentation, observation status would be appropriate.

POLICY REFERENCE:
UnitedHealthcare Medical Policy Bulletin 2026-HK-001

--------------------------------------------------------------------------------
YOUR APPEAL RIGHTS
--------------------------------------------------------------------------------

** PEER-TO-PEER REVIEW **
You may request a peer-to-peer review within 48 HOURS of this notice.
Call: 1-800-555-0123, Option 3
Reference: Case #DEN-2026-8847592

================================================================================
               PEER-TO-PEER MUST BE REQUESTED WITHIN 48 HOURS
================================================================================
'''

# ============================================================================
# SYNTHETIC PATIENTS
# ============================================================================

PATIENT_HYPERKALEMIA = '''{
  "patient_id": "PAT-001",
  "demographics": {
    "first_name": "John",
    "last_name": "Smith",
    "date_of_birth": "1958-03-15",
    "age": 67,
    "gender": "Male",
    "mrn": "8847291"
  },
  "insurance": {
    "payer": "United Healthcare",
    "member_id": "UHC-8847291-01",
    "group_number": "GRP-449281"
  },
  "medical_history": {
    "conditions": ["CKD Stage 3B", "Hypertension", "Type 2 Diabetes", "Gout"]
  },
  "medications": ["Lisinopril 20mg daily", "Metformin 1000mg BID", "Allopurinol 300mg daily"],
  "baseline_labs": {"creatinine": 2.1, "potassium": 4.8, "gfr": 35}
}'''

# ============================================================================
# FILE MAPPING
# ============================================================================

FILES = {
    "payer_policies/united_healthcare.txt": UNITED_HEALTHCARE_POLICY,
    "payer_policies/aetna.txt": AETNA_POLICY,
    "payer_policies/cigna.txt": CIGNA_POLICY,
    "payer_policies/blue_cross.txt": BLUE_CROSS_POLICY,
    "sample_dictations/dictation_hyperkalemia.txt": DICTATION_HYPERKALEMIA,
    "sample_denials/denial_hyperkalemia.txt": DENIAL_HYPERKALEMIA,
    "synthetic_patients/patient_001.json": PATIENT_HYPERKALEMIA,
}

def setup():
    """Create all directories and files"""
    print("🏥 Setting up Project Sentinel demo data...")
    print(f"   Base directory: {BASE_DIR}")
    
    # Create directories
    for dir_name in DIRECTORIES:
        dir_path = BASE_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ Created directory: {dir_name}/")
    
    # Create files
    for file_path, content in FILES.items():
        full_path = BASE_DIR / file_path
        full_path.write_text(content.strip())
        print(f"   ✓ Created file: {file_path}")
    
    # Create __init__.py
    init_path = BASE_DIR / "__init__.py"
    init_path.write_text('"""Demo data for Project Sentinel"""')
    
    print("\n✅ Demo data setup complete!")
    print(f"   - {len(DIRECTORIES)} directories created")
    print(f"   - {len(FILES)} files created")
    print("\n🚀 You can now start the backend with: uvicorn app.main:app --reload")

if __name__ == "__main__":
    setup()
