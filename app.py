import streamlit as st
from supabase import create_client, Client
import time

# ==========================================
# Supabase 연결 정보 (🚨 실제 키로 대체해야 합니다!)
# ==========================================
# 실제 배포 시에는 secrets.toml 파일에 저장하고 st.secrets에서 불러와야 합니다.
SUPABASE_URL = "YOUR_SUPABASE_URL"
SUPABASE_KEY = "YOUR_ANON_PUBLIC_KEY"

# Supabase 클라이언트 초기화
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 1. 사용자 설정 및 초기화
# ==========================================

st.set_page_config(page_title="실시간 친구 채팅 앱", page_icon="⚡")
st.title("실시간 친구 채팅 앱 💬⚡")

# 사용자 이름 설정 (이전과 동일하게 설정)
if "username" not in st.session_state or not st.session_state.username:
    # 이 섹션은 사용자가 이름을 입력할 때까지 반복됩니다.
    with st.empty():
        user_name_input = st.text_input("당신의 이름을 입력해주세요:", key="initial_name_input")
        if user_name_input:
            st.session_state.username = user_name_input
            st.rerun() 
    # 이름 설정이 안 되면 아래 채팅 로직 실행 방지
    st.stop()
    
current_user = st.session_state.username
st.write(f"환영합니다, **{current_user}**님!")

# ==========================================
# 2. 메시지 불러오기 및 실시간 업데이트
# ==========================================

# 1초마다 앱을 새로고침하는 코드를 삽입하여 실시간 효과를 냅니다.
# (Streamlit은 폴링(Polling) 방식을 사용해 실시간처럼 보이게 합니다.)
time.sleep(1)
st.rerun()

def load_messages():
    """Supabase에서 메시지를 가져와 시간 순으로 정렬합니다."""
    try:
        response = supabase.table("messages").select("*").order("created_at").execute()
        # response.data는 리스트 형태의 메시지 딕셔너리입니다.
        return response.data
    except Exception as e:
        st.error(f"메시지를 불러오는 데 실패했습니다: {e}")
        return []

# 메시지 로드
messages = load_messages()

# 채팅 기록 표시
for message in messages:
    sender = message['sender']
    content = message['content']
    
    # 내 메시지와 상대방 메시지를 구분하여 다른 UI로 표시
    role_display = "user" if sender == current_user else "assistant"
    
    with st.chat_message(role_display, avatar=sender[0].upper()): # 아바타에 사용자 이름의 첫 글자를 사용
        st.markdown(f"**{sender}**: {content}")

# ==========================================
# 3. 새 메시지 전송
# ==========================================

if prompt := st.chat_input("메시지를 입력하세요..."):
    
    # 1. 화면에 즉시 메시지 표시
    with st.chat_message("user"):
        st.markdown(f"**{current_user}**: {prompt}")
        
    # 2. Supabase에 메시지 저장
    try:
        supabase.table("messages").insert({
            "sender": current_user, 
            "content": prompt
        }).execute()
        
        # 메시지 전송 후 화면을 새로고침하여 다른 사용자가 보낸 메시지도 즉시 확인 (rerun이 폴링 역할을 함)
        st.rerun() 
        
    except Exception as e:
        st.error(f"메시지 전송에 실패했습니다: {e}")
