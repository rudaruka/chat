import streamlit as st
from supabase import create_client, Client
import time # (1) 무한 루프 수정을 위해 time.sleep(1) 제거 예정

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
    # (주의: Supabase의 'created_at' 자동 생성 기능에 의존하는 경우,
    # 클라이언트의 타임존 설정이 필요할 수 있으나, 여기서는 기본 설정 사용)
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 2. 메시지 불러오기 함수
# ==========================================

# 메시지를 캐싱하지 않음: 채팅 앱 특성상 항상 최신 정보를 불러와야 함
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
    # (2) st.empty() 제거: username이 없을 때만 입력 위젯을 표시
    user_name_input = st.text_input("당신의 이름을 입력해주세요:", key="initial_name_input")
    
    if user_name_input:
        st.session_state.username = user_name_input.strip()
        # st.rerun()은 이름 설정 후 메인 로직을 바로 실행하게 함
        st.rerun() 
    else:
        # 이름이 설정되지 않았으면 이후 로직 실행 방지
        st.stop() 
    
current_user = st.session_state.username
st.subheader(f"대화명: **{current_user}**")
st.markdown("---")


# 3-2. 실시간 효과를 위한 폴링(Polling) 설정 제거
# (1) 무한 루프의 원인이 되는 time.sleep(1) 및 st.rerun()을 제거합니다.
# 대신 사용자가 메시지를 보낼 때만 st.rerun()을 호출하여 새로고침을 유도합니다.


# 3-3. 채팅 기록 표시
# 채팅 기록 컨테이너를 스크롤 가능하게 분리하여 메시지가 많아져도 UI가 깨지지 않게 합니다.
chat_container = st.container(height=400, border=True)

with chat_container:
    messages = load_messages()
    for message in messages:
        sender = message.get('sender', 'Unknown')
        content = message.get('content', '')
        
        # 내 메시지와 상대방 메시지를 구분하여 다른 UI로 표시
        # Streamlit의 관행에 따라 'user'/'assistant' 역할 사용
        role_display = "user" if sender == current_user else "assistant"
        
        # 아바타에 사용자 이름의 첫 글자를 사용하거나 기본 아이콘 사용
        avatar = sender[0].upper() if sender else None
        
        with st.chat_message(role_display, avatar=avatar):
            # bold 태그를 사용하여 누가 보냈는지 명확하게 표시
            st.markdown(f"**{sender}**: {content}")

# 3-4. 새 메시지 입력 및 전송
if prompt := st.chat_input("메시지를 입력하세요...", key="chat_input"):
    
    # 1. Supabase에 메시지 저장
    try:
        supabase.table("messages").insert({
            "sender": current_user, 
            "content": prompt
        }).execute()
        
        # 메시지 전송 후 화면을 새로고침하여 다른 사용자가 보낸 메시지도 즉시 확인 
        # (이것이 실시간 효과를 내는 유일한 st.rerun()입니다)
        st.rerun() 
        
    except Exception as e:
        st.error(f"메시지 전송에 실패했습니다: {e}")

# 3-5. 실시간 업데이트 버튼 (선택 사항)
# 사용자가 직접 업데이트를 원할 때만 새로고침하도록 버튼을 추가할 수 있습니다.
if st.button("새 메시지 확인/업데이트", key="refresh_button"):
    st.rerun()
