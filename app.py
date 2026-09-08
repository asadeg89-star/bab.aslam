import sqlite3
from datetime import date
import io
import pandas as pd
import streamlit as st
from streamlit_searchbox import st_searchbox

# 1. إعداد قاعدة البيانات وتأسيس الجداول
conn = sqlite3.connect("quran_center.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_name TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS hifz_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_name TEXT,
    surah TEXT,
    from_ayah INTEGER,
    to_ayah INTEGER,
    rating TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS review_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_name TEXT,
    amount TEXT,
    rating TEXT
)
""")
conn.commit()

st.set_page_config(
    page_title="إدارة حلقة القرآن", page_icon="📖", layout="centered"
)

# --------------------------------------------------
# تنسيق الواجهة لتكون من اليمين إلى اليسار (RTL)
# --------------------------------------------------
st.markdown(
    """
    <style>
    /* تطبيق الاتجاه والمحاذاة من اليمين إلى اليسار */
    html, body, [class*="st-"], [class*="css"], div, p, span, h1, h2, h3, h4, label {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* محاذاة عناصر الأدوات والقوائم */
    .stSelectbox, .stTextInput, .stRadio, .stButton, .stDateInput, .stNumberInput {
        direction: rtl !important;
        text-align: right !important;
    }

    /* محاذاة خيارات الراديو أفقياً وتعديل هوامشها */
    div[data-testid="stMarkdownContainer"] > p {
        text-align: right !important;
    }
    
    /* تعديل الاتجاه للشريط الجانبي */
    section[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📖 برنامج إدارة مركز التحفيظ")

# 2. القائمة الجانبية لإدارة الطلاب (إضافة + إزالة)
st.sidebar.header("⚙️ إدارة الطلاب")

# قسم إضافة طالب
st.sidebar.subheader("➕ إضافة طالب جديد")
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

st.sidebar.divider()

# جلب قائمة الطلاب الحالية مرتبة أبجدياً
cursor.execute("SELECT name FROM students ORDER BY name ASC")
students_list = [row[0] for row in cursor.fetchall()]


# دالة البحث اللايف (Live Search) لتصفية الأسماء مباشرة
def search_students(search_term: str):
    if not search_term:
        return students_list
    return [
        s
        for s in students_list
        if s.strip().lower().startswith(search_term.strip().lower())
    ]


# قسم إزالة طالب
st.sidebar.subheader("🗑️ إزالة طالب")
if students_list:
    student_to_remove = st.sidebar.selectbox(
        "اختر الطالب المراد إزالته:",
        students_list,
        index=None,
        placeholder="اختر الطالب للحذف...",
        key="remove_select",
    )
    if st.sidebar.button("حذف الطالب", type="secondary"):
        if student_to_remove:
            cursor.execute(
                "DELETE FROM students WHERE name = ?", (student_to_remove,)
            )
            conn.commit()
            st.sidebar.success(f"تمت إزالة الطالب ({student_to_remove}) بنجاح!")
            st.rerun()
        else:
            st.sidebar.warning("يرجى اختيار طالب أولاً لإزالته.")
else:
    st.sidebar.info("لا يوجد طلاب مضافون حالياً.")

# --------------------------------------------------
# الواجهة الرئيسية لتسجيل البيانات
# --------------------------------------------------
if not students_list:
    st.info("👈 لا يوجد طلاب مضافون بعد! قم بإضافة الطلاب من القائمة الجانبية.")
else:
    entry_date = st.date_input("📅 تحديد تاريخ اليوم:", date.today())
    st.divider()

    tab1, tab2, tab3 = st.tabs(
        ["📝 الحضور والغياب المجمع", "📖 الحفظ الجديد", "🔄 المراجعة"]
    )

    # --- 1. قسم الحضور والغياب المجمع ---
    with tab1:
        st.markdown("### 📋 كشف الحضور والغياب الجماعي")

        search_att = st.text_input(
            "🔍 تصفية القائمة بكتابة بداية الاسم:", "", key="search_att"
        )
        filtered_att_students = [
            s
            for s in students_list
            if s.lower().startswith(search_att.strip().lower())
        ]

        st.caption("حدد حالة كل طالب ثم اضغط على زر الحفظ النهائي بالأسفل:")

        attendance_results = {}
        status_options = ["حضور", "غياب", "غياب بعذر", "تأخير"]

        for idx, student in enumerate(filtered_att_students):
            st.write(f"*{idx + 1}. {student}*")
            selected_status = st.radio(
                f"حالة {student}:",
                options=status_options,
                index=0,
                key=f"att_{student}",
                horizontal=True,
                label_visibility="collapsed",
            )
            attendance_results[student] = selected_status
            st.divider()

        if st.button("💾 حفظ كشف الحضور لجميع الطلاب الظاهرين", type="primary"):
            for student_name, status in attendance_results.items():
                cursor.execute(
                    """
                    INSERT INTO attendance_records (date, student_name, status)
                    VALUES (?, ?, ?)
                """,
                    (str(entry_date), student_name, status),
                )
            conn.commit()
            st.success(
                f"✅ تم حفظ حضور {len(attendance_results)} طالب بتاريخ {entry_date} بنجاح!"
            )

    # --- 2. قسم الحفظ الجديد (مُعدّل للتقييم السريع فقط) ---
    with tab2:
        st.markdown("### تسجيل الحفظ الجديد")

        selected_student_hifz = st_searchbox(
            search_students,
            placeholder="🔍 اكتب اسم الطالب أو الحرف الأول مباشرة...",
            key="hifz_live_search",
        )

        if selected_student_hifz:
            st.success(f"تم اختيار الطالب: *{selected_student_hifz}*")

        st.divider()

        hifz_rating = st.radio(
            "تقييم الحفظ:",
            ["جيد", "إعادة"],
            horizontal=True,
            key="hifz_rate",
        )

        if st.button("حفظ التسميع 💾", key="save_hifz"):
            if not selected_student_hifz:
                st.error("⚠️ يرجى اختيار اسم الطالب أولاً من قائمة البحث!")
            else:
                cursor.execute(
                    """
                    INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(entry_date),
                        selected_student_hifz,
                        "-",
                        0,
                        0,
                        hifz_rating,
                    ),
                )
                conn.commit()
                st.success(
                    f"تم حفظ تسميع الطالب ({selected_student_hifz}) وتقييمه: [{hifz_rating}] بنجاح!"
                )

    # --- 3. قسم المراجعة ---
    with tab3:
        st.markdown("### تسجيل المراجعة")

        selected_student_rev = st_searchbox(
            search_students,
            placeholder="🔍 اكتب اسم الطالب أو الحرف الأول مباشرة...",
            key="rev_live_search",
        )

        if selected_student_rev:
            st.success(f"تم اختيار الطالب: *{selected_student_rev}*")

        st.divider()

        review_amount = st.text_input(
            "مقدار المراجعة:", "من سورة يس إلى الواقعة", key="rev_amount"
        )
        review_rating = st.selectbox(
            "تقييم المراجعة:",
            ["ممتاز", "جيد جداً", "جيد", "لم يراجع"],
            key="rev_rate",
        )
        if st.button("حفظ المراجعة 💾", key="save_rev"):
            if not selected_student_rev:
                st.error("⚠️ يرجى اختيار اسم الطالب أولاً من قائمة البحث!")
            else:
                cursor.execute(
                    """
                    INSERT INTO review_records (date, student_name, amount, rating)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        str(entry_date),
                        selected_student_rev,
                        review_amount,
                        review_rating,
                    ),
                )
                conn.commit()
                st.success(
                    f"تم حفظ مراجعة الطالب ({selected_student_rev}) بنجاح!"
                )

# --------------------------------------------------
# قسم تصدير واستعراض البيانات
# --------------------------------------------------
st.divider()
st.subheader("📊 تصدير البيانات إلى ملف Excel")

export_mode = st.radio(
    "اختر طريقة التصدير المطلوبة:",
    ["تصدير جميع الطلاب (تنسيق شبكي أفقي)", "تصدير طالب محدد فقط (تقرير شخصي)"],
    horizontal=True,
)

if export_mode == "تصدير طالب محدد فقط (تقرير شخصي)":
    single_student = st.selectbox(
        "🔎 اختر اسم الطالب لتنزيل ملفه الخاص:",
        students_list,
        index=None,
        placeholder="اضغط واكتب اسم الطالب...",
        key="export_single_search",
    )

    if single_student:
        df_att_single = pd.read_sql_query(
            f"SELECT date AS التاريخ, student_name AS الطالب, status AS حالة_الحضور FROM attendance_records WHERE student_name = '{single_student}' ORDER BY date DESC",
            conn,
        )
        df_hifz_single = pd.read_sql_query(
            f"SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM hifz_records WHERE student_name = '{single_student}' ORDER BY date DESC",
            conn,
        )
        df_rev_single = pd.read_sql_query(
            f"SELECT date AS التاريخ, student_name AS الطالب, amount AS مقدار_المراجعة, rating AS التقييم FROM review_records WHERE student_name = '{single_student}' ORDER BY date DESC",
            conn,
        )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_att_single.to_excel(
                writer, index=False, sheet_name="سجل_الحضور"
            )
            df_hifz_single.to_excel(writer, index=False, sheet_name="سجل_الحفظ")
            df_rev_single.to_excel(
                writer, index=False, sheet_name="سجل_المراجعة"
            )
        excel_data = output.getvalue()

        st.download_button(
            label=f"📥 تنزيل ملف Excel الخاص بـ ({single_student})",
            data=excel_data,
            file_name=f"تقرير_{single_student}_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
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

    df_hifz_raw = pd.read_sql_query(
        "SELECT date AS التاريخ, student_name AS الطالب, rating AS الحفظ FROM hifz_records",
        conn,
    )
    if not df_hifz_raw.empty:
        df_hifz_pivot = df_hifz_raw.pivot_table(
            index="التاريخ", columns="الطالب", values="الحفظ", aggfunc="first"
        ).reset_index()
    else:
        df_hifz_pivot = pd.DataFrame(columns=["التاريخ"])

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

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_att_pivot.to_excel(writer, index=False, sheet_name="سجل_الحضور")
        df_hifz_pivot.to_excel(writer, index=False, sheet_name="سجل_الحفظ")
        df_rev_pivot.to_excel(writer, index=False, sheet_name="سجل_المراجعة")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 تنزيل ملف Excel الشبكي الشامل لجميع الطلاب",
        data=excel_data,
        file_name=f"تقرير_المركز_المجمع_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
