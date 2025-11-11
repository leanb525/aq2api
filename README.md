## Amazon Q → OpenAI / Anthropic Bridge (Flask Edition)



## 大家可以看我的 [Cloudflare Worker 版本部署（更加方便）](https://github.com/leanb525/aq2worker)

把 **Amazon Q Developer** 的 Claude 能力转成兼容 **OpenAI Chat Completions** 与 **Anthropic Messages** 的本地服务，方便在 Claude Code、Cursor、Continue、Open WebUI 等工具中复用同一个模型入口。

---

### 功能一览

- OpenAI `/v1/chat/completions` 与 Anthropic `/v1/messages` 双协议兼容
- SSE 流式输出，已针对 Claude Code / Anthropic IDE 适配事件格式
- 自动刷新 access_token：优先读取 Amazon Q CLI 数据库，失败再调用 OIDC `/token`
- 支持自定义 CA Bundle / 禁用 SSL 验证（方便企业代理环境排障）
- 便捷凭证管理：`amazonq_credentials.json` + `info.py` 提取脚本

当前仓库只包含 **Flask 单账号版本（`main.py`）**，没有 FastAPI 多账号实现；文档中所有步骤均以现有文件为准。

---

### 仓库结构

| 路径 | 说明 |
| ---- | ---- |
| `main.py` | Flask 服务器，暴露 OpenAI / Anthropic 兼容接口 |
| `amazonq_credentials.json` | 凭证存储文件（运行时自动更新） |
| `config.json` | 可选配置（日志、流式缓冲、SSL） |
| `info.py` | 从 Amazon Q CLI 数据库导出 `clientId / clientSecret / refreshToken` |
| `CLAUDE.md` | 额外说明/备忘 |

---

### 环境准备

| 项目 | 建议版本 |
| --- | --- |
| Python | 3.10+（推荐 3.11） |
| pip | 最新 |
| Amazon Q CLI | 已登录 (`amazon-q auth`) |

> `requirements.txt` 只包含通用依赖（requests 等）。请另外安装 `flask`：
> ```bash
> pip install flask
> pip install -r requirements.txt
> ```

---

### 安装步骤

```bash
git clone <repo-url>
cd aq2api

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install flask requests
pip install -r requirements.txt
```

---

### 获取 Amazon Q 凭证

1. **通过 info.py 导出（推荐）**
   ```bash
   python info.py > amazonq_credentials.json
   ```
   输出包含 `client_id / client_secret / refresh_token` 等字段，`main.py` 启动时自动读取。

2. **手动编辑 `amazonq_credentials.json`**
   ```json
   {
     "client_id": "KwJ4zv...",
     "client_secret": "<JWT>",
     "refresh_token": "aorAAAA...",
     "profile_arn": "arn:aws:..."   // 可选
   }
   ```

> 程序也会尝试从 `~/.local/share/amazon-q/data.sqlite3` 抓取最新 token；只要本机 CLI 已登录即可自动覆盖 `access_token`。

---

### 配置（可选）

创建 `config.json` 并覆盖默认值：

```json
{
  "logging": {
    "level": "INFO",
    "log_requests": true,
    "log_responses": true,
    "log_token_refresh": true,
    "max_log_length": 500
  },
  "performance": {
    "stream_chunk_size": 1024,
    "buffer_max_size": 10240,
    "token_refresh_margin_seconds": 300
  },
  "ssl": {
    "verify_oidc": true,
    "ca_bundle": "/path/to/corp-root.pem"
  }
}
```

常用环境变量：

| 变量 | 用途 |
| --- | --- |
| `AMAZONQ_CA_BUNDLE` / `AWS_CA_BUNDLE` / `REQUESTS_CA_BUNDLE` | 指定自定义 CA 文件 |
| `DISABLE_AMAZONQ_SSL_VERIFY` | 设为 `1` 暂时跳过 OIDC SSL 验证（仅调试） |
| `ANTHROPIC_VERSION` | 覆盖 SSE/JSON 响应中的 `anthropic-version` 头 |

---

### 启动服务

```bash
python main.py
```

默认监听 `http://0.0.0.0:8000`。首次启动会提示是否已加载凭证，并在日志中显示两个上游端点：

- Amazon Q API: `https://codewhisperer.us-east-1.amazonaws.com`
- OIDC Token: `https://oidc.us-east-1.amazonaws.com`

---

### 对外端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/v1/chat/completions` | OpenAI Chat Completions 兼容 |
| `POST` | `/v1/messages` | Anthropic Messages 兼容（默认流式） |
| `GET` | `/v1/models` | 列出可选模型 ID |
| `GET/POST` | `/credentials` | 管理 `amazonq_credentials.json` |
| `GET` | `/test/token` | 强制刷新 token 并返回预览 |
| `GET` | `/health` | 简易健康检查 |

`/v1/messages` 在未显式声明 `stream:false` 时总是走 SSE，并按照 Anthropic 规范发送 `message_start → content_block_delta → message_stop` 事件。

---

### 调用示例

**OpenAI SDK（Python）**

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="dummy-key")

resp = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[{"role": "user", "content": "介绍一下 Amazon Q"}],
    stream=False,
)
print(resp.choices[0].message.content)
```

**OpenAI 流式（curl）**

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4.5","messages":[{"role":"user","content":"说个笑话"}],"stream":true}'
```

**Anthropic SDK (Messages API)** — 默认会收到流式事件，也可设置 `stream: false` 获得一次性响应。

```python
from anthropic import Anthropic

client = Anthropic(base_url="http://127.0.0.1:8000/v1", api_key="dummy-key")

resp = client.messages.create(
    model="claude-sonnet-4",
    max_tokens=2048,
    messages=[{"role": "user", "content": "列一个使用指南"}],
    stream=False,
)
print(resp.content[0].text)
```

---

### 常见问题

| 现象 | 排查建议 |
| --- | --- |
| `CERTIFICATE_VERIFY_FAILED` | 确认是否处在代理/自签环境，设置 `AMAZONQ_CA_BUNDLE` 或暂时 `DISABLE_AMAZONQ_SSL_VERIFY=1` |
| `/token` 400/401 | `refresh_token` 失效或 clientSecret 过期，重新运行 `amazon-q auth` + `python info.py` |
| 403 Forbidden | access_token 过期 → 调用 `/test/token`；或 Amazon Q 尚未在当前账号启用 |
| SSE 非流式 | 确保客户端命中 `/v1/messages` 或明确 `stream:true`；检查代理是否缓冲响应 |
| `Amazon Q CLI 数据库未找到` | 运行 `amazon-q auth`；若路径不一致，手动复制 `data.sqlite3` 并更新 `info.py` |

---

### 许可证

MIT（默认）。欢迎提交 Issue / PR 改进文档与功能。*** End Patch*** End Patch ***
