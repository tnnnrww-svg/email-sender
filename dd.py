import requests
import json
import os
import smtplib
import imaplib
import email
from email.header import decode_header
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st

# مكتبة ReportLab لتوليد ملفات الـ PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

HISTORY_FILE = "sent_companies.json"


def load_sent_companies():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_sent_company(name, email_addr, city, status="تم الإرسال 📤"):
    sent_list = load_sent_companies()
    updated = False
    for comp in sent_list:
        if comp['email'].strip().lower() == email_addr.strip().lower():
            comp['status'] = status
            comp['city'] = city
            updated = True
            break
    if not updated:
        sent_list.append({"name": name, "email": email_addr, "city": city, "status": status})

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sent_list, f, ensure_ascii=False, indent=4)


def generate_cover_letter_pdf(filename, text_content, company_name, city):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, f"Bewerbung - Ausbildung in der Pflege")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Institution: {company_name} | Region: {city}")
    c.line(50, height - 80, width - 50, height - 80)

    c.setFont("Helvetica", 10)
    text_object = c.beginText(50, height - 100)
    text_object.setTextOrigin(50, height - 100)
    text_object.setLeading(14)

    for line in text_content.split('\n'):
        if len(line) > 90:
            chunks = [line[i:i + 90] for i in range(0, len(line), 90)]
            for chunk in chunks:
                text_object.textLine(chunk)
        else:
            text_object.textLine(line)

    c.drawText(text_object)
    c.save()


API_KEY = "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"
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "https://localhost",
    "X-Title": "NursingSmartBot",
    "Content-Type": "application/json"
}

st.title("🇩🇪 النظام الاحترافي المتقدم لطلبات التمريض في ألمانيا (بالفحص التلقائي)")
st.write("التحكم الكامل، تخصيص الرسائل، تتبع الحالة، والفحص التلقائي للردود الواردة عبر Gmail!")

# الشريط الجانبي
st.sidebar.header("إعدادات البريد والبحث")
sender_email = st.sidebar.text_input("إيميلك الشخصي:", "rdwanesliwi091@gmail.com")
sender_password = st.sidebar.text_input("كلمة سر التطبيق (App Password):", type="password")

target_city = st.sidebar.text_input("أدخل اسم المدينة أو المنطقة في ألمانيا:", "Berlin")
batch_size = st.sidebar.slider("اختر عدد المؤسسات في كل دفعة:", min_value=10, max_value=50, value=50, step=10)

uploaded_cv = st.file_uploader("1. ارفع سيرتك الذاتية (CV بصيغة PDF):", type=["pdf"])

already_sent = load_sent_companies()
sent_emails = [comp['email'] for comp in already_sent]

st.markdown("---")

# زر فحص البريد الوارد أوتوماتيكياً وتحديث الحالات
if st.sidebar.button("📥 فحص الردود الواردة وتحديث الحالات"):
    if not sender_password:
        st.error("المرجو إدخال كلمة سر التطبيق (App Password) في الشريط الجانبي أولاً!")
    else:
        with st.spinner("جاري الاتصال بصندوق الوارد وفحص الإيميلات الواردة..."):
            try:
                # الاتصال بخدمة IMAP الخاصة بـ Gmail
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(sender_email, sender_password)
                mail.select("inbox")

                # البحث عن أحدث الرسائل
                status, messages = mail.search(None, "ALL")
                if status == "OK":
                    email_ids = messages[0].split()
                    # أخذ آخر 30 رسالة لتسريع العملية
                    recent_ids = email_ids[-30:]

                    matched_count = 0
                    all_history = load_sent_companies()

                    for e_id in recent_ids:
                        res, msg_data = mail.fetch(e_id, "(RFC822)")
                        if res == "OK":
                            for response_part in msg_data:
                                if isinstance(response_part, tuple):
                                    msg = email.message_from_bytes(response_part[1])
                                    # استخراج المرسل
                                    from_header = msg.get("From", "")
                                    subject_header = msg.get("Subject", "")

                                    # فك تشفير العنوان لو كان بصيغة مرمزة
                                    subject_decoded = ""
                                    for part, encoding in decode_header(subject_header):
                                        if isinstance(part, bytes):
                                            subject_decoded += part.decode(encoding or "utf-8", errors="ignore")
                                        else:
                                            subject_decoded += str(part)

                                    # البحث عما إذا كان المرسل موجود في قائمة الشركات التي أرسلنا لها
                                    for comp in all_history:
                                        comp_email = comp.get('email', '').strip().lower()
                                        if comp_email in from_header.lower():
                                            # تحليل محتوى الرد لتحديد الحالة بناء على الكلمات المفتاحية الألمانية
                                            body_text = ""
                                            if msg.is_multipart():
                                                for part in msg.walk():
                                                    if part.get_content_type() == "text/plain":
                                                        try:
                                                            body_text += part.get_payload(decode=True).decode("utf-8",
                                                                                                              errors="ignore")
                                                        except:
                                                            pass
                                            else:
                                                try:
                                                    body_text += msg.get_payload(decode=True).decode("utf-8",
                                                                                                     errors="ignore")
                                                except:
                                                    pass

                                            body_lower = (subject_decoded + " " + body_text).lower()

                                            new_status = "رد مستلم 📬"
                                            if any(word in body_lower for word in
                                                   ["absage", "leider", "kنnnen wir", "nicht berücksichtigen"]):
                                                new_status = "مرفوض ❌"
                                            elif any(word in body_lower for word in
                                                     ["einladung", "gesprنch", "vorstellungsgespräch", "termin",
                                                      "interview", "freuen uns"]):
                                                new_status = "مقابلة مقترحة 📅"

                                            if comp.get('status') != new_status:
                                                save_sent_company(comp.get('name'), comp.get('email'), comp.get('city'),
                                                                  status=new_status)
                                                matched_count += 1

                mail.logout()
                st.success(f"✅ تم الفحص بنجاح! تم تحديث حالة {matched_count} شركة بناءً على ردودهم الجديدة.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء الاتصال بالبريد: {e}")

# زر البحث لجلب الشركات بالعدد المختار
if st.button(f"🔍 ابحث واجلب {batch_size} مؤسسة جديدة"):
    if not target_city:
        st.error("المرجو إدخال اسم المدينة أولاً!")
    else:
        st.info(f"🤖 جاري جلب قائمة دقيقة تضم **{batch_size} مؤسسة تمريض** في مدينة أو منطقة **{target_city}**...")

        scouting_prompt = f"""
        Act as an expert German healthcare job scout. Generate a JSON list of exactly {batch_size} real or representative hospitals, nursing care facilities, or clinics in '{target_city}' offering 'Ausbildung in der Pflege'.
        For each institution, provide:
        1. "name": Institution Name
        2. "email": Official Application Email (e.g., bewerbung@...)

        Format the output strictly as a JSON list of objects with keys: "name" and "email". Do not include markdown code blocks, just pure JSON. Make sure there are {batch_size} items.
        """

        scout_payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": scouting_prompt}],
            "max_tokens": 4000
        }

        scout_response = requests.post(url, headers=headers, data=json.dumps(scout_payload))

        if scout_response.status_code == 200:
            ai_content = scout_response.json()['choices'][0]['message']['content']
            try:
                if "```json" in ai_content:
                    ai_content = ai_content.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_content:
                    ai_content = ai_content.split("```")[1].split("```")[0].strip()

                discovered_institutions = json.loads(ai_content)
                st.session_state['discovered'] = discovered_institutions
                st.session_state['current_city'] = target_city
                st.success(f"🎉 تم جلب {len(discovered_institutions)} مؤسسة بنجاح! راجع الأقسام أدناه.")
            except Exception as e:
                st.error(f"حدث خطأ في تنظيم بيانات الشركات: {e}")
        else:
            st.error("فشل الاتصال بالذكاء الاصطناعي لجلب الشركات.")

if 'discovered' in st.session_state and st.session_state['discovered']:
    st.markdown("---")

    new_companies = []
    old_companies = []

    for inst in st.session_state['discovered']:
        if inst.get("email") in sent_emails:
            old_companies.append(inst)
        else:
            new_companies.append(inst)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="الشركات الجديدة المتاحة للإرسال", value=len(new_companies))
    with col2:
        st.metric(label="الشركات الموجودة في الذاكرة (أرسلت لها من قبل)", value=len(old_companies))

    st.markdown("---")

    tab1, tab2 = st.tabs(["🆕 الشركات الجديدة (للقرار والإرسال)", "📂 الأرشيف وتتبع الحالة التلقائي"])

    with tab1:
        if len(new_companies) == 0:
            st.info("لا توجد شركات جديدة في هذه القائمة، كلها مسجلة لديك مسبقاً!")
        else:
            st.subheader(f"قائمة الشركات الجديدة ({len(new_companies)} شركة):")

            with st.form("new_companies_form"):
                selected_new_indices = []

                for i, inst in enumerate(new_companies):
                    comp_name = inst.get("name")
                    comp_email = inst.get("email")

                    st.markdown(f"**{i + 1}. 🏥 {comp_name}** (`{comp_email}`)")
                    choose = st.checkbox(f"تحديد للإرسال إلى {comp_name}", value=True, key=f"new_check_{i}")
                    if choose:
                        selected_new_indices.append(inst)
                    st.markdown("---")

                submit_button = st.form_submit_button("🚀 إرسال الطلبات للشركات الجديدة المحددة فقط")

                if submit_button:
                    if not sender_password:
                        st.error("المرجو إدخال كلمة سر التطبيق (App Password) في الشريط الجانبي أولاً!")
                    elif uploaded_cv is None:
                        st.error("المرجو رفع ملف الـ CV بصيغة PDF أولاً!")
                    elif not selected_new_indices:
                        st.warning("لم تقم بتحديد أي شركة للإرسال!")
                    else:
                        st.info(
                            f"جاري معالجة وتوليد رسائل الـ PDF وإرسالها إلى {len(selected_new_indices)} مؤسسة مختارة...")

                        for inst in selected_new_indices:
                            comp_name = inst.get("name")
                            comp_email = inst.get("email")
                            city = st.session_state.get('current_city', target_city)

                            st.write(f"⏳ معالجة وتوليد PDF وإرسال إلى: {comp_name}...")

                            letter_prompt = f"""
                            Write a professional, formal, and highly motivated Cover Letter in German for an 'Ausbildung in der Pflege' at {comp_name} in {city}.
                            The applicant (Radwan) is dedicated, has a strong background including volunteering (like Red Cross / first aid), and is eager to start his nursing career.
                            Make it persuasive, polite, and structured properly according to German standards.
                            """

                            letter_payload = {
                                "model": "deepseek/deepseek-chat",
                                "messages": [{"role": "user", "content": letter_prompt}]
                            }

                            letter_res = requests.post(url, headers=headers, data=json.dumps(letter_payload))

                            if letter_res.status_code == 200:
                                cover_text = letter_res.json()['choices'][0]['message']['content']
                                pdf_filename = f"Anschreiben_{comp_name.replace(' ', '_').replace('/', '_')}.pdf"
                                generate_cover_letter_pdf(pdf_filename, cover_text, comp_name, city)

                                try:
                                    msg = MIMEMultipart()
                                    msg['From'] = sender_email
                                    msg['To'] = comp_email
                                    msg['Bcc'] = sender_email
                                    msg['Subject'] = f"Bewerbung für die Ausbildung als Pflegefachkraft - Radwan Sliwi"

                                    email_body = f"Sehr geehrte Damen und Herren,\n\nim Anhang übersende ich Ihnen meine Bewerbungsunterlagen (Anschreiben und Lebenslauf) für die Ausbildung als Pflegefachkraft bei {comp_name}.\n\nMit freundlichen Grüßen,\nRadwan Sliwi"
                                    msg.attach(MIMEText(email_body, 'plain', 'utf-8'))

                                    with open(pdf_filename, "rb") as f_pdf:
                                        part_pdf = MIMEBase("application", "octet-stream")
                                        part_pdf.set_payload(f_pdf.read())
                                    encoders.encode_base64(part_pdf)
                                    part_pdf.add_header("Content-Disposition",
                                                        f"filename=Anschreiben_{comp_name.replace(' ', '_').replace('/', '_')}.pdf")
                                    msg.attach(part_pdf)

                                    part_cv = MIMEBase("application", "octet-stream")
                                    part_cv.set_payload(uploaded_cv.getvalue())
                                    encoders.encode_base64(part_cv)
                                    part_cv.add_header("Content-Disposition", f"filename=CV_Radwan_Sliwi.pdf")
                                    msg.attach(part_cv)

                                    server = smtplib.SMTP('smtp.gmail.com', 587)
                                    server.starttls()
                                    server.login(sender_email, sender_password)
                                    recipients = [comp_email, sender_email]
                                    server.sendmail(sender_email, recipients, msg.as_string())
                                    server.quit()

                                    if os.path.exists(pdf_filename):
                                        os.path.exists(pdf_filename) and os.remove(pdf_filename)

                                    save_sent_company(comp_name, comp_email, city, status="تم الإرسال 📤")
                                    st.success(f"تم إرسال الطلب بنجاح إلى: {comp_name} ✅")
                                    time.sleep(1.5)
                                except Exception as e:
                                    st.error(f"خطأ في إرسال الإيميل إلى {comp_name}: {e}")
                            else:
                                st.error(f"خطأ في توليد رسالة التحفيز لـ {comp_name}.")

                        st.success("🎉 تمت عملية الإرسال للمؤسسات المحددة بنجاح تام!")

    with tab2:
        st.subheader("📂 الأرشيف الشامل وحالات الطلبات (التحديث التلقائي واليدوي)")
        all_sent_history = load_sent_companies()

        if len(all_sent_history) > 0:
            for s_comp in all_sent_history:
                col_a, col_b, col_c = st.columns([3, 2, 2])
                with col_a:
                    st.write(f"🏢 **{s_comp.get('name')}** (`{s_comp.get('email')}`)")
                with col_b:
                    current_stat = s_comp.get('status', 'تم الإرسال 📤')
                    st.write(f"📍 المنطقة: {s_comp.get('city', 'ألمانيا')} | الحالة: **{current_stat}**")
                with col_c:
                    # إمكانية التعديل اليدوي كاحتياط لو أردت
                    new_status = st.selectbox(
                        "تغيير الحالة:",
                        ["تم الإرسال 📤", "رد مستلم 📬", "مقابلة مقترحة 📅", "مرفوض ❌"],
                        index=["تم الإرسال 📤", "رد مستلم 📬", "مقابلة مقترحة 📅", "مرفوض ❌"].index(
                            current_stat) if current_stat in ["تم الإرسال 📤", "رد مستلم 📬", "مقابلة مقترحة 📅",
                                                              "مرفوض ❌"] else 0,
                        key=f"status_{s_comp.get('email')}"
                    )
                    if new_status != current_stat:
                        save_sent_company(s_comp.get('name'), s_comp.get('email'), s_comp.get('city'),
                                          status=new_status)
                st.markdown("---")
        else:
            st.info("لم يتم إرسال أي طلب حتى الآن.")