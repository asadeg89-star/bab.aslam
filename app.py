import sqlite3
from datetime import date
import io
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="إدارة حلقة القرآن", page_icon="📖", layout="centered")

AHZAB_LIST = [
    "الأعلى", "النبأ", "الجن", "الملك", "الجمعة", "المجادلة", "الرحمن", 
    "قال فما خطبكم", "لقد رضي", "الأحقاف", "قل أولو جئتكم", "إليه يرد", 
    "وبقوم مالي", "فمن أظلم", "فنبذناه", "وما أنزلنا", "قل من يرزقكم", 
    "إن المسلمين", "ومن يسلم", "ولا تجادلوا", "ولقد وصلنا", "قل الحمد لله", 
    "قالوا أأنؤمن", "وقال الذين لا يرجون", "يأيها الذين آمنوا", "المؤمنون", 
    "الحج", "الأنبياء", "طه", "قال ألم أقل لك", "أولم يَرَوْا", "سبحان الذي", 
    "وقال الله", "الحجر", "أمن يعلم", "وما أبرئ", "وإلى مدين", "وما من دابة", 
    "الذين أحسنوا", "إنما السبيل", "يأيها الذين آمنوا", "واعلموا", "وإذ نتقنا", 
    "قال الملأ", "الأعراف", "ولو أننا نزلنا", "إنما يستجيب", "لتجدن", 
    "قال رجلان", "لا يحب", "الله لا إله إلا هو", "المحصنات", "يستبشرون", 
    "لن تنالوا", "قل أؤنبئكم", "تلك الرسل", "واذكروا الله", "سيقول", "وإذا لقوا", "الفاتحة"
]

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

st.markdown("""
    <style>
    .stMainBlockContainer { direction: rtl !important; text-align: right !important; }
    .stMainBlockContainer div, .stMainBlockContainer p, .stMainBlockContainer label, 
    .stMainBlockContainer h1, .stMainBlockContainer h2, .stMainBlockContainer h3 {
        text-align: right !important; direction: rtl !important;
    }
    section[data-testid="stSidebar"] { direction: ltr !important; }
    section[data-testid="stSidebar"] * { direction: rtl !important; text-align: right !important; }
    
    .custom-table {
        width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; direction: rtl; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;
    }
    .custom-table th { background-color: #f8f9fa; color: #333; font-weight: bold; padding: 10px; border-bottom: 2px solid #dee2e6; }
    .custom-table td { padding: 10px; border-bottom: 1px solid #e9ecef; }
    .custom-table tr:nth-of-type(even) { background-color: #fdfdfd; }
    .badge-good { background-color: #d1fae5; color: #065f46; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-retry { background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-absent { background-color: #f3f4f6; color: #4b5563; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
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
    st.title("🔐 تسجيل الدخول للبرنامج")
    with st.form("login_form"):
        username_input = st.text_input("اسم المستخدم:")
        password_input = st.text_input("كلمة المرور:", type="password")
        submit_login = st.form_submit_button("تسجيل الدخول", type="primary")
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

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.query_params.clear()
    st.rerun()

st.sidebar.divider()
st.title("📖 برنامج إدارة مركز التحفيظ")

cursor.execute("SELECT name FROM students ORDER BY name ASC")
students_list = [row[0] for row in cursor.fetchall()]

if not students_list:
    st.info("👈 لا يوجد طلاب مضافون بعد! قم بإضافة الطلاب من القائمة الجانبية.")
else:
    entry_date = st.date_input("📅 تحديد تاريخ اليوم:", date.today())
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📝 الحضور والغياب المجمع والتصدير", "📖 الحفظ الجديد", "🔄 المراجعة"])

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

        if st.button("💾 حفظ كشف الحضور لجميع الطلاب الظاهرين", type="primary"):
            for student_name, status in attendance_results.items():
                cursor.execute("DELETE FROM attendance_records WHERE date = ? AND student_name = ?", (str(entry_date), student_name))
                cursor.execute("INSERT INTO attendance_records (date, student_name, status) VALUES (?, ?, ?)", (str(entry_date), student_name, status))
                
                # إذا كان الطالب غائباً يتم تثبيت الحفظ والمراجعة كـ "غائب" تلقائياً
                if status in ["غياب", "غياب بعذر"]:
                    cursor.execute("DELETE FROM hifz_records WHERE date = ? AND student_name = ?", (str(entry_date), student_name))
                    cursor.execute("INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating) VALUES (?, ?, ?, ?, ?, ?)", (str(entry_date), student_name, "-", 0, 0, "غائب"))
                    
                    cursor.execute("DELETE FROM review_records WHERE date = ? AND student_name = ?", (str(entry_date), student_name))
                    cursor.execute("INSERT INTO review_records (date, student_name, amount, rating) VALUES (?, ?, ?, ?)", (str(entry_date), student_name, "غائب", "غائب"))
                    
            conn.commit()
            st.success("✅ تم حفظ كشف الحضور وتحديث السجلات بنجاح!")

        st.divider()
        st.subheader("📊 تصدير السجلات إلى ملف Excel")
        export_option = st.selectbox("اختر نوع الكشف المراد معاينته وتنزيله:", ["كشف الحضور والغياب الشبكي", "كشف الحفظ الشبكي", "كشف المراجعة الشبكي", "تقرير شخصي كامل لطالب محدد"])

        if export_option == "تقرير شخصي كامل لطالب محدد":
            single_student = st.selectbox("🔎 اختر اسم الطالب لتنزيل ملفه الخاص:", students_list, index=None, placeholder="اضغط واكتب اسم الطالب...", key="export_single_search")
            if single_student:
                df_att_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, status AS حالة_الحضور FROM attendance_records WHERE student_name = '{single_student}' ORDER BY date DESC", conn)
                df_hifz_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM hifz_records WHERE student_name = '{single_student}' ORDER BY date DESC", conn)
                df_rev_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, amount AS حزب_المراجعة, rating AS التقييم FROM review_records WHERE student_name = '{single_student}' ORDER BY date DESC", conn)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_att_single.to_excel(writer, index=False, sheet_name='سجل_الحضور')
                    df_hifz_single.to_excel(writer, index=False, sheet_name='سجل_الحفظ')
                    df_rev_single.to_excel(writer, index=False, sheet_name='سجل_المراجعة')
                st.download_button(label=f"📥 تنزيل ملف Excel الشامل لـ ({single_student})", data=output.getvalue(), file_name=f"تقرير_{single_student}_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        elif export_option == "كشف الحضور والغياب الشبكي":
            df_att_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, status AS الحالة FROM attendance_records", conn)
            df_pivot = df_att_raw.pivot_table(index='التاريخ', columns='الطالب', values='الحالة', aggfunc='first').reset_index() if not df_att_raw.empty else pd.DataFrame(columns=["التاريخ"])
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)

        elif export_option == "كشف الحفظ الشبكي":
            df_hifz_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM hifz_records", conn)
            df_pivot = df_hifz_raw.pivot_table(index='التاريخ', columns='الطالب', values='التقييم', aggfunc='first').reset_index() if not df_hifz_raw.empty else pd.DataFrame(columns=["التاريخ"])
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)

        elif export_option == "كشف المراجعة الشبكي":
            df_rev_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, (amount || ' [' || rating || ']') AS المراجعة FROM review_records", conn)
            df_pivot = df_rev_raw.pivot_table(index='التاريخ', columns='الطالب', values='المراجعة', aggfunc='first').reset_index() if not df_rev_raw.empty else pd.DataFrame(columns=["التاريخ"])
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### 📖 تسجيل الحفظ الجديد")
        selected_student_hifz = st.selectbox("🔍 اختر اسم الطالب أو اكتب للبحث:", students_list, index=None, placeholder="اضغط لاختيار الطالب أو اكتب اسمه...", key="hifz_select_student")
        
        if selected_student_hifz:
            # التحقق مما إذا كان الطالب مسجلاً كغائب في نفس اليوم
            cursor.execute("SELECT status FROM attendance_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_hifz))
            att_row = cursor.fetchone()
            is_absent = att_row and att_row[0] in ["غياب", "غياب بعذر"]

            if is_absent:
                st.error(f"⚠️ تنبيه: الطالب (*{selected_student_hifz}*) مسجل كـ *({att_row[0]})* في هذا اليوم، لذلك لا يمكن تسجيل حفظ له وستبقى حالته غائباً.")
                # فرض وتحديث الحفظ تلقائياً ليكون غائباً
                cursor.execute("DELETE FROM hifz_records WHERE date = ? AND student_name = ?", (str(entry_date), selected_student_hifz))
                cursor.execute("INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating) VALUES (?, ?, ?, ?, ?, ?)", (str(entry_date), selected_student_hifz, "-", 0, 0, "غائب"))
                conn.commit()
            else:
                st.success(f"تم اختيار الطالب: *{selected_student_hifz}*")
                hifz_rating = st.radio("تقييم الحفظ اليوم:", ["جيد", "إعادة", "غائب"], horizontal=True, key="hifz_rate")
                
                if st.button("حفظ التسميع 💾", key="save_hifz", type="primary"):
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
                current_hizb_text = st.session_state["selected_hizb"] if st.session_state["selected_hizb"] else "اضغط هنا لاختيار الحزب (من الأعلى إلى الفاتحة) 🔻"
                if st.button(f"🟢 {current_hizb_text}", use_container_width=True, key="toggle_hizb_btn"):
                    st.session_state["show_hizb_grid"] = not st.session_state["show_hizb_grid"]
                    st.rerun()

                if st.session_state["show_hizb_grid"]:
                    st.info("اضغط على اسم الحزب لاختياره مباشرة:")
                    for idx, hizb in enumerate(AHZAB_LIST):
                        if st.button(hizb, key=f"hizb_btn_{idx}", use_container_width=True):
                            st.session_state["selected_hizb"] = hizb
                            st.session_state["show_hizb_grid"] = False
                            st.rerun()

                review_hizb = st.session_state["selected_hizb"]
                if review_hizb:
                    st.success(f"تم تحديد الحزب: *{review_hizb}*")
                    review_rating = st.radio("تقييم المراجعة اليوم:", ["جيد", "إعادة"], horizontal=True, key="rev_rate")
                    
                    if st.button("حفظ المراجعة 💾", key="save_rev", type="primary"):
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
