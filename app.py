import sqlite3
from datetime import date
import io
import pandas as pd
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

# جدول الحضور
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

# جدول الحفظ
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

# جدول المراجعة
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

# جلب قائمة الطلاب
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

    # --- 1. قسم الحضور والغياب ---
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

    # --- 2. قسم الحفظ الجديد ---
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

    # --- 3. قسم المراجعة ---
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
# قسم تصدير واستعراض البيانات (فردي وشامل)
# --------------------------------------------------
st.divider()
st.subheader("📊 استعراض وتنزيل تقارير Excel")

# خيار تحديد نطاق التنزيل (طالب معين أم جميع الطلاب)
export_scope = st.radio(
    "اختر نطاق البيانات المطلوب تصديرها:",
    ["جميع الطلاب معاً", "طالب محدد فقط"],
    horizontal=True,
)

if export_scope == "طالب محدد فقط":
    filter_student = st.selectbox(
        "اختر الطالب المراد تنزيل بياناته:", students_list
    )

    query_att = (
        f"SELECT student_name AS اسم_الطالب, date AS التاريخ, status AS حالة_الحضور FROM attendance_records WHERE student_name = '{filter_student}' ORDER BY date DESC"
    )
    query_hifz = (
        f"SELECT student_name AS اسم_الطالب, date AS التاريخ, surah AS السورة, from_ayah AS من_آية, to_ayah AS إلى_آية, rating AS التقييم FROM hifz_records WHERE student_name = '{filter_student}' ORDER BY date DESC"
    )
    query_rev = (
        f"SELECT student_name AS اسم_الطالب, date AS التاريخ, amount AS مقدار_المراجعة, rating AS التقييم FROM review_records WHERE student_name = '{filter_student}' ORDER BY date DESC"
    )
    file_prefix = f"تقرير_الطالب_{filter_student}"
else:
    query_att = "SELECT student_name AS اسم_الطالب, date AS التاريخ, status AS حالة_الحضور FROM attendance_records ORDER BY date DESC, student_name ASC"
    query_hifz = "SELECT student_name AS اسم_الطالب, date AS التاريخ, surah AS السورة, from_ayah AS من_آية, to_ayah AS إلى_آية, rating AS التقييم FROM hifz_records ORDER BY date DESC, student_name ASC"
    query_rev = "SELECT student_name AS اسم_الطالب, date AS التاريخ, amount AS مقدار_المراجعة, rating AS التقييم FROM review_records ORDER BY date DESC, student_name ASC"
    file_prefix = "تقرير_جميع_الطلاب"

# قراءة البيانات
df_att = pd.read_sql_query(query_att, conn)
df_hifz = pd.read_sql_query(query_hifz, conn)
df_rev = pd.read_sql_query(query_rev, conn)

# معاينة السجلات في الواجهة
view_option = st.selectbox(
    "اختر السجل للمعاينة قبل التنزيل:",
    ["سجل الحضور", "سجل الحفظ الجديد", "سجل المراجعة"],
)

if view_option == "سجل الحضور":
    st.dataframe(df_att)
elif view_option == "سجل الحفظ الجديد":
    st.dataframe(df_hifz)
else:
    st.dataframe(df_rev)

# إنشاء ملف Excel يحتوي على العمود "اسم الطالب" كعمود أساسي
output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_att.to_excel(writer, index=False, sheet_name="سجل_الحضور")
    df_hifz.to_excel(writer, index=False, sheet_name="سجل_الحفظ")
    df_rev.to_excel(writer, index=False, sheet_name="سجل_المراجعة")
excel_data = output.getvalue()

# زر التنزيل
st.download_button(
    label=f"📥 تنزيل Excel ({file_prefix})",
    data=excel_data,
    file_name=f"{file_prefix}_{date.today()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
