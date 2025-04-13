import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime
import hmac
import sqlite3
import json
import uuid
import base64
from pathlib import Path

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 用户认证相关函数
def check_password():
    """检查用户是否已登录或密码是否正确"""
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    
    if st.session_state["authentication_status"]:
        return True
    
    # 创建登录表单
    login_form = st.form("登录")
    username = login_form.text_input("用户名")
    password = login_form.text_input("密码", type="password")
    login_submit = login_form.form_submit_button("登录")
    
    # 创建注册链接
    if login_form.markdown("[没有账号？点击注册](javascript:void(0))", unsafe_allow_html=True):
        st.session_state["show_register"] = True
    
    # 处理注册表单
    if "show_register" in st.session_state and st.session_state["show_register"]:
        register_form = st.form("注册")
        new_username = register_form.text_input("新用户名")
        new_password = register_form.text_input("新密码", type="password")
        confirm_password = register_form.text_input("确认密码", type="password")
        register_submit = register_form.form_submit_button("注册")
        
        if register_submit:
            if new_password != confirm_password:
                st.error("两次输入的密码不一致")
            elif not new_username or not new_password:
                st.error("用户名和密码不能为空")
            else:
                # 检查用户是否已存在
                if user_exists(new_username):
                    st.error("用户名已存在")
                else:
                    # 创建新用户
                    if create_user(new_username, new_password):
                        st.success("注册成功，请登录")
                        st.session_state["show_register"] = False
                    else:
                        st.error("注册失败，请重试")
    
    # 处理登录
    if login_submit:
        if not username or not password:
            st.error("请输入用户名和密码")
        elif verify_user(username, password):
            st.session_state["authentication_status"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("用户名或密码错误")
    
    return False

def user_exists(username):
    """检查用户是否存在"""
    conn = get_user_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def create_user(username, password):
    """创建新用户"""
    try:
        conn = get_user_db_connection()
        cursor = conn.cursor()
        # 生成密码哈希
        password_hash = generate_password_hash(password)
        # 插入新用户
        cursor.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"创建用户时出错: {str(e)}")
        return False

def verify_user(username, password):
    """验证用户密码"""
    conn = get_user_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        stored_password_hash = result[0]
        return verify_password_hash(stored_password_hash, password)
    
    return False

def generate_password_hash(password):
    """生成密码哈希"""
    # 在实际应用中应使用更安全的方法，如bcrypt
    return hmac.new(b"streamlit-secret-key", password.encode(), "sha256").hexdigest()

def verify_password_hash(stored_hash, password):
    """验证密码哈希"""
    generated_hash = generate_password_hash(password)
    return hmac.compare_digest(stored_hash, generated_hash)

def get_user_db_connection():
    """获取用户数据库连接"""
    # 确保数据目录存在
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 连接数据库
    db_path = os.path.join(data_dir, "users.db")
    conn = sqlite3.connect(db_path)
    
    # 创建用户表（如果不存在）
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        api_key_openai TEXT,
        api_key_gemini TEXT,
        custom_endpoint TEXT
    )
    ''')
    conn.commit()
    
    return conn

def save_user_api_keys(username, api_key_openai=None, api_key_gemini=None, custom_endpoint=None):
    """保存用户的API密钥"""
    try:
        conn = get_user_db_connection()
        cursor = conn.cursor()
        
        # 更新API密钥
        update_fields = []
        params = []
        
        if api_key_openai is not None:
            update_fields.append("api_key_openai = ?")
            params.append(api_key_openai)
        
        if api_key_gemini is not None:
            update_fields.append("api_key_gemini = ?")
            params.append(api_key_gemini)
        
        if custom_endpoint is not None:
            update_fields.append("custom_endpoint = ?")
            params.append(custom_endpoint)
        
        if update_fields:
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = ?"
            params.append(username)
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        print(f"保存API密钥时出错: {str(e)}")
        return False

def get_user_api_keys(username):
    """获取用户的API密钥"""
    try:
        conn = get_user_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT api_key_openai, api_key_gemini, custom_endpoint FROM users WHERE username = ?", 
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "api_key_openai": result[0] or "",
                "api_key_gemini": result[1] or "",
                "custom_endpoint": result[2] or ""
            }
        
        return {"api_key_openai": "", "api_key_gemini": "", "custom_endpoint": ""}
    except Exception as e:
        print(f"获取API密钥时出错: {str(e)}")
        return {"api_key_openai": "", "api_key_gemini": "", "custom_endpoint": ""}

def get_user_specific_data_path(username, filename=None):
    """获取用户特定的数据路径"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    user_data_dir = os.path.join(base_dir, "data", "users", username)
    
    # 确保用户数据目录存在
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    
    if filename:
        return os.path.join(user_data_dir, filename)
    
    return user_data_dir

# 导入自定义模块
from modules.file_parser import DocxParser, PdfParser
from modules.ai_summary import SummaryFactory
from modules.word_template import WordTemplate
from modules.data_storage import DataStorage

# 设置页面配置
st.set_page_config(
    page_title="文件处理平台",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 检查用户是否已登录
if check_password():
    # 用户已登录，显示主应用
    username = st.session_state["username"]
    
    # 初始化会话状态
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'current_summary' not in st.session_state:
        st.session_state.current_summary = ""
    if 'current_file_content' not in st.session_state:
        st.session_state.current_file_content = ""
    if 'current_file_name' not in st.session_state:
        st.session_state.current_file_name = ""
    
    # 获取用户特定的数据存储路径
    user_db_path = get_user_specific_data_path(username, "history.db")
    
    # 初始化数据存储
    data_storage = DataStorage(db_path=user_db_path)
    
    # 页面标题
    st.title("文件处理平台")
    st.markdown(f"欢迎, {username}! 上传Word或PDF文件，提取内容并使用AI进行总结")
    
    # 添加退出按钮
    if st.sidebar.button("退出登录"):
        st.session_state["authentication_status"] = False
        st.rerun()
    
    # 侧边栏 - 配置区域
    with st.sidebar:
        st.header("配置")
        
        # 获取用户的API密钥
        user_api_keys = get_user_api_keys(username)
        
        # API类型选择
        api_type = st.selectbox(
            "选择AI API类型",
            ["OpenAI", "Google Gemini"],
            index=0
        )
        
        # 根据API类型显示相应的配置选项
        if api_type == "OpenAI":
            # OpenAI API配置
            api_key = st.text_input(
                "OpenAI API密钥", 
                type="password",
                value=user_api_keys["api_key_openai"]
            )
            
            # 添加模型选择
            openai_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "自定义模型"]
            selected_model = st.selectbox(
                "选择模型",
                openai_models,
                index=0
            )
            
            # 如果选择自定义模型，显示输入框
            custom_model = None
            if selected_model == "自定义模型":
                custom_model = st.text_input("输入自定义模型名称", value="gpt-3.5-turbo")
                selected_model = custom_model
            
            # 自定义endpoint
            use_custom_endpoint = st.checkbox("使用自定义Endpoint")
            endpoint = None
            if use_custom_endpoint:
                endpoint = st.text_input(
                    "自定义Endpoint URL", 
                    value=user_api_keys["custom_endpoint"] or "https://api.openai.com/v1/chat/completions"
                )
            
            # 保存API密钥
            if api_key != user_api_keys["api_key_openai"] or (use_custom_endpoint and endpoint != user_api_keys["custom_endpoint"]):
                save_user_api_keys(
                    username, 
                    api_key_openai=api_key, 
                    custom_endpoint=endpoint if use_custom_endpoint else None
                )
                st.success("API配置已保存")
            
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
                
            # 保存选择的模型到会话状态
            st.session_state["selected_model"] = selected_model
        else:
            # Google Gemini API配置
            api_key = st.text_input(
                "Google Gemini API密钥", 
                type="password",
                value=user_api_keys["api_key_gemini"]
            )
            
            # 保存API密钥
            if api_key != user_api_keys["api_key_gemini"]:
                save_user_api_keys(username, api_key_gemini=api_key)
                st.success("API配置已保存")
            
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key
            
            endpoint = None  # Gemini不支持自定义endpoint
        
        # 模板选择
        template_file = st.selectbox(
            "选择Word模板",
            ["默认模板", "自定义模板"],
            index=0
        )
        
        # 历史记录
        st.header("历史记录")
        history_records = data_storage.get_all_records()
        if history_records:
            for record in history_records:
                st.write(f"{record['timestamp']} - {record['file_name']}")
    
    # 主界面 - 文件上传和处理区域
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("文件上传")
        
        # 文件上传
        uploaded_file = st.file_uploader("选择Word或PDF文件", type=["docx", "pdf"])
        
        if uploaded_file is not None:
            # 保存上传的文件到用户特定目录
            user_file_dir = get_user_specific_data_path(username, "files")
            if not os.path.exists(user_file_dir):
                os.makedirs(user_file_dir)
            
            file_path = os.path.join(user_file_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"文件 '{uploaded_file.name}' 上传成功!")
            
            # 文件解析
            file_content = ""
            if uploaded_file.name.endswith('.docx'):
                parser = DocxParser(file_path)
                file_content = parser.extract_content()
            elif uploaded_file.name.endswith('.pdf'):
                parser = PdfParser(file_path)
                file_content = parser.extract_content()
            
            # 更新会话状态
            st.session_state.current_file_content = file_content
            st.session_state.current_file_name = uploaded_file.name
            
            # 显示文件内容
            st.subheader("文件内容")
            st.text_area("提取的内容", file_content, height=300, disabled=True)
        
        # 指定章节输入
        st.subheader("指定章节或关键内容")
        specified_content = st.text_area("输入需要特别关注的章节或内容描述", height=100)
        
        # 处理按钮
        if st.button("处理文件"):
            if not st.session_state.current_file_content:
                st.error("请先上传文件!")
            elif not api_key:
                api_name = "OpenAI" if api_type == "OpenAI" else "Google Gemini"
                st.error(f"请输入{api_name} API密钥!")
            else:
                with st.spinner("正在处理..."):
                    # 根据选择的API类型创建相应的总结类
                    api_type_lower = "openai" if api_type == "OpenAI" else "gemini"
                    
                    # 获取选定的模型（如果是OpenAI）
                    selected_model = None
                    if api_type == "OpenAI" and "selected_model" in st.session_state:
                        selected_model = st.session_state["selected_model"]
                    
                    ai_summary = SummaryFactory.create_summary(api_type_lower, api_key, endpoint, selected_model)
                    
                    # 调用AI总结
                    summary_result = ai_summary.generate_summary(
                        st.session_state.current_file_content,
                        specified_content
                    )
                    
                    # 更新会话状态
                    st.session_state.current_summary = summary_result
                    
                    # 保存到历史记录
                    record = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "file_name": st.session_state.current_file_name,
                        "file_content": st.session_state.current_file_content,
                        "specified_content": specified_content,
                        "summary": summary_result,
                        "api_type": api_type,
                        "username": username
                    }
                    data_storage.add_record(record)
                    st.session_state.history.append(record)
                    
                    # 更新Word模板
                    word_template = WordTemplate()
                    output_file = word_template.fill_template(
                        st.session_state.current_file_name,
                        specified_content,
                        summary_result
                    )
                    
                    st.success("处理完成!")
    
    with col2:
        st.header("AI总结结果")
        
        # 显示当前总结
        if st.session_state.current_summary:
            st.text_area("AI总结内容", st.session_state.current_summary, height=300, disabled=True)
            
            # 提供下载链接
            if 'output_file' in locals():
                with open(output_file, "rb") as file:
                    st.download_button(
                        label="下载Word文档",
                        data=file,
                        file_name=f"总结_{st.session_state.current_file_name}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        else:
            st.info("上传并处理文件后，AI总结将显示在这里")
        
        # 历史记录
        st.subheader("最近处理记录")
        if st.session_state.history:
            for i, record in enumerate(reversed(st.session_state.history[-5:])):
                with st.expander(f"{record['timestamp']} - {record['file_name']}"):
                    st.write(f"API类型: {record.get('api_type', '未指定')}")
                    st.write(f"指定内容: {record['specified_content']}")
                    st.write(f"总结: {record['summary']}")
    
    # 页脚
    st.markdown("---")
    st.markdown("© 2025 文件处理平台 | 支持OpenAI和Google Gemini API")
