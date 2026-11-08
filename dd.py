import streamlit as st
import requests
import json
import os
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "institutions.json"

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def load_rows():
    rows = load_json(DATA_FILE, [])
    return rows if isinstance(rows, list) else []

def save_rows(rows):
    save_json(DATA_FILE, rows)

def add_or_update(rows, item):
    key = (item.get("email") or "").lower()
    for row in rows:
        if key and (row.get("email") or "").lower() == key:
            for k, v in item.items():
                if v not in (None, ""):
                    row[k] = v
            return
    rows.append(item)

st.set_page_config(page_title="Ausbildung Finder", page_icon="🇩🇪", layout="wide")

if "rows" not in st.session_state:
    st.session_state.rows = load_rows()

st.title("🇩🇪 نظام أتمتة إرسال طلبات الشغل في ألمانيا")
st.caption("بحث سريع، تخزين دائم، إرسال جماعي، وإعادة إرسال مخصصة للمؤسسات السابقة.")

# ==========================
# الشريط الجانبي (الإعدادات)
# ==========================
with st.sidebar:
    st.header("⚙️ إعدادات الإرسال والملفات")
    gmail_user = st.text_input("بريد Gmail الخاص بك", placeholder="name@gmail.com")
    gmail_pass = st.text_input("كلمة مرور التطبيقات (App Password)", type="password")
    
    st.subheader("🤖 مفتاح الذكاء الاصطناعي")
    ai_key = st.text_input("OpenRouter API Key", value="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", type="password")
    
    st.subheader("📄 ملف السيرة الذاتية (CV)")
    cv_upload = st.file_uploader("رفع الـ CV بصيغة PDF", type=["pdf"])
    cv_path = ""
    if cv_upload:
        cv_path = str(APP_DIR / "cv_for_applications.pdf")
        Path(cv_path).write_bytes(cv_upload.getvalue())
        st.success("✅ تم حفظ الـ CV بنجاح!")
        
    st.divider()
    if st.button("🗑️ مسح الأرشيف والمؤسسات المخزنة"):
        if DATA_FILE.exists():
            DATA_FILE.unlink()
        st.session_state.rows = []
        st.success("تم مسح الأرشيف بنجاح!")
        st.rerun()

# ==========================
# الواجهة عبر 5 تبويبات منظمة
# ==========================
tabs = st.tabs([
    "🔍 البحث وجلب المؤسسات", 
    "📋 الأرشيف وحالة الطلبات", 
    "📊 سجل وتتبع الإرسال", 
    "📤 إرسال الطلبات والتحكم الفاصل",
    "🔄 إعادة الإرسال للمرسل لها مسبقاً"
])

status_options = ['لم يتم الإرسال بعد', 'تم إرسال الطلب 📤', 'في انتظار الرد ⏳', 'تم الرد / قبول مبدئي 🎉']

# --- التبويب 1: البحث وجلب المؤسسات ---
with tabs[0]:
    st.subheader("البحث الفوري عن مؤسسات التمريض في ألمانيا")
    c1, c2 = st.columns([2, 1])
    with c1:
        target_city = st.text_input("المدينة أو المنطقة (اتركها فارغة للبحث في عموم ألمانيا Bundesweit):")
    with c2:
        num_institutions = st.slider("عدد المؤسسات:", min_value=5, max_value=50, value=20, step=5)
        
    if st.button("🚀 ابحث وجلب المؤسسات الآن", type="primary"):
        if not ai_key:
            st.error("الرجاء إدخال مفتاح OpenRouter API في الشريط الجانبي.")
        else:
            with st.spinner(f"🔄 جاري جلب قائمة دقيقة تضم {num_institutions} مؤسسة طبية..."):
                scout_prompt = f"""
                Act as an expert German healthcare job scout. Generate a JSON list of exactly {num_institutions} real or representative hospitals, nursing care facilities, or clinics in Germany.
                Target location: {target_city if target_city else "Germany (Bundesweit)"}.
                For each institution, provide:
                1. "name": Institution Name
                2. "email": Official Application email (e.g., bewerbung@...)
                3. "city": City Name
                4. "website": Official website URL (e.g., https://www.example.de)

                Format the output strictly as a JSON list of objects with keys: "name", "email", "city", "website". Do not include markdown code blocks, just pure JSON, make sure it is valid JSON.
                """
                
                try:
                    resp = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {ai_key}", "Content-Type": "application/json"},
                        json={
                            "model": "openrouter/auto",
                            "messages": [{"role": "user", "content": scout_prompt}],
                            "max_tokens": 4000
                        },
                        timeout=30
                    )
                    
                    if resp.status_code == 200:
                        ai_content = resp.json()['choices'][0]['message']['content']
                        if "```json" in ai_content:
                            ai_content = ai_content.split("```json")[1].split("```")[0].strip()
                        elif "```" in ai_content:
                            ai_content = ai_content.split("```")[1].split("```")[0].strip()
                            
                        new_companies = json.loads(ai_content)
                        added_count = 0
                        
                        for comp in new_companies:
                            item = {
                                "name": comp.get("name", "مؤسسة طبية"),
                                "website": comp.get("website", ""),
                                "email": comp.get("email", ""),
                                "status": "لم يتم الإرسال بعد",
                                "last_log": "لم يتم محاولة الإرسال بعد",
                                "city": comp.get("city", target_city if target_city else "Germany"),
                                "notes": ""
                            }
                            add_or_update(st.session_state.rows, item)
                            added_count += 1
                            
                        save_rows(st.session_state.rows)
                        st.success(f"✅ تم بنجاح جلب وتخزين {added_count} مؤسسة جديدة في الأرشيف!")
                        st.rerun()
                    else:
                        st.error(f"❌ خطأ في الاتصال: {resp.status_code}")
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {e}")

# --- التبويب 2: الأرشيف وحالة الطلبات ---
with tabs[1]:
    st.subheader(f"📋 الأرشيف وحالة الطلبات ({len(st.session_state.rows)} مؤسسة مخزنة)")
    
    if st.session_state.rows:
        for idx, row in enumerate(st.session_state.rows):
            current_status = row.get('status', 'لم يتم الإرسال بعد')
            if current_status not in status_options:
                current_status = 'لم يتم الإرسال بعد'
                
            with st.expander(f"{idx+1}. {row.get('name','بدون اسم')} — المدينة: {row.get('city','')} | الحالة: [{current_status}]"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    row["name"] = st.text_input("اسم المؤسسة", row.get("name",""), key=f"name_{idx}")
                    row["email"] = st.text_input("البريد الإلكتروني", row.get("email",""), key=f"email_{idx}")
                    row["city"] = st.text_input("المدينة", row.get("city",""), key=f"city_{idx}")
                with col2:
                    new_status = st.selectbox(
                        "حالة الطلب:",
                        status_options,
                        index=status_options.index(current_status),
                        key=f"status_t2_{idx}"
                    )
                    if new_status != row.get('status'):
                        row['status'] = new_status
                        save_rows(st.session_state.rows)
                
                st.write(f"📌 **آخر سجل إرسال:** `{row.get('last_log', 'لا توجد محاولة سابقة')}`")
                
                if st.button("💾 حفظ التعديلات", key=f"save_row_{idx}"):
                    save_rows(st.session_state.rows)
                    st.success("تم الحفظ بنجاح!")
    else:
        st.info("لا توجد مؤسسات مخزنة حالياً.")

# --- التبويب 3: سجل وتتبع الإرسال ---
with tabs[2]:
    st.subheader("📊 سجل تتبع الإرسال لكل بريد إلكتروني")
    
    if st.session_state.rows:
        for idx, row in enumerate(st.session_state.rows):
            name = row.get('name', 'بدون اسم')
            email = row.get('email', 'لا يوجد بريد')
            status = row.get('status', 'لم يتم الإرسال بعد')
            log = row.get('last_log', 'لم يتم محاولة الإرسال بعد')
            
            if "تم إرسال" in status:
                icon = "✅"
            elif "فشل" in str(log):
                icon = "❌"
            else:
                icon = "⏳"
                
            st.markdown(f"**{idx+1}. {icon} {name}**")
            st.write(f"📧 البريد: `{email}` | الحالة: **{status}**")
            st.info(f"📝 تفاصيل السجل: {log}")
            st.markdown("---")
    else:
        st.info("لا توجد سجلات تتبع حالياً.")

# --- التبويب 4: إرسال الطلبات والتحكم الفاصل ---
with tabs[3]:
    st.subheader("📤 الإرسال الجماعي والفردي مع التحديث التلقائي للحالة")
    
    custom_subject = st.text_input("موضوع الرسالة (Subject / Betreff):", value="Bewerbung als Pflegefachkraft / Ausbildung", key="main_subj")
    
    default_body = st.text_area(
        "نص الرسالة الموحدة باللغة الألمانية:",
        value="""Sehr geehrte Damen und Herren,

ich bewerbe mich hiermit um eine Ausbildung als Pflegefachkraft in Ihrer Einrichtung. Ich komme aus Marokko, habe das marokkanische Baccalauréat abgeschlossen und lerne derzeit Deutsch. 

Im Anhang finden Sie meinen Lebenslauf. Über eine positive Rückmeldung freue ich mich sehr.

Mit freundlichen Grüßen,
Radwan Slioui""",
        height=180,
        key="main_body"
    )
    
    ready_to_send = [r for r in st.session_state.rows if r.get("email")]
    st.write(f"إجمالي المؤسسات الجاهزة للإرسال: **{len(ready_to_send)}**")
    
    if ready_to_send:
        st.markdown("### ⚡ الإرسال الجماعي التلقائي بفاصل زمني")
        bulk_delay = st.slider("اختر الفارق الزمني بين كل رسالة وأخرى (ثواني):", min_value=1, max_value=20, value=3, key="bulk_delay_slider")
        
        if st.button("🚀 إرسال الرسالة والسيرة الذاتية لجميع المؤسسات دفعة واحدة", type="primary"):
            if not gmail_user or not gmail_pass:
                st.error("❌ يرجى إدخال بريد Gmail و App Password في الشريط الجانبي.")
            else:
                progress_bar = st.progress(0)
                success_count = 0
                fail_count = 0
                total = len(ready_to_send)
                status_log = st.empty()
                
                for i, row in enumerate(ready_to_send):
                    try:
                        msg = EmailMessage()
                        msg["From"] = gmail_user
                        msg["To"] = row["email"]
                        msg["Subject"] = custom_subject
                        msg.set_content(default_body)
                        
                        if cv_path and Path(cv_path).exists():
                            p = Path(cv_path)
                            msg.add_attachment(p.read_bytes(), maintype="application", subtype="pdf", filename=p.name)
                            
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as smtp:
                            smtp.login(gmail_user, gmail_pass)
                            smtp.send_message(msg)
                            
                        row["status"] = "تم إرسال الطلب 📤"
                        row["last_log"] = f"تم الإرسال بنجاح بتاريخ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                        success_count += 1
                        status_log.success(f"✅ [تم الإرسال وتحديث الحالة] إلى: {row.get('name')}")
                    except Exception as ex:
                        fail_count += 1
                        row["last_log"] = f"فشل الإرسال — السبب: {ex}"
                        status_log.error(f"❌ [لم تُرسل] إلى {row.get('name')} — السبب: {ex}")
                        
                    progress_bar.progress((i + 1) / total)
                    time.sleep(bulk_delay)
                    
                save_rows(st.session_state.rows)
                st.success(f"🎉 انتهى الإرسال الجماعي: نجح إرسال {success_count} | فشل إرسال {fail_count}.")
                st.rerun()
                
        st.divider()
        st.markdown("### 📨 الإرسال الفردي وتتبع الحالة التلقائية")
        for idx, row in enumerate(ready_to_send):
            current_status = row.get('status', 'لم يتم الإرسال بعد')
            
            c_info, c_status, c_btn = st.columns([2, 1, 1])
            with c_info:
                st.write(f"**{idx+1}. {row.get('name')}**\n`{row.get('email')}`")
                st.caption(f"السجل: {row.get('last_log', 'لم تُرسل بعد')}")
            with c_status:
                st.markdown(f"<br>**الحالة:** `{current_status}`", unsafe_allow_html=True)
            with c_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📤 إرسال فردي", key=f"send_one_{idx}"):
                    if not gmail_user or not gmail_pass:
                        st.error("أدخل بيانات Gmail.")
                    else:
                        try:
                            msg = EmailMessage()
                            msg["From"] = gmail_user
                            msg["To"] = row["email"]
                            msg["Subject"] = custom_subject
                            msg.set_content(default_body)
                            
                            if cv_path and Path(cv_path).exists():
                                p = Path(cv_path)
                                msg.add_attachment(p.read_bytes(), maintype="application", subtype="pdf", filename=p.name)
                                
                            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as smtp:
                                smtp.login(gmail_user, gmail_pass)
                                smtp.send_message(msg)
                                
                            row["status"] = "تم إرسال الطلب 📤"
                            row["last_log"] = f"تم الإرسال فردياً بنجاح بتاريخ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                            save_rows(st.session_state.rows)
                            st.success(f"تم الإرسال وتحديث الحالة تلقائياً! 📤")
                            st.rerun()
                        except Exception as ex:
                            row["last_log"] = f"فشل الإرسال الفردي — السبب: {ex}"
                            save_rows(st.session_state.rows)
                            st.error(f"❌ لم تُرسل الإيميل! خطأ: {ex}")
            st.markdown("---")
    else:
        st.info("لا توجد مؤسسات للإرسال حالياً. ابحث وجلب المؤسسات أولاً.")

# --- التبويب 5: إعادة الإرسال للمؤسسات المُرسل لها مسبقاً ---
with tabs[4]:
    st.subheader("🔄 إعادة الإرسال للمؤسسات التي تم إرسال الطلب لها مسبقاً")
    st.caption("هنا تظهر فقط المؤسسات التي تمتلك بريداً إلكترونياً وحالتها 'تم إرسال الطلب 📤'.")
    
    # تصفية المؤسسات التي تم إرسال الطلب لها فقط
    sent_institutions = [r for r in st.session_state.rows if r.get("email") and r.get("status") == "تم إرسال الطلب 📤"]
    
    if sent_institutions:
        st.write(f"عدد المؤسسات المُرسل لها مسبقاً والمتاحة لإعادة الإرسال: **{len(sent_institutions)}**")
        
        # ➕ خيار تحديد الكل (Select All)
        select_all_tab5 = st.checkbox("☑️ تحديد الكل / إلغاء الكل", key="select_all_tab5_box")
        
        selected_tab5 = []
        for idx, row in enumerate(sent_institutions):
            is_checked = st.checkbox(
                f"{row.get('name')} — `{row.get('email')}` (المدينة: {row.get('city', 'N/A')})",
                value=select_all_tab5,
                key=f"tab5_chk_{idx}"
            )
            if is_checked:
                selected_tab5.append(row)
                
        st.divider()
        st.markdown("### ⚡ إعدادات إعادة الإرسال الجماعي")
        resend_subject_t5 = st.text_input("موضوع الرسالة لإعادة الإرسال (Subject):", value="Erinnerung / Bewerbung als Pflegefachkraft", key="t5_subj")
        resend_delay_t5 = st.slider("الفارق الزمني بين كل رسالة وأخرى (ثواني):", min_value=1, max_value=20, value=3, key="t5_delay")
        
        resend_body_t5 = st.text_area(
            "نص رسالة التذكير أو إعادة الإرسال بالألمانية:",
            value="""Sehr geehrte Damen und Herren,

ich bezziehe mich auf meine vorherige Bewerbung als Pflegefachkraft in Ihrer Einrichtung und möchte mein großes Interesse an einer Ausbildung bei Ihnen bekräftigen. 

Im Anhang finden Sie meinen Lebenslauf erneut. Über eine positive Rückmeldung freue ich mich sehr.

Mit freundlichen Grüßen,
Radwan Slioui""",
            height=160,
            key="t5_body"
        )
        
        if selected_tab5:
            if st.button("🚀 إعادة إرسال الطلب للمؤسسات المحددة فقط", type="primary"):
                if not gmail_user or not gmail_pass:
                    st.error("❌ يرجى إدخال بريد Gmail و App Password في الشريط الجانبي.")
                else:
                    progress_bar = st.progress(0)
                    success_count = 0
                    fail_count = 0
                    total = len(selected_tab5)
                    log_t5 = st.empty()
                    
                    for i, row in enumerate(selected_tab5):
                        try:
                            msg = EmailMessage()
                            msg["From"] = gmail_user
                            msg["To"] = row["email"]
                            msg["Subject"] = resend_subject_t5
                            msg.set_content(resend_body_t5)
                            
                            if cv_path and Path(cv_path).exists():
                                p = Path(cv_path)
                                msg.add_attachment(p.read_bytes(), maintype="application", subtype="pdf", filename=p.name)
                                
                            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as smtp:
                                smtp.login(gmail_user, gmail_pass)
                                smtp.send_message(msg)
                                
                            row["last_log"] = f"إعادة إرسال ناجحة بتاريخ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                            success_count += 1
                            log_t5.success(f"✅ [تمت إعادة الإرسال] إلى: {row.get('name')}")
                        except Exception as ex:
                            fail_count += 1
                            row["last_log"] = f"فشل إعادة الإرسال — السبب: {ex}"
                            log_t5.error(f"❌ [فشل] إلى {row.get('name')} — السبب: {ex}")
                            
                        progress_bar.progress((i + 1) / total)
                        time.sleep(resend_delay_t5)
                        
                    save_rows(st.session_state.rows)
                    st.success(f"🎉 انتهت عملية إعادة الإرسال: نجح {success_count} | فشل {fail_count}.")
                    st.rerun()
        else:
            st.warning("⚠️ الرجاء تحديد مؤسسة واحدة على الأقل من القائمة أعلاه لإعادة الإرسال.")
    else:
        st.info("ℹ️ لا توجد حالياً أي مؤسسات بالحالة 'تم إرسال الطلب 📤'. بمجرد إرسال الطلبات في التبويب الرابع، ستظهر هنا تلقائياً لتتمكن من إعادة التواصل معها.")
