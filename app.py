import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# Cấu hình trang
st.set_page_config(
    page_title="Game Table Manager",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File lưu trữ dữ liệu
DATA_FILE = "game_data.json"

class Debit:
    def __init__(self, user_id1, user_id2, amount):
        self.user_id1 = user_id1
        self.user_id2 = user_id2
        self.amount = amount
    
    def check_amount(self, user_id, players_dict):
        """Kiểm tra số tiền nợ từ góc nhìn của user_id"""
        if user_id == self.user_id1:
            other_name = players_dict.get(self.user_id2, {}).get("name", "Unknown")
            if self.amount < 0:
                return f"Bạn nợ {other_name}: {abs(self.amount):,} VND", "negative"
            else:
                return f"Bạn cho {other_name}: {abs(self.amount):,} VND", "positive"
        
        elif user_id == self.user_id2:
            other_name = players_dict.get(self.user_id1, {}).get("name", "Unknown")
            if self.amount > 0:
                return f"Bạn nợ {other_name}: {abs(self.amount):,} VND", "negative"
            else:
                return f"Bạn cho {other_name}: {abs(self.amount):,} VND", "positive"
        
        return "Lỗi ID", "neutral"
    
    def add_amount(self, user_id, money):
        """Thêm tiền vào khoản nợ"""
        if user_id == self.user_id1:
            self.amount += money
        elif user_id == self.user_id2:
            self.amount -= money

def load_data():
    """Tải dữ liệu từ file JSON"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                players = data.get("players", {})
                debits_data = data.get("debits", [])
                debits = [
                    Debit(item["user_id1"], item["user_id2"], item["amount"])
                    for item in debits_data
                ]
                return players, debits
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
    
    return {}, []

def save_data(players, debits):
    """Lưu dữ liệu vào file JSON"""
    try:
        data = {
            "players": players,
            "debits": [
                {
                    "user_id1": debit.user_id1,
                    "user_id2": debit.user_id2,
                    "amount": debit.amount
                }
                for debit in debits
            ]
        }
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Lỗi khi lưu dữ liệu: {e}")

def parse_amount(amount_str):
    """Chuyển đổi chuỗi số tiền (hỗ trợ 'k' cho nghìn)"""
    try:
        amount_str = str(amount_str).strip().lower()
        if amount_str.endswith('k'):
            return int(float(amount_str[:-1]) * 1000)
        else:
            return int(float(amount_str))
    except ValueError:
        return None

# Khởi tạo session state
if 'players' not in st.session_state:
    st.session_state.players, st.session_state.debits = load_data()

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

def add_notification(message, type="info"):
    """Thêm thông báo"""
    st.session_state.notifications.append({
        "message": message,
        "type": type,
        "time": datetime.now().strftime("%H:%M:%S")
    })

def show_notifications():
    """Hiển thị thông báo"""
    if st.session_state.notifications:
        with st.container():
            for notif in st.session_state.notifications[-3:]:  # Chỉ hiển thị 3 thông báo gần nhất
                if notif["type"] == "success":
                    st.success(f"[{notif['time']}] {notif['message']}")
                elif notif["type"] == "error":
                    st.error(f"[{notif['time']}] {notif['message']}")
                elif notif["type"] == "warning":
                    st.warning(f"[{notif['time']}] {notif['message']}")
                else:
                    st.info(f"[{notif['time']}] {notif['message']}")

# Header
st.title("🎮 Game Table Manager")
st.markdown("---")

# Sidebar - User Management
with st.sidebar:
    st.header("👤 Quản lý người dùng")
    
    if st.session_state.current_user is None:
        st.subheader("Đăng nhập")
        username = st.text_input("Nhập tên của bạn:", key="login_input")

        if st.button("🎯 Tham gia bàn", use_container_width=True):
            if username.strip():
                existing_names = [player["name"] for player in st.session_state.players.values()]
                if username in existing_names:
                    # Đăng nhập vào tài khoản đã có
                    for uid, player in st.session_state.players.items():
                        if player["name"] == username:
                            st.session_state.current_user = uid
                            add_notification(f"Đăng nhập thành công với tài khoản '{username}'!", "success")
                            st.rerun()
                            break
                else:
                    # Tạo user mới
                    user_id = f"user_{len(st.session_state.players) + 1}_{int(datetime.now().timestamp())}"
                    st.session_state.players[user_id] = {
                        "name": username,
                        "join_time": datetime.now().isoformat()
                    }
                    st.session_state.current_user = user_id
                    save_data(st.session_state.players, st.session_state.debits)
                    add_notification(f"{username} đã tham gia bàn chơi!", "success")
                    st.rerun()
            else:
                add_notification("Vui lòng nhập tên của bạn!", "error")

    
    else:
        current_name = st.session_state.players[st.session_state.current_user]["name"]
        st.success(f"Xin chào, **{current_name}**! 👋")
        
        if st.button("🚪 Rời bàn", use_container_width=True):
            # Xóa user và các khoản nợ liên quan
            user_id = st.session_state.current_user
            user_name = st.session_state.players[user_id]["name"]
            
            # Xóa player
            del st.session_state.players[user_id]
            
            # Xóa các khoản nợ liên quan
            st.session_state.debits = [
                debit for debit in st.session_state.debits
                if debit.user_id1 != user_id and debit.user_id2 != user_id
            ]
            
            st.session_state.current_user = None
            save_data(st.session_state.players, st.session_state.debits)
            add_notification(f"{user_name} đã rời khỏi bàn chơi!", "info")
            st.rerun()
    
    st.markdown("---")
    
    # Thông tin thống kê
    st.subheader("📊 Thống kê")
    st.metric("Số người chơi", len(st.session_state.players))
    st.metric("Số khoản nợ", len(st.session_state.debits))

# Main content
if st.session_state.current_user is None:
    st.info("👈 Vui lòng đăng nhập để sử dụng ứng dụng!")
    
else:
    # Hiển thị thông báo
    show_notifications()
    
    # Action buttons
    col2, col3, col4 = st.columns(3)
    

    
    with col2:
        show_players = st.button("👥 Danh sách người chơi", use_container_width=True)
    
    with col3:
        show_debts = st.button("💰 Xem nợ của tôi", use_container_width=True)
    
    with col4:
        if st.button("🔄 Làm mới", use_container_width=True):
            players, debits = load_data()
            st.session_state.players = players
            st.session_state.debits = debits
            add_notification("Đã làm mới dữ liệu từ file!", "info")
            st.rerun()

    
    st.markdown("---")
    
    # Tabs for different functions
    tab1, tab2, tab3 = st.tabs(["💸 Thêm nợ", "📋 Danh sách", "📊 Thống kê"])
    
    with tab1:
        st.subheader("💸 Thêm khoản nợ")
        
        # Lọc ra những người chơi khác (không phải current user)
        other_players = {
            uid: player for uid, player in st.session_state.players.items()
            if uid != st.session_state.current_user
        }
        
        if not other_players:
            st.warning("Không có người chơi nào khác để thêm nợ!")
        else:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                selected_player = st.selectbox(
                    "Chọn người chơi:",
                    options=list(other_players.keys()),
                    format_func=lambda x: other_players[x]["name"],
                    key="debt_player_select"
                )
            
            with col2:
                debt_amount = st.text_input(
                    "Số tiền:",
                    placeholder="VD: 50000 hoặc 50k",
                    key="debt_amount_input"
                )
            
            with col3:
                st.write("")  # Spacer
                if st.button("➕ Thêm nợ", use_container_width=True):
                    if selected_player and debt_amount:
                        amount = parse_amount(debt_amount)
                        if amount is not None:
                            # Tìm khoản nợ đã tồn tại
                            existing_debt = None
                            for debit in st.session_state.debits:
                                if ((debit.user_id1 == st.session_state.current_user and debit.user_id2 == selected_player) or
                                    (debit.user_id1 == selected_player and debit.user_id2 == st.session_state.current_user)):
                                    existing_debt = debit
                                    break
                            
                            if existing_debt:
                                existing_debt.add_amount(st.session_state.current_user, amount)
                            else:
                                new_debt = Debit(st.session_state.current_user, selected_player, amount)
                                st.session_state.debits.append(new_debt)
                            
                            save_data(st.session_state.players, st.session_state.debits)
                            other_name = other_players[selected_player]["name"]
                            add_notification(f"Đã thêm {other_name} với số tiền {amount:,} VND vào danh sách nợ.", "success")
                            st.rerun()
                        else:
                            add_notification("Số tiền không hợp lệ!", "error")
                    else:
                        add_notification("Vui lòng chọn người chơi và nhập số tiền!", "error")
    
    with tab2:
        if show_players or st.session_state.get('show_players_tab', False):
            st.subheader("👥 Danh sách người chơi")
            
            if st.session_state.players:
                players_data = []
                for uid, player in st.session_state.players.items():
                    join_time = datetime.fromisoformat(player["join_time"])
                    players_data.append({
                        "Tên": player["name"],
                        "Thời gian tham gia": join_time.strftime("%H:%M:%S - %d/%m/%Y"),
                        "Trạng thái": "🟢 Online" if uid == st.session_state.current_user else "⚪ Offline"
                    })
                
                df = pd.DataFrame(players_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có người chơi nào trong bàn.")
        
        if show_debts or st.session_state.get('show_debts_tab', False):
            st.subheader("💰 Danh sách nợ của bạn")
            
            user_debts = [
                debit for debit in st.session_state.debits
                if debit.user_id1 == st.session_state.current_user or debit.user_id2 == st.session_state.current_user
            ]
            
            if user_debts:
                debt_data = []
                for debit in user_debts:
                    debt_text, debt_type = debit.check_amount(st.session_state.current_user, st.session_state.players)
                    debt_data.append({
                        "Mô tả": debt_text,
                        "Loại": "Cho vay" if debt_type == "positive" else "Nợ",
                        "Số tiền": f"{abs(debit.amount):,} VND"
                    })
                
                df = pd.DataFrame(debt_data)
                
                # Tô màu theo loại nợ
                def highlight_debt_type(row):
                    if row['Loại'] == 'Cho vay':
                        return ['background-color: #d4edda; color: #000000'] * len(row)
                    else:
                        return ['background-color: #f8d7da; color: #000000'] * len(row)

                
                styled_df = df.style.apply(highlight_debt_type, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Tổng kết
                total_lend = sum(abs(d.amount) for d in user_debts if d.check_amount(st.session_state.current_user, st.session_state.players)[1] == "positive")
                total_owe = sum(abs(d.amount) for d in user_debts if d.check_amount(st.session_state.current_user, st.session_state.players)[1] == "negative")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💚 Tổng cho vay", f"{total_lend:,} VND")
                with col2:
                    st.metric("❤️ Tổng nợ", f"{total_owe:,} VND")
                with col3:
                    balance = total_lend - total_owe
                    st.metric("⚖️ Cân bằng", f"{balance:,} VND", delta=f"{balance:,}")
                    
            else:
                st.info("Bạn không có khoản nợ nào.")
    
    with tab3:
        st.subheader("📊 Thống kê tổng quan")
        
        if st.session_state.players and st.session_state.debits:
            # Thống kê theo người chơi
            player_stats = {}
            for uid, player in st.session_state.players.items():
                total_lend = 0
                total_owe = 0
                debt_count = 0
                
                for debit in st.session_state.debits:
                    if debit.user_id1 == uid or debit.user_id2 == uid:
                        debt_count += 1
                        debt_text, debt_type = debit.check_amount(uid, st.session_state.players)
                        if debt_type == "positive":
                            total_lend += abs(debit.amount)
                        elif debt_type == "negative":
                            total_owe += abs(debit.amount)
                
                player_stats[player["name"]] = {
                    "Tổng cho vay": total_lend,
                    "Tổng nợ": total_owe,
                    "Cân bằng": total_lend - total_owe,
                    "Số khoản nợ": debt_count
                }
            
            # Hiển thị bảng thống kê
            if player_stats:
                stats_df = pd.DataFrame(player_stats).T
                stats_df = stats_df.round(0).astype(int)
                
                # Format tiền tệ
                for col in ["Tổng cho vay", "Tổng nợ", "Cân bằng"]:
                    stats_df[col] = stats_df[col].apply(lambda x: f"{x:,} VND")
                
                st.dataframe(stats_df, use_container_width=True)
                
                # Biểu đồ
                if len(st.session_state.players) > 1:
                    chart_data = pd.DataFrame({
                        'Người chơi': list(player_stats.keys()),
                        'Cân bằng': [stats['Cân bằng'] for stats in player_stats.values()]
                    })
                    st.bar_chart(chart_data.set_index('Người chơi'))
            
        else:
            st.info("Chưa có dữ liệu để thống kê.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <small>🎮 Game Table Manager | Quản lý nợ thông minh</small>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-save on any change
save_data(st.session_state.players, st.session_state.debits)