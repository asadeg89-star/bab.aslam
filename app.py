import sqlite3
from datetime import date
import streamlit as st

# 1. إعداد قاعدة البيانات وتأسيس الجداول
conn = sqlite3.connect("quran_center.db", check_same_thread=False)
cursor = conn.cursor()

# جدول الطلاب
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
"""
)

# جدول التقييمات
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

st.set_page_config(
    page_title="إدارة حلقة القرآن", page_icon="📖", layout="centered"
)
st.title("📖 برنامج إدارة مركز التحفيظ")

# 2. قسم إضافة طالب جديد من الواجهة
st.sidebar.header("➕ إدارة الطلاب")
new_student = st.sidebar.text_input("اسم الطالب الجديد:")
if st.sidebar.button("إضافة الطالب"):
    if new_student.strip() != "":
        try:
            cursor.execute(
                "INSERT INTO students (name) VALUES (?)", (new_student.strip(),)
            )
            conn.commit()
            st.sidebar.success(f"تمت إضافة الطالب: {new_student}")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.error("هذا الاسم موجود بالفعل!")
    else:
        st.sidebar.warning("يرجى كتابة اسم الطالب.")

# جلب قائمة الطلاب الحالية من قاعدة البيانات
cursor.execute("SELECT name FROM students ORDER BY name ASC")
students_list = [row[0] for row in cursor.fetchall()]

# 3. واجهة التقييم اليومي
st.subheader("تسجيل التقييم اليومي")

if not students_list:
    st.info("👈 لا يوجد طلاب مضافون بعد! قم بإضافة الطلاب من القائمة الجانبية.")
else:
    selected_student = st.selectbox("اختر اسم الطالب:", students_list)
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
        review_amount = st.text_input(
            "مقدار المراجعة:", "من سورة يس إلى الواقعة"
        )
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

# 4. عرض السجلات
st.divider()
st.subheader("📋 السجلات المخزنة")
if st.checkbox("عرض جميع السجلات"):
    cursor.execute(
        "SELECT date, student_name, attendance, surah, hifz_rating, review_rating FROM records ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    st.dataframe(rows)
