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
    # قراءة النص الكامل للـ JSON من الـ Secrets
    if "gcp_service_account" in st.secrets:
      if "json_key" in st.secrets["gcp_service_account"]:
        json_str = st.secrets["gcp_service_account"]["json_key"]
        creds_dict = json.loads(json_str)
      else:
        creds_dict = dict(st.secrets["gcp_service_account"])
    else:
      raise ValueError("لم يتم العثور على إعدادات gcp_service_account في Secrets")

    # --- الحل الجذري لإصلاح صيغة الـ private_key ---
    if "private_key" in creds_dict:
      # تحويل الرموز النصية للسطر الجديد إلى أسطر حقيقية
      creds_dict["private_key"] = (
          creds_dict["private_key"].replace("\\n", "\n").strip()
      )
      # إزالة أي علامات تنصيص إضافية قد تكون علقت بالغلط
      if creds_dict["private_key"].startswith(
          '"'
      ) and creds_dict["private_key"].endswith('"'):
        creds_dict["private_key"] = creds_dict["private_key"][1:-1]

    # استخدام البيانات المصححة لإنشاء الاعتماد
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
