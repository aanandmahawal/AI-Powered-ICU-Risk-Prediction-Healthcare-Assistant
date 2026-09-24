# RiskCare ICU Dataset

`RiskCare_ICU_Dataset_26000_patients.csv` is the dataset the RiskCare ICU risk model is trained on.
It has **26,000 synthetic adult patients**, one row per patient, with 10 clinical parameters
and a yes/no ICU admission outcome. No real patient records are included.

| Part | Patients | ICU admissions | Description |
|---|---|---|---|
| Core cohort (`source = cohort`) | 20,000 | 11.8% | The RiskCare synthetic patient cohort |
| Extreme-range extension (`source = extreme_range`) | 6,000 | 42.2% | Cohort patients with one or two vital signs at extreme values, so the model covers the full range the app accepts |
| **Total** | **26,000** | | |

## Columns

| Column | Meaning | Unit / values | Range |
|---|---|---|---|
| `patient_id` | Patient identifier (`RC…` cohort, `RCX…` extension) | text | |
| `age_years` | Age | years | 18–100 |
| `heart_rate_bpm` | Heart rate | beats per minute | 30–200 |
| `systolic_bp_mmhg` | Systolic blood pressure | mmHg | 50–250 |
| `diastolic_bp_mmhg` | Diastolic blood pressure | mmHg | 30–149 |
| `respiratory_rate_bpm` | Respiratory rate | breaths per minute | 5–50 |
| `spo2_percent` | Oxygen saturation | % | 70–100 |
| `temperature_f` | Body temperature | °F | 90.0–110.0 |
| `supplemental_oxygen` | Receiving oxygen by mask or cannula | 0 = no, 1 = yes | |
| `level_of_consciousness` | ACVPU scale | Alert, Voice, Pain, Unresponsive | |
| `comorbidity_index` | Burden of chronic illness | 0 (none) – 5 (severe) | |
| `icu_admission` | **Outcome:** admitted to ICU | 0 = no, 1 = yes | |
| `source` | Which part of the dataset the row belongs to | `cohort`, `extreme_range` | |

## How it was prepared

1. **Cohort.** The RiskCare synthetic cohort of 20,000 adult patients. 786 rows recorded a
   diastolic pressure at or above the systolic pressure, which is physically impossible; they
   were corrected by keeping the systolic reading and setting diastolic to systolic − 20 mmHg.
2. **Extreme-range extension.** The cohort covers, for example, temperatures only up to 104.9 °F
   and heart rates up to 160 bpm. 6,000 extra patients were created by taking cohort patients and
   moving one or two vital signs into the uncovered range (e.g. fever up to 110 °F, heart rate up
   to 200 bpm, SpO₂ down to 70%). Their ICU outcome combines the risk the cohort gives the same
   patient at the nearest normal value with a clinical penalty that grows with how extreme the
   value is.

## Model

`python train_model.py` trains the app's model on all 26,000 patients: XGBoost with a stratified
70 / 15 / 15 split into training, validation and test patients.

| Metric | Value |
|---|---|
| ROC-AUC, 5-fold cross-validation | **0.86** |
| ROC-AUC, held-out test patients | 0.87 |
| ROC-AUC, held-out test patients from the core cohort only | 0.82 |
