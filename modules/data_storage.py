import sqlite3
import json
import os
from datetime import datetime

class DataStorage:
    """数据存储管理类"""
    
    def __init__(self, storage_type="sqlite", db_path=None, json_path=None):
        """
        初始化数据存储管理器
        
        参数:
            storage_type (str): 存储类型，可选 "sqlite" 或 "json"
            db_path (str, optional): SQLite数据库文件路径，如果不提供则使用默认路径
            json_path (str, optional): JSON文件路径，如果不提供则使用默认路径
        """
        self.storage_type = storage_type
        
        # 设置默认路径
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, "data")
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 设置数据库路径
        if not db_path:
            self.db_path = os.path.join(data_dir, "history.db")
        else:
            self.db_path = db_path
            
        # 设置JSON文件路径
        if not json_path:
            self.json_path = os.path.join(data_dir, "history.json")
        else:
            self.json_path = json_path
        
        # 初始化存储
        if storage_type == "sqlite":
            self._init_sqlite()
        elif storage_type == "json":
            self._init_json()
    
    def _init_sqlite(self):
        """初始化SQLite数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建历史记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_content TEXT,
                specified_content TEXT,
                summary TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"初始化SQLite数据库时出错: {str(e)}")
    
    def _init_json(self):
        """初始化JSON文件"""
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w') as f:
                json.dump([], f)
    
    def add_record(self, record):
        """
        添加历史记录
        
        参数:
            record (dict): 记录字典，应包含timestamp、file_name、file_content、specified_content和summary字段
            
        返回:
            bool: 是否成功添加记录
        """
        try:
            # 确保记录包含必要字段
            if 'file_name' not in record or 'summary' not in record:
                print("记录缺少必要字段")
                return False
            
            # 确保记录包含时间戳
            if 'timestamp' not in record:
                record['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 根据存储类型添加记录
            if self.storage_type == "sqlite":
                return self._add_record_sqlite(record)
            elif self.storage_type == "json":
                return self._add_record_json(record)
            
            return False
            
        except Exception as e:
            print(f"添加记录时出错: {str(e)}")
            return False
    
    def _add_record_sqlite(self, record):
        """添加记录到SQLite数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO history (timestamp, file_name, file_content, specified_content, summary)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                record.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                record.get('file_name', ''),
                record.get('file_content', ''),
                record.get('specified_content', ''),
                record.get('summary', '')
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"添加记录到SQLite时出错: {str(e)}")
            return False
    
    def _add_record_json(self, record):
        """添加记录到JSON文件"""
        try:
            # 读取现有记录
            with open(self.json_path, 'r') as f:
                records = json.load(f)
            
            # 添加新记录
            records.append(record)
            
            # 写回文件
            with open(self.json_path, 'w') as f:
                json.dump(records, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"添加记录到JSON时出错: {str(e)}")
            return False
    
    def get_record(self, record_id=None, file_name=None):
        """
        获取单条历史记录
        
        参数:
            record_id (int, optional): 记录ID
            file_name (str, optional): 文件名称
            
        返回:
            dict: 记录字典，如果未找到则返回None
        """
        try:
            if self.storage_type == "sqlite":
                return self._get_record_sqlite(record_id, file_name)
            elif self.storage_type == "json":
                return self._get_record_json(record_id, file_name)
            
            return None
            
        except Exception as e:
            print(f"获取记录时出错: {str(e)}")
            return None
    
    def _get_record_sqlite(self, record_id=None, file_name=None):
        """从SQLite数据库获取记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            cursor = conn.cursor()
            
            if record_id:
                cursor.execute("SELECT * FROM history WHERE id = ?", (record_id,))
            elif file_name:
                cursor.execute("SELECT * FROM history WHERE file_name = ? ORDER BY timestamp DESC LIMIT 1", (file_name,))
            else:
                cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 1")
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            
            return None
            
        except Exception as e:
            print(f"从SQLite获取记录时出错: {str(e)}")
            return None
    
    def _get_record_json(self, record_id=None, file_name=None):
        """从JSON文件获取记录"""
        try:
            # 读取所有记录
            with open(self.json_path, 'r') as f:
                records = json.load(f)
            
            if not records:
                return None
            
            if record_id is not None and record_id < len(records):
                return records[record_id]
            elif file_name:
                # 查找匹配文件名的最新记录
                for record in reversed(records):
                    if record.get('file_name') == file_name:
                        return record
            else:
                # 返回最新记录
                return records[-1]
            
            return None
            
        except Exception as e:
            print(f"从JSON获取记录时出错: {str(e)}")
            return None
    
    def get_all_records(self, limit=None):
        """
        获取所有历史记录
        
        参数:
            limit (int, optional): 限制返回的记录数量
            
        返回:
            list: 记录列表
        """
        try:
            if self.storage_type == "sqlite":
                return self._get_all_records_sqlite(limit)
            elif self.storage_type == "json":
                return self._get_all_records_json(limit)
            
            return []
            
        except Exception as e:
            print(f"获取所有记录时出错: {str(e)}")
            return []
    
    def _get_all_records_sqlite(self, limit=None):
        """从SQLite数据库获取所有记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if limit:
                cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"从SQLite获取所有记录时出错: {str(e)}")
            return []
    
    def _get_all_records_json(self, limit=None):
        """从JSON文件获取所有记录"""
        try:
            # 读取所有记录
            with open(self.json_path, 'r') as f:
                records = json.load(f)
            
            # 按时间戳排序（假设记录中有timestamp字段）
            records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            if limit:
                return records[:limit]
            else:
                return records
            
        except Exception as e:
            print(f"从JSON获取所有记录时出错: {str(e)}")
            return []
    
    def delete_record(self, record_id):
        """
        删除历史记录
        
        参数:
            record_id (int): 记录ID
            
        返回:
            bool: 是否成功删除记录
        """
        try:
            if self.storage_type == "sqlite":
                return self._delete_record_sqlite(record_id)
            elif self.storage_type == "json":
                return self._delete_record_json(record_id)
            
            return False
            
        except Exception as e:
            print(f"删除记录时出错: {str(e)}")
            return False
    
    def _delete_record_sqlite(self, record_id):
        """从SQLite数据库删除记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM history WHERE id = ?", (record_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"从SQLite删除记录时出错: {str(e)}")
            return False
    
    def _delete_record_json(self, record_id):
        """从JSON文件删除记录"""
        try:
            # 读取所有记录
            with open(self.json_path, 'r') as f:
                records = json.load(f)
            
            if record_id < 0 or record_id >= len(records):
                return False
            
            # 删除指定记录
            records.pop(record_id)
            
            # 写回文件
            with open(self.json_path, 'w') as f:
                json.dump(records, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"从JSON删除记录时出错: {str(e)}")
            return False
    
    def export_records(self, output_format="json", output_path=None):
        """
        导出历史记录
        
        参数:
            output_format (str): 输出格式，可选 "json" 或 "csv"
            output_path (str, optional): 输出文件路径，如果不提供则使用默认路径
            
        返回:
            str: 导出文件路径，如果导出失败则返回None
        """
        try:
            # 获取所有记录
            records = self.get_all_records()
            
            if not records:
                print("没有记录可导出")
                return None
            
            # 确定输出路径
            if not output_path:
                base_dir = os.path.dirname(os.path.dirname(__file__))
                data_dir = os.path.join(base_dir, "data")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                
                if output_format == "json":
                    output_path = os.path.join(data_dir, f"export_{timestamp}.json")
                elif output_format == "csv":
                    output_path = os.path.join(data_dir, f"export_{timestamp}.csv")
            
            # 导出记录
            if output_format == "json":
                with open(output_path, 'w') as f:
                    json.dump(records, f, indent=2)
                return output_path
            elif output_format == "csv":
                import csv
                
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # 写入表头
                    if records:
                        writer.writerow(records[0].keys())
                        
                        # 写入数据行
                        for record in records:
                            writer.writerow(record.values())
                
                return output_path
            
            return None
            
        except Exception as e:
            print(f"导出记录时出错: {str(e)}")
            return None
