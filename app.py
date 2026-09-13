import io
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
    # جلب النص الكامل للـ JSON من الـ Secrets الذي قمت بإضافته للتو
    if "gcp_service_account" in st.secrets:
      if "json_key" in st.secrets["gcp_service_account"]:
        json_str = st.secrets["gcp_service_account"]["json_key"]
        creds_dict = json.loads(json_str)
      else:
        # طريقة احتياطية قديمة
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
          creds_dict["private_key"] = creds_dict["private_key"].replace(
              "\\n", "\n"
          )
    else:
      raise ValueError("لم يتم العثور على إعدادات gcp_service_account في Secrets")

    # تحويل البيانات إلى ملف بايتات وهمي لتجاوز خطأ التشفير نهائياً
    creds_file_bytes = io.BytesIO(json.dumps(creds_dict).encode("utf-8"))

    creds = Credentials.from_service_account_file(
        creds_file_bytes, scopes=SCOPES
    )
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
