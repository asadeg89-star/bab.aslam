from datetime import date
import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مركز تحفيظ باب السلام", page_icon="📖", layout="centered"
)

# معرف ملف جوجل شيت الخاص بك
SHEET_ID = "1BB4CAm4M1tQN74s5whI8M0-GiT5tjS0i8Aw3n31B1pY"


# دالة عامة لجلب أي ورقة (Tab) من جوجل شيت عبر الـ GID أو الاسم
@st.cache_data(ttl=60)
def load_sheet_data(sheet_name_or_gid):
  try:
    # يمكن استخدام الـ GID لكل ورقة عمل لضمان قراءتها بدقة
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name_or_gid}"
    df = pd.read_csv(url)
    return df
  except Exception as e:
    return pd.DataFrame()


AHZAB_LIST = [
    "الفاتحة",
    "وإذا لقوا",
    "سيقول",
    "واذكروا الله",
    "تلك الرسل",
    "قل أؤنبئكم",
    "لن تنالوا",
    "يستبشرون",
    "المحصنات",
    "الله لا إله إلا هو",
    "لا يحب",
    "قال رجلان",
    "لتجدن",
    "إنما يستجيب",
    "ولو أننا نزلنا",
    "الأعراف",
    "قال الملأ",
    "وإذ نتقنا",
    "واعلموا",
    "يأيها الذين آمنوا",
    "إنما السبيل",
    "الذين أحسنوا",
    "وما من دابة",
    "وإلى مدين",
    "وما أبرئ",
    "أمن يعلم",
    "الحجر",
    "وقال الله",
    "سبحان الذي",
    "أولم يَرَوْا",
    "قال ألم أقل لك",
    "طه",
    "الأنبياء",
    "الحج",
    "المؤمنون",
    "يأيها الذين آمنوا",
    "وقال الذين لا يرجون",
    "قالوا أأنؤمن",
    "قل الحمد لله",
    "ولقد وصلنا",
    "ولا تجادلوا",
    "ومن يسلم",
    "إن المسلمين",
    "قل من يرزقكم",
    "وما أنزلنا",
    "فنبذناه",
    "فمن أظلم",
    "وبقوم مالي",
    "إليه يرد",
    "قل أولو جئتكم",
    "الأحقاف",
    "لقد رضي",
    "قال فما خطبكم",
    "الرحمن",
    "المجادلة",
    "الجمعة",
    "الملك",
    "الجن",
    "النبأ",
    "الأعلى",
]

AHZAB_LIST_DESC = list(reversed(AHZAB_LIST))

# تحميل البيانات من صفحات جوجل شيت (يجب أن تتأكد من وجود صفحات بهذا الاسم في ملف الشيت)
df_users = load_sheet_data("users")
df_students = load_sheet_data("students")
df_attendance = load_sheet_data("attendance_records")
df_hifz = load_sheet_data("hifz_records")
df_review = load_sheet_data("review_records")

# التأكد من وجود حساب المسؤول الافتراضي إذا كانت الصفحة فارغة
if df_users.empty or "username" not in df_users.columns:
  df_users = pd.DataFrame(
      [{"username": "admin", "password": "admin123", "role": "admin"}]
  )

st.markdown(
    """
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
    </style>
    """,
    unsafe_allow_html=True,
)

if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False
  st.session_state["username"] = ""
  st.session_state["role"] = ""

if "user" in st.query_params:
  logged_username = st.query_params["user"]
  matched_user = df_users[df_users["username"] == logged_username]
  if not matched_user.empty:
    st.session_state["authenticated"] = True
    st.session_state["username"] = logged_username
    st.session_state["role"] = matched_user.iloc[0]["role"]

if not st.session_state["authenticated"]:
  st.markdown(
      "<h2 style='text-align: center; color: #0f766e;'>🔐 تسجيل الدخول لبرنامج"
      " مركز تحفيظ باب السلام (السحابي)</h2>",
      unsafe_allow_html=True,
  )
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    with st.form("login_form"):
      username_input = st.text_input("اسم المستخدم:")
      password_input = st.text_input("كلمة المرور:", type="password")
      submit_login = st.form_submit_button(
          "تسجيل الدخول", type="primary", use_container_width=True
      )
      if submit_login:
        matched = df_users[
            (df_users["username"] == username_input.strip())
            & (df_users["password"] == password_input.strip())
        ]
        if not matched.empty:
          st.session_state["authenticated"] = True
          st.session_state["username"] = username_input.strip()
          st.session_state["role"] = matched.iloc[0]["role"]
          st.query_params["user"] = username_input.strip()
          st.success("تم تسجيل الدخول بنجاح!")
          st.rerun()
        else:
          st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
  st.stop()

st.sidebar.markdown(f"👤 مرحباً بك: **{st.session_state['username']}**")
st.sidebar.caption(
    f"الرتبة: {'مدير النظام' if st.session_state['role'] == 'admin' else 'معلم'}"
)

if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
  st.session_state["authenticated"] = False
  st.session_state["username"] = ""
  st.session_state["role"] = ""
  st.query_params.clear()
  st.rerun()

st.sidebar.divider()

st.markdown(
    """
    <div class="app-header">
        <span>📖</span>
        <h1>مركز تحفيظ باب السلام (مربوط بجوجل شيت)</h1>
    </div>
""",
    unsafe_allow_html=True,
)

students_list = (
    df_students["name"].dropna().tolist() if not df_students.empty else []
)

if not students_list:
  st.info(
      "👈 يجب إنشاء ورقة عمل (Tabs) في ملف جوجل شيت باسم `students` وتتضمن عموداً"
      " باسم `name` يحتوي على أسماء الطلاب."
  )
else:
  entry_date = st.date_input(
      "📅 تحديد التاريخ:",
      date.today(),
      disabled=(st.session_state["role"] != "admin"),
  )
  st.divider()

  tab1, tab2, tab3 = st.tabs(
      ["📝 الحضور والغياب", "📖 الحفظ الجديد", "🔄 المراجعة"]
  )

  with tab1:
    st.markdown("### 📋 كشف الحضور والغياب")
    st.dataframe(
        df_attendance
        if not df_attendance.empty
        else pd.DataFrame(columns=["date", "student_name", "status"]),
        use_container_width=True,
        hide_index=True,
    )

  with tab2:
    st.markdown("### 📖 سجل الحفظ")
    st.dataframe(
        df_hifz
        if not df_hifz.empty
        else pd.DataFrame(
            columns=["date", "student_name", "surah", "from_ayah", "rating"]
        ),
        use_container_width=True,
        hide_index=True,
    )

  with tab3:
    st.markdown("### 🔄 سجل المراجعة")
    st.dataframe(
        df_review
        if not df_review.empty
        else pd.DataFrame(
            columns=["date", "student_name", "amount", "rating"]
        ),
        use_container_width=True,
        hide_index=True,
    )
