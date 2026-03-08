import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
import base64
import uuid
import requests  # 新增：网络请求库

# === 核心数据层：接入 JSONBin 云端数据库 ===
# 我们将从 Streamlit 的“安全抽屉”里读取秘钥，防止泄露
BIN_ID = st.secrets["BIN_ID"]
API_KEY = st.secrets["API_KEY"]
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"

HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

def load_db():
    """去云端保险箱拿数据"""
    try:
        response = requests.get(JSONBIN_URL, headers=HEADERS)
        if response.status_code == 200:
            # JSONBin 返回的数据包裹在一个叫 "record" 的壳子里
            return response.json().get("record", {"users": {}, "places": []})
    except Exception as e:
        st.error(f"云端数据库连接失败: {e}")
    # 如果没拿到，返回空的保底数据
    return {"users": {}, "places": []}

def save_db(db):
    """把最新数据存回云端保险箱"""
    try:
        # 使用 PUT 请求覆盖更新整个 JSONBin
        requests.put(JSONBIN_URL, json=db, headers=HEADERS)
    except Exception as e:
        st.error(f"数据保存到云端失败: {e}")

# 👇 处理图片的函数👇
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

# ================= 1. 登录与极简双重验证 =================
if st.session_state.current_user is None:
    st.title("🌍 欢迎来到 Vibe 探店宇宙")
    st.markdown("请输入代号与4位专属ID。")
    st.info("💡 提示：首次输入将自动为你创建档案。添加好友时需提供完整组合（如：橘子猫#8291）。")
    
    with st.form("login_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            username = st.text_input("我的代号", placeholder="如：橘子猫").strip()
        with col2:
            user_id = st.text_input("4位数字ID", max_chars=4, type="password", placeholder="如: 8291").strip()
            
        submit_login = st.form_submit_button("🚀 验证并进入地图")
        
        if submit_login:
            if not username or len(user_id) != 4 or not user_id.isdigit():
                st.error("请输入有效的代号，以及纯4位数字的专属ID哦！")
            else:
                full_identity = f"{username}#{user_id}"
                if full_identity not in st.session_state.db["users"]:
                    st.session_state.db["users"][full_identity] = {"friends": []}
                    save_db(st.session_state.db)
                    st.success(f"欢迎新朋友！你的专属通行证是：{full_identity}")
                
                st.session_state.current_user = full_identity
                st.rerun() 
    st.stop() 

# ================= 2. 侧边栏：社交与通讯录 =================
me = st.session_state.current_user

# 兼容旧数据：确保当前用户有 friends 和 pending_requests 列表
if "pending_requests" not in st.session_state.db["users"][me]:
    st.session_state.db["users"][me]["pending_requests"] = []
if "friends" not in st.session_state.db["users"][me]:
    st.session_state.db["users"][me]["friends"] = []

my_info = st.session_state.db["users"][me]

with st.sidebar:
    st.write(f"### 👑 你好，\n**{me}**")
    if st.button("🚪 退出登录"):
        st.session_state.current_user = None
        st.rerun()
        
    st.divider()
    
    # --- 处理收到的好友申请 ---
    pending = my_info.get("pending_requests", [])
    if pending:
        st.write("#### 🔔 新的好友申请")
        for applicant in pending:
            st.info(f"👤 **{applicant}** 想加你为好友")
            col_y, col_n = st.columns(2)
            with col_y:
                if st.button("同意", key=f"y_{applicant}"):
                    st.session_state.db = load_db() # 强制拿最新数据
                    # 双向添加好友
                    st.session_state.db["users"][me]["friends"].append(applicant)
                    # 确保对方也有 friends 列表
                    if "friends" not in st.session_state.db["users"][applicant]:
                        st.session_state.db["users"][applicant]["friends"] = []
                    st.session_state.db["users"][applicant]["friends"].append(me)
                    # 从申请列表中移除
                    st.session_state.db["users"][me]["pending_requests"].remove(applicant)
                    save_db(st.session_state.db)
                    st.success("已成为好友！")
                    st.rerun()
            with col_n:
                if st.button("拒绝", key=f"n_{applicant}"):
                    st.session_state.db = load_db()
                    st.session_state.db["users"][me]["pending_requests"].remove(applicant)
                    save_db(st.session_state.db)
                    st.rerun()
        st.divider()

    # --- 发送好友申请 ---
    st.write("#### 🤝 添加新朋友")
    st.caption("需提供对方的 代号#4位ID")
    new_friend = st.text_input("输入完整标识 (如 老王#1122)：").strip()
    
    if st.button("发送好友申请"):
        st.session_state.db = load_db() # 强制刷新防时间差
        my_info = st.session_state.db["users"][me] 
        
        if not new_friend or "#" not in new_friend:
            st.warning("格式不对哦，记得加上英文的 # 和 4位数字ID。")
        elif new_friend == me:
            st.warning("不能添加自己哦！")
        elif new_friend not in st.session_state.db["users"]:
            st.error("查无此人！请核对对方的代号和ID。")
        elif new_friend in my_info.get("friends", []):
            st.info("你们已经是好友啦！")
        else:
            # 将自己加入对方的 pending_requests (待处理申请) 列表
            target_user = st.session_state.db["users"][new_friend]
            if "pending_requests" not in target_user:
                target_user["pending_requests"] = []
            
            if me in target_user["pending_requests"]:
                st.info("已经发送过申请啦，请耐心等待对方同意~")
            else:
                target_user["pending_requests"].append(me)
                save_db(st.session_state.db)
                st.success(f"申请已发送给 {new_friend}！")

    st.divider()
    st.write("#### 📋 我的美食搭子")
    if not my_info.get("friends"):
        st.write("还没有好友，快把你的专属标识发给朋友吧！")
    else:
        for f in my_info["friends"]:
            st.write(f"👤 {f}")


# ================= 3. 主界面：朋友圈地图 =================
st.title("🗺️ 探店朋友圈")
st.markdown("这里只显示 **你** 和 **你的好友** 打卡过的美食。")

# 权限过滤：只看自己和好友的
visible_places = [
    place for place in st.session_state.db["places"]
    if place["author"] == me or place["author"] in my_info["friends"]
]

if len(visible_places) > 0:
    last_place = visible_places[-1]
    m = folium.Map(location=[last_place['lat'], last_place['lon']], zoom_start=13)

    for place in visible_places:
        img_html = f'<img src="{place["image"]}" width="100%" style="border-radius: 8px; margin-top: 5px;">' if place.get("image") else ""
        
        # 计算综合评分
        overall_score = round((place['score_taste'] + place['score_env'] + place['score_service'] + place['score_plating'] + place['score_value']) / 5, 1)
        tags_str = " ".join(place.get("tags", []))
        
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 220px;">
            <div style="background:#FFE4E1; padding:3px; border-radius:5px; font-size:12px; color:#c0392b; margin-bottom:5px;">
                📢 发布者: {place['author']}
            </div>
            <h4 style="color: #FF4B4B; margin: 0 0 5px 0;">{place['name']}</h4>
            <span style="font-size:11px; color:gray;">{tags_str}</span><br>
            <b>💰 人均:</b> ￥{place['price']} | <b>🏆 综合:</b> {overall_score}/10<br>
            <hr style="margin: 5px 0;">
            <b style="color:green;">✅ 优点:</b> {place.get('pros', '无')}<br>
            <b style="color:red;">❌ 缺点:</b> {place.get('cons', '无')}<br>
            {img_html}
        </div>
        """
        
        icon_color = 'red' if place['author'] == me else 'blue'
        
        folium.Marker(
            location=[place['lat'], place['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{place['author']} 推荐的 {place['name']}",
            icon=folium.Icon(color=icon_color, icon='info-sign')
        ).add_to(m)

    st_folium(m, width=700, height=500)
else:
    st.info("地图空空如也，快去下方发布第一条记录吧！")

st.divider()
# ================= 3.5 互动区：好友点评与讨论 =================
st.divider()
st.subheader("💬 探店评论区")

if visible_places:
    # 制作一个下拉菜单，让用户选择要评论的餐厅
    place_options = {f"【{p['name']}】 (由 {p['author']} 发布)": p for p in visible_places}
    selected_place_name = st.selectbox("选择你想查看或点评的餐厅：", list(place_options.keys()))
    selected_place = place_options[selected_place_name]
    
    # 展示历史评论
    comments = selected_place.get("comments", [])
    if comments:
        for c in comments:
            # 用气泡的形式展示评论
            st.markdown(f"<div style='background-color:#F0F2F6; padding:10px; border-radius:10px; margin-bottom:10px;'>"
                        f"<span style='color:#FF4B4B; font-weight:bold;'>👤 {c['author']}</span> : {c['content']}</div>", 
                        unsafe_allow_html=True)
    else:
        st.caption("这家店还没有人评论，快来抢沙发！")
        
    # 发表新评论
    with st.form(key=f"comment_form_{selected_place['id']}", clear_on_submit=True):
        new_comment = st.text_input("写下你的点评或回复：", placeholder="比如：这家店的排骨确实绝了！")
        submit_comment = st.form_submit_button("发送评论")
        
        if submit_comment and new_comment.strip():
            st.session_state.db = load_db() # 强制拿最新数据
            # 在数据库中找到这家店，把评论塞进去
            for p in st.session_state.db["places"]:
                if p["id"] == selected_place["id"]:
                    if "comments" not in p:
                        p["comments"] = []
                    p["comments"].append({"author": me, "content": new_comment.strip()})
                    break
            save_db(st.session_state.db)
            st.success("评论发送成功！")
            st.rerun()
# ================= 4. 发布新记录 (五维测评) =================
st.subheader("📝 发布新探店记录")

with st.form("add_place_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("餐厅名称*", placeholder="例如：老王烧烤")
        lat = st.text_input("纬度 (Lat)*", value="1.2838")
    with col2:
        price = st.number_input("人均价格 (￥)", min_value=0, step=10)
        lon = st.text_input("经度 (Lon)*", value="103.8591")
        
    st.markdown("##### 📊 五维精准测评")
    col_a, col_b = st.columns(2)
    with col_a:
        s_taste = st.slider("😋 味道口感", 0.0, 10.0, 7.5, 0.5)
        s_env = st.slider("🛋️ 环境氛围", 0.0, 10.0, 7.5, 0.5)
        s_service = st.slider("💁 服务体验", 0.0, 10.0, 7.5, 0.5)
    with col_b:
        s_plating = st.slider("📸 颜值出片", 0.0, 10.0, 7.5, 0.5)
        s_value = st.slider("💰 性价比", 0.0, 10.0, 7.5, 0.5)

    tags = st.multiselect("🏷️ 场景标签", ["🌹 约会首选", "💼 打工人食堂", "🍻 朋友聚餐", "📷 出片圣地", "🌙 深夜食堂", "💣 绝对避雷"])
    pros = st.text_input("✅ 夸一夸 (最惊艳的一点)", placeholder="例如：肉质很嫩")
    cons = st.text_input("❌ 吐吐槽 (最需要改进的一点)", placeholder="例如：上菜太慢")
    uploaded_file = st.file_uploader("上传美食照片 📸", type=["png", "jpg", "jpeg"])
    
    submitted = st.form_submit_button("💾 锁定誓约，发布记录！", use_container_width=True)

    if submitted:
        if not name or not lat or not lon:
            st.error("店名和经纬度是必填的哦！")
        else:
            try:
                img_base64 = get_image_base64(uploaded_file)
                new_record = {
                    "id": uuid.uuid4().hex,  # 核心：生成不可篡改的唯一ID
                    "author": me,
                    "name": name,
                    "lat": float(lat),
                    "lon": float(lon),
                    "price": price,
                    "score_taste": s_taste,
                    "score_env": s_env,
                    "score_service": s_service,
                    "score_plating": s_plating,
                    "score_value": s_value,
                    "tags": tags,
                    "pros": pros,
                    "cons": cons,
                    "image": img_base64
                }
                
                st.session_state.db["places"].append(new_record)
                save_db(st.session_state.db)
                st.success(f"发布成功！记录已永久铭刻在地图上。")
                st.rerun() 
            except ValueError:
                st.error("经纬度格式不对，请输入纯数字！")

# ================= 5. 编辑模式 (不可删除) =================
st.divider()
st.subheader("✏️ 修正我的探店记录")
st.caption("注：记录一经发布不可删除，但你可以随时更正内容，这是你的信誉誓约。")

# 只过滤出自己发布的帖子
my_own_places = [p for p in st.session_state.db["places"] if p["author"] == me]

if my_own_places:
    # 生成一个选项字典，方便用户通过名字选择，同时带有ID防重名
    options = {f"{p['name']} (记录ID:{p['id'][:4]})": p for p in my_own_places}
    selected_option = st.selectbox("选择要修改的记录：", list(options.keys()))
    
    target_place = options[selected_option]
    
    with st.expander("展开编辑表单", expanded=False):
        with st.form("edit_form"):
            e_name = st.text_input("餐厅名称", value=target_place["name"])
            col1, col2 = st.columns(2)
            with col1:
                e_lat = st.text_input("纬度", value=str(target_place["lat"]))
                e_price = st.number_input("人均价格", value=target_place.get("price", 0), step=10)
            with col2:
                e_lon = st.text_input("经度", value=str(target_place["lon"]))
            
            st.markdown("##### 重新测评")
            e_taste = st.slider("😋 味道", 0.0, 10.0, target_place.get("score_taste", 7.5))
            e_tags = st.multiselect("🏷️ 标签", ["🌹 约会首选", "💼 打工人食堂", "🍻 朋友聚餐", "📷 出片圣地", "🌙 深夜食堂", "💣 绝对避雷"], default=target_place.get("tags", []))
            e_pros = st.text_input("✅ 优点", value=target_place.get("pros", ""))
            e_cons = st.text_input("❌ 缺点", value=target_place.get("cons", ""))
            
            e_img = st.file_uploader("重新上传照片 (不选则保留原图) 📸", type=["png", "jpg", "jpeg"], key=f"img_{target_place['id']}")
            
            update_btn = st.form_submit_button("💾 保存修改")
            
            if update_btn:
                try:
                    # 在数据库中找到对应的记录并更新
                    for p in st.session_state.db["places"]:
                        if p["id"] == target_place["id"]:
                            p["name"] = e_name
                            p["lat"] = float(e_lat)
                            p["lon"] = float(e_lon)
                            p["price"] = e_price
                            p["score_taste"] = e_taste
                            p["tags"] = e_tags
                            p["pros"] = e_pros
                            p["cons"] = e_cons
                            
                            # 如果上传了新图，就覆盖旧图；否则保持不变
                            if e_img is not None:
                                p["image"] = get_image_base64(e_img)
                            break
                            
                    save_db(st.session_state.db)
                    st.success("修改已生效！")
                    st.rerun()
                except ValueError:
                    st.error("坐标必须是数字哦！")
else:
    st.info("你还没有发布过任何记录，下方暂无内容可编辑。")
