# 🚀 Deploying Streamlit + Firebase on GCP (Hackathon Setup)

This guide explains how to deploy a Streamlit app with Firebase integration using **Google Cloud Run** and **Firebase Hosting**.

---

## 1️⃣ Prerequisites
- A **Google Cloud project** (create via [Google Cloud Console](https://console.cloud.google.com/))
- A **Firebase project** (linked to the same Google Cloud project)
- Install locally:
  - [gcloud CLI](https://cloud.google.com/sdk/docs/install)
  - [Docker](https://docs.docker.com/get-docker/)
  - Python 3.9+

---

## 2️⃣ Project Setup
1. Clone your repo and navigate inside:

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```
2. Enable required APIs
```bash
gcloud services enable run.googleapis.com firebase.googleapis.com artifactregistry.googleapis.com
```
3. Login to gcloud
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```
6️⃣ Deploy to Cloud Run

1. Build and push container:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/streamlit-app
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy streamlit-app \
  --image gcr.io/YOUR_PROJECT_ID/streamlit-app \
  --platform managed \
  --allow-unauthenticated \
  --region us-central1
```

3. You’ll get a live URL like:
```bash
https://streamlit-app-xxxxxx-uc.a.run.app
```
7️⃣ (Optional) Connect Firebase Hosting

1. If you want a custom domain like your-app.web.app:
```bash
firebase init hosting
firebase deploy --only hosting
```

2. Update firebase.json to proxy requests to Cloud Run:
```bash
{
  "hosting": {
    "rewrites": [
      {
        "source": "**",
        "run": {
          "serviceId": "streamlit-app",
          "region": "us-central1"
        }
      }
    ]
  }
}
```
8️⃣ Using Firebase in App

1. Example app.py:
```bash
import streamlit as st
import pyrebase
import os, json

# Load config from file (or env vars)
with open("firebase_config.json") as f:
    firebaseConfig = json.load(f)

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

st.title("🔥 Streamlit + Firebase on Cloud Run")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.success("Logged in!")
    except:
        st.error("Login failed")

if st.button("Save Test"):
    db.child("messages").push({"user": email, "msg": "Hello Cloud Run!"})
    st.success("Message saved to Firebase")
```
9️⃣ Done 🎉

1. App deployed on Cloud Run

2. Accessible via Firebase Hosting (optional)

3. Firebase services integrated (Auth, Firestore, Storage, etc.)

⚡ Hackathon Tips

1. Use Cloud Run free tier (2M requests/month free).

2. Firebase free tier is generous (Auth, Firestore, Storage).

3. Use firebase_config.json directly for hackathon speed, but in production move keys to GCP Secret Manager.