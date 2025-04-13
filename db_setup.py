import os
import sqlite3
import json
from datetime import datetime

def init_database():
    """初始化数据库，创建必要的表"""
    # 确保数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 用户数据库
    users_db_path = os.path.join(data_dir, "users.db")
    conn_users = sqlite3.connect(users_db_path)
    cursor_users = conn_users.cursor()
    
    # 创建用户表
    cursor_users.execute('''
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
    
    # 创建管理员用户（如果不存在）
    cursor_users.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor_users.fetchone():
        # 使用简单的哈希方法，实际应用中应使用更安全的方法
        import hmac
        admin_password_hash = hmac.new(b"streamlit-secret-key", b"admin", "sha256").hexdigest()
        cursor_users.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            ("admin", admin_password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    conn_users.commit()
    conn_users.close()
    
    # 创建用户数据目录
    users_data_dir = os.path.join(data_dir, "users")
    if not os.path.exists(users_data_dir):
        os.makedirs(users_data_dir)
    
    print("数据库初始化完成")

def create_user_database(username):
    """为用户创建专用数据库"""
    # 确保用户数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    user_data_dir = os.path.join(data_dir, "users", username)
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    
    # 创建用户历史记录数据库
    db_path = os.path.join(user_data_dir, "history.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建历史记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_content TEXT,
        specified_content TEXT,
        summary TEXT NOT NULL,
        api_type TEXT,
        username TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # 创建用户文件目录
    user_files_dir = os.path.join(user_data_dir, "files")
    if not os.path.exists(user_files_dir):
        os.makedirs(user_files_dir)
    
    print(f"用户 {username} 的数据库初始化完成")

def backup_database():
    """备份所有数据库"""
    # 确保备份目录存在
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 当前时间戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 备份用户数据库
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    users_db_path = os.path.join(data_dir, "users.db")
    
    if os.path.exists(users_db_path):
        import shutil
        backup_path = os.path.join(backup_dir, f"users_{timestamp}.db")
        shutil.copy2(users_db_path, backup_path)
        print(f"用户数据库已备份到 {backup_path}")
    
    # 备份用户历史记录数据库
    users_data_dir = os.path.join(data_dir, "users")
    if os.path.exists(users_data_dir):
        for username in os.listdir(users_data_dir):
            user_db_path = os.path.join(users_data_dir, username, "history.db")
            if os.path.exists(user_db_path):
                import shutil
                user_backup_dir = os.path.join(backup_dir, username)
                if not os.path.exists(user_backup_dir):
                    os.makedirs(user_backup_dir)
                backup_path = os.path.join(user_backup_dir, f"history_{timestamp}.db")
                shutil.copy2(user_db_path, backup_path)
                print(f"用户 {username} 的历史记录数据库已备份到 {backup_path}")
    
    print("数据库备份完成")

if __name__ == "__main__":
    # 初始化数据库
    init_database()
    
    # 创建管理员用户数据库
    create_user_database("admin")
    
    # 备份数据库（可选）
    # backup_database()
