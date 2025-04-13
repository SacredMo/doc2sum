import os
import json
import requests
from typing import Optional, Dict, Any, List, Union

class BaseSummary:
    """基础AI总结类，定义通用接口"""
    
    def generate_summary(self, content: str, specified_content: Optional[str] = None, max_tokens: int = 1000) -> str:
        """
        生成内容总结
        
        参数:
            content (str): 需要总结的文本内容
            specified_content (str, optional): 指定的章节或关键内容描述
            max_tokens (int, optional): 生成摘要的最大长度
            
        返回:
            str: 生成的摘要内容
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def generate_structured_summary(self, content: str, sections: Optional[List[str]] = None) -> Dict[str, str]:
        """
        生成结构化总结
        
        参数:
            content (str): 需要总结的文本内容
            sections (list, optional): 需要包含在总结中的章节列表，例如["背景", "主要发现", "结论"]
            
        返回:
            dict: 结构化的总结内容
        """
        raise NotImplementedError("子类必须实现此方法")


class OpenAISummary(BaseSummary):
    """OpenAI API内容总结类"""
    
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, model: Optional[str] = None):
        """
        初始化OpenAI API客户端
        
        参数:
            api_key (str, optional): OpenAI API密钥，如果不提供则尝试从环境变量获取
            endpoint (str, optional): 自定义API端点，如果不提供则使用默认端点
            model (str, optional): 使用的模型名称，如果不提供则使用默认模型
        """
        # 如果没有提供API密钥，尝试从环境变量获取
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            
        if not api_key:
            raise ValueError("未提供OpenAI API密钥，请通过参数传入或设置OPENAI_API_KEY环境变量")
        
        self.api_key = api_key
        
        # 设置API端点
        self.endpoint = endpoint or "https://api.openai.com/v1/chat/completions"
        
        # 设置模型
        self.model = model or "gpt-3.5-turbo"
    
    def generate_summary(self, content: str, specified_content: Optional[str] = None, max_tokens: int = 1000) -> str:
        """
        生成内容总结
        
        参数:
            content (str): 需要总结的文本内容
            specified_content (str, optional): 指定的章节或关键内容描述
            max_tokens (int, optional): 生成摘要的最大长度
            
        返回:
            str: 生成的摘要内容
        """
        try:
            # 构建提示词
            if specified_content:
                system_prompt = "你是一个专业的文档总结助手，擅长提取文本的关键信息并生成简洁明了的总结。"
                user_prompt = f"""请对以下文本内容进行总结，特别关注这些方面：{specified_content}
                
文本内容：
{content}

请提供一个全面但简洁的总结，突出文本的主要观点和关键信息，特别是与指定内容相关的部分。
总结应该保持客观，不添加原文中没有的信息。"""
            else:
                system_prompt = "你是一个专业的文档总结助手，擅长提取文本的关键信息并生成简洁明了的总结。"
                user_prompt = f"""请对以下文本内容进行总结：
                
文本内容：
{content}

请提供一个全面但简洁的总结，突出文本的主要观点和关键信息。
总结应该保持客观，不添加原文中没有的信息。"""
            
            # 构建API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens
            }
            
            # 发送API请求
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=json.dumps(data)
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 提取生成的内容
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "API返回结果格式异常，未能提取到总结内容。"
            
        except requests.exceptions.RequestException as e:
            return f"API请求错误: {str(e)}"
        except ValueError as e:
            return f"JSON解析错误: {str(e)}"
        except Exception as e:
            return f"生成摘要时出错: {str(e)}"
    
    def generate_structured_summary(self, content: str, sections: Optional[List[str]] = None) -> Dict[str, str]:
        """
        生成结构化总结
        
        参数:
            content (str): 需要总结的文本内容
            sections (list, optional): 需要包含在总结中的章节列表，例如["背景", "主要发现", "结论"]
            
        返回:
            dict: 结构化的总结内容
        """
        try:
            # 默认章节
            if not sections:
                sections = ["背景", "主要内容", "关键点", "结论"]
            
            # 构建提示词
            sections_str = "、".join(sections)
            system_prompt = "你是一个专业的文档总结助手，擅长提取文本的关键信息并生成结构化的总结。"
            user_prompt = f"""请对以下文本内容进行结构化总结，包含以下章节：{sections_str}
            
文本内容：
{content}

请为每个章节提供简洁但全面的总结，突出文本的主要观点和关键信息。
总结应该保持客观，不添加原文中没有的信息。
请以JSON格式返回结果，每个章节作为一个键。格式如下：
{{
  "章节1": "章节1的总结内容",
  "章节2": "章节2的总结内容",
  ...
}}"""
            
            # 构建API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            
            # 发送API请求
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=json.dumps(data)
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 提取生成的内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"].strip()
                try:
                    # 尝试解析JSON
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试手动解析
                    result_dict = {}
                    for section in sections:
                        if section in content:
                            # 查找章节标题
                            start_idx = content.find(f'"{section}"')
                            if start_idx != -1:
                                # 查找冒号后的内容
                                colon_idx = content.find(':', start_idx)
                                if colon_idx != -1:
                                    # 查找下一个逗号或大括号
                                    end_idx = content.find(',', colon_idx)
                                    if end_idx == -1:
                                        end_idx = content.find('}', colon_idx)
                                    
                                    if end_idx != -1:
                                        # 提取内容
                                        section_content = content[colon_idx+1:end_idx].strip()
                                        # 去除引号
                                        if section_content.startswith('"') and section_content.endswith('"'):
                                            section_content = section_content[1:-1]
                                        result_dict[section] = section_content
                    
                    return result_dict if result_dict else {"错误": "无法解析API返回的JSON结果"}
            else:
                return {"错误": "API返回结果格式异常，未能提取到总结内容。"}
            
        except requests.exceptions.RequestException as e:
            return {"错误": f"API请求错误: {str(e)}"}
        except ValueError as e:
            return {"错误": f"JSON解析错误: {str(e)}"}
        except Exception as e:
            return {"错误": f"生成结构化摘要时出错: {str(e)}"}


# 保留原有的GeminiSummary类，但让它继承BaseSummary
import google.generativeai as genai

class GeminiSummary(BaseSummary):
    """Google Gemini API内容总结类"""
    
    def __init__(self, api_key=None):
        """
        初始化Gemini API客户端
        
        参数:
            api_key (str, optional): Google Gemini API密钥，如果不提供则尝试从环境变量获取
        """
        # 如果没有提供API密钥，尝试从环境变量获取
        if not api_key:
            api_key = os.environ.get("GOOGLE_API_KEY")
            
        if not api_key:
            raise ValueError("未提供Google Gemini API密钥，请通过参数传入或设置GOOGLE_API_KEY环境变量")
            
        # 配置API
        genai.configure(api_key=api_key)
        
        # 获取模型
        self.model = genai.GenerativeModel('gemini-pro')
        
    def generate_summary(self, content, specified_content=None, max_tokens=1000):
        """
        生成内容总结
        
        参数:
            content (str): 需要总结的文本内容
            specified_content (str, optional): 指定的章节或关键内容描述
            max_tokens (int, optional): 生成摘要的最大长度
            
        返回:
            str: 生成的摘要内容
        """
        try:
            # 构建提示词
            if specified_content:
                prompt = f"""
                请对以下文本内容进行总结，特别关注这些方面：{specified_content}
                
                文本内容：
                {content}
                
                请提供一个全面但简洁的总结，突出文本的主要观点和关键信息，特别是与指定内容相关的部分。
                总结应该保持客观，不添加原文中没有的信息。
                """
            else:
                prompt = f"""
                请对以下文本内容进行总结：
                
                文本内容：
                {content}
                
                请提供一个全面但简洁的总结，突出文本的主要观点和关键信息。
                总结应该保持客观，不添加原文中没有的信息。
                """
            
            # 调用API生成摘要
            response = self.model.generate_content(prompt)
            
            # 返回生成的摘要
            return response.text
            
        except Exception as e:
            return f"生成摘要时出错: {str(e)}"
    
    def generate_structured_summary(self, content, sections=None):
        """
        生成结构化总结
        
        参数:
            content (str): 需要总结的文本内容
            sections (list, optional): 需要包含在总结中的章节列表，例如["背景", "主要发现", "结论"]
            
        返回:
            dict: 结构化的总结内容
        """
        try:
            # 默认章节
            if not sections:
                sections = ["背景", "主要内容", "关键点", "结论"]
            
            # 构建提示词
            sections_str = "、".join(sections)
            prompt = f"""
            请对以下文本内容进行结构化总结，包含以下章节：{sections_str}
            
            文本内容：
            {content}
            
            请为每个章节提供简洁但全面的总结，突出文本的主要观点和关键信息。
            总结应该保持客观，不添加原文中没有的信息。
            请以JSON格式返回结果，每个章节作为一个键。
            """
            
            # 调用API生成结构化摘要
            response = self.model.generate_content(prompt)
            
            # 解析结果
            # 注意：这里假设API返回的是格式化的JSON字符串，实际使用时可能需要额外处理
            result = {}
            response_text = response.text
            
            # 简单解析返回的文本，提取各章节内容
            for section in sections:
                if section in response_text:
                    # 查找章节标题
                    start_idx = response_text.find(f"{section}")
                    if start_idx != -1:
                        # 查找下一个章节或结尾
                        next_section_idx = float('inf')
                        for next_section in sections:
                            if next_section != section:
                                temp_idx = response_text.find(f"{next_section}", start_idx + len(section))
                                if temp_idx != -1 and temp_idx < next_section_idx:
                                    next_section_idx = temp_idx
                        
                        if next_section_idx == float('inf'):
                            section_content = response_text[start_idx + len(section):].strip()
                        else:
                            section_content = response_text[start_idx + len(section):next_section_idx].strip()
                        
                        # 清理内容
                        section_content = section_content.strip(":\n -")
                        result[section] = section_content
            
            return result
            
        except Exception as e:
            return {"错误": f"生成结构化摘要时出错: {str(e)}"}


# 工厂类，用于创建不同的AI总结实例
class SummaryFactory:
    """AI总结工厂类，用于创建不同的AI总结实例"""
    
    @staticmethod
    def create_summary(api_type: str, api_key: Optional[str] = None, endpoint: Optional[str] = None, model: Optional[str] = None) -> BaseSummary:
        """
        创建AI总结实例
        
        参数:
            api_type (str): API类型，可选 "openai" 或 "gemini"
            api_key (str, optional): API密钥
            endpoint (str, optional): 自定义API端点（仅OpenAI支持）
            model (str, optional): 模型名称（仅OpenAI支持）
            
        返回:
            BaseSummary: AI总结实例
        """
        if api_type.lower() == "openai":
            return OpenAISummary(api_key, endpoint, model)
        elif api_type.lower() == "gemini":
            return GeminiSummary(api_key)
        else:
            raise ValueError(f"不支持的API类型: {api_type}，请选择 'openai' 或 'gemini'")
