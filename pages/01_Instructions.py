import streamlit as st

# --- GLOBAL RTL + STYLE FIXES ---
st.markdown("""
<style>
            
/* Force dark background */
.stApp {
    background-color: #1E1E2E !important;
}

/* Also cover the sidebar and main block */
section[data-testid="stSidebar"] {
    background-color: #16161E !important;
}

/* Full RTL support */
html, body, [class*="css"], .stMarkdown, .stText, p, div, ul, li {
    direction: rtl !important;
    text-align: right !important;
}

/* Light text for dark backgrounds */
body, div, p, span, li, h1, h2, h3, h4, h5, h6 {
    color: #F2F2F2 !important;
}

/* Title styling */
.big-title {
    font-size: 40px !important;
    font-weight: bold;
    color: #5DADE2;
    margin-bottom: 25px;
}

/* Section header */
.section-header {
    font-size: 28px !important;
    font-weight: bold;
    color: #F5B041;
    margin-top: 25px;
}

/* Bullet text */
.bullet-text {
    font-size: 22px !important;
    line-height: 1.9;
}

/* Warning box */
.warning-box {
    background-color: #FDEDEC;
    border-right: 6px solid #C0392B;
    padding: 18px;
    font-size: 22px;
    margin-top: 25px;
    color: #7B241C !important;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)

# --- PAGE CONTENT ---
st.markdown("<div class='big-title'>ברוכים הבאים לגרסת הדמו של מבחן הקלפים</div>", unsafe_allow_html=True)

st.markdown("<div class='section-header'>הסבר</div>", unsafe_allow_html=True)

st.markdown("""
<div class='bullet-text'>

- כל שלב מורכב מקלף מטרה ו־4 אפשרויות בחירה 
 
- ישנו רק קלף אחד שמתאים לקלף המטרה בהתבסס על חוק  
- החוק כולל התאמה בין שני מאפיינים של הקלף  
- אם בחרת בקלף הנכון — תתקבל הודעה ירוקה על תשובה נכונה  
- אם בחרת בקלף בו רק אחד המאפיינים מתאים — תתקבל הודעה צהובה שהתשובה כמעט נכונה  
- אם בחרת בקלף בו אין אפילו מאפיין אחד מתוך החוק - תתקבל הודעה אדומה כי התשובה לא נכונה
- לפעמים החוק יתחלף בלי להזהיר מראש.  
- לפעמים יכולה להופיע הודעה על מעבר לשלב הבא - המשמעות היא שהחוק התחלף בוודאות
- כמות הצעדים: 60
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='warning-box'>
<strong>מה נספר?</strong><br>
כמות תשובות נכונות (לא כולל תשובות מיד אחרי החלפת חוק)
כמות חוקים שנמצאו (כמות הפעמים שמועמד עבר לשלב הבא כי ענה נכון על X תשובות נכונות ברצף)
כמות טעויות נגררות (טעות עקב שימוש בחוק קודם )
כמות טעויות לא נגררות

</div>
""", unsafe_allow_html=True)

# --- BUTTON ---
if st.button("התחל את המבחן"):
    st.switch_page("pages/02_Card_Trials.py")