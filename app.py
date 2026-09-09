import sqlite3
from datetime import date
import io
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="إدارة حلقة القرآن", page_icon="📖", layout="centered")

# 1. إعداد قائمة أسماء الأحزاب فقط (من الأعلى إلى الفاتحة)
AHZAB_LIST = [
    "الأعلى",
    "النبأ",
    "الجن",
    "الملك",
    "الجمعة",
    "المجادلة",
    "الرحمن",
    "قال فما خطبكم",
    "لقد رضي",
    "الأحقاف",
    "قل أولو جئتكم",
    "إليه يرد",
    "وبقوم مالي",
    "فمن أظلم",
    "فنبذناه",
    "وما أنزلنا",
    "قل من يرزقكم",
    "إن المسلمين",
    "ومن يسلم",
    "ولا تجادلوا",
    "ولقد وصلنا",
    "قل الحمد لله",
    "قالوا أأنؤمن",
    "وقال الذين لا يرجون",
    "يأيها الذين آمنوا",
    "المؤمنون",
    "الحج",
    "الأنبيائ",
    "طه",
    "قال ألم أقل لك",
    "أولم يَرَوْا",
    "سبحان الذي",
    "وقال الله",
    "الحجر",
    "أمن يعلم",
    "وما أبرئ",
    "وإلى مدين",
    "وما من دابة",
    "الذين أحسنوا",
    "إنما السبيل",
    "يأيها الذين آمنوا",
    "واعلموا",
    "وإذ نتقنا",
    "قال الملأ",
    "الأعراف",
    "ولو أننا نزلنا",
    "إنما يستجيب",
    "لتجدن",
    "قال رجلان",
    "لا يحب",
    "الله لا إله إلا هو",
    "المحصنات",
    "يستبشرون",
    "لن تنالوا",
    "قل أؤنبئكم",
    "تلك الرسل",
    "واذكروا الله",
    "سيقول",
    "وإذا لقوا",
    "الفاتحة"
]

# 2. إعداد قاعدة البيانات وتأسيس الجداول
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

# تنسيق الاتجاه RTL وتصميم زر اختيار الحزب
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
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 15px;
        text-align: center;
        direction: rtl;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
    }
    .custom-table th {
        background-color: #f8f9fa;
        color: #333;
        font-weight: bold;
        padding: 10px;
        border-bottom: 2px solid #dee2e6;
    }
    .custom-table td {
        padding: 10px;
        border-bottom: 1px solid #e9ecef;
    }
    .custom-table tr:nth-of-type(even) {
        background-color: #fdfdfd;
    }
    .badge-good {
        background-color: #d1fae5;
        color: #065f46;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
    }
    .badge-retry {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
    }
    
    /* تحسين شكل زر اختيار الحزب للوضوح العالي */
    div[data-testid="stPopover"] > button {
        width: 100% !important;
        background-color: #f0fdf4 !important;
        border: 2px solid #16a34a !important;
        color: #15803d !important;
        font-weight: bold !important;
        font-size: 17px !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# نظام الجلسات باستخدام الرابط (st.query_params)
# --------------------------------------------------
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

# --------------------------------------------------
# الواجهة الرئيسية بعد تسجيل الدخول
# --------------------------------------------------
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
                df_rev_single = pd.read_sql_query(f"SELECT date AS التاريخ, student_name AS الطالب, amount AS حزب_المراجعة, rating AS التقييم FROM review_records WHERE student_name = '{single_student}' ORDER BY date DESC", conn)
                
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
            
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
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
            
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
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
            
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
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
        
        selected_student_hifz = st.selectbox(
            "🔍 اختر اسم الطالب أو اكتب للبحث:",
            students_list,
            index=None,
            placeholder="اضغط لاختيار الطالب أو اكتب اسمه...",
            key="hifz_select_student"
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

            st.markdown(f"#### 📊 سجل إنجاز الطالب (آخر 10 نتائج): *{selected_student_hifz}*")

            df_student_hifz = pd.read_sql_query(
                "SELECT date AS التاريخ, rating AS التقييم FROM hifz_records WHERE student_name = ? ORDER BY date DESC, id DESC LIMIT 10",
                conn, params=(selected_student_hifz,)
            )

            if not df_student_hifz.empty:
                html_table = "<table class='custom-table'><thead><tr><th>التاريخ</th><th>التقييم</th></tr></thead><tbody>"
                for _, row in df_student_hifz.iterrows():
                    badge = "badge-good" if row['التقييم'] == "جيد" else "badge-retry"
                    html_table += f"<tr><td>{row['التاريخ']}</td><td><span class='{badge}'>{row['التقييم']}</span></td></tr>"
                html_table += "</tbody></table>"

                st.markdown(html_table, unsafe_allow_html=True)

                st.divider()

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
    # TAB 3: المراجعة (تختفي النافذة فور اختيار الحزب)
    # --------------------------------------------------
    with tab3:
        st.markdown("### 🔄 تسجيل المراجعة")
        selected_student_rev = st.selectbox(
            "🔍 اختر اسم الطالب أو اكتب للبحث:",
            students_list,
            index=None,
            placeholder="اضغط لاختيار الطالب أو اكتب اسمه...",
            key="rev_select_student"
        )
        
        if selected_student_rev:
            st.success(f"تم اختيار الطالب: *{selected_student_rev}*")

            # تهيئة المتغير الحافظ للحزب المختار
            if "selected_hizb" not in st.session_state:
                st.session_state["selected_hizb"] = AHZAB_LIST[0]

            def on_hizb_change():
                st.session_state["selected_hizb"] = st.session_state["temp_hizb_choice"]

            st.write("📖 *اختر حزب المراجعة:*")
            
            # نافذة الاختيار تغلق تلقائياً فور النقر على أي حزب
            with st.popover(f"🟢 الحزب المختار حالياً: {st.session_state['selected_hizb']} (اضغط للتغيير)", use_container_width=True):
                st.radio(
                    "اختر اسم الحزب:",
                    AHZAB_LIST,
                    index=AHZAB_LIST.index(st.session_state["selected_hizb"]),
                    key="temp_hizb_choice",
                    on_change=on_hizb_change
                )
            
            review_hizb = st.session_state["selected_hizb"]
            
            review_rating = st.radio("تقييم المراجعة اليوم:", ["جيد", "إعادة"], horizontal=True, key="rev_rate")
            
            if st.button("حفظ المراجعة 💾", key="save_rev", type="primary"):
                cursor.execute("""
                    INSERT INTO review_records (date, student_name, amount, rating)
                    VALUES (?, ?, ?, ?)
                """, (str(entry_date), selected_student_rev, review_hizb, review_rating))
                conn.commit()
                st.success(f"تم حفظ مراجعة الطالب ({selected_student_rev}) بنجاح!")
                st.rerun()

            st.divider()

            # عرض سجل نتائج المراجعة
            st.markdown(f"#### 📊 سجل مراجعة الطالب (آخر 10 نتائج): *{selected_student_rev}*")

            df_student_rev = pd.read_sql_query(
                "SELECT date AS التاريخ, amount AS حزب_المراجعة, rating AS التقييم FROM review_records WHERE student_name = ? ORDER BY date DESC, id DESC LIMIT 10",
                conn, params=(selected_student_rev,)
            )

            if not df_student_rev.empty:
                html_table = "<table class='custom-table'><thead><tr><th>التاريخ</th><th>حزب المراجعة</th><th>التقييم</th></tr></thead><tbody>"
                for _, row in df_student_rev.iterrows():
                    badge = "badge-good" if row['التقييم'] == "جيد" else "badge-retry"
                    html_table += f"<tr><td>{row['التاريخ']}</td><td>{row['حزب_المراجعة']}</td><td><span class='{badge}'>{row['التقييم']}</span></td></tr>"
                html_table += "</tbody></table>"

                st.markdown(html_table, unsafe_allow_html=True)

                st.divider()

                rating_counts = df_student_rev['التقييم'].value_counts().reset_index()
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
                st.info("لا توجد سجلات مراجعة سابقة لهذا الطالب حتى الآن.")
