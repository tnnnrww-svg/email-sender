import streamlit as st
import requests
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# جلب مفتاح الأمان بطريقة آمنة من إعدادات Streamlit Secrets
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except Exception:
    API_KEY = ""

st.title("🇩🇪 نظام أتمتة إرسال طلبات الشغل في ألمانيا (Bundesweit)")
st.write("التحكم الكامل، تخصيص الرسائل، تتبع الحالة، والفحص التلقائي للردود الواردة.")

# رفع السيرة الذاتية
uploaded_file = st.file_uploader("1. ارفع سيرتك الذاتية (CV بصيغة PDF):", type=["pdf"])

target_city = st.text_input("أدخل اسم المدينة أو المنطقة (مثال: Berlin أو اتركها فارغة للبحث في كل ألمانيا):")

if st.button("🔍 ابحث وجلب 50 مؤسسة جديدة"):
    if not API_KEY:
        st.error("❌ مفتاح OPENROUTER_API_KEY غير موجود في إعدادات Secrets في Streamlit Cloud. الرجاء إضافته.")
    else:
        if not target_city:
            st.info("🔄 جاري جلب قائمة دقيقة تضم 50 مؤسسة تمريض في عموم ألمانيا (Bundesweit)...")
        else:
            st.info(f"🔄 جاري جلب قائمة دقيقة تضم 50 مؤسسة تمريض في مدينة أو منطقة {target_city}...")

        scout_prompt = f"""
        Act as an expert German healthcare job scout. Generate a JSON list of exactly 50 real or representative hospitals, nursing care facilities, or clinics in Germany.
        Target location: {target_city if target_city else "Germany (Bundesweit)"}.
        For each institution, provide:
        1. "name": Institution Name
        2. "email": Official Application email (e.g., bewerbung@...)
        3. "city": City Name

        Format the output strictly as a JSON list of objects with keys: "name", "email", "city". Do not include markdown code blocks, just pure JSON, make sure it is valid JSON.
        """

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        scout_payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": scout_prompt}],
            "max_tokens": 4000
        }

        try:
            scout_response = requests.post(url, headers=headers, data=json.dumps(scout_payload))
            
            if scout_response.status_code == 200:
                ai_content = scout_response.json()['choices'][0]['message']['content']
                # تنظيف الكود من ماركداون إن وجدت
                if "```json" in ai_content:
                    ai_content = ai_content.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_content:
                    ai_content = ai_content.split("```")[1].split("```")[0].strip()
                
                companies = json.loads(ai_content)
                st.success(f"✅ تم بنجاح جلب {len(companies)} مؤسسة طبية في ألمانيا!")
                
                # عرض الشركات كمثال
                st.write(companies[:5])
            else:
                st.error(f"❌ فشل الاتصال بالذكاء الاصطناعي لجلب الشركات. رمز الخطأ: {scout_response.status_code}")
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء الاتصال: {e}")
