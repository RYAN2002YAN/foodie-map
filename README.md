# foodie-map
# 🌍 Vibe 探店朋友圈 (Foodie Map)

> 拒绝繁杂的公众点评，用几十行 Python 代码，构建属于你和好朋友的私密美食地图。

这是一个基于 Python + Streamlit 构建的轻量级、响应式 Web 应用。它不仅是一个可以记录经纬度、图片和评价的美食手记，更是一个带有**极简双重认证**和**私密社交过滤**功能的“专属朋友圈”。感谢Gemini！！！

## ✨ 核心功能 (Features)

* **🔐 极简双重认证 (Name#ID)**：无需复杂的注册流程，输入「代号 + 4位数字ID」即刻生成你的专属通行证（例：`橘子猫#8291`），天然防撞库。
* **🤝 私密通讯录**：通过精准匹配标识添加好友。地图上的坐标**仅你与你的好友可见**，打造真正的私域美食圈。
* **📊 五维精准测评**：摒弃模糊的综合打分，引入“味道、环境、服务、出片、性价比”五维雷达评分，配合“红黑榜”强制总结，拒绝流水账。
* **☁️ 云端永久记忆**：接入 JSONBin 轻量级云数据库，图片转 Base64 存储，数据实时同步，永不丢失。
* **✏️ 誓约编辑模式**：记录一经发布不可删除（作为吃货的誓约），但支持随时更正错别字或坐标。

---

## 🚀 零基础部署教程 (Deployment Guide)

无需购买服务器，任何人都可以通过以下 3 步免费拥有自己的探店地图！

### Step 1: 准备云端数据库 (JSONBin)
1. 访问 [JSONBin.io](https://jsonbin.io/) 免费注册账号。
2. 点击 `+ Create New`，在编辑框内粘贴以下初始代码并点击 Save：
   ```json
   {
     "users": {},
     "places": []
   }
3.保存后，复制网页链接中生成的随机字符，这就是你的 Bin ID。
4.去左侧菜单栏找到 API Keys，复制你的 Master Key (即 API Key)。

### Step 2: 准备 GitHub 仓库
1.Fork 本仓库，或者新建一个公开仓库。
2.确保你的仓库里有这 2 个文件：
   app.py
   requirements.txt(内容必须包含：streamlit, folium, streamlit-folium, requests)

### Step 3: 准备上传Streamlit Cloud
1.访问 Streamlit Community Cloud 并用 GitHub 登录。
2.点击 New app，选择你的刚刚准备好的代码仓库，Main file path 填写 app.py。
3.关键一步：在点击 Deploy 之前，点击页面上的 Advanced settings (或者部署后进入 Settings -> Secrets)。
4.在 Secrets 文本框中填入你第一步拿到的两把钥匙：
   BIN_ID = "你的_Bin_ID"
   API_KEY = "你的_Master_Key"
