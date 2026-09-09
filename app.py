import sqlite3
from datetime import date
import io
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="مركز تحفيظ باب السلام", page_icon="📖", layout="centered")

# القائمة الأساسية مترتبة تصاعدياً (من الفاتحة إلى النهاية)
AHZAB_LIST = [
    "الفاتحة", "وإذا لقوا", "سيقول", "واذكروا الله", "تلك الرسل", "قل أؤنبئكم", 
    "لن تنالوا", "يستبشرون", "المحصنات", "الله لا إله إلا هو", "لا يحب", 
    "قال رجلان", "لتجدن", "إنما يستجيب", "ولو أننا نزلنا", "الأعراف", 
    "قال الملأ", "وإذ نتقنا", "واعلموا", "يأيها الذين آمنوا", "إنما السبيل", 
    "الذين أحسنوا", "وما من دابة", "وإلى مدين", "وما أبرئ", "أمن يعلم", 
    "الحجر", "وقال الله", "سبحان الذي", "أولم يَرَوْا", "قال ألم أقل لك", 
    "طه", "الأنبياء", "الحج", "المؤمنون", "يأيها الذين آمنوا", "وقال الذين لا يرجون", 
    "قالوا أأنؤمن", "قل الحمد لله", "ولقد وصلنا", "ولا تجادلوا", "ومن يسلم", 
    "إن المسلمين", "قل من يرزقكم", "وما أنزلنا", "فنبذناه", "فمن أظلم", 
    "وبقوم مالي", "إليه يرد", "قل أولو جئتكم", "الأحقاف", "لقد رضي", 
    "قال فما خطبكم", "الرحمن", "المجادلة", "الجمعة", "الملك", "الجن", "النبأ", "الأعلى"
]

AHZAB_LIST_DESC = list(reversed(AHZAB_LIST))

conn = sqlite3.connect("quran_center.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

cursor.execute("SELECT * FROM users WHERE username = 'admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "admin"))
    conn.commit()

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

# تنظيف التكرارات القديمة تلقائياً
cursor.execute("DELETE FROM attendance_records WHERE id NOT IN (SELECT MAX(id) FROM attendance_records GROUP BY date, student_name)")
cursor.execute("DELETE FROM hifz_records WHERE id NOT IN (SELECT MAX(id) FROM hifz_records GROUP BY date, student_name)")
cursor.execute("DELETE FROM review_records WHERE id NOT IN (SELECT MAX(id) FROM review_records GROUP BY date, student_name)")
conn.commit()

# تصميم جمالي عصري (Modern UI & CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif !important;
    }
    
    .stMainBlockContainer { 
        direction: rtl !important; 
        text-align: right !important; 
        background-color: #fcfdfd;
        padding: 2rem;
        border-radius: 16px;
    }
    .stMainBlockContainer div, .stMainBlockContainer p, .stMainBlockContainer label, 
    .stMainBlockContainer h1, .stMainBlockContainer h2, .stMainBlockContainer h3 {
        text-align: right !important; 
        direction: rtl !important; 
    }
    
    section[data-testid="stSidebar"] { 
        direction: ltr !important; 
        background-color: #f4f7f6;
        border-left: 1px solid #e1e8e6;
    }
    section[data-testid="stSidebar"] * { 
        direction: rtl !important; 
        text-align: right !important; 
    }
    
    /* تنسيق عنوان التطبيق ليكون متناسقاً ومرتباً */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        background: #f8fafc;
        padding: 15px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .app-header h1 {
        color: #0f766e;
        margin: 0;
        font-size: 24px;
        font-weight: 700;
    }
    .app-header span {
        font-size: 28px;
    }

    /* تنسيق الجداول المخصصة */
    .custom-table {
        width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; direction: rtl; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .custom-table th { background-color: #0f766e; color: #ffffff; font-weight: 600; padding: 12px; border-bottom: 2px solid #0d9488; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #edf2f7; color: #1e293b; }
    .custom-table tr:nth-of-type(even) { background-color: #f8fafc; }
    
    /* شارات التقييم الملونة */
    .badge-good { background-color: #d1fae5; color: #065f46; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block; }
    .badge-retry { background-color: #fee2e2; color: #991b1b; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block; }
    .badge-absent { background-color: #f1f5f9; color: #475569; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block; }
    
    /* تخصيص الأزرار والعناصر الجمالية */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 118, 110, 0.15);
    }
    </style>
    """, unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

if "user" in st.query_params:
    logged_username = st.query_params["user"]
    cursor.execute("SELECT role FROM users WHERE username = ?", (logged_username,))
    user_data = cursor.fetchone()
    if user_data:
        st.session_state["authenticated"] = True
        st.session_state["username"] = logged_username
        st.session_state["role"] = user_data[0]

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #0f766e;'>🔐 تسجيل الدخول لبرنامج مركز تحفيظ باب السلام</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username_input = st.text_input("اسم المستخدم:")
            password_input = st.text_input("كلمة المرور:", type="password")
            submit_login = st.form_submit_button("تسجيل الدخول", type="primary", use_container_width=True)
            if submit_login:
                cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username_input.strip(), password_input.strip()))
                user_match = cursor.fetchone()
                if user_match:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username_input.strip()
                    st.session_state["role"] = user_match[0]
                    st.query_params["user"] = username_input.strip()
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
    st.stop()

st.sidebar.markdown(f"👤 مرحباً بك: *{st.session_state['username']}*")
st.sidebar.caption(f"الرتبة: {'مدير النظام (رئيسي)' if st.session_state['role'] == 'admin' else 'معلم (مستخدم)'}")

if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.query_params.clear()
    st.rerun()

st.sidebar.divider()

if st.session_state['role'] == 'admin':
    st.sidebar.markdown("### ⚙️ لوحة تحكم المدير")
    
    with st.sidebar.expander("👥 إدارة الطلاب (إضافة / حذف)"):
        new_student = st.text_input("اسم الطالب الجديد:")
        if st.button("➕ إضافة الطالب", use_container_width=True):
            if new_student.strip():
                try:
                    cursor.execute("INSERT INTO students (name) VALUES (?)", (new_student.strip(),))
                    conn.commit()
                    st.success(f"تم إضافة الطالب ({new_student}) بنجاح!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("اسم الطالب موجود مسبقاً!")
            else:
                st.warning("يرجى كتابة اسم الطالب.")

        cursor.execute("SELECT name FROM students ORDER BY name ASC")
        current_students_list = [row[0] for row in cursor.fetchall()]
        if current_students_list:
            del_student = st.selectbox("اختر الطالب للحذف:", current_students_list, index=None, placeholder="اختر طالباً...", key="del_stu_sidebar")
            if st.button("🗑️ حذف الطالب المحدد", type="primary", use_container_width=True):
                if del_student:
                    cursor.execute("DELETE FROM students WHERE name = ?", (del_student,))
                    cursor.execute("DELETE FROM attendance_records WHERE student_name = ?", (del_student,))
                    cursor.execute("DELETE FROM hifz_records WHERE student_name = ?", (del_student,))
                    cursor.execute("DELETE FROM review_records WHERE student_name = ?", (del_student,))
                    conn.commit()
                    st.success(f"تم حذف الطالب ({del_student}) وجميع سجلاته بنجاح!")
                    st.rerun()

    with st.sidebar.expander("📥 خيارات الاسترداد والتصدير"):
        export_format_choice = st.radio("اختر صيغة التنزيل:", ["Excel (.xlsx)", "PDF (.html/print)"], horizontal=True, key="sidebar_export_fmt")
        
        export_option = st.selectbox(
            "اختر الكشف أو التقرير:", 
            [
                "تنزيل قاعدة البيانات الشاملة (Backup)", 
                "كشف الحضور والغياب الشبكي", 
                "كشف الحفظ الشبكي", 
                "كشف المراجعة الشبكي", 
                "تقرير شخصي كامل لطالب محدد"
            ],
            key="sidebar_export_option"
        )

        cursor.execute("SELECT name FROM students ORDER BY name ASC")
        all_students_sidebar = [row[0] for row in cursor.fetchall()]

        if export_option == "تقرير شخصي كامل لطالب محدد":
            single_student_sb = st.selectbox("🔎 اختر اسم الطالب:", all_students_sidebar, index=None, placeholder="اكتب اسم الطالب...", key="sb_single_stu")
            if single_student_sb:
                df_att_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, status AS حالة_الحضور FROM attendance_records WHERE student_name = '{single_student_sb}' ORDER BY date DESC", conn)
                df_hifz_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM hifz_records WHERE student_name = '{single_student_sb}' ORDER BY date DESC", conn)
                df_rev_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, amount AS حزب_المراجعة, rating AS التقييم FROM review_records WHERE student_name = '{single_student_sb}' ORDER BY date DESC", conn)
                
                if "Excel" in export_format_choice:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_att_single.to_excel(writer, index=False, sheet_name='سجل_الحضور')
                        df_hifz_single.to_excel(writer, index=False, sheet_name='سجل_الحفظ')
                        df_rev_single.to_excel(writer, index=False, sheet_name='سجل_المراجعة')
                    st.download_button(
                        label=f"📥 تنزيل Excel لـ ({single_student_sb})", 
                        data=output.getvalue(), 
                        file_name=f"تقرير_{single_student_sb}_{date.today()}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    html_single = f"""
                    <html dir="rtl"><head><meta charset="utf-8"><style>body{{font-family:Tahoma; text-align:right;}} table{{width:100%; border-collapse:collapse;}} th,td{{border:1px solid #ddd; padding:6px; text-align:center;}} th{{background:#eee;}}</style></head>
                    <body><h2>تقرير الطالب: {single_student_sb}</h2>
                    <h3>الحضور</h3>{df_att_single.to_html(index=False)}
                    <h3>الحفظ</h3>{df_hifz_single.to_html(index=False)}
                    <h3>المراجعة</h3>{df_rev_single.to_html(index=False)}</body></html>
                    """
                    st.download_button(label=f"📥 تنزيل PDF/HTML لـ ({single_student_sb})", data=html_single, file_name=f"تقرير_{single_student_sb}.html", mime="text/html", use_container_width=True)

        elif export_option == "تنزيل قاعدة البيانات الشاملة (Backup)":
            if st.button("تنزيل النسخة الاحتياطية الكاملة", use_container_width=True):
                df_att_all = pd.read_sql_query("SELECT * FROM attendance_records", conn)
                df_hifz_all = pd.read_sql_query("SELECT * FROM hifz_records", conn)
                df_rev_all = pd.read_sql_query("SELECT * FROM review_records", conn)
                df_students_all = pd.read_sql_query("SELECT * FROM students", conn)

                if "Excel" in export_format_choice:
                    output_backup = io.BytesIO()
                    with pd.ExcelWriter(output_backup, engine='openpyxl') as writer:
                        df_students_all.to_excel(writer, index=False, sheet_name='الطلاب')
                        df_att_all.to_excel(writer, index=False, sheet_name='السجل_اليومي_للحضور')
                        df_hifz_all.to_excel(writer, index=False, sheet_name='سجل_الحفظ')
                        df_rev_all.to_excel(writer, index=False, sheet_name='سجل_المراجعة')
                    
                    st.download_button(
                        label="📥 تنزيل النسخة الاحتياطية (Excel)", 
                        data=output_backup.getvalue(), 
                        file_name=f"Quran_Center_Backup_{date.today()}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                else:
                    html_backup = f"""
                    <html dir="rtl"><head><meta charset="utf-8"><style>body{{font-family:Tahoma; text-align:right;}} table{{width:100%; border-collapse:collapse;}} th,td{{border:1px solid #ddd; padding:6px; text-align:center;}} th{{background:#eee;}}</style></head>
                    <body><h2>النسخة الاحتياطية الشاملة - {date.today()}</h2>
                    <h3>الطلاب</h3>{df_students_all.to_html(index=False)}
                    <h3>الحضور</h3>{df_att_all.to_html(index=False)}
                    <h3>الحفظ</h3>{df_hifz_all.to_html(index=False)}
                    <h3>المراجعة</h3>{df_rev_all.to_html(index=False)}</body></html>
                    """
                    st.download_button(label="📥 تنزيل النسخة الاحتياطية (PDF/HTML)", data=html_backup, file_name=f"Backup_{date.today()}.html", mime="text/html", use_container_width=True)

        elif export_option == "كشف الحضور والغياب الشبكي":
            df_att_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, status AS الحالة FROM attendance_records", conn)
            df_pivot = df_att_raw.pivot_table(index='التاريخ', columns='الطالب', values='الحالة', aggfunc='first').reset_index() if not df_att_raw.empty else pd.DataFrame(columns=["التاريخ"])
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            if not df_pivot.empty:
                if "Excel" in export_format_choice:
                    out_p = io.BytesIO()
                    df_pivot.to_excel(out_p, index=False)
                    st.download_button("📥 تحميل الكشف كـ Excel", out_p.getvalue(), "كشف_الحضور.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                else:
                    st.download_button("📥 تحميل الكشف كـ HTML/PDF", df_pivot.to_html(index=False), "كشف_الحضور.html", "text/html", use_container_width=True)

        elif export_option == "كشف الحفظ الشبكي":
            df_hifz_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM hifz_records", conn)
            df_pivot = df_hifz_raw.pivot_table(index='التاريخ', columns='الطالب', values='التقييم', aggfunc='first').reset_index() if not df_hifz_raw.empty else pd.DataFrame(columns=["التاريخ"])
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            if not df_pivot.empty:
                if "Excel" in export_format_choice:
                    out_p = io.BytesIO()
                    df_pivot.to_excel(out_p, index=False)
                    st.download_button("📥 تحميل الكشف كـ Excel", out_p.getvalue(), "كشف_الحفظ.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                else:
                    st.download_button("📥 تحميل الكشف كـ HTML/PDF", df_pivot.to_html(index=False), "كشف_الحفظ.html", "text/html", use_container_width=True)

        elif export_option == "كشف المراجعة الشبكي":
            df_rev_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, (amount || ' [' || rating || ']') AS المراجعة FROM review_records", conn)
            df_pivot = df_rev_raw.pivot_table(index='التاريخ', columns='الطالب', values='المراجعة', aggfunc='first').reset_index() if not df_rev_raw.empty else pd.DataFrame(columns=["التاريخ"])
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            if not df_pivot.empty:
                if "Excel" in export_format_choice:
                    out_p = io.BytesIO()
                    df_pivot.to_excel(out_p, index=False)
                    st.download_button("📥 تحميل الكشف كـ Excel", out_p.getvalue(), "كشف_المراجعة.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                else:
                    st.download_button("📥 تحميل الكشف كـ HTML/PDF", df_pivot.to_html(index=False), "كشف_المراجعة.html", "text/html", use_container_width=True)

    with st.sidebar.expander("🗑️ مسح وإعادة تعيين بيانات التجربة"):
        st.warning("⚠️ سيؤدي هذا الخيار إلى حذف جميع الطلاب، وحركات الحضور، وسجلات الحفظ والمراجعة نهائياً للبدء بنظافة.")
        confirm_reset = st.checkbox("أوافق على مسح كافة البيانات والتجارب", key="confirm_reset_box")
        if st.button("🚨 مسح وإعادة تعيين البرنامج بالكامل", type="primary", use_container_width=True):
            if confirm_reset:
                cursor.execute("DELETE FROM attendance_records")
                cursor.execute("DELETE FROM hifz_records")
                cursor.execute("DELETE FROM review_records")
                cursor.execute("DELETE FROM students")
                conn.commit()
                st.success("✅ تم مسح كافة البيانات بنجاح وأصبح البرنامج نظيفاً وجاهزاً.")
                st.rerun()
            else:
                st.error("يرجى تحديد مربع التأكيد أولاً.")

    st.sidebar.divider()

# عرض الاسم بشكل مرتب ومنسق في سطر واحد مع الأيقونة
st.markdown("""
    <div class="app-header">
        <span>📖</span>
        <h1>مركز تحفيظ باب السلام</h1>
    </div>
""", unsafe_allow_html=True)

cursor.execute("SELECT name FROM students ORDER BY name ASC")
students_list = [row[0] for row in cursor.fetchall()]

if not students_list:
    st.info("👈 لا يوجد طلاب مضافون بعد! قم بإضافة الطلاب من القائمة الجانبية (لوحة تحكم المدير).")
else:
    entry_date = st.date_input("📅 تحديد تاريخ اليوم:", date.today())
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📝 الحضور والغياب الجماعي", "📖 الحفظ الجديد", "🔄 المراجعة", "🎯 متابعة تسلسل الأحزاب"])

    with tab1:
        st.markdown("### 📋 كشف الحضور والغياب الجماعي")
        search_att = st.text_input("🔍 تصفية القائمة بكتابة بداية الاسم:", "", key="search_att")
        filtered_att_students = [s for s in students_list if s.lower().startswith(search_att.strip().lower())]
        
        attendance_results = {}
        status_options = ["حضور", "غياب", "غياب بعذر", "تأخير"]

        for idx, student in enumerate(filtered_att_students):
            st.write(f"*{idx + 1}. {student}*")
            selected_status = st.radio(
                f"حالة {student}:", options=status_options, index=0, key=f"att_{student}", horizontal=True, label_visibility="collapsed"
            )
            attendance_results[student] = selected_status
            st.divider()

        if st.button("💾 حفظ كشف الحضور لجميع الطلاب الظاهرين", type="primary", use_container_width=True):
            for student_name, status in attendance_results.items():
                cursor.execute("DELETE FROM attendance_records WHERE date = ? AND student_name = ?", (str(entry_date), student_name))
                cursor.execute("INSERT INTO attendance_records (date, student_name, status) VALUES (?, ?, ?)", (str(entry_date), student_name, status))
                
                if status in ["غياب", "غياب بعذر"]:
                    cursor.execute("DELETE FROM hifz_records WHERE date = ? AND student_name = ?", (str(entry_date), student_name))
                    cursor.execute("INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating) VALUES (?, ?, ?, ?, ?, ?)", (str(entry_date), student_name, "-", 0, 0, "غائب"))
                    
                    cursor.execute("DELETE FROM review_records WHERE date = ? AND student_name = ?", (str(entry_date), student_name))
                    cursor.execute("INSERT INTO review_records (date, student_name, amount, rating) VALUES (?, ?, ?, ?)", (str(entry_date), student_name, "غائب", "غائب"))
                    
            conn.commit()
            st.success("✅ تم حفظ كشف الحضور وتحديث السجلات بنجاح!")

    with tab2:
        st.markdown("### 📖 تسجيل الحفظ الجديد")
        selected_student_hifz = st.selectbox("🔍 اختر اسم الطالب أو اكتب للبحث:", students_list, index=None, placeholder="اضغط لاختيار الطالب أو اكتب اسمه...", key="hifz_select_student")
        
        if selected_student_hifz:
            cursor.execute("SELECT status FROM attendance_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_hifz))
            att_row = cursor.fetchone()
            is_absent = att_row and att_row[0] in ["غياب", "غياب بعذر"]

            if is_absent:
                st.error(f"⚠️ تنبيه: الطالب (*{selected_student_hifz}*) مسجل كـ *({att_row[0]})* في هذا اليوم، لذلك لا يمكن تسجيل حفظ له وستبقى حالته غائباً.")
                cursor.execute("DELETE FROM hifz_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_hifz))
                cursor.execute("INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating) VALUES (?, ?, ?, ?, ?, ?)", (str(entry_date), selected_student_hifz, "-", 0, 0, "غائب"))
                conn.commit()
            else:
                st.success(f"تم اختيار الطالب: *{selected_student_hifz}*")
                hifz_rating = st.radio("تقييم الحفظ اليوم:", ["جيد", "إعادة", "غائب"], horizontal=True, key="hifz_rate")
                
                if st.button("حفظ التسميع 💾", key="save_hifz", type="primary", use_container_width=True):
                    cursor.execute("DELETE FROM hifz_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_hifz))
                    cursor.execute("INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating) VALUES (?, ?, ?, ?, ?, ?)", (str(entry_date), selected_student_hifz, "-", 0, 0, hifz_rating))
                    conn.commit()
                    st.success(f"تم تحديث حفظ الطالب ({selected_student_hifz}) بنجاح!")
                    st.rerun()

            st.divider()
            st.markdown(f"#### 📊 سجل إنجاز الطالب (آخر 10 نتائج): *{selected_student_hifz}*")
            df_student_hifz = pd.read_sql_query("SELECT date AS التاريخ, rating AS التقييم FROM hifz_records WHERE student_name = ? ORDER BY date DESC LIMIT 10", conn, params=(selected_student_hifz,))

            if not df_student_hifz.empty:
                html_table = "<table class='custom-table'><thead><tr><th>التاريخ</th><th>التقييم</th></tr></thead><tbody>"
                for _, row in df_student_hifz.iterrows():
                    badge = "badge-good" if row['التقييم'] == "جيد" else ("badge-retry" if row['التقييم'] == "إعادة" else "badge-absent")
                    html_table += f"<tr><td>{row['التاريخ']}</td><td><span class='{badge}'>{row['التقييم']}</span></td></tr>"
                html_table += "</tbody></table>"
                st.markdown(html_table, unsafe_allow_html=True)

    with tab3:
        st.markdown("### 🔄 تسجيل المراجعة")
        selected_student_rev = st.selectbox("🔍 اختر اسم الطالب أو اكتب للبحث:", students_list, index=None, placeholder="اضغط لاختيار الطالب أو اكتب اسمه...", key="rev_select_student")
        
        if selected_student_rev:
            cursor.execute("SELECT status FROM attendance_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_rev))
            att_row_rev = cursor.fetchone()
            is_absent_rev = att_row_rev and att_row_rev[0] in ["غياب", "غياب بعذر"]

            if is_absent_rev:
                st.error(f"⚠️ تنبيه: الطالب (*{selected_student_rev}*) مسجل كـ *({att_row_rev[0]})* في هذا اليوم، لذلك لا يمكن تسجيل مراجعة له وستبقى حالته غائباً.")
                cursor.execute("DELETE FROM review_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_rev))
                cursor.execute("INSERT INTO review_records (date, student_name, amount, rating) VALUES (?, ?, ?, ?)", (str(entry_date), selected_student_rev, "غائب", "غائب"))
                conn.commit()
            else:
                st.success(f"تم اختيار الطالب: *{selected_student_rev}*")
                if "selected_hizb" not in st.session_state:
                    st.session_state["selected_hizb"] = None
                if "show_hizb_grid" not in st.session_state:
                    st.session_state["show_hizb_grid"] = False

                st.write("📖 *حزب المراجعة:*")
                current_hizb_text = st.session_state["selected_hizb"] if st.session_state["selected_hizb"] else "اضغط هنا لاختيار الحزب (تنازلياً) 🔻"
                if st.button(f"🟢 {current_hizb_text}", use_container_width=True, key="toggle_hizb_btn"):
                    st.session_state["show_hizb_grid"] = not st.session_state["show_hizb_grid"]
                    st.rerun()

                if st.session_state["show_hizb_grid"]:
                    st.info("اضغط على اسم الحزب لاختياره مباشرة (الترتيب تنازلي من النهاية للبداية):")
                    for idx, hizb in enumerate(AHZAB_LIST_DESC):
                        if st.button(hizb, key=f"hizb_btn_{idx}", use_container_width=True):
                            st.session_state["selected_hizb"] = hizb
                            st.session_state["show_hizb_grid"] = False
                            st.rerun()

                review_hizb = st.session_state["selected_hizb"]
                if review_hizb:
                    st.success(f"تم تحديد الحزب: *{review_hizb}*")
                    review_rating = st.radio("تقييم المراجعة اليوم:", ["جيد", "إعادة"], horizontal=True, key="rev_rate")
                    
                    if st.button("حفظ المراجعة 💾", key="save_rev", type="primary", use_container_width=True):
                        cursor.execute("DELETE FROM review_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_rev))
                        cursor.execute("INSERT INTO review_records (date, student_name, amount, rating) VALUES (?, ?, ?, ?)", (str(entry_date), selected_student_rev, review_hizb, review_rating))
                        conn.commit()
                        st.success(f"تم تحديث مراجعة الطالب ({selected_student_rev}) بنجاح!")
                        st.session_state["selected_hizb"] = None
                        st.rerun()
                else:
                    st.warning("⚠️ يرجى اختيار الحزب أولاً قبل حفظ المراجعة.")

            st.divider()
            st.markdown(f"#### 📊 سجل مراجعة الطالب (آخر 10 نتائج): *{selected_student_rev}*")
            df_student_rev = pd.read_sql_query("SELECT date AS التاريخ, amount AS حزب_المراجعة, rating AS التقييم FROM review_records WHERE student_name = ? ORDER BY date DESC LIMIT 10", conn, params=(selected_student_rev,))

            if not df_student_rev.empty:
                html_table = "<table class='custom-table'><thead><tr><th>التاريخ</th><th>حزب المراجعة</th><th>التقييم</th></tr></thead><tbody>"
                for _, row in df_student_rev.iterrows():
                    badge = "badge-good" if row['التقييم'] == "جيد" else ("badge-retry" if row['التقييم'] == "إعادة" else "badge-absent")
                    html_table += f"<tr><td>{row['التاريخ']}</td><td>{row['حزب_المراجعة']}</td><td><span class='{badge}'>{row['التقييم']}</span></td></tr>"
                html_table += "</tbody></table>"
                st.markdown(html_table, unsafe_allow_html=True)

    with tab4:
        st.markdown("### 🎯 متابعة تسلسل الأحزاب (مراجعة الحلقة)")
        st.info("💡 *آلية النظام التصاعدية:* إذا اجتاز الطالب الحزب السابق بتقدير **(جيد)**، فإن النظام يحدد تلقائياً أن دوره اليوم هو مراجعة الحزب الذي يليه في الترتيب.")
        
        search_target_hizb = st.selectbox("🔎 اختر الحزب المطلوب لمعرفة الطلاب المطالبين بمراجعته اليوم:", AHZAB_LIST_DESC, index=0, key="circle_review_search")
        
        if search_target_hizb:
            target_index = AHZAB_LIST.index(search_target_hizb)
            if target_index > 0:
                previous_hizb = AHZAB_LIST[target_index - 1]
                st.markdown(f"📌 *التحليل:* الطلاب الذين أتقنوا حزب (*{previous_hizb}*) بتقدير *(جيد)* في آخر تسميع، دورهم المفترض اليوم في مراجعة حزب (*{search_target_hizb}*).")
                
                query_expected = f"""
                SELECT r.student_name AS الطالب, r.date AS تاريخ_آخر_إنجاز, r.amount AS الحزب_السابق 
                FROM review_records r
                JOIN (
                    SELECT student_name, MAX(id) as max_id 
                    FROM review_records 
                    WHERE amount = ? AND rating = 'جيد' 
                    GROUP BY student_name
                ) latest ON r.id = latest.max_id
                """
                df_expected = pd.read_sql_query(query_expected, conn, params=(previous_hizb,))
                
                if not df_expected.empty:
                    st.success(f"الطلاب المفترض مراجعتهم لـ ({search_target_hizb}) اليوم بناءً على التسلسل:")
                    html_exp_table = "<table class='custom-table'><thead><tr><th>اسم الطالب</th><th>آخر تاريخ إنجاز</th><th>الحزب السابق المجتاز</th><th>الحزب الحالي المطلوب</th></tr></thead><tbody>"
                    for _, row in df_expected.iterrows():
                        html_exp_table += f"<tr><td><b>{row['الطالب']}</b></td><td>{row['تاريخ_آخر_إنجاز']}</td><td>{row['الحزب_السابق']}</td><td><span class='badge-good'>{search_target_hizb}</span></td></tr>"
                    html_exp_table += "</tbody></table>"
                    st.markdown(html_exp_table, unsafe_allow_html=True)
                else:
                    st.warning(f"لايوجد طلاب مسجلين اجتازوا حزب ({previous_hizb}) بتقدير 'جيد' حتى الآن.")
            else:
                st.info("هذا هو الحزب الأول في الترتيب (الفاتحة).")

            st.divider()
            st.markdown(f"#### 📋 السجل الفعلي لمن راجعوا حزب ({search_target_hizb}) بالفعل:")
            df_actual_rev = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM review_records WHERE amount = ? ORDER BY date DESC", conn, params=(search_target_hizb,))
            if not df_actual_rev.empty:
                st.dataframe(df_actual_rev, use_container_width=True, hide_index=True)
            else:
                st.info(f"لم يتم تسجيل أي مراجعة فعلية لحزب ({search_target_hizb}) حتى الآن.")
