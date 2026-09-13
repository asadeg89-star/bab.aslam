import pandas as pd
import streamlit as st

# رابط جوجل شيت الخاص بك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BB4CAm4M1tQN74s5whI8M0-GiT5tjS0i8Aw3n31B1pY/edit?usp=drivesdk"


@st.cache_data(ttl=600)  # تخزين مؤقت للبيانات لتسريع التطبيق وحفظها
def load_data_from_sheet(url):
  try:
    # تحويل رابط الشيت إلى رابط تصدير بصيغة CSV ليتم قراءته مباشرة وبسهولة تامة
    csv_url = url.replace("/edit?usp=drivesdk", "/export?format=csv")
    df = pd.read_csv(csv_url)
    return df
  except Exception as e:
    st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
    return None


st.title("تطبيق القرآن الكريم والأحزاب")
st.write("جاري جلب البيانات بأمان واحترافية...")

# تحميل وعرض البيانات
df = load_data_from_sheet(SHEET_URL)

if df is not None and not df.empty:
  st.success("تم الاتصال بنجاح وقراءة البيانات من Google Sheets!")

  # عرض البيانات في جدول تفاعلي
  st.dataframe(df)

  # يمكنك البدء في استخدام البيانات هنا (مثلاً البحث أو عرض سور/أحزاب معينة)
else:
  st.warning(
      "لم يتم العثور على بيانات، يجدر التأكد من أن الرابط عام (Anyone with the"
      " link can view)."
  )
