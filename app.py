import json
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def connect_to_sheets():
  try:
    raw_key = st.secrets["gcp_service_account"]["private_key"]

    # تنظيف جذري لأي نقطة أو فراغات في بداية أو نهاية المفتاح
    clean_key = str(raw_key).strip().lstrip(".")

    # إصلاح تنسيق الأسطر لو كانت مخزنة بطريقة خاطئة
    if "\\n" in clean_key and "\n" not in clean_key:
      clean_key = clean_key.replace("\\n", "\n")

    # التأكد من أن المفتاح يبدأ بالشكل الصحيح تماماً
    if "BEGIN PRIVATE KEY" in clean_key and not clean_key.startswith(
        "-----BEGIN PRIVATE KEY-----"
    ):
      parts = clean_key.split("-----BEGIN PRIVATE KEY-----")
      if len(parts) > 1:
        clean_key = "-----BEGIN PRIVATE KEY-----" + parts[1]

    creds_dict = {
        "type": "service_account",
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": clean_key,
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"][
            "auth_provider_x509_cert_url"
        ],
        "client_x509_cert_url": st.secrets["gcp_service_account"][
            "client_x509_cert_url"
        ],
    }

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

  except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    return None


st.title("تطبيق القرآن الكريم والأحزاب")

client = connect_to_sheets()

if client:
  st.success("تم الاتصال بنجاح بـ Google Sheets!")
