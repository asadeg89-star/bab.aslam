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
    # جلب إعدادات الـ Secrets كاملة
    secrets_dict = dict(st.secrets["gcp_service_account"])

    # التأكد من إصلاح أي مشاكل في صيغة الـ private_key
    private_key = secrets_dict.get("private_key", "")
    # معالجة الأسطر والمسافات الزائدة لضمان توافق المفتاح مع نظام التشفير
    private_key = private_key.replace("\\n", "\n")
    if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
      # إذا لم تبدأ بالشكل الصحيح، نقوم بتنظيفها
      private_key = private_key.strip('"').strip("'")

    secrets_dict["private_key"] = private_key

    creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

  except Exception as e:
    st.error(f"خطأ في الاتصال بجداول جوجل: {e}")
    return None


st.title("تطبيق إدارة البيانات والاحزاب")

client = connect_to_sheets()

if client:
  st.success("تم الاتصال بنجاح بـ Google Sheets!")
  # ---> ضع هنا باقي كود تطبيقك الخاص بالأحزاب وعرض البيانات <---
