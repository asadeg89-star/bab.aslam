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
    # جلب بيانات الاعتماد مباشرة من الـ Streamlit Secrets
    secrets_dict = dict(st.secrets["gcp_service_account"])

    # تنظيف المفتاح السري وإصلاح أي مشكلة في الأسطر تلقائياً
    if "private_key" in secrets_dict:
      pk = secrets_dict["private_key"]
      pk = pk.strip('"').strip("'").replace("\\n", "\n")
      secrets_dict["private_key"] = pk

    creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

  except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    return None


st.title("تطبيق القرآن الكريم والأحزاب")

client = connect_to_sheets()

if client:
  st.success("تم الاتصال بنجاح بـ Google Sheets!")
  # اضف كود قراءة وقبض الجدول هنا
