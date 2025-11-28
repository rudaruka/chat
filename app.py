import streamlit as st
from supabase import create_client, Client
import time

# ==========================================
# 1. Supabase 연결 설정 (Secrets에서 불러오기)
# ==========================================

# Secrets에서 변수를 안전하게 로드합니다.
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except KeyError:
    st.error("🚨 Supabase 연결 정보(Secrets)를 찾을 수 없습니다. Streamlit Cloud의 Secrets 설정 또는 .streamlit/secrets.toml 파일을 확인해주세요.")
    st.stop() # 설정이 없으면 앱 실행을 중지

# Supabase 클라이언트 초기화 (캐시 사용으로 재실행 시 연결 유지)
@st.cache_resource
def init_connection() -> Client:
    """Supabase 클라이언트 연결을 초기화합니다."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 2. 메시지 불러오기 함수
# ==========================================

def load_messages():
    """Supabase 테이블에서 모든 메시지를 불러와 시간 순으로 정렬합니다."""
    try:
        # 'messages' 테이블에서 모든 열을 불러오고 'created_at' 시간 순으로 오름차순 정렬
        response = supabase.table("messages").select("*").order("created_at").execute()
        return response.data
    except Exception as e:
        st.error(f"메시지를 불러오는 데 실패했습니다: {e}")
        return []

# ==========================================
# 3. Streamlit 앱 메인 로직
# ==========================================

st.set_page_config(page_title="실시간 친구 채팅 앱", page_icon="⚡")
st.title("실시간 친구 채팅 앱 💬⚡")

# 3-1. 사용자 이름 설정
if "username" not in st.session_state or not st.session_state.username:
    
    with st.empty():
        user_name_input = st.text_input("당신의 이름을 입력해주세요:", key="initial_name_input")
        
        if user_name_input:
            st.session_state.username = user_name_input.strip()
            st.rerun() 
    st.stop() # 이름이 설정될 때까지 아래 로직 실행 방지
    
current_user = st.session_state.username
st.subheader(f"대화명: **{current_user}**")
st.markdown("---")


# 3-2. 실시간 효과를 위한 폴링(Polling) 설정
# Streamlit은 웹소켓을 지원하지 않으므로, st.rerun()을 사용하여 주기적으로 화면을 새로고침하여 실시간 효과를 냅니다.
time.sleep(1) # 1초 대기
st.rerun() # 앱을 새로고침하여 메시지를 다시 불러오도록 함


# 3-3. 채팅 기록 표시
messages = load_messages()
for message in messages:
    sender = message.get('sender', 'Unknown')
    content = message.get('content', '')
    
    # 내 메시지와 상대방 메시지를 구분하여 다른 UI로 표시
    role_display = "user" if sender == current_user else "assistant"
    
    # 아바타에 사용자 이름의 첫 글자를 사용하거나 기본 아이콘 사용
    avatar = sender[0].upper() if sender else None
    
    with st.chat_message(role_display, avatar=avatar):
        # bold 태그를 사용하여 누가 보냈는지 명확하게 표시
        st.markdown(f"**{sender}**: {content}")

# 3-4. 새 메시지 입력 및 전송
if prompt := st.chat_input("메시지를 입력하세요..."):
    
    # 1. Supabase에 메시지 저장
    try:
        supabase.table("messages").insert({
            "sender": current_user, 
            "content": prompt
        }).execute()
        
        # 메시지 전송 후 화면을 새로고침하여 다른 사용자가 보낸 메시지도 즉시 확인 
        st.rerun() 
        
    except Exception as e:
        st.error(f"메시지 전송에 실패했습니다: {e}")
