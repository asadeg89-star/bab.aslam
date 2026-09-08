import sqlite3
from datetime import date
import io
import pandas as pd
import streamlit as st

# 1. إعداد قاعدة البيانات وتأسيس الجداول
conn = sqlite3.connect("quran_center.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_name TEXT,
    status TEXT
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS hifz_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_name TEXT,
    surah TEXT,
    from_ayah INTEGER,
    to_ayah INTEGER,
    rating TEXT
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS review_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_name TEXT,
    amount TEXT,
    rating TEXT
)
"""
)
conn.commit()

st.set_page_config(
    page_title="إدارة حلقة القرآن", page_icon="📖", layout="centered"
)
st.title("📖 برنامج إدارة مركز التحفيظ")

# 2. القائمة الجانبية لإدارة الطلاب
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

cursor.execute("SELECT name FROM students ORDER BY name ASC")
students_list = [row[0] for row in cursor.fetchall()]

if not students_list:
    st.info("👈 لا يوجد طلاب مضافون بعد! قم بإضافة الطلاب من القائمة الجانبية.")
else:
    st.subheader("تسجيل التقييم اليومي")
    selected_student = st.selectbox("اختر اسم الطالب:", students_list)
    entry_date = st.date_input("التاريخ:", date.today())

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        ["📝 الحضور والغياب", "📖 الحفظ الجديد", "🔄 المراجعة"]
    )

    with tab1:
        st.markdown("### تسجيل الحضور والغياب")
        attendance_status = st.radio(
            "حالة الحضور:",
            ["حاضر", "غائب", "غائب بعذر"],
            horizontal=True,
            key="att_status",
        )
        if st.button("حفظ الحضور 💾", key="save_att"):
            cursor.execute(
                """
                INSERT INTO attendance_records (date, student_name, status)
                VALUES (?, ?, ?)
            """,
                (str(entry_date), selected_student, attendance_status),
            )
            conn.commit()
            st.success(
                f"تم حفظ حضور الطالب ({selected_student}) كـ [{attendance_status}] بنجاح!"
            )

    with tab2:
        st.markdown("### تسجيل الحفظ الجديد")
        surah = st.text_input("سورة الحفظ:", "البقرة", key="hifz_surah")
        col1, col2 = st.columns(2)
        with col1:
            from_ayah = st.number_input(
                "من آية:", min_value=1, value=1, key="hifz_from"
            )
        with col2:
            to_ayah = st.number_input(
                "إلى آية:", min_value=1, value=10, key="hifz_to"
            )

        hifz_rating = st.selectbox(
            "تقييم الحفظ:",
            ["ممتاز", "جيد جداً", "جيد", "إعادة تسميع", "لم يحفظ"],
            key="hifz_rate",
        )
        if st.button("حفظ التسميع 💾", key="save_hifz"):
            cursor.execute(
                """
                INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    str(entry_date),
                    selected_student,
                    surah,
                    from_ayah,
                    to_ayah,
                    hifz_rating,
                ),
            )
            conn.commit()
            st.success(
                f"تم حفظ تسميع الطالب ({selected_student}) لسورة {surah} بنجاح!"
            )

    with tab3:
        st.markdown("### تسجيل المراجعة")
        review_amount = st.text_input(
            "مقدار المراجعة:", "من سورة يس إلى الواقعة", key="rev_amount"
        )
        review_rating = st.selectbox(
            "تقييم المراجعة:",
            ["ممتاز", "جيد جداً", "جيد", "لم يراجع"],
            key="rev_rate",
        )
        if st.button("حفظ المراجعة 💾", key="save_rev"):
            cursor.execute(
                """
                INSERT INTO review_records (date, student_name, amount, rating)
                VALUES (?, ?, ?, ?)
            """,
                (str(entry_date), selected_student, review_amount, review_rating),
            )
            conn.commit()
            st.success(f"تم حفظ مراجعة الطالب ({selected_student}) بنجاح!")

# --------------------------------------------------
# قسم إعادة تنسيق وتصدير الجداول بالعرض أفصقياً (Pivot)
# --------------------------------------------------
st.divider()
st.subheader("📊 استعراض وتنزيل تقارير Excel الشبكية")

# 1. تجهيز جدول الحضور الشبكي
df_att_raw = pd.read_sql_query(
    "SELECT date AS التاريخ, student_name AS الطالب, status AS الحالة FROM attendance_records",
    conn,
)
if not df_att_raw.empty:
    df_att_pivot = df_att_raw.pivot_table(
        index="التاريخ", columns="الطالب", values="الحالة", aggfunc="first"
    ).reset_index()
else:
    df_att_pivot = pd.DataFrame(columns=["التاريخ"])

# 2. تجهيز جدول الحفظ الشبكي (سورة والآيات والتقييم)
df_hifz_raw = pd.read_sql_query(
    "SELECT date AS التاريخ, student_name AS الطالب, (surah || ' [' || from_ayah || '-' || to_ayah || '] - ' || rating) AS الحفظ FROM hifz_records",
    conn,
)
if not df_hifz_raw.empty:
    df_hifz_pivot = df_hifz_raw.pivot_table(
        index="التاريخ", columns="الطالب", values="الحفظ", aggfunc="first"
    ).reset_index()
else:
    df_hifz_pivot = pd.DataFrame(columns=["التاريخ"])

# 3. تجهيز جدول المراجعة الشبكي
df_rev_raw = pd.read_sql_query(
    "SELECT date AS التاريخ, student_name AS الطالب, (amount || ' - ' || rating) AS المراجعة FROM review_records",
    conn,
)
if not df_rev_raw.empty:
    df_rev_pivot = df_rev_raw.pivot_table(
        index="التاريخ", columns="الطالب", values="المراجعة", aggfunc="first"
    ).reset_index()
else:
    df_rev_pivot = pd.DataFrame(columns=["التاريخ"])

# معاينة السجلات في الواجهة
view_option = st.selectbox(
    "اختر السجل للمعاينة قبل التنزيل:",
    ["سجل الحضور الشبكي", "سجل الحفظ الشبكي", "سجل المراجعة الشبكي"],
)

if view_option == "سجل الحضور الشبكي":
    st.dataframe(df_att_pivot)
elif view_option == "سجل الحفظ الشبكي":
    st.dataframe(df_hifz_pivot)
else:
    st.dataframe(df_rev_pivot)

# إنشاء ملف Excel بالتنسيق الشبكي الجديد
output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_att_pivot.to_excel(writer, index=False, sheet_name="سجل_الحضور")
    df_hifz_pivot.to_excel(writer, index=False, sheet_name="سجل_الحفظ")
    df_rev_pivot.to_excel(writer, index=False, sheet_name="سجل_المراجعة")
excel_data = output.getvalue()

# زر التنزيل
st.download_button(
    label="📥 تنزيل ملف Excel الشبكي الشامل",
    data=excel_data,
    file_name=f"تقرير_المركز_المجمع_{date.today()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
