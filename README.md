# aq2api


> 通过群之前佬友提供的python脚本 `info.py` 获取凭证信息

## 凭证文件格式

`amazonq_credentials.json` 需要包含：

```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "refresh_token": "your_refresh_token",
  "access_token": "will_be_auto_updated",
  "region": "us-east-1",//改为你自己账号对应的地区
}
```

## 配置文件

创建 `config.json` 文件来自定义服务行为。

### 默认配置

```json
{
  "logging": {
    "enabled": true,
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
  }
}
```

## 配置项说明

### logging 日志配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | boolean | `true` | 是否启用日志 |
| `level` | string | `"INFO"` | 日志级别: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` |
| `log_requests` | boolean | `true` | 是否记录请求日志 |
| `log_responses` | boolean | `true` | 是否记录响应日志 |
| `log_token_refresh` | boolean | `true` | 是否记录 token 刷新日志 |
| `max_log_length` | integer | `500` | 日志内容最大长度（字符） |

### performance 性能配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `stream_chunk_size` | integer | `1024` | 流式读取的块大小（字节） |
| `buffer_max_size` | integer | `10240` | 缓冲区最大大小（字符） |
| `token_refresh_margin_seconds` | integer | `300` | Token 过期前多少秒刷新 |