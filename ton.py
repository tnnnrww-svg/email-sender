import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import time

st.title("تطبيق إرسال البريد الإلكتروني")

# إدخال البيانات الأساسية
sender_email = st.text_input("البريد الإلكتروني للراسل (Gmail):")
sender_password = st.text_input("كلمة مرور التطبيق (App Password):", type="password")
recipient_emails = st.text_area("قائمة إيميلات المستقبلين (إيميل في كل سطر):")

subject_template = st.text_input("عنوان الرسالة:")
body_template = st.text_area("محتوى الرسالة:")
uploaded_files = st.file_uploader("إرفاق ملفات (اختياري)", accept_multiple_files=True)

delay_seconds = st.number_input("وقت الانتظار بين الرسائل (بالثواني):", min_value=1, value=2)

if st.button("إرسال البريد"):
    if not sender_email or not sender_password or not recipient_emails:
        st.error("يرجى ملء جميع الحقول المطلوبة!")
    else:
        email_list = [email.strip() for email in recipient_emails.split("\n") if email.strip()]
        total_emails = len(email_list)
        success_count = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # الاتصال بسيرفر SMTP الخاص بـ Gmail
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, sender_password)

            for index, email_to in enumerate(email_list):
                msg = MIMEMultipart()
                msg["From"] = sender_email
                msg["To"] = email_to
                msg["Subject"] = subject_template

                # إضافة نص الرسالة
                msg.attach(MIMEText(body_template, "plain"))

                # إضافة المرفقات إن وجدت
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        file_data = uploaded_file.read()
                        file_name = uploaded_file.name

                        # إعادة مؤشر القراءة للحفاظ على إعادة التكرار
                        uploaded_file.seek(0)

                        part = MIMEApplication(file_data, Name=file_name)
                        part['Content-Disposition'] = f'attachment; filename="{file_name}"'
                        msg.attach(part)

                # إرسال الرسالة
                server.send_message(msg)
                success_count += 1

                status_text.text(f"تم الإرسال بنجاح إلى: {email_to} ({index + 1}/{total_emails})")
                progress_bar.progress((index + 1) / total_emails)

                # وقت انتظار لتجنب حظر البريد
                time.sleep(delay_seconds)

            server.quit()
            st.success(f"تم إرسال {success_count} إيميل بنجاح! 🚀")

        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال أو الإرسال: {e}")