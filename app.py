import sqlite3
from datetime import date
import streamlit as st

# 1. إعداد قاعدة البيانات
conn = sqlite3.connect("quran_center.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_name TEXT,
    attendance TEXT,
    surah TEXT,
    from_ayah INTEGER,
    to_ayah INTEGER,
    hifz_rating TEXT,
    review_amount TEXT,
    review_rating TEXT
)
"""
)
conn.commit()

# 2. واجهة التطبيق على الهاتف
st.set_page_config(
    page_title="إدارة حلقة القرآن", page_icon="📖", layout="centered"
)
st.title("📖 برنامج إدارة مركز التحفيظ")

# قائمة الطلاب (يمكنك تعديلها أو إضافتها من الكود)
STUDENTS = ["أحمد محمد", "عبدالله علي", "عمر خالد", "يوسف أحمد"]

st.subheader("تسجيل التقييم اليومي")

# اختيار الطالب والتاريخ
selected_student = st.selectbox("اختر اسم الطالب:", STUDENTS)
entry_date = st.date_input("التاريخ:", date.today())

with st.form("evaluation_form", clear_on_submit=True):
    st.markdown("### 1. الحضور والغياب")
    attendance = st.radio(
        "حالة الحضور:",
        ["حاضر", "غائب", "غائب بعذر"],
        horizontal=True,
    )

    st.markdown("### 2. الحفظ الجديد")
    surah = st.text_input("سورة الحفظ:", "البقرة")
    col1, col2 = st.columns(2)
    with col1:
        from_ayah = st.number_input("من آية:", min_value=1, value=1)
    with col2:
        to_ayah = st.number_input("إلى آية:", min_value=1, value=10)

    hifz_rating = st.selectbox(
        "تقييم الحفظ:",
        ["ممتاز", "جيد جداً", "جيد", "إعادة تسميع", "لم يحفظ"],
    )

    st.markdown("### 3. المراجعة")
    review_amount = st.text_input("مقدار المراجعة:", "من سورة يس إلى الواقعة")
    review_rating = st.selectbox(
        "تقييم المراجعة:",
        ["ممتاز", "جيد جداً", "جيد", "لم يراجع"],
    )

    submit_button = st.form_submit_button("حفظ البيانات 💾")

    if submit_button:
        cursor.execute(
            """
            INSERT INTO records (date, student_name, attendance, surah, from_ayah, to_ayah, hifz_rating, review_amount, review_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(entry_date),
                selected_student,
                attendance,
                surah,
                from_ayah,
                to_ayah,
                hifz_rating,
                review_amount,
                review_rating,
            ),
        )
        conn.commit()
        st.success(f"تم حفظ بيانات الطالب {selected_student} بنجاح!")

# عرض السجلات السابقة
st.divider()
st.subheader("📋 السجلات المخزنة")
if st.checkbox("عرض جميع السجلات"):
    cursor.execute(
        "SELECT date, student_name, attendance, surah, hifz_rating, review_rating FROM records ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    st.dataframe(rows)
