# 🏥 RiskCare: ICU Risk Prediction & Medical AI Assistant

**[Live app](https://ai-powered-icu-risk-prediction-healthcare-assistant-ayv3bdhwnk.streamlit.app/)** · **[GitHub](https://github.com/aanandmahawal/AI-Powered-ICU-Risk-Prediction-Healthcare-Assistant)**

RiskCare is a web app that predicts how likely a patient is to need the **ICU**. It also has an **AI medical assistant** that explains the result, answers health questions and reads medical reports.

- **ICU risk model:** XGBoost trained on 26,000 synthetic patients, scoring **0.86 ROC-AUC**
- **MedAssist AI:** a chatbot (Groq LLM) that gives advice based on the patient's vitals and explains uploaded reports
- **Multiple patients:** assess a whole ward at once and see who needs help first

> ⚠️ For education and demonstration only. The data is synthetic, and this is not a medical device.

---

## ✨ Features

**👤 Single patient**
- Enter 10 details: age, heart rate, blood pressure, breathing rate, SpO₂, temperature, oxygen support, consciousness and long-term illnesses.
- Get the **ICU risk %** with a band: Low < 10%, Moderate 10–30%, High 30–60%, Critical ≥ 60%.
- Also see the **NEWS2 score** (a hospital warning score), abnormal values and alerts.

**👥 Multiple patients**
- Type patients into a table, or upload a **CSV/Excel** file (a template is provided).
- Get patients **ranked by risk** with a priority label (🔴 Urgent → 🟢 Routine), and download the results.

**💬 MedAssist AI**
- Answers medical questions using the current patient's details.
- **Upload a medical report** (PDF, Word, photo). It reads the report, explains each result (✅ normal, 🔺 high, 🔻 low), gives an overall health status and suggests next steps.
- If the file isn't a medical report (a bill, a CV, etc.), it politely says so.

---

## 🛠️ Tech stack

| Part | Tools |
|---|---|
| Machine learning | XGBoost, scikit-learn, pandas, NumPy |
| AI chatbot | Groq API: GPT-OSS 20B (text), Qwen 3.8 27B (reads images) |
| Reading files | pypdf, pypdfium2, python-docx, Pillow, openpyxl |
| Web app and hosting | Streamlit, Streamlit Community Cloud, GitHub |

## 📁 Project files

| File | What it does |
|---|---|
| `app.py` | Main page: layout, sidebar, chat panel |
| `predictor.py` | Single-patient form and results |
| `ward.py` | Multiple-patient table, file upload and ranking |
| `reports.py` | Reads and explains medical reports |
| `chatbot.py` | Talks to the Groq AI |
| `clinical.py` | Medical rules: NEWS2, normal ranges, risk bands |
| `train_model.py` | Trains and tests the model |
| `data/` | The 26K-patient dataset and its description |
| `model/` | The trained model and its scores |

---

## 📊 Dataset

**26,000 synthetic (computer-generated) patients**, with 10 inputs each and an answer: *went to ICU (1) or not (0)*.

| Part | Patients | Went to ICU |
|---|---|---|
| Normal patients | 20,000 | 11.8% |
| Extreme cases (e.g. 110 °F fever, SpO₂ 70%) | 6,000 | 42.2% |
| **Total** | **26,000** | **18.8%** |

- **Fixed bad rows:** 786 rows had impossible blood pressure (lower number ≥ upper number). They were corrected, not deleted.
- **Why extreme cases?** A tree model can't predict well outside the values it has seen. Adding extreme patients means a 108 °F fever gives a sensible **~72% risk**, not a wrong answer.

---

## 🤖 The model

**How it was trained**
1. Clean and check the data.
2. Test it fairly with **5-fold cross-validation**.
3. Split the data: 70% to learn, 15% to decide when to stop, 15% for the final test.
4. Train XGBoost. It stopped automatically at **817 trees**.
5. Save the model and its scores.

**Main settings**

| Setting | Value | In simple words |
|---|---|---|
| Tree depth | 3 | Small trees, so it learns general patterns, not noise |
| Learning rate | 0.02 | Learns slowly and carefully |
| Early stopping | 150 | Stops when it stops improving |
| Subsample | 0.8 | Each tree sees a random 80% of data, which prevents memorising |
| Monotone constraints | on | Follows medical logic (see below) |

**Results**

| Score | Value |
|---|---|
| **ROC-AUC (5-fold CV)** | **0.86 ± 0.003** |
| ROC-AUC on unseen test patients | 0.87 |
| NEWS2 hospital score, for comparison | 0.75 |

➡️ The model beats the standard hospital score, and its results are stable.

---

## 📚 Key concepts in simple words

### XGBoost
A **decision tree** asks yes/no questions ("Is SpO₂ below 92?") to reach an answer. **XGBoost** builds hundreds of small trees **one after another**, and **each new tree fixes the mistakes of the earlier ones**. Together they give a strong prediction. It's the go-to model for table data like this.

### Train / validation / test split
- **Training (70%):** the model learns from these patients.
- **Validation (15%):** used to decide when to stop training.
- **Test (15%):** kept hidden until the end, for an honest final score.

### 5-fold cross-validation (CV)
A fairer way to test a model than a single split.
1. Split the 26,000 patients into **5 equal groups** ("folds").
2. Train **5 times**. Each time, learn from 4 groups and test on the 1 left out:

| Round | Learns from | Tested on |
|---|---|---|
| 1 | Folds 2, 3, 4, 5 | Fold 1 |
| 2 | Folds 1, 3, 4, 5 | Fold 2 |
| 3 | Folds 1, 2, 4, 5 | Fold 3 |
| 4 | Folds 1, 2, 3, 5 | Fold 4 |
| 5 | Folds 1, 2, 3, 4 | Fold 5 |

3. **Average the 5 scores.**

Every patient gets tested once, and the score doesn't depend on luck. Here: **0.861 ± 0.003**. The small ± means the model is stable. **"Stratified"** means each group has the same share of ICU patients (~19%).

### ROC-AUC
It measures **how well the model ranks sick patients above healthy ones**.
- **0.5** is random guessing, and **1.0** is perfect.
- **0.86** means that 86% of the time, the model gives a real ICU patient a higher risk than a non-ICU patient.

### Why not accuracy?
Only 19% of patients went to the ICU. A useless model that always says "no ICU" would be **81% accurate** but miss every sick patient. So accuracy can mislead here, and ROC-AUC is used instead.

### Precision and recall
- **Precision:** of the patients we flagged, how many really needed ICU?
- **Recall:** of the patients who needed ICU, how many did we catch?

Lowering the alert cut-off catches more sick patients (recall goes from 46% to 73% at a 0.2 cut-off) but gives more false alarms. In hospitals, **missing a sick patient is worse than a false alarm**.

### Overfitting
When a model **memorises** the training data instead of learning general patterns, it fails on new patients. It was prevented here with small trees, early stopping, random subsampling and cross-validation.

### Monotone constraints
**Rules that force the model to follow medical common sense.** Risk can only go **up** with age, illnesses, oxygen support and reduced consciousness, and only go **down** as SpO₂ improves.

### Calibration
The risk % can be trusted as a real chance: of patients shown **~24% risk**, about **24%** actually went to the ICU.

### SHAP values
They explain **why** the model gave a result by showing how much each input pushed the risk **up or down** (e.g. "low SpO₂ raised the risk the most"). The chatbot uses them to explain results.

### NEWS2
A **standard hospital score** that gives 0–3 points per vital sign and adds them up. **7 or more** means an emergency. The model is compared against it as a baseline (0.87 vs 0.75).

### Synthetic data
**Computer-generated patients** that look realistic. Real patient data needs special permission and privacy protection.

---

## 💬 How MedAssist AI works

- **LLM:** an AI that writes text. It runs on **Groq**, which is very fast.
- **System prompt:** hidden instructions that tell the AI its role: answer medical questions only, never diagnose or give medicine doses, and warn about urgent risk.
- **Context:** the patient's vitals, ICU risk and uploaded reports are sent along with each question, so answers are personalised (similar to **RAG**). It remembers the last 10 messages.
- **Report upload, in 3 steps:**
  1. **Read:** text is read from PDF and Word files, and an **image-reading AI (OCR)** reads photos and scans.
  2. **Check:** the AI decides whether it's a real medical report.
  3. **Explain:** it gives a clear summary, a results table, a health status and next steps.
- **Safety:** instructions hidden inside a document are ignored (**prompt-injection** protection). The AI only uses values written in the report, and the API key is never uploaded to GitHub.

---

## 🚀 Run it locally

```bash
git clone https://github.com/aanandmahawal/AI-Powered-ICU-Risk-Prediction-Healthcare-Assistant.git
cd AI-Powered-ICU-Risk-Prediction-Healthcare-Assistant
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your free Groq key from [console.groq.com/keys](https://console.groq.com/keys):
```
GROQ_API_KEY=gsk_your_key_here
```

Then run the app with `streamlit run app.py`, which opens http://localhost:8501. To retrain the model, run `python train_model.py`.

**Deploy:** on [share.streamlit.io](https://share.streamlit.io), pick this repo with `app.py` as the main file, then add `GROQ_API_KEY` under **Settings → Secrets**.

---

## ⚠️ Limitations and future work

- Uses **synthetic data**. It needs testing on real hospital data (e.g. MIMIC-IV).
- Looks at **one moment** in time, not changes over hours.
- **Future work:** vitals over time, lab values, a smarter alert cut-off, and connecting to hospital systems.

---

## 🎯 Interview quick answers

| Question | Short answer |
|---|---|
| Why XGBoost? | It's the best choice for table data. It's fast and accurate, and its results are easy to explain with SHAP. |
| Why ROC-AUC, not accuracy? | Only 19% go to the ICU, so always saying "no" is already 81% accurate. ROC-AUC checks ranking instead. |
| What is 5-fold CV? | Split the data into 5 groups, train on 4, test on 1, repeat 5 times and average: 0.86 ± 0.003. |
| How did you stop overfitting? | Small trees, early stopping (817 trees), random subsampling and cross-validation. |
| How do you explain a prediction? | SHAP values show which inputs raised or lowered the risk. |
| What are monotone constraints? | Rules that keep the model medically logical (e.g. lower SpO₂ never lowers risk). |
| Why did 108 °F once give 100%? | A hard-coded rule, plus trees can't predict beyond the data they've seen. I removed the rule and added 6,000 extreme cases. Now it's ~72%. |
| How are fake uploads handled? | An AI check step decides whether the file is a medical report, and hidden instructions in files are ignored. |
| Which alert cut-off in a hospital? | A lower one that catches more sick patients (0.2 gives 73% recall), as long as the number of false alarms stays manageable. |

---

*Built with Streamlit, XGBoost and Groq · For education and demonstration only.*
