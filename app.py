import pandas as pd
import streamlit as st

# استخراج معرف الملف (ID) مباشرة من الرابط الخاص بك بطريقة مضمونة
SHEET_ID = "1BB4CAm4M1tQN74s5whI8M0-GiT5tjS0i8Aw3n31B1pY"
# بناء رابط تصدير الـ CSV الصحيح للعموم
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


@st.cache_data(ttl=600)
def load_data():
  try:
    df = pd.read_csv(CSV_URL)
    return df
  except Exception as e:
    # سنتأكد من إظهار سبب الخطأ بدقة لنعرف هل هو بسبب الصلاحيات أم لا
    return str(e)


st.title("تطبيق القرآن الكريم والأحزاب")

# محاولة جلب البيانات
result = load_data()

if isinstance(result, pd.DataFrame):
  if not result.empty:
    st.success("تم الاتصال بنجاح وقراءة بيانات القرآن الكريم والأحزاب!")
    st.dataframe(result)
  else:
    st.warning("الملف فارغ ولا يحتوي على بيانات حالياً.")
else:
  st.error(f"خطأ في الصلاحيات أو الرابط: {result}")
  st.info(
      "ملاحظة هامة: تأكد من أن الملف في جوجل شيت مضبوط على 'Anyone with the link'"
      " (أي شخص لديه الرابط يمكنه العرض)."
  )
