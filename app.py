import io
import json
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
    # 1. جلب بيانات السيرفرف أكاونت من الـ Secrets كـ Dict أو String
    if "gcp_service_account" in st.secrets:
      secret_data = st.secrets["gcp_service_account"]

      # إذا كانت مخزنة كـ Dictionary
      if isinstance(secret_data, dict):
        creds_dict = dict(secret_data)
      # إذا كانت مخزنة كنص JSON عادي
      elif isinstance(secret_data, str):
        creds_dict = json.loads(secret_data)
      else:
        raise ValueError("صيغة بيانات الـ Secrets غير صحيحة.")

      # 2. الحل الجذري: تحويل الـ Dictionary إلى كائن با이트ات وهمي (BytesIO)
      # لكي تتجنب تماماً خطأ Cannot convert str to a seekable bit stream
      creds_json_string = json.dumps(creds_dict)
      creds_file_bytes = io.BytesIO(creds_json_string.encode("utf-8"))

      # 3. الاعتماد على from_service_account_file مع الملف الوهمي
      creds = Credentials.from_service_account_file(
          creds_file_bytes, scopes=SCOPES
      )
    else:
      # محاولة قراءة البيانات بالطريقة التقليدية إذا وُجدت في السيكريتس كملف مباشر
      creds = Credentials.from_service_account_info(
          st.secrets["google_credentials"], scopes=SCOPES
      )

    client = gspread.authorize(creds)
    return client

  except Exception as e:
    st.error(f"خطأ في الاتصال بجداول جوجل: {e}")
    return None


# اختبار الاتصال وعرض الواجهة البسيطة
st.title("تطبيق ربط جداول جوجل")

client = connect_to_sheets()

if client:
  st.success("تم الاتصال بنجاح بـ Google Sheets!")
  # ضع هنا باقي كود تطبيقك لجلب البيانات أو عرضها
  try:
    # مثال: فتح شيت باسم معين أو أول شيت متاح
    # sheet = client.open("اسم_الملف_خاصتك").sheet1
    # data = sheet.get_all_records()
    # st.write(data)
    pass
  except Exception as ex:
    st.warning(f"ملاحظة أثناء محاولة قراءة الجدول: {ex}")
