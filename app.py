import sqlite3
from datetime import date
import io
import pandas as pd
import streamlit as st
import altair as alt
from streamlit_searchbox import st_searchbox

# 1. إعداد قاعدة البيانات وتأسيس الجداول
conn = sqlite3.connect("quran_center.db", check_same_thread=False)
cursor = conn.cursor()

# جدول المستخدمين للتسجيل والدخول
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# إنشاء حساب أدمن رئيسي افتراضي إذا لم يكن موجوداً
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

st.set_page_config(page_title="إدارة حلقة القرآن", page_icon="📖", layout="centered")

# تنسيق الاتجاه RTL
st.markdown("""
    <style>
    .stMainBlockContainer { direction: rtl !important; text-align: right !important; }
    .stMainBlockContainer div, .stMainBlockContainer p, .stMainBlockContainer label, 
    .stMainBlockContainer h1, .stMainBlockContainer h2, .stMainBlockContainer h3 {
        text-align: right !important; direction: rtl !important;
    }
    section[data-testid="stSidebar"] { direction: ltr !important; }
    section[data-testid="stSidebar"] * { direction: rtl !important; text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# نظام تسجيل الدخول وإدارة الجلسة
# --------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

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
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
    st.stop()

# --------------------------------------------------
# الواجهة الرئيسية بعد تسجيل الدخول
# --------------------------------------------------
st.sidebar.markdown(f"👤 مرحباً بك: *{st.session_state['username']}*")
st.sidebar.caption(f"الرتبة: {'مدير النظام (رئيسي)' if st.session_state['role'] == 'admin' else 'معلم (مستخدم)'}")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.rerun()

st.sidebar.divider()
st.title("📖 برنامج إدارة مركز التحفيظ")

# --------------------------------------------------
# قسم إدارة المستخدمين (للمستخدم الرئيسي Admin فقط)
# --------------------------------------------------
if st.session_state["role"] == "admin":
    st.sidebar.header("👑 إدارة حسابات المستخدمين")
    new_user = st.sidebar.text_input("اسم مستخدم جديد:", key="add_user_name")
    new_pass = st.sidebar.text_input("كلمة المرور:", type="password", key="add_user_pass")
    
    if st.sidebar.button("إضافة مستخدم جديد"):
        if new_user.strip() and new_pass.strip():
            try:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (new_user.strip(), new_pass.strip(), "user"))
                conn.commit()
                st.sidebar.success(f"تم إنشاء حساب للمستخدم: {new_user}")
            except sqlite3.IntegrityError:
                st.sidebar.error("اسم المستخدم هذا مسجل مسبقاً.")
        else:
            st.sidebar.warning("يرجى ملء كافة البيانات.")

    st.sidebar.divider()

# --------------------------------------------------
# إدارة الطلاب
# --------------------------------------------------
st.sidebar.header("⚙️ إدارة الطلاب")

if st.session_state["role"] == "admin":
    st.sidebar.subheader("➕ إضافة طالب جديد")
    new_student = st.sidebar.text_input("اسم الطالب الجديد:")
    if st.sidebar.button("إضافة الطالب"):
        if new_student.strip() != "":
            try:
                cursor.execute("INSERT INTO students (name) VALUES (?)", (new_student.strip(),))
                conn.commit()
                st.sidebar.success(f"تمت إضافة الطالب: {new_student}")
                st.rerun()
            except sqlite3.IntegrityError:
                st.sidebar.error("هذا الاسم موجود بالفعل!")
        else:
            st.sidebar.warning("يرجى كتابة اسم الطالب.")

    st.sidebar.divider()

# جلب قائمة الطلاب
cursor.execute("SELECT name FROM students ORDER BY name ASC")
students_list = [row[0] for row in cursor.fetchall()]

def search_students(search_term: str):
    if not search_term:
        return students_list
    return [s for s in students_list if s.strip().lower().startswith(search_term.strip().lower())]

if st.session_state["role"] == "admin":
    st.sidebar.subheader("🗑️ إزالة طالب")
    if students_list:
        student_to_remove = st.sidebar.selectbox(
            "اختر الطالب المراد إزالته:",
            students_list,
            index=None,
            placeholder="اختر الطالب للحذف...",
            key="remove_select"
        )
        if st.sidebar.button("حذف الطالب", type="secondary"):
            if student_to_remove:
                cursor.execute("DELETE FROM students WHERE name = ?", (student_to_remove,))
                conn.commit()
                st.sidebar.success(f"تمت إزالة الطالب ({student_to_remove}) بنجاح!")
                st.rerun()
            else:
                st.sidebar.warning("يرجى اختيار طالب أولاً لإزالته.")

# --------------------------------------------------
# الواجهة الرئيسية لتسجيل البيانات
# --------------------------------------------------
if not students_list:
    st.info("👈 لا يوجد طلاب مضافون بعد! قم بإضافة الطلاب من القائمة الجانبية.")
else:
    entry_date = st.date_input("📅 تحديد تاريخ اليوم:", date.today())
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📝 الحضور والغياب المجمع والتصدير", "📖 الحفظ الجديد", "🔄 المراجعة"])

    # --------------------------------------------------
    # TAB 1: الحضور والغياب وتصدير البيانات
    # --------------------------------------------------
    with tab1:
        st.markdown("### 📋 كشف الحضور والغياب الجماعي")
        search_att = st.text_input("🔍 تصفية القائمة بكتابة بداية الاسم:", "", key="search_att")
        filtered_att_students = [s for s in students_list if s.lower().startswith(search_att.strip().lower())]
        
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
                label_visibility="collapsed"
            )
            attendance_results[student] = selected_status
            st.divider()

        if st.button("💾 حفظ كشف الحضور لجميع الطلاب الظاهرين", type="primary"):
            for student_name, status in attendance_results.items():
                cursor.execute("""
                    INSERT INTO attendance_records (date, student_name, status)
                    VALUES (?, ?, ?)
                """, (str(entry_date), student_name, status))
            conn.commit()
            st.success("✅ تم حفظ الحضور بنجاح!")

        # --------------------------------------------------
        # قسم تصدير البيانات إلى Excel
        # --------------------------------------------------
        st.divider()
        st.subheader("📊 تصدير السجلات إلى ملف Excel")
        
        export_option = st.selectbox(
            "اختر نوع الكشف المراد معاينته وتنزيله:",
            ["كشف الحضور والغياب الشبكي", "كشف الحفظ الشبكي", "كشف المراجعة الشبكي", "تقرير شخصي كامل لطالب محدد"]
        )

        if export_option == "تقرير شخصي كامل لطالب محدد":
            single_student = st.selectbox(
                "🔎 اختر اسم الطالب لتنزيل ملفه الخاص:",
                students_list,
                index=None,
                placeholder="اضغط واكتب اسم الطالب...",
                key="export_single_search"
            )
            
            if single_student:
                df_att_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, status AS حالة_الحضور FROM attendance_records WHERE student_name = '{single_student}' ORDER BY date DESC", conn)
                df_hifz_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM hifz_records WHERE student_name = '{single_student}' ORDER BY date DESC", conn)
                df_rev_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, amount AS مقدار_المراجعة, rating AS التقييم FROM review_records WHERE student_name = '{single_student}' ORDER BY date DESC", conn)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_att_single.to_excel(writer, index=False, sheet_name='سجل_الحضور')
                    df_hifz_single.to_excel(writer, index=False, sheet_name='سجل_الحفظ')
                    df_rev_single.to_excel(writer, index=False, sheet_name='سجل_المراجعة')
                excel_data = output.getvalue()
                
                st.download_button(
                    label=f"📥 تنزيل ملف Excel الشامل لـ ({single_student})",
                    data=excel_data,
                    file_name=f"تقرير_{single_student}_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        elif export_option == "كشف الحضور والغياب الشبكي":
            df_att_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, status AS الحالة FROM attendance_records", conn)
            df_pivot = df_att_raw.pivot_table(index='التاريخ', columns='الطالب', values='الحالة', aggfunc='first').reset_index() if not df_att_raw.empty else pd.DataFrame(columns=["التاريخ"])
            
            st.dataframe(df_pivot, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_pivot.to_excel(writer, index=False, sheet_name='كشف_الحضور')
            
            st.download_button(
                label="📥 تنزيل كشف الحضور والغياب الشبكي",
                data=output.getvalue(),
                file_name=f"كشف_الحضور_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        elif export_option == "كشف الحفظ الشبكي":
            df_hifz_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, rating AS التقييم FROM hifz_records", conn)
            df_pivot = df_hifz_raw.pivot_table(index='التاريخ', columns='الطالب', values='التقييم', aggfunc='first').reset_index() if not df_hifz_raw.empty else pd.DataFrame(columns=["التاريخ"])
            
            st.dataframe(df_pivot, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_pivot.to_excel(writer, index=False, sheet_name='كشف_الحفظ')
            
            st.download_button(
                label="📥 تنزيل كشف الحفظ الشبكي",
                data=output.getvalue(),
                file_name=f"كشف_الحفظ_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        elif export_option == "كشف المراجعة الشبكي":
            df_rev_raw = pd.read_sql_query("SELECT date AS التاريخ, student_name AS الطالب, (amount || ' [' || rating || ']') AS المراجعة FROM review_records", conn)
            df_pivot = df_rev_raw.pivot_table(index='التاريخ', columns='الطالب', values='المراجعة', aggfunc='first').reset_index() if not df_rev_raw.empty else pd.DataFrame(columns=["التاريخ"])
            
            st.dataframe(df_pivot, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_pivot.to_excel(writer, index=False, sheet_name='كشف_المراجعة')
            
            st.download_button(
                label="📥 تنزيل كشف المراجعة الشبكي",
                data=output.getvalue(),
                file_name=f"كشف_المراجعة_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # --------------------------------------------------
    # TAB 2: الحفظ الجديد
    # --------------------------------------------------
    with tab2:
        st.markdown("### 📖 تسجيل الحفظ الجديد")
        
        selected_student_hifz = st_searchbox(
            search_students,
            placeholder="🔍 اكتب اسم الطالب أو الحرف الأول مباشرة...",
            key="hifz_live_search"
        )
        
        if selected_student_hifz:
            st.success(f"تم اختيار الطالب: *{selected_student_hifz}*")
            
            hifz_rating = st.radio("تقييم الحفظ اليوم:", ["جيد", "إعادة"], horizontal=True, key="hifz_rate")
            
            if st.button("حفظ التسميع 💾", key="save_hifz", type="primary"):
                cursor.execute("""
                    INSERT INTO hifz_records (date, student_name, surah, from_ayah, to_ayah, rating)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (str(entry_date), selected_student_hifz, "-", 0, 0, hifz_rating))
                conn.commit()
                st.success(f"تم حفظ تسميع الطالب ({selected_student_hifz})!")
                st.rerun()

            st.divider()

            st.markdown(f"#### 📊 سجل إنجاز الطالب: *{selected_student_hifz}*")

            # جلب البيانات مرتبة من الأحدث إلى الأقدم حسب التاريخ
            df_student_hifz = pd.read_sql_query(
                "SELECT date AS التاريخ, rating AS التقييم FROM hifz_records WHERE student_name = ? ORDER BY date DESC, id DESC",
                conn, params=(selected_student_hifz,)
            )

            if not df_student_hifz.empty:
                # 1. عرض جدول البيانات أولاً (مرتب من الأحدث إلى الأقدم)
                st.dataframe(df_student_hifz, use_container_width=True)

                st.divider()

                # 2. عرض الرسم البياني (Chart) ثانياً
                rating_counts = df_student_hifz['التقييم'].value_counts().reset_index()
                rating_counts.columns = ['التقييم', 'العدد']

                bars = alt.Chart(rating_counts).mark_bar(
                    cornerRadiusTopLeft=10,
                    cornerRadiusTopRight=10,
                    width=60
                ).encode(
                    x=alt.X('التقييم:N', title='نوع التقييم', axis=alt.Axis(labelAngle=0, labelFontSize=14, titleFontSize=14)),
                    y=alt.Y('العدد:Q', title='عدد المرات', axis=alt.Axis(labelFontSize=12, titleFontSize=14)),
                    color=alt.Color('التقييم:N', scale=alt.Scale(domain=['جيد', 'إعادة'], range=['#10b981', '#ef4444']), legend=None),
                    tooltip=['التقييم', 'العدد']
                )

                text = bars.mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,
                    fontSize=14,
                    fontWeight='bold'
                ).encode(
                    text='العدد:Q'
                )

                chart = (bars + text).properties(height=280)

                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("لا توجد سجلات حفظ سابقة لهذا الطالب حتى الآن.")

    # --------------------------------------------------
    # TAB 3: المراجعة
    # --------------------------------------------------
    with tab3:
        st.markdown("### 🔄 تسجيل المراجعة")
        selected_student_rev = st_searchbox(
            search_students,
            placeholder="🔍 اكتب اسم الطالب أو الحرف الأول مباشرة...",
            key="rev_live_search"
        )
        
        if selected_student_rev:
            st.success(f"تم اختيار الطالب: *{selected_student_rev}*")

        st.divider()
        review_amount = st.text_input("مقدار المراجعة:", "من سورة يس إلى الواقعة", key="rev_amount")
        review_rating = st.selectbox("تقييم المراجعة:", ["ممتاز", "جيد جداً", "جيد", "لم يراجع"], key="rev_rate")
        
        if st.button("حفظ المراجعة 💾", key="save_rev", type="primary"):
            if not selected_student_rev:
                st.error("⚠️ يرجى اختيار اسم الطالب أولاً من قائمة البحث!")
            else:
                cursor.execute("""
                    INSERT INTO review_records (date, student_name, amount, rating)
                    VALUES (?, ?, ?, ?)
                """, (str(entry_date), selected_student_rev, review_amount, review_rating))
                conn.commit()
                st.success(f"تم حفظ مراجعة الطالب ({selected_student_rev})!")
