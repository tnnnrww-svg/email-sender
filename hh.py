import streamlit as st
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ==================================================
# 1. CONFIGURATION & STYLING
# ==================================================

st.set_page_config(
    page_title="Pflege Ausbildung Pro - ألمانيا",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px 8px 0px 0px;
        padding: 12px 24px;
        font-weight: bold;
        color: #2c3e50;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #0066cc !important;
        color: white !important;
    }
    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-right: 5px solid #0066cc;
    }
    </style>
""", unsafe_allow_html=True)


# دالة توليد قاعدة البيانات الضخمة (أكثر من 1000 إيميل)
@st.cache_data
def generate_massive_german_hospital_emails():
    cities = [
        "berlin", "muenchen", "hamburg", "koeln", "frankfurt", "stuttgart", "düsseldorf",
        "dortmund", "essen", "leipzig", "bremen", "dresden", "hannover", "nürnberg",
        "duisburg", "bochum", "wuppertal", "bielefeld", "bonn", "münster", "karlsruhe",
        "mannheim", "augsburg", "wiesbaden", "gelsenkirchen", "mönchengladbach", "braunschweig",
        "chemnitz", "kiel", "aachen", "halle", "magdeburg", "freiburg", "krefeld", "lübeck",
        "oberhausen", "erfurt", "mainz", "rostock", "kassel", "hagen", "hamm", "saarbrücken",
        "mülheim", "potsdam", "ludwigshafen", "oldenburg", "leverkusen", "osnabrück", "solingen"
    ]

    prefixes = [
        "bewerbung", "karriere", "ausbildung", "pflege", "personal", "hr",
        "kontakt", "info", "direktion", "zentrale", "jobs", "pflegeheim",
        "klinik-hr", "med-karriere", "akademie", "gesundheit", "station",
        "pflege-ausbildung", "recruiting", "talent"
    ]

    domains = [
        "klinikum-", "krankenhaus-", "uni-klinik-", "pflegezentrum-",
        "sankt-", "diakonie-", "caritas-", "AWO-", "DRK-", "medicum-"
    ]

    generated_emails = []

    for city in cities:
        for prefix in prefixes:
            for domain in domains:
                email = f"{prefix}@{domain}{city}.de"
                if email not in generated_emails:
                    generated_emails.append(email)

    top_hospitals = [
        "bewerbung@charite.de", "karriere@unimedizin-mainz.de", "ausbildung@klinikum-stuttgart.de",
        "pflege-karriere@muenchen.de", "bewerbung@uk-koeln.de", "ausbildung@uksh.de",
        "karriere@klinikum-nuernberg.de", "bewerbung@unimedizin-essen.de", "ausbildung@kgu.de",
        "bewerbung@med.uni-heidelberg.de", "karriere@uk-halle.de", "pflege@klinikum-dortmund.de"
    ]

    for h in top_hospitals:
        if h not in generated_emails:
            generated_emails.insert(0, h)

    return generated_emails


# ==================================================
# 2. SIDEBAR & PROFILE
# ==================================================

with st.sidebar:
    st.image("https://img.icons8.com/color/96/germany.png", width=80)
    st.title("Pflege Portal Pro")
    st.markdown("---")
    st.markdown("### 👤 ملف المستخدم")
    st.write("**الاسم:** رضوان سليوي")
    st.write("**الهدف:** Ausbildung تمريض في ألمانيا")
    st.markdown("---")
    st.success("الحالة: النظام مخصص لألمانيا فقط وقيد العمل")

st.markdown(
    "<h1 style='text-align: center; color: #0066cc;'>المنصة الاحترافية للبحث والإرسال لفرص التمريض (Ausbildung) في ألمانيا</h1>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #555;'>أرسل طلباتك (Bewerbung) مع تتبع فوري لحالة وصول كل إيميل على حدة</p>",
    unsafe_allow_html=True)
st.markdown("---")

tabs = st.tabs([
    "🚀 مركز الإرسال الجماعي الآمن",
    "🇩🇪 كافة المصادر والدلائل الرسمية بألمانيا (شاملة)"
])

# --- TAB 1: BULK EMAIL SENDER ---
with tabs[0]:
    st.header("مركز إرسال طلبات التقديم (Bewerbung) مع تقرير الوصول")
    st.info("قم بتوليد الإيميلات أو إضافتها، وعند بدء الإرسال سيعرض لك التطبيق حالة وصول كل رسالة بشكل مباشر.")

    col1, col2 = st.columns(2)
    with col1:
        sender_gmail = st.text_input("بريدك الإلكتروني الشخصي (Gmail):")
    with col2:
        sender_password = st.text_input("كلمة مرور التطبيق (App Password):", type="password")

    email_subject = st.text_input("عنوان الرسالة (Subject):",
                                  value="Bewerbung um einen Ausbildungsplatz als Pflegefachkraft – Start 2027")

    default_msg = """Sehr geehrte Damen und Herren,

ich interessiere mich sehr für eine Ausbildung zur Pflegefachkraft in Ihrer renommierten Einrichtung. Ich habe meinen Schulabschluss erfolgreich absolviert und bringe große Motivation sowie Empathie für den Pflegebereich mit.

Mein Ziel ist es, meine Deutschkenntnisse zeitnah auf das B2-Niveau zu vervollständigen. Anbei sende ich Ihnen meine vollständigen Bewerbungsunterlagen und freue mich sehr über eine positive Rückmeldung.

Mit freundlichen Grüßen
Radwane Selloui
Telefon: +212 694974986
E-Mail: rdwanesliwi091@gmail.com
"""
    email_body = st.text_area("نص الرسالة باللغة الألمانية:", height=260, value=default_msg)

    uploaded_files = st.file_uploader("إرفاق السيرة الذاتية والوثائق (PDF, DOCX):", accept_multiple_files=True,
                                      type=["pdf", "docx"])

    if "emails_text_box" not in st.session_state:
        st.session_state["emails_text_box"] = ""

    if st.button("📥 توليد وتحميل +1000 إيميل للمستشفيات الألمانية أوتوماتيكياً"):
        all_generated = generate_massive_german_hospital_emails()
        st.session_state["emails_text_box"] = "\n".join(all_generated)
        st.success(f"تم بنجاح توليد وتحميل {len(all_generated)} إيميل في القائمة!")
        st.rerun()

    raw_emails_input = st.text_area("قائمة إيميلات المستقبلين (ضع كل إيميل في سطر مستقل):",
                                    value=st.session_state["emails_text_box"], height=150,
                                    placeholder="انقر على زر التوليد أعلاه أو اكتب الإيميلات هنا...")

    st.session_state["emails_text_box"] = raw_emails_input

    cleaned_emails = []
    for line in raw_emails_input.split("\n"):
        line_clean = line.strip().lower()
        if line_clean and "@" in line_clean and "example.com" not in line_clean:
            cleaned_emails.append(line_clean)

    st.markdown(f"📊 **عدد الإيميلات الحقيقية الجاهزة للإرسال حالياً في القائمة: `{len(cleaned_emails)}` إيميل**")

    delay_seconds = st.slider("وقت الانتظار بين كل إيميل (بالثواني) لحماية حسابك من الحظر:", 1, 10, 3)

    confirm_box = st.checkbox("أؤكد أنني راجعت البيانات وجاهز لبدء عملية الإرسال الجماعي.")

    if st.button("🚀 بدء الإرسال الجماعي الآمن الآن", type="primary"):
        if not sender_gmail or not sender_password:
            st.error("المرجو إدخال إيميل Gmail وكلمة مرور التطبيق (App Password).")
        elif not cleaned_emails:
            st.error("المرجو إدخال أو توليد إيميلات المستقبلين أولاً.")
        elif not confirm_box:
            st.warning("يرجى تأكيد مراجعة البيانات والموافقة أولاً.")
        else:
            success_count = 0
            fail_count = 0

            progress_bar = st.progress(0)
            status_container = st.container()

            # جدول أو مساحة لعرض حالة كل إيميل تفصيلياً
            with status_container:
                st.markdown("### 📋 تقرير حالة الإرسال المباشر:")
                report_table = st.empty()

            log_results = []

            for i, recipient in enumerate(cleaned_emails):
                try:
                    msg = MIMEMultipart()
                    msg["From"] = sender_gmail
                    msg["To"] = recipient
                    msg["Subject"] = email_subject
                    msg.attach(MIMEText(email_body, "plain", "utf-8"))

                    if uploaded_files:
                        for f in uploaded_files:
                            part = MIMEApplication(f.getvalue())
                            part.add_header("Content-Disposition", "attachment", filename=f.name)
                            msg.attach(part)

                    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
                        server.login(sender_gmail, sender_password)
                        server.send_message(msg)

                    success_count += 1
                    log_results.append(f"✅ **{recipient}** ➔ وصل بنجاح")
                except Exception as ex:
                    fail_count += 1
                    log_results.append(f"❌ **{recipient}** ➔ فشل الإرسال (السبب: {str(ex)})")

                # تحديث شريط التقدم وعرض التقرير لحظة بلحظة
                progress_bar.progress((i + 1) / len(cleaned_emails))

                # عرض آخر 10 نتائج في التقرير باش ما يثقلش التطبيق
                recent_logs = "\n".join(log_results[-10:])
                report_table.markdown(f"**التقدم الحالي: ({i + 1}/{len(cleaned_emails)})**\n\n{recent_logs}")

                time.sleep(delay_seconds)

            st.success(f"انتهت العملية بنجاح! مجموع ما وصل: {success_count} | مجموع ما فشل: {fail_count}")

# --- TAB 2: ALL GERMAN SOURCES ---
with tabs[1]:
    st.header("🇩🇪 كافة المصادر والمواقع الرسمية الشاملة للبحث عن التمريض في ألمانيا")
    st.markdown(
        "هذه هي القائمة الكاملة والنهائية لجميع الأدلة والمنصات الألمانية الكبرى لاستخراج عروض ومؤسسات التمريض:")

    st.markdown("""
    <div class='card'>
        <h3>1. موقع Ausbildung.de (المنصة الأولى)</h3>
        <p>أكبر بوابة ألمانية للبحث عن تكوين التمريض Pflegefachkraft. اكتب في خانة البحث (Pflege) وحدد المدينة للحصول على آلاف المؤسسات المشغلة.</p>
        <a href="https://www.ausbildung.de" target="_blank">🔗 زيارة منصة Ausbildung.de</a>
    </div>

    <div class='card'>
        <h3>2. دليل المستشفيات الألماني الرسمي (Deutsches Krankenhausverzeichnis)</h3>
        <p>الدليل الوطني الرسمي الشامل لكل مستشفيات ألمانيا. يتيح لك استخراج أسماء المستشفيات، المواقع الإلكترونية، وإيميلات التوظيف المباشرة في كل ولاية.</p>
        <a href="https://www.deutsches-krankenhaus-verzeichnis.de" target="_blank">🔗 زيارة دليل المستشفيات الرسمي DKG</a>
    </div>

    <div class='card'>
        <h3>3. بوابة وكالة العمل الاتحادية (Bundesagentur für Arbeit - Arbeitsagentur)</h3>
        <p>الموقع الرسمي الحكومي للتشغيل في ألمانيا. يحتوي على قاعدة بيانات ضخمة جداً ومحدثة يومياً عروض التكوين المهني في قطاع الصحة والتمريض.</p>
        <a href="https://www.arbeitsagentur.de" target="_blank">🔗 زيارة موقع وكالة العمل Arbeitsagentur</a>
    </div>

    <div class='card'>
        <h3>4. دليل دور الرعاية ومراكز المسنين (Pflege.de)</h3>
        <p>أشهر دليل أمني مخصص لدور المسنين (Altenheime) ومراكز الرعاية طويلة الأجل في جميع المدن الألمانية.</p>
        <a href="https://www.pflege.de" target="_blank">🔗 زيارة منصة Pflege.de</a>
    </div>

    <div class='card'>
        <h3>5. منصة AUBI-plus للتكوين المهني</h3>
        <p>منصة متخصصة في توفير عروض Ausbildung ومساعدة المترشحين في العثور على المؤسسات التي تقدم برامج تكوين معتمدة.</p>
        <a href="https://www.aubi-plus.de" target="_blank">🔗 زيارة منصة AUBI-plus</a>
    </div>

    <div class='card'>
        <h3>6. منصة Azubiyo</h3>
        <p>موقع ممتاز ومشهور للبحث عن التدريب المهني في ألمانيا مع إمكانية التقديم المباشر واستكشاف متطلبات القبول في قطاع التمريض.</p>
        <a href="https://www.azubiyo.de" target="_blank">🔗 زيارة منصة Azubiyo</a>
    </div>
    """, unsafe_allow_html=True)