import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# إعداد نطاق الصلاحيات لجداول جوجل
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def connect_to_sheets():
  try:
    # قراءة بيانات السيرفيس أكونت مباشرة كـ Dictionary من إعدادات Streamlit Secrets
    # تأكد أن المفتاح في الـ Secrets مطابق تماماً (مثلاً gcp_service_account)
    creds_dict = dict(st.secrets["gcp_service_account"])

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
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
