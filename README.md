# Field Test Companion — Streamlit Prototype

SIH Problem Statement 26231 — Digital Companion for Field Drug Testing.

Flow: Officer ID -> Test Details -> Camera -> CV Processing -> Result -> SHA-256 Record -> PDF Report -> Test Records.

## Run
```powershell
cd FieldTest_Companion_Streamlit
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Use the phone browser camera or upload a saved photo. Keep the reference card on the LEFT and test strip/reaction area on the RIGHT.

This is a prototype. Classification is presumptive and not laboratory-confirmatory or chemically validated.
