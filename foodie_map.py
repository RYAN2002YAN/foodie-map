import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
import base64

DB_FILE = "social_db.json"

# === 数据层：加载与保存关系型数据 ===
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 初始化空数据库结构
    return {"users": {}, "places": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def get_image_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        b64 = base64.b64encode(bytes_data).decode()
        return f"data:{uploaded_file.type};base64,{b64}"
    return None

# === 初始化全局状态 ===
st.set_page_config(page_title="Vibe 探店朋友圈", page_icon="🌍", layout="centered")

if 'db' not in st.session_state:
    st.session_state.db = load_db()
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# ================= 1. 登录与注册系统 =================
if st.session_state.current_user is None:
    st.title("🌍 欢迎来到 Vibe 探店宇宙")
    st.markdown("请输入你的专属代号进入地图。如果是新代号，将自动为你注册。")
    
    with st.form("login_form"):
        username = st.text_input("我的代号 (如：橘子猫):").strip()
        submit_login = st.form_submit_button("🚀 进入地图")
        
        if submit_login and username:
            # 如果是新用户，自动在数据库中创建他的档案
            if username not in st.session_state.db["users"]:
                st.session_state.db["users"][username] = {"friends": []}
                save_db(st.session_state.db)
                st.success(f"欢迎新朋友 {username}！档案已建立。")
                
            st.session_state.current_user = username
            st.rerun() # 刷新页面，进入主界面
    st.stop() # 停止渲染下方的代码，直到用户登录

# ================= 2. 主界面：侧边栏 (社交功能) =================
me = st.session_state.current_user
my_info = st.session_state.db["users"][me]

with st.sidebar:
    st.write(f"### 👑 你好，{me}！")
    if st.button("🚪 退出登录"):
        st.session_state.current_user = None
        st.rerun()
        
    st.divider()
    
    # --- 加好友功能 ---
    st.write("#### 🤝 添加好友")
    new_friend = st.text_input("输入好友的代号：").strip()
    if st.button("添加"):
        if new_friend == me:
            st.warning("不能添加自己哦！")
        elif new_friend not in st.session_state.db["users"]:
            st.error("找不到这个代号，他/她注册了吗？")
        elif new_friend in my_info["friends"]:
            st.info("你们已经是好友啦！")
        else:
            # 双向添加好友
            my_info["friends"].append(new_friend)
            st.session_state.db["users"][new_friend]["friends"].append(me)
            save_db(st.session_state.db)
            st.success(f"成功添加 {new_friend} 为好友！")
            st.rerun()

    st.divider()
    st.write("#### 📋 我的通讯录")
    if not my_info["friends"]:
        st.write("还没有好友，快去邀请朋友加入吧！")
    else:
        for f in my_info["friends"]:
            st.write(f"👤 {f}")


# ================= 3. 主界面：朋友圈地图 =================
st.title("🗺️ 探店朋友圈")
st.markdown("这里只显示 **你** 和 **你的好友** 打卡过的美食。")

# 核心逻辑：数据权限过滤 (Data Filtering)
# 只挑出作者是我自己，或者作者是我的好友的地点
visible_places = [
    place for place in st.session_state.db["places"]
    if place["author"] == me or place["author"] in my_info["friends"]
]

if len(visible_places) > 0:
    # 地图中心点设为最新可见的一个点
    last_place = visible_places[-1]
    m = folium.Map(location=[last_place['lat'], last_place['lon']], zoom_start=13)

    for place in visible_places:
        img_html = f'<img src="{place["image"]}" width="100%" style="border-radius: 8px; margin-top: 5px;">' if place.get("image") else ""
        
        # 弹窗加入发布者信息
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 200px;">
            <div style="background:#FFE4E1; padding:3px; border-radius:5px; font-size:12px; color:#c0392b; margin-bottom:5px;">
                📢 发布者: {place['author']}
            </div>
            <h4 style="color: #FF4B4B; margin: 0 0 5px 0;">{place['name']}</h4>
            <b>💰 人均:</b> ￥{place['price']}<br>
            <b>⭐ 评分:</b> {'⭐' * int(float(place['taste']))} ({place['taste']})<br>
            <hr style="margin: 8px 0;">
            <p style="font-size: 13px; color: #555;">{place['description']}</p>
            {img_html}
        </div>
        """
        
        # 如果是好友发的，图标变成蓝色；自己发的是红色
        icon_color = 'red' if place['author'] == me else 'blue'
        
        folium.Marker(
            location=[place['lat'], place['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{place['author']} 推荐的 {place['name']}",
            icon=folium.Icon(color=icon_color, icon='info-sign')
        ).add_to(m)

    st_folium(m, width=700, height=500)
else:
    st.info("地图空空如也，你或者你的好友还没发布过探店记录呢！")

st.divider()

# ================= 4. 发布新探店 (自动绑定作者) =================
st.subheader("📝 分享新探店到朋友圈")

with st.form("add_place_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("餐厅名称*", placeholder="例如：老王烧烤")
        lat = st.text_input("纬度 (Lat)*", value="1.2838")
        price = st.number_input("人均价格 (￥)", min_value=0, step=10)
    with col2:
        taste = st.selectbox("味道评分*", ["1", "2", "3", "4", "5"], index=4)
        lon = st.text_input("经度 (Lon)*", value="103.8591")
        
    description = st.text_area("详细测评与心得", placeholder="这家店的环境怎么样？...", height=100)
    uploaded_file = st.file_uploader("上传美食照片 📸", type=["png", "jpg", "jpeg"])
    submitted = st.form_submit_button("💾 发布到朋友圈", use_container_width=True)

    if submitted:
        if not name or not lat or not lon:
            st.error("店名和经纬度是必填的哦！")
        else:
            try:
                img_base64 = get_image_base64(uploaded_file)
                new_record = {
                    "author": me,       # 核心：自动打上当前登录用户的思想钢印
                    "name": name,
                    "lat": float(lat),
                    "lon": float(lon),
                    "price": price,
                    "taste": taste,
                    "description": description,
                    "image": img_base64 
                }
                
                st.session_state.db["places"].append(new_record)
                save_db(st.session_state.db)
                
                st.success(f"发布成功！你的好友现在能在地图上看到【{name}】了！")
                st.rerun() 
            except ValueError:
                st.error("经纬度格式不对，请检查是否输入了纯数字！")
