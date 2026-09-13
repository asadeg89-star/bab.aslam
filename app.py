from datetime import date
import io
import json
import pandas as pd
import streamlit as st
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="مركز تحفيظ باب السلام", page_icon="📖", layout="centered")

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

# --- الاتصال بجداول جوجل (Google Sheets) المعدل ليعمل بسلاسة ---
@st.cache_resource
def init_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # تحويل الـ secrets إلى قاموس (Dictionary) بشكل آمن
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # التصحيح التلقائي لمفتاح الـ Private Key في حال وجود مشكلة في الأسطر الجديدة
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("QuranCenterDB")
    return spreadsheet

try:
    sh = init_google_sheets()
    users_sheet = sh.worksheet("users")
    students_sheet = sh.worksheet("students")
    attendance_sheet = sh.worksheet("attendance_records")
    hifz_sheet = sh.worksheet("hifz_records")
    review_sheet = sh.worksheet("review_records")
except Exception as e:
    st.error(f"خطأ في الاتصال بجداول جوجل: تأكد من إعداد ملف الـ Secrets وصلاحيات الملف. التفاصيل: {e}")
    st.stop()

# --- دوال مساعدة للتعامل مع جداول جوجل كـ DataFrames ---
def get_data(worksheet):
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def save_data(worksheet, df):
    worksheet.clear()
    if not df.empty:
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    else:
        worksheet.update([[]])

# التحقق من وجود جدول المستخدمين أو إنشاء حساب الأدمن الافتراضي
df_users = get_data(users_sheet)
if df_users.empty or 'username' not in df_users.columns:
    df_users = pd.DataFrame([{"username": "admin", "password": "admin123", "role": "admin"}])
    save_data(users_sheet, df_users)

# التأكد من بقية الجداول
df_students = get_data(students_sheet)
if df_students.empty or 'name' not in df_students.columns:
    df_students = pd.DataFrame(columns=["name"])
    save_data(students_sheet, df_students)

df_att = get_data(attendance_sheet)
if df_att.empty or 'date' not in df_att.columns:
    df_att = pd.DataFrame(columns=["id", "date", "student_name", "status"])
    save_data(attendance_sheet, df_att)

df_hifz = get_data(hifz_sheet)
if df_hifz.empty or 'date' not in df_hifz.columns:
    df_hifz = pd.DataFrame(columns=["id", "date", "student_name", "surah", "from_ayah", "to_ayah", "rating"])
    save_data(hifz_sheet, df_hifz)

df_rev = get_data(review_sheet)
if df_rev.empty or 'date' not in df_rev.columns:
    df_rev = pd.DataFrame(columns=["id", "date", "student_name", "amount", "rating"])
    save_data(review_sheet, df_rev)


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
    .stMainBlockContainer { direction: rtl !important; text-align: right !important; background-color: #fcfdfd; padding: 1.5rem; border-radius: 16px; }
    .stMainBlockContainer div, .stMainBlockContainer p, .stMainBlockContainer label, .stMainBlockContainer h1, .stMainBlockContainer h2, .stMainBlockContainer h3 { text-align: right !important; direction: rtl !important; }
    section[data-testid="stSidebar"] { direction: ltr !important; background-color: #f4f7f6; border-left: 1px solid #e1e8e6; }
    section[data-testid="stSidebar"] * { direction: rtl !important; text-align: right !important; }
    .app-header { display: flex; align-items: center; justify-content: center; gap: 12px; background: #f8fafc; padding: 12px; border-radius: 14px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    .app-header h1 { color: #0f766e; margin: 0; font-size: 22px; font-weight: 700; }
    .custom-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; direction: rtl; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; }
    .custom-table th { background-color: #0f766e; color: #ffffff; padding: 12px; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #edf2f7; color: #1e293b; }
    .badge-good { background-color: #d1fae5; color: #065f46; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; }
    .badge-retry { background-color: #fee2e2; color: #991b1b; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; }
    .badge-none { background-color: #fef3c7; color: #92400e; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; }
    .badge-absent { background-color: #f1f5f9; color: #475569; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; }
    div.stButton > button { border-radius: 10px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

if "user" in st.query_params:
    logged_username = st.query_params["user"]
    df_u = get_data(users_sheet)
    user_row = df_u[df_u['username'] == logged_username]
    if not user_row.empty:
        st.session_state["authenticated"] = True
        st.session_state["username"] = logged_username
        st.session_state["role"] = str(user_row.iloc[0]['role'])

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #0f766e;'>🔐 تسجيل الدخول لبرنامج مركز تحفيظ باب السلام</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username_input = st.text_input("اسم المستخدم:")
            password_input = st.text_input("كلمة المرور:", type="password")
            submit_login = st.form_submit_button("تسجيل الدخول", type="primary", use_container_width=True)
            if submit_login:
                df_u = get_data(users_sheet)
                match = df_u[(df_u['username'] == username_input.strip()) & (df_u['password'] == password_input.strip())]
                if not match.empty:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username_input.strip()
                    st.session_state["role"] = str(match.iloc[0]['role'])
                    st.query_params["user"] = username_input.strip()
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
    st.stop()

st.sidebar.markdown(f"👤 مرحباً بك: **{st.session_state['username']}**")
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
    
    with st.sidebar.expander("👨‍🏫 إدارة المعلمين"):
        new_teacher_user = st.text_input("اسم المستخدم للمعلم:")
        new_teacher_pass = st.text_input("كلمة المرور:", type="password", key="new_t_pass")
        if st.button("➕ إضافة المعلم", use_container_width=True):
            if new_teacher_user.strip() and new_teacher_pass.strip():
                df_u = get_data(users_sheet)
                if new_teacher_user.strip() in df_u['username'].values:
                    st.error("اسم المستخدم هذا موجود مسبقاً.")
                else:
                    new_row = pd.DataFrame([{"username": new_teacher_user.strip(), "password": new_teacher_pass.strip(), "role": "user"}])
                    df_u = pd.concat([df_u, new_row], ignore_index=True)
                    save_data(users_sheet, df_u)
                    st.success(f"تم إضافة المعلم ({new_teacher_user}) بنجاح!")
                    st.rerun()
            else:
                st.warning("يرجى إدخال اسم المستخدم وكلمة المرور.")

    with st.sidebar.expander("🗑️ حذف معلم"):
        df_u = get_data(users_sheet)
        teachers_list = df_u[df_u['username'] != 'admin']['username'].tolist()
        if teachers_list:
            selected_teacher_to_delete = st.selectbox("اختر المعلم للحذف:", teachers_list, index=None, placeholder="اختر معلماً...")
            confirm_teacher_del = st.checkbox("أوافق على حذف هذا المعلم نهائياً", key="confirm_teacher_del_box")
            if st.button("🗑️ حذف المعلم المحدد", type="primary", use_container_width=True):
                if selected_teacher_to_delete and confirm_teacher_del:
                    df_u = df_u[df_u['username'] != selected_teacher_to_delete]
                    save_data(users_sheet, df_u)
                    st.success(f"تم حذف المعلم ({selected_teacher_to_delete}) بنجاح!")
                    st.rerun()
                else:
                    st.error("يرجى اختيار معلم وتحديد مربع التأكيد.")
        else:
            st.info("لا يوجد معلمون مضافون للحذف.")

    with st.sidebar.expander("👥 إدارة الطلاب"):
        new_student = st.text_input("اسم الطالب الجديد:")
        if st.button("➕ إضافة الطالب", use_container_width=True):
            if new_student.strip():
                df_s = get_data(students_sheet)
                if df_s.empty or new_student.strip() not in df_s['name'].values:
                    new_row = pd.DataFrame([{"name": new_student.strip()}])
                    df_s = pd.concat([df_s, new_row], ignore_index=True)
                    save_data(students_sheet, df_s)
                    st.success(f"تم إضافة الطالب ({new_student}) بنجاح!")
                    st.rerun()
                else:
                    st.error("اسم الطالب موجود مسبقاً!")
            else:
                st.warning("يرجى كتابة اسم الطالب.")

        df_s = get_data(students_sheet)
        current_students_list = df_s['name'].tolist() if not df_s.empty else []
        if current_students_list:
            del_student = st.selectbox("اختر الطالب للحذف:", current_students_list, index=None, placeholder="اختر طالباً...")
            if st.button("🗑️ حذف الطالب المحدد", type="primary", use_container_width=True):
                if del_student:
                    save_data(students_sheet, df_s[df_s['name'] != del_student])
                    df_att_now = get_data(attendance_sheet)
                    save_data(attendance_sheet, df_att_now[df_att_now['student_name'] != del_student])
                    df_hifz_now = get_data(hifz_sheet)
                    save_data(hifz_sheet, df_hifz_now[df_hifz_now['student_name'] != del_student])
                    df_rev_now = get_data(review_sheet)
                    save_data(review_sheet, df_rev_now[df_rev_now['student_name'] != del_student])
                    st.success(f"تم حذف الطالب ({del_student}) وسجلاته بنجاح!")
                    st.rerun()

    with st.sidebar.expander("📥 خيارات التصدير والتقارير"):
        export_format_choice = st.radio("صيغة التنزيل:", ["Excel (.xlsx)", "PDF (.html/print)"], horizontal=True)
        export_option = st.selectbox("الكشف أو التقرير:", ["تنزيل قاعدة البيانات الشاملة (Backup)", "كشف الحضور والغياب الشبكي", "كشف الحفظ الشبكي", "كشف المراجعة الشبكي"])

        if export_option == "تنزيل قاعدة البيانات الشاملة (Backup)":
            if st.button("تنزيل النسخة الاحتياطية الكاملة", use_container_width=True):
                df_st_all = get_data(students_sheet)
                df_at_all = get_data(attendance_sheet)
                df_hi_all = get_data(hifz_sheet)
                df_re_all = get_data(review_sheet)
                if "Excel" in export_format_choice:
                    output_backup = io.BytesIO()
                    with pd.ExcelWriter(output_backup, engine='openpyxl') as writer:
                        df_st_all.to_excel(writer, index=False, sheet_name='الطلاب')
                        df_at_all.to_excel(writer, index=False, sheet_name='السجل_اليومي_للحضور')
                        df_hi_all.to_excel(writer, index=False, sheet_name='سجل_الحفظ')
                        df_re_all.to_excel(writer, index=False, sheet_name='سجل_المراجعة')
                    st.download_button("📥 تنزيل النسخة (Excel)", output_backup.getvalue(), f"Quran_Backup_{date.today()}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

        elif export_option == "كشف الحضور والغياب الشبكي":
            df_att_raw = get_data(attendance_sheet)
            if not df_att_raw.empty:
                df_pivot = df_att_raw.pivot_table(index='date', columns='student_name', values='status', aggfunc='first').reset_index()
                st.dataframe(df_pivot, use_container_width=True, hide_index=True)
                out_p = io.BytesIO()
                df_pivot.to_excel(out_p, index=False)
                st.download_button("📥 تحميل الكشف كـ Excel", out_p.getvalue(), "كشف_الحضور.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

        elif export_option == "كشف الحفظ الشبكي":
            df_hifz_raw = get_data(hifz_sheet)
            if not df_hifz_raw.empty:
                df_pivot = df_hifz_raw.pivot_table(index='date', columns='student_name', values='rating', aggfunc='first').reset_index()
                st.dataframe(df_pivot, use_container_width=True, hide_index=True)
                out_p = io.BytesIO()
                df_pivot.to_excel(out_p, index=False)
                st.download_button("📥 تحميل الكشف كـ Excel", out_p.getvalue(), "كشف_الحفظ.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

        elif export_option == "كشف المراجعة الشبكي":
            df_rev_raw = get_data(review_sheet)
            if not df_rev_raw.empty:
                df_rev_raw['rev_full'] = df_rev_raw['amount'] + ' [' + df_rev_raw['rating'] + ']'
                df_pivot = df_rev_raw.pivot_table(index='date', columns='student_name', values='rev_full', aggfunc='first').reset_index()
                st.dataframe(df_pivot, use_container_width=True, hide_index=True)
                out_p = io.BytesIO()
                df_pivot.to_excel(out_p, index=False)
                st.download_button("📥 تحميل الكشف كـ Excel", out_p.getvalue(), "كشف_المراجعة.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.sidebar.divider()

st.markdown("""
    <div class="app-header">
        <span>📖</span>
        <h1>مركز تحفيظ باب السلام</h1>
    </div>
""", unsafe_allow_html=True)

df_students_main = get_data(students_sheet)
students_list = df_students_main['name'].tolist() if not df_students_main.empty else []

if not students_list:
    st.info("👈 لا يوجد طلاب مضافون بعد! قم بإضافة الطلاب من القائمة الجانبية (لوحة تحكم المدير).")
else:
    if st.session_state['role'] == 'admin':
        entry_date = st.date_input("📅 تحديد التاريخ (خاص بمدير النظام):", date.today())
        st.markdown("---")
        st.markdown("#### 🔒 إغلاق اليوم")
        confirm_close_day = st.checkbox("أوافق على إغلاق اليوم وترصيد السجلات الفارغة لـ (لم يسمع)")
        if st.button("🔒 إغلاق اليوم", type="primary", use_container_width=True):
            if confirm_close_day:
                df_att_chk = get_data(attendance_sheet)
                present_students = df_att_chk[(df_att_chk['date'] == str(entry_date)) & (df_att_chk['status'] == 'حضور')]['student_name'].tolist()
                
                df_hifz_chk = get_data(hifz_sheet)
                df_rev_chk = get_data(review_sheet)
                updated_count = 0
                
                for s_name in present_students:
                    if df_hifz_chk[(df_hifz_chk['date'] == str(entry_date)) & (df_hifz_chk['student_name'] == s_name)].empty:
                        new_h = pd.DataFrame([{"date": str(entry_date), "student_name": s_name, "surah": "-", "from_ayah": 0, "to_ayah": 0, "rating": "لم يسمع"}])
                        df_hifz_chk = pd.concat([df_hifz_chk, new_h], ignore_index=True)
                        updated_count += 1
                        
                    if df_rev_chk[(df_rev_chk['date'] == str(entry_date)) & (df_rev_chk['student_name'] == s_name)].empty:
                        new_r = pd.DataFrame([{"date": str(entry_date), "student_name": s_name, "amount": "لم يسمع", "rating": "لم يسمع"}])
                        df_rev_chk = pd.concat([df_rev_chk, new_r], ignore_index=True)
                        updated_count += 1
                
                save_data(hifz_sheet, df_hifz_chk)
                save_data(review_sheet, df_rev_chk)
                st.success(f"✅ تم إغلاق اليوم وترصيد الحالات الفارغة بـ (لم يسمع) لـ {updated_count} سجل!")
            else:
                st.error("⚠️ يرجى تحديد مربع التأكيد أولاً.")
    else:
        entry_date = date.today()
        st.caption(f"📅 تاريخ التسجيل اليوم: **{entry_date}**")

    st.divider()

    if st.session_state['role'] == 'admin':
        tab1, tab2, tab3, tab4 = st.tabs(["📝 الحضور والغياب الجماعي", "📖 الحفظ الجديد", "🔄 المراجعة", "🎯 متابعة تسلسل الأحزاب"])
    else:
        tab1, tab2, tab3 = st.tabs(["📝 الحضور والغياب الجماعي", "📖 الحفظ الجديد", "🔄 المراجعة"])

    with tab1:
        st.markdown("### 📋 كشف الحضور والغياب الجماعي")
        search_att = st.text_input("🔍 تصفية القائمة بكتابة بداية الاسم:", "")
        filtered_att_students = [s for s in students_list if s.lower().startswith(search_att.strip().lower())]
        
        attendance_results = {}
        status_options = ["حضور", "غياب", "غياب بعذر", "تأخير"]

        for idx, student in enumerate(filtered_att_students):
            col_name, col_status = st.columns([1.2, 2.8])
            with col_name:
                st.markdown(f"<div style='padding-top: 6px; font-weight: 600;'>{idx + 1}. {student}</div>", unsafe_allow_html=True)
            with col_status:
                selected_status = st.radio(f"حالة {student}:", options=status_options, index=0, key=f"att_{student}", horizontal=True, label_visibility="collapsed")
                attendance_results[student] = selected_status
            st.markdown("<hr style='margin: 4px 0px; border-color: #f1f5f9;'>", unsafe_allow_html=True)

        if st.button("💾 حفظ كشف الحضور لجميع الطلاب", type="primary", use_container_width=True):
            df_att_all = get_data(attendance_sheet)
            df_hi_all = get_data(hifz_sheet)
            df_re_all = get_data(review_sheet)
            
            for student_name, status in attendance_results.items():
                df_att_all = df_att_all[~((df_att_all['date'] == str(entry_date)) & (df_att_all['student_name'] == student_name))]
                new_a = pd.DataFrame([{"date": str(entry_date), "student_name": student_name, "status": status}])
                df_att_all = pd.concat([df_att_all, new_a], ignore_index=True)
                
                if status in ["غياب", "غياب بعذر"]:
                    df_hi_all = df_hi_all[~((df_hi_all['date'] == str(entry_date)) & (df_hi_all['student_name'] == student_name))]
                    new_h = pd.DataFrame([{"date": str(entry_date), "student_name": student_name, "surah": "-", "from_ayah": 0, "to_ayah": 0, "rating": "غائب"}])
                    df_hi_all = pd.concat([df_hi_all, new_h], ignore_index=True)
                    
                    df_re_all = df_re_all[~((df_re_all['date'] == str(entry_date)) & (df_re_all['student_name'] == student_name))]
                    new_r = pd.DataFrame([{"date": str(entry_date), "student_name": student_name, "amount": "غائب", "rating": "غائب"}])
                    df_re_all = pd.concat([df_re_all, new_r], ignore_index=True)
                    
            save_data(attendance_sheet, df_att_all)
            save_data(hifz_sheet, df_hi_all)
            save_data(review_sheet, df_re_all)
            st.success("✅ تم حفظ كشف الحضور بنجاح!")

    with tab2:
        st.markdown("### 📖 تسجيل الحفظ الجديد")
        selected_student_hifz = st.selectbox("🔍 اختر اسم الطالب:", students_list, index=None, placeholder="اختر طالباً...", key="hifz_select_student")
        if selected_student_hifz:
            df_att_chk = get_data(attendance_sheet)
            att_row = df_att_chk[(df_att_chk['date'] == str(entry_date)) & (df_att_chk['student_name'] == selected_student_hifz)]
            is_absent = not att_row.empty and att_row.iloc[0]['status'] in ["غياب", "غياب بعذر"]

            if is_absent:
                st.error(f"⚠️ تنبيه: الطالب (**{selected_student_hifz}**) مسجل غائب اليوم.")
            else:
                hifz_rating = st.radio("تقييم الحفظ اليوم:", ["جيد", "إعادة"], horizontal=True, key="hifz_rate")
                if st.button("حفظ التسميع 💾", type="primary", use_container_width=True):
                    df_hi_all = get_data(hifz_sheet)
                    df_hi_all = df_hi_all[~((df_hi_all['date'] == str(entry_date)) & (df_hi_all['student_name'] == selected_student_hifz))]
                    new_h = pd.DataFrame([{"date": str(entry_date), "student_name": selected_student_hifz, "surah": "-", "from_ayah": 0, "to_ayah": 0, "rating": hifz_rating}])
                    df_hi_all = pd.concat([df_hi_all, new_h], ignore_index=True)
                    save_data(hifz_sheet, df_hi_all)
                    st.success("✅ تم تحديث الحفظ بنجاح!")
                    st.rerun()

            st.divider()
            df_hifz_all = get_data(hifz_sheet)
            df_student_hifz = df_hifz_all[df_hifz_all['student_name'] == selected_student_hifz].sort_values(by='date', ascending=False).head(10)
            if not df_student_hifz.empty:
                html_table = "<table class='custom-table'><thead><tr><th>التاريخ</th><th>التقييم</th></tr></thead><tbody>"
                for _, row in df_student_hifz.iterrows():
                    badge = "badge-good" if row['rating'] == "جيد" else ("badge-retry" if row['rating'] == "إعادة" else "badge-none")
                    html_table += f"<tr><td>{row['date']}</td><td><span class='{badge}'>{row['rating']}</span></td></tr>"
                html_table += "</tbody></table>"
                st.markdown(html_table, unsafe_allow_html=True)

    with tab3:
        st.markdown("### 🔄 تسجيل المراجعة")
        selected_student_rev = st.selectbox("🔍 اختر اسم الطالب:", students_list, index=None, placeholder="اختر طالباً...", key="rev_select_student")
        if selected_student_rev:
            df_att_chk = get_data(attendance_sheet)
            att_row = df_att_chk[(df_att_chk['date'] == str(entry_date)) & (df_att_chk['student_name'] == selected_student_rev)]
            is_absent = not att_row.empty and att_row.iloc[0]['status'] in ["غياب", "غياب بعذر"]

            if is_absent:
                st.error(f"⚠️ تنبيه: الطالب (**{selected_student_rev}**) مسجل غائب اليوم.")
            else:
                if "selected_hizb" not in st.session_state:
                    st.session_state["selected_hizb"] = None
                if "show_hizb_grid" not in st.session_state:
                    st.session_state["show_hizb_grid"] = False

                current_hizb_text = st.session_state["selected_hizb"] if st.session_state["selected_hizb"] else "اختر الحزب 🔻"
                if st.button(f"🟢 {current_hizb_text}", use_container_width=True):
                    st.session_state["show_hizb_grid"] = not st.session_state["show_hizb_grid"]
                    st.rerun()

                if st.session_state["show_hizb_grid"]:
                    for idx, hizb in enumerate(AHZAB_LIST_DESC):
                        if st.button(hizb, key=f"hizb_btn_{idx}", use_container_width=True):
                            st.session_state["selected_hizb"] = hizb
                            st.session_state["show_hizb_grid"] = False
                            st.rerun()

                review_hizb = st.session_state["selected_hizb"]
                if review_hizb:
                    review_rating = st.radio("تقييم المراجعة:", ["جيد", "إعادة"], horizontal=True, key="rev_rate")
                    if st.button("حفظ المراجعة 💾", type="primary", use_container_width=True):
                        df_rev_all = get_data(review_sheet)
                        df_rev_all = df_rev_all[~((df_rev_all['date'] == str(entry_date)) & (df_rev_all['student_name'] == selected_student_rev))]
                        new_r = pd.DataFrame([{"date": str(entry_date), "student_name": selected_student_rev, "amount": review_hizb, "rating": review_rating}])
                        df_rev_all = pd.concat([df_rev_all, new_r], ignore_index=True)
                        save_data(review_sheet, df_rev_all)
                        st.success("✅ تم حفظ المراجعة!")
                        st.session_state["selected_hizb"] = None
                        st.rerun()

    if st.session_state['role'] == 'admin':
        with tab4:
            st.markdown("### 🎯 متابعة تسلسل الأحزاب")
            search_target_hizb = st.selectbox("🔎 اختر الحزب المطلوب لمعرفة الطلاب:", AHZAB_LIST_DESC, index=0)
            if search_target_hizb:
                df_rev_all = get_data(review_sheet)
                if not df_rev_all.empty:
                    st.dataframe(df_rev_all[df_rev_all['amount'] == search_target_hizb], use_container_width=True, hide_index=True)
                else:
                    st.info("لا توجد سجلات مراجعة بعد.")
