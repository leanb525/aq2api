import json
import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Generator

import requests
import urllib3
from flask import Flask, request, jsonify, Response

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载配置
def load_config() -> Dict:
    """加载配置文件"""
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {
        "logging": {
            "enabled": True,
            "level": "INFO",
            "log_requests": True,
            "log_responses": True,
            "log_token_refresh": True,
            "max_log_length": 500
        },
        "performance": {
            "stream_chunk_size": 1024,
            "buffer_max_size": 10240,
            "token_refresh_margin_seconds": 300
        }
    }

CONFIG = load_config()

# 配置日志
log_config = CONFIG.get("logging", {})
if log_config.get("enabled", True):
    logging.basicConfig(
        level=getattr(logging, log_config.get("level", "INFO")),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Amazon Q 配置
AMAZONQ_ENDPOINT = "https://codewhisperer.us-east-1.amazonaws.com"
SSO_OIDC_ENDPOINT = "https://oidc.us-east-1.amazonaws.com"

# 性能配置
STREAM_CHUNK_SIZE = CONFIG.get("performance", {}).get("stream_chunk_size", 1024)
BUFFER_MAX_SIZE = CONFIG.get("performance", {}).get("buffer_max_size", 10240)
TOKEN_REFRESH_MARGIN = CONFIG.get("performance", {}).get("token_refresh_margin_seconds", 300)


class AmazonQAuthManager:
    """Amazon Q OAuth 认证管理器"""

    def __init__(self, credentials_path: str = "amazonq_credentials.json"):
        self.credentials_path = credentials_path
        self.access_token = None
        self.token_expiry = None
        self.credentials = self._load_credentials()
        # 初始化时直接加载 access_token
        if self.credentials.get('access_token'):
            self.access_token = self.credentials['access_token']
            if log_config.get("log_token_refresh", True):
                logger.info(f"✓ 从配置文件加载 access_token (长度: {len(self.access_token)})")

    def _load_credentials(self) -> Dict:
        """加载凭证"""
        if os.path.exists(self.credentials_path):
            with open(self.credentials_path, 'r') as f:
                return json.load(f)
        return {}

    def set_credentials(self, credentials: Dict):
        """设置凭证"""
        self.credentials = credentials
        # 保存到文件
        with open(self.credentials_path, 'w') as f:
            json.dump(credentials, f, indent=2)
        logger.info("凭证已保存")

    def _extract_token_from_cli_db(self) -> bool:
        """从 Amazon Q CLI 数据库提取最新 token"""
        try:
            from pathlib import Path
            db_path = Path.home() / ".local/share/amazon-q/data.sqlite3"

            if not db_path.exists():
                logger.error(f"Amazon Q CLI 数据库未找到: {db_path}")
                return False

            if log_config.get("log_token_refresh", True):
                logger.info("尝试从 Amazon Q CLI 数据库提取最新 token...")
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 提取 token 信息
            cursor.execute(
                "SELECT value FROM auth_kv WHERE key = 'codewhisperer:odic:token'"
            )
            token_row = cursor.fetchone()

            if token_row:
                token_data = json.loads(token_row[0])
                new_access_token = token_data.get('access_token')

                if new_access_token:
                    self.access_token = new_access_token
                    self.credentials['access_token'] = new_access_token

                    # 更新 refresh_token（如果有）
                    if token_data.get('refresh_token'):
                        self.credentials['refresh_token'] = token_data['refresh_token']

                    # 保存到文件
                    with open(self.credentials_path, 'w') as f:
                        json.dump(self.credentials, f, indent=2)

                    if log_config.get("log_token_refresh", True):
                        logger.info(f"✓ 从 CLI 数据库提取 token 成功，长度: {len(new_access_token)}")
                    conn.close()
                    return True

            conn.close()
            return False

        except Exception as e:
            logger.error(f"从 CLI 数据库提取 token 失败: {e}")
            return False

    def _refresh_access_token(self) -> str:
        """刷新 access_token（优先从 CLI 数据库提取，失败则尝试 API 刷新）"""

        # 方法1: 从 Amazon Q CLI 数据库提取（最可靠）
        if self._extract_token_from_cli_db():
            return self.access_token

        # 方法2: 使用 refresh_token 通过 API 刷新
        if not self.credentials.get('refresh_token'):
            raise ValueError("未设置 refresh_token 且无法从 CLI 数据库提取 token")

        url = f"{SSO_OIDC_ENDPOINT}/token"

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.credentials['refresh_token'],
            "client_id": self.credentials['client_id'],
            "client_secret": self.credentials['client_secret']
        }

        try:
            logger.info(f"正在通过 API 刷新 token，URL: {url}")
            logger.info(f"请求数据: grant_type={data['grant_type']}, client_id={data['client_id'][:20]}...")

            response = requests.post(url, data=data, timeout=30)

            logger.info(f"Token 刷新响应状态码: {response.status_code}")

            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data['accessToken']  # 注意：AWS 返回的是 accessToken 不是 access_token
            # 设置过期时间（提前配置的时间刷新）
            expires_in = token_data.get('expiresIn', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - TOKEN_REFRESH_MARGIN)

            # 更新凭证文件
            self.credentials['access_token'] = self.access_token
            with open(self.credentials_path, 'w') as f:
                json.dump(self.credentials, f, indent=2)

            logger.info(f"✓ API 刷新 token 成功，有效期: {expires_in}秒")
            logger.info(f"✓ Token 前20字符: {self.access_token[:20]}...")
            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ API 刷新 token 失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"✗ 错误响应状态码: {e.response.status_code}")
                logger.error(f"✗ 错误响应内容: {e.response.text}")
            raise

    def get_access_token(self) -> str:
        """获取有效的 access_token（如果过期或不存在则自动刷新）"""
        # 如果 token 不存在或已过期，自动刷新
        if not self.access_token or (self.token_expiry and datetime.now() >= self.token_expiry):
            logger.info("Access token 不存在或已过期，正在自动刷新...")
            return self._refresh_access_token()
        return self.access_token


class AmazonQClient:
    """Amazon Q API 客户端"""

    def __init__(self, auth_manager: AmazonQAuthManager):
        self.auth_manager = auth_manager
        self.endpoint = AMAZONQ_ENDPOINT
        self.region = "us-east-1"
        self.service = "bedrock"

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头（基于 VS Code 插件抓包）"""
        access_token = self.auth_manager.get_access_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "x-amzn-codewhisperer-optout": "false"
        }

    def _sign_request(self, method: str, url: str, headers: Dict[str, str], payload: str) -> Dict[str, str]:
        """
        为 AWS API 请求添加 Signature V4 签名
        使用 Bearer token 而不是 AWS credentials
        """
        # 对于使用 Bearer token 的请求，直接返回原始 headers
        # Bedrock 应该支持 Bearer token 认证
        access_token = self.auth_manager.get_access_token()

        # 使用标准的 Bedrock headers
        signed_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        return signed_headers

    def send_message(
            self,
            message: str,
            conversation_id: Optional[str] = None,
            profile_arn: Optional[str] = None,
            model_id: str = "claude-sonnet-4.5",
            retry_on_auth_error: bool = True,
            stream: bool = False
    ):
        """发送消息到 Amazon Q（基于 VS Code 插件抓包）
        
        Args:
            retry_on_auth_error: 如果遇到 403 错误是否自动刷新 token 并重试
        """

        # 如果没有 conversation_id，创建新对话
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # 使用 REST 端点（不使用 X-Amz-Target）
        url = f"{self.endpoint}/generateAssistantResponse"

        payload = {
            "conversationState": {
                "chatTriggerType": "MANUAL",
                "conversationId": conversation_id,
                "currentMessage": {
                    "userInputMessage": {
                        "content": message,
                        "images": [],
                        "modelId": model_id,
                        "origin": "IDE",
                        "userInputMessageContext": {
                            "editorState": {
                                "useRelevantDocuments": False,
                                "workspaceFolders": []
                            },
                            "envState": {
                                "operatingSystem": "linux"
                            }
                        }
                    }
                },
                "history": []
            }
        }

        headers = self._get_headers()
        payload_str = json.dumps(payload)

        try:
            if log_config.get("log_requests", True):
                logger.info(f"发送请求到 Amazon Q: {url}")
                max_len = log_config.get("max_log_length", 500)
                logger.info(f"请求 payload: {json.dumps(payload, ensure_ascii=False)[:max_len]}")

            response = requests.post(url, headers=headers, data=payload_str, timeout=60, verify=False, stream=stream)

            if log_config.get("log_responses", True):
                logger.info(f"响应状态码: {response.status_code}")
                if not stream:
                    logger.info(f"响应内容长度: {len(response.text)} 字符")

            # 检测 403 错误并自动刷新 token 重试
            if response.status_code == 403 and retry_on_auth_error:
                logger.warning("收到 403 错误，可能是 token 过期，正在自动刷新...")
                try:
                    # 刷新 token
                    self.auth_manager._refresh_access_token()
                    logger.info("Token 刷新成功，正在重试请求...")

                    # 更新 headers 并重试（只重试一次）
                    headers = self._get_headers()
                    response = requests.post(url, headers=headers, data=payload_str, timeout=60, verify=False, stream=stream)
                    logger.info(f"重试后响应状态码: {response.status_code}")
                except Exception as refresh_error:
                    logger.error(f"刷新 token 失败: {refresh_error}")
                    # 继续执行原有的错误处理

            response.raise_for_status()

            # 如果请求流式输出，返回 response 对象本身
            if stream:
                return response
            
            # 否则返回原始文本响应（Event Stream 格式）
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Amazon Q API 请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"响应内容: {e.response.text[:500]}")
            raise


def extract_json_from_buffer(buffer: str, start_pattern: str = '{"content":') -> tuple:
    """
    从缓冲区提取完整的 JSON 对象（优化版，减少内存分配）
    
    Returns:
        (json_str, remaining_buffer) 如果找到完整对象
        (None, buffer) 如果没有找到
    """
    start = buffer.find(start_pattern)
    if start == -1:
        return None, buffer
    
    # 状态机解析 JSON
    depth = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(buffer)):
        char = buffer[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"':
            in_string = not in_string
        
        if not in_string:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    # 找到完整的 JSON 对象
                    return buffer[start:i+1], buffer[i+1:]
    
    # 没有找到完整对象
    return None, buffer


class OpenAIConverter:
    """OpenAI 格式转换器"""

    @staticmethod
    def messages_to_content(messages: List[Dict]) -> str:
        """将 OpenAI/Anthropic messages 转换为单个消息内容"""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")

                # 处理 Anthropic 格式：content 是数组
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                    return " ".join(text_parts)

                # 处理 OpenAI 格式：content 是字符串
                return content
        return ""

    @staticmethod
    def parse_event_stream(raw_response: str) -> str:
        """解析 AWS Event Stream 格式的响应
        
        使用 JSON 解析器逐个提取 {"content":"..."} 对象，
        正确处理转义字符和特殊字符（如 HTML 标签、引号等）
        """
        json_objects = []
        
        # 状态机解析多个JSON对象
        depth = 0
        current_obj = ""
        in_string = False
        escape_next = False
        
        for char in raw_response:
            if escape_next:
                current_obj += char
                escape_next = False
                continue
                
            if char == '\\':
                current_obj += char
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
            
            if not in_string:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
            
            current_obj += char
            
            # 当深度回到0且当前对象不为空时，说明一个JSON对象结束
            if depth == 0 and current_obj.strip():
                try:
                    obj = json.loads(current_obj.strip())
                    if 'content' in obj:
                        json_objects.append(obj['content'])
                    current_obj = ""
                except json.JSONDecodeError:
                    # 如果解析失败，继续累积字符
                    pass
        
        # 拼接所有提取的内容
        if json_objects:
            return ''.join(json_objects)
        
        # 如果没有找到有效的JSON对象，返回原始内容
        return raw_response

    @staticmethod
    def amazonq_to_openai_response(
            amazonq_raw_response: str,
            model: str,
            conversation_id: str
    ) -> Dict:
        """将 Amazon Q Event Stream 响应转换为 OpenAI 格式"""

        # 解析 Event Stream
        content = OpenAIConverter.parse_event_stream(amazonq_raw_response)

        response = {
            "id": f"chatcmpl-{conversation_id[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }

        return response

    @staticmethod
    def create_stream_chunk(content: str, model: str, chunk_type: str = "content", format_type: str = "openai") -> str:
        """创建 SSE 流式响应块
        
        chunk_type: 'start', 'content_start', 'content', 'content_end', 'end'
        """
        if format_type == "anthropic":
            # Anthropic 格式
            if chunk_type == "start":
                chunk = {
                    "type": "message_start",
                    "message": {
                        "id": f"msg_{uuid.uuid4().hex[:8]}",
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": model,
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0}
                    }
                }
            elif chunk_type == "content_start":
                chunk = {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {
                        "type": "text",
                        "text": ""
                    }
                }
            elif chunk_type == "content":
                chunk = {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {
                        "type": "text_delta",
                        "text": content
                    }
                }
            elif chunk_type == "content_end":
                chunk = {
                    "type": "content_block_stop",
                    "index": 0
                }
            else:  # end
                chunk = {
                    "type": "message_delta",
                    "delta": {
                        "stop_reason": "end_turn",
                        "stop_sequence": None
                    },
                    "usage": {
                        "output_tokens": 0
                    }
                }
        else:
            # OpenAI 格式
            chunk = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": content} if chunk_type == "content" else {},
                        "finish_reason": "stop" if chunk_type == "end" else None
                    }
                ]
            }
        return f"data: {json.dumps(chunk)}\n\n"


# 全局实例
auth_manager = AmazonQAuthManager()
amazonq_client = AmazonQClient(auth_manager)
converter = OpenAIConverter()


@app.route('/v1/chat/completions', methods=['POST'])
def openai_chat_completions():
    """OpenAI 兼容的聊天接口"""
    return _handle_chat_request(format_type="openai")


@app.route('/v1/messages', methods=['POST'])
def anthropic_messages():
    """Anthropic 兼容的聊天接口"""
    return _handle_chat_request(format_type="anthropic")


def _handle_chat_request(format_type: str = "openai"):
    """处理聊天请求的通用逻辑"""
    try:
        data = request.json
        if log_config.get("log_requests", True):
            max_len = log_config.get("max_log_length", 500)
            data_str = json.dumps(data, ensure_ascii=False)
            logger.info(f"收到请求 ({format_type}): {data_str[:max_len]}")

        # 提取参数 - 兼容 OpenAI 和 Anthropic 格式
        messages = data.get('messages', [])
        model = data.get('model', 'claude-sonnet-4.5')
        stream = data.get('stream', False)

        if not messages:
            return jsonify({"error": "messages 参数不能为空"}), 400

        # 转换消息
        content = converter.messages_to_content(messages)
        if log_config.get("log_requests", True):
            max_len = log_config.get("max_log_length", 500)
            logger.info(f"转换后的消息内容: {content[:max_len]}")

        # 生成会话 ID
        conversation_id = str(uuid.uuid4())

        # 调用 Amazon Q
        try:
            # 支持通过 model 参数指定 model_id
            model_id = "claude-sonnet-4.5"
            if model in ["claude-sonnet-4.5", "claude-sonnet-4", "amazon-q"]:
                if model == "claude-sonnet-4.5":
                    model_id = "claude-sonnet-4.5"
                elif model == "claude-sonnet-4":
                    model_id = "claude-sonnet-4"

            amazonq_response = amazonq_client.send_message(
                message=content,
                conversation_id=conversation_id,
                profile_arn=auth_manager.credentials.get('profile_arn'),
                model_id=model_id,
                stream=stream  # 传递 stream 参数
            )
            if not stream and log_config.get("log_responses", True):
                logger.info(f"Amazon Q 响应长度: {len(amazonq_response)}")
        except Exception as e:
            logger.error(f"调用 Amazon Q 失败: {e}")
            return jsonify({
                "error": {
                    "message": f"Amazon Q API 调用失败: {str(e)}",
                    "type": "amazon_q_error",
                    "code": "service_unavailable"
                }
            }), 503

        # 转换响应
        if stream:
            # 真正的流式响应 - 实时从 Amazon Q 读取并转发
            def generate():
                try:
                    # 发送开始事件
                    if format_type == "anthropic":
                        yield converter.create_stream_chunk("", model, chunk_type="start", format_type="anthropic")
                        yield converter.create_stream_chunk("", model, chunk_type="content_start", format_type="anthropic")
                    
                    # 实时读取 Amazon Q 的流式响应
                    buffer = ""
                    for chunk in amazonq_response.iter_content(chunk_size=STREAM_CHUNK_SIZE, decode_unicode=True):
                        if chunk:
                            buffer += chunk
                            
                            # 防止缓冲区无限增长
                            if len(buffer) > BUFFER_MAX_SIZE:
                                logger.warning(f"缓冲区超过限制 ({BUFFER_MAX_SIZE} 字符)，清空前面部分")
                                buffer = buffer[-BUFFER_MAX_SIZE:]
                            
                            # 尝试从缓冲区提取完整的 JSON 对象
                            while True:
                                json_str, buffer = extract_json_from_buffer(buffer)
                                if json_str is None:
                                    break
                                
                                try:
                                    obj = json.loads(json_str)
                                    if 'content' in obj:
                                        text = obj['content']
                                        # 立即发送这个文本片段
                                        if format_type == "anthropic":
                                            yield converter.create_stream_chunk(text, model, chunk_type="content", format_type="anthropic")
                                        else:
                                            yield converter.create_stream_chunk(text, model, chunk_type="content", format_type="openai")
                                except json.JSONDecodeError:
                                    pass
                    
                    # 发送结束事件
                    if format_type == "anthropic":
                        yield converter.create_stream_chunk("", model, chunk_type="content_end", format_type="anthropic")
                        yield converter.create_stream_chunk("", model, chunk_type="end", format_type="anthropic")
                    else:
                        yield converter.create_stream_chunk("", model, chunk_type="end", format_type="openai")
                        yield "data: [DONE]\n\n"
                    
                    if log_config.get("log_responses", True):
                        logger.info("流式响应完成")
                    
                except Exception as e:
                    logger.error(f"流式响应过程中出错: {e}", exc_info=True)
                    # 发送错误
                    error_chunk = {
                        "error": {
                            "message": str(e),
                            "type": "stream_error"
                        }
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            return Response(generate(), mimetype='text/event-stream')
        else:
            # 非流式响应
            openai_response = converter.amazonq_to_openai_response(
                amazonq_response, model, conversation_id
            )
            if log_config.get("log_responses", True):
                max_len = log_config.get("max_log_length", 500)
                content_preview = openai_response['choices'][0]['message']['content'][:max_len]
                logger.info(f"非流式返回内容: {content_preview}...")

            if format_type == "anthropic":
                # Anthropic 非流式格式
                anthropic_response = {
                    "id": f"msg_{uuid.uuid4().hex}",
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": openai_response['choices'][0]['message']['content']
                        }
                    ],
                    "model": model,
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 0
                    }
                }
                return jsonify(anthropic_response)
            else:
                return jsonify(openai_response)

    except Exception as e:
        logger.error(f"处理请求时发生错误: {e}", exc_info=True)
        return jsonify({
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_error"
            }
        }), 500


@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出可用的模型"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "claude-sonnet-4.5",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic"
            },
            {
                "id": "claude-sonnet-4",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "anthropic"
            },
            {
                "id": "amazon-q",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "amazon"
            }
        ]
    })


@app.route('/credentials', methods=['POST'])
def set_credentials():
    """设置 Amazon Q 凭证"""
    try:
        credentials = request.json
        required_fields = ['refresh_token', 'client_id', 'client_secret']

        for field in required_fields:
            if field not in credentials:
                return jsonify({
                    "error": f"缺少必需字段: {field}"
                }), 400

        auth_manager.set_credentials(credentials)

        return jsonify({
            "message": "凭证设置成功",
            "has_profile_arn": bool(credentials.get('profile_arn'))
        })
    except Exception as e:
        logger.error(f"设置凭证失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/credentials', methods=['GET'])
def get_credentials_status():
    """获取凭证状态"""
    has_credentials = bool(auth_manager.credentials.get('refresh_token'))
    has_token = bool(auth_manager.access_token)

    return jsonify({
        "has_credentials": has_credentials,
        "has_access_token": has_token,
        "token_expiry": auth_manager.token_expiry.isoformat() if auth_manager.token_expiry else None
    })


@app.route('/test/token', methods=['GET'])
def test_token():
    """测试 token 刷新功能"""
    try:
        logger.info("=" * 50)
        logger.info("开始测试 token 刷新")
        logger.info("=" * 50)

        # 强制刷新 token
        auth_manager.access_token = None
        auth_manager.token_expiry = None

        access_token = auth_manager.get_access_token()

        return jsonify({
            "success": True,
            "message": "Token 刷新成功",
            "token_preview": access_token[:30] + "..." if len(access_token) > 30 else access_token,
            "token_length": len(access_token),
            "token_expiry": auth_manager.token_expiry.isoformat() if auth_manager.token_expiry else None
        })
    except Exception as e:
        logger.error(f"Token 测试失败: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "has_credentials": bool(auth_manager.credentials.get('refresh_token'))
    })


@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        "message": "Amazon Q to OpenAI API Bridge",
        "version": "2.0.0",
        "auth_method": "OAuth 2.0",
        "endpoints": {
            "openai_chat": "/v1/chat/completions",
            "anthropic_messages": "/v1/messages",
            "models": "/v1/models",
            "credentials": "/credentials",
            "health": "/health"
        },
        "default_model": "claude-sonnet-4.5"
    })


if __name__ == '__main__':
    logger.info("启动 Amazon Q to OpenAI API Bridge")
    logger.info(f"Amazon Q 端点: {AMAZONQ_ENDPOINT}")
    logger.info(f"SSO OIDC 端点: {SSO_OIDC_ENDPOINT}")

    # 检查是否已有凭证
    if auth_manager.credentials.get('refresh_token'):
        logger.info("✓ 已加载 Amazon Q 凭证")
    else:
        logger.warning("✗ 未找到凭证，请通过 POST /credentials 设置")

    app.run(host='0.0.0.0', port=8000, debug=True)
