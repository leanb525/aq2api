# Amazon Q to OpenAI API Bridge - Cloudflare Worker Deployment Guide

This guide will help you deploy the Amazon Q to OpenAI/Anthropic API Bridge as a Cloudflare Worker.

## Prerequisites

1. **Cloudflare Account**: Sign up at https://dash.cloudflare.com/sign-up
2. **Node.js**: Install Node.js 18+ from https://nodejs.org/
3. **Amazon Q Credentials**: You need:
   - `client_id`
   - `client_secret`
   - `refresh_token`
   - `access_token` (optional, will be auto-refreshed)

## Quick Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Login to Cloudflare

```bash
npx wrangler login
```

This will open your browser to authenticate with Cloudflare.

### 3. Get Your Account ID

```bash
npx wrangler whoami
```

Copy your account ID and update `wrangler.toml`:

```toml
account_id = "your-account-id-here"
```

### 4. Create KV Namespace (Optional but Recommended)

KV namespace is used to store credentials persistently:

```bash
npx wrangler kv:namespace create "CREDENTIALS"
```

Copy the output and update `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "CREDENTIALS"
id = "your-kv-namespace-id-here"
```

For production environment:

```bash
npx wrangler kv:namespace create "CREDENTIALS" --env production
```

### 5. Set Up Secrets

Set your Amazon Q credentials as secrets:

```bash
npx wrangler secret put CLIENT_ID
# Paste your client_id when prompted

npx wrangler secret put CLIENT_SECRET
# Paste your client_secret when prompted

npx wrangler secret put REFRESH_TOKEN
# Paste your refresh_token when prompted

# Optional: Set initial access token
npx wrangler secret put ACCESS_TOKEN
# Paste your access_token when prompted (or skip if you want it to be auto-refreshed)
```

### 6. Deploy to Cloudflare

**Deploy to development:**

```bash
npm run dev
```

This starts a local development server at `http://localhost:8787`

**Deploy to production:**

```bash
npm run deploy:production
```

## Configuration

### Your Credentials

Based on your provided config, here are the values you'll need to set:

```bash
# CLIENT_ID
KwJ4zvscaSQ8ZWU7SAu-0XVzLWVhc3QtMQ

# CLIENT_SECRET
eyJraWQiOiJrZXktMTU2NDAyODA5OSIsImFsZyI6IkhTMzg0In0.eyJzZXJpYWxpemVkIjoie1wiY2xpZW50SWRcIjp7XCJ2YWx1ZVwiOlwiS3dKNHp2c2NhU1E4WldVN1NBdS0wWFZ6TFdWaGMzUXRNUVwifSxcImlkZW1wb3RlbnRLZXlcIjpudWxsLFwidGVuYW50SWRcIjpudWxsLFwiY2xpZW50TmFtZVwiOlwiQVdTIElERSBFeHRlbnNpb25zIGZvciBWU0NvZGVcIixcImJhY2tmaWxsVmVyc2lvblwiOm51bGwsXCJjbGllbnRUeXBlXCI6XCJQVUJMSUNcIixcInRlbXBsYXRlQXJuXCI6bnVsbCxcInRlbXBsYXRlQ29udGV4dFwiOm51bGwsXCJleHBpcmF0aW9uVGltZXN0YW1wXCI6MTc3MDMxMTEwMy4wMzk5OTczOTQsXCJjcmVhdGVkVGltZXN0YW1wXCI6MTc2MjUzNTEwMy4wMzk5OTczOTQsXCJ1cGRhdGVkVGltZXN0YW1wXCI6MTc2MjUzNTEwMy4wMzk5OTczOTQsXCJjcmVhdGVkQnlcIjpudWxsLFwidXBkYXRlZEJ5XCI6bnVsbCxcInN0YXR1c1wiOm51bGwsXCJpbml0aWF0ZUxvZ2luVXJpXCI6XCJodHRwczpcL1wvdmlldy5hd3NhcHBzLmNvbVwvc3RhcnRcL1wiLFwiZW50aXRsZWRSZXNvdXJjZUlkXCI6bnVsbCxcImVudGl0bGVkUmVzb3VyY2VDb250YWluZXJJZFwiOm51bGwsXCJleHRlcm5hbElkXCI6bnVsbCxcInNvZnR3YXJlSWRcIjpudWxsLFwic2NvcGVzXCI6W3tcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjpjb21wbGV0aW9uc1wiLFwic3RhdHVzXCI6XCJJTklUSUFMXCIsXCJhcHBsaWNhdGlvbkFyblwiOm51bGwsXCJmcmllbmRseUlkXCI6XCJjb2Rld2hpc3BlcmVyXCIsXCJ1c2VDYXNlQWN0aW9uXCI6XCJjb21wbGV0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjphbmFseXNpc1wiLFwic3RhdHVzXCI6XCJJTklUSUFMXCIsXCJhcHBsaWNhdGlvbkFyblwiOm51bGwsXCJmcmllbmRseUlkXCI6XCJjb2Rld2hpc3BlcmVyXCIsXCJ1c2VDYXNlQWN0aW9uXCI6XCJhbmFseXNpc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjpjb252ZXJzYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImNvbnZlcnNhdGlvbnNcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifSx7XCJmdWxsU2NvcGVcIjpcImNvZGV3aGlzcGVyZXI6dHJhbnNmb3JtYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRyYW5zZm9ybWF0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjp0YXNrYXNzaXN0XCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRhc2thc3Npc3RcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifV0sXCJhdXRoZW50aWNhdGlvbkNvbmZpZ3VyYXRpb25cIjpudWxsLFwic2hhZG93QXV0aGVudGljYXRpb25Db25maWd1cmF0aW9uXCI6bnVsbCxcImVuYWJsZWRHcmFudHNcIjp7XCJBVVRIX0NPREVcIjp7XCJ0eXBlXCI6XCJJbW11dGFibGVBdXRob3JpemF0aW9uQ29kZUdyYW50T3B0aW9uc1wiLFwicmVkaXJlY3RVcmlzXCI6W1wiaHR0cDpcL1wvMTI3LjAuMC4xXC9vYXV0aFwvY2FsbGJhY2tcIl19LFwiUkVGUkVTSF9UT0tFTlwiOntcInR5cGVcIjpcIkltbXV0YWJsZVJlZnJlc2hUb2tlbkdyYW50T3B0aW9uc1wifX0sXCJlbmZvcmNlQXV0aE5Db25maWd1cmF0aW9uXCI6bnVsbCxcIm93bmVyQWNjb3VudElkXCI6bnVsbCxcInNzb0luc3RhbmNlQWNjb3VudElkXCI6bnVsbCxcInVzZXJDb25zZW50XCI6bnVsbCxcIm5vbkludGVyYWN0aXZlU2Vzc2lvbnNFbmFibGVkXCI6bnVsbCxcImFzc29jaWF0ZWRJbnN0YW5jZUFyblwiOm51bGwsXCJpc0JhY2tmaWxsZWRcIjpmYWxzZSxcImhhc0luaXRpYWxTY29wZXNcIjp0cnVlLFwiYXJlQWxsU2NvcGVzQ29uc2VudGVkVG9cIjpmYWxzZSxcImlzRXhwaXJlZFwiOmZhbHNlLFwic3NvU2NvcGVzXCI6W10sXCJncm91cFNjb3Blc0J5RnJpZW5kbHlJZFwiOntcImNvZGV3aGlzcGVyZXJcIjpbe1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmNvbXBsZXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImNvbXBsZXRpb25zXCIsXCJ0eXBlXCI6XCJJbW11dGFibGVBY2Nlc3NTY29wZVwiLFwic2NvcGVUeXBlXCI6XCJBQ0NFU1NfU0NPUEVcIn0se1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmFuYWx5c2lzXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImFuYWx5c2lzXCIsXCJ0eXBlXCI6XCJJbW11dGFibGVBY2Nlc3NTY29wZVwiLFwic2NvcGVUeXBlXCI6XCJBQ0NFU1NfU0NPUEVcIn0se1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmNvbnZlcnNhdGlvbnNcIixcInN0YXR1c1wiOlwiSU5JVElBTFwiLFwiYXBwbGljYXRpb25Bcm5cIjpudWxsLFwiZnJpZW5kbHlJZFwiOlwiY29kZXdoaXNwZXJlclwiLFwidXNlQ2FzZUFjdGlvblwiOlwiY29udmVyc2F0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjp0YXNrYXNzaXN0XCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRhc2thc3Npc3RcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifSx7XCJmdWxsU2NvcGVcIjpcImNvZGV3aGlzcGVyZXI6dHJhbnNmb3JtYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRyYW5zZm9ybWF0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9XX0sXCJzaG91bGRHZXRWYWx1ZUZyb21UZW1wbGF0ZVwiOmZhbHNlLFwiaGFzUmVxdWVzdGVkU2NvcGVzXCI6ZmFsc2UsXCJjb250YWluc09ubHlTc29TY29wZXNcIjpmYWxzZSxcImlzVjFCYWNrZmlsbGVkXCI6ZmFsc2UsXCJpc1YyQmFja2ZpbGxlZFwiOmZhbHNlLFwiaXNWM0JhY2tmaWxsZWRcIjpmYWxzZSxcImlzVjRCYWNrZmlsbGVkXCI6ZmFsc2V9In0.DHISHGWVPbx_BWnB4tigfmkIfdhahaLPPpLgiMDOF9LeDhgbkeJXkIF2KGyjVABI

# REFRESH_TOKEN
aorAAAAAGmEpW0BqAaQuIlvPsiWVqoJmkeKZnS07JKg37G0CftWC8xmapxjxAHVSWLHZsbcr3m3uTotOQFGYYhTDMBkc0:MGUCMQDO++uHKayPaKZIj9+7vNJkYn2I/UZ+0UzpG3WozrQiDZEt2F2jfaQZ1WWMghJEnEcCMGHomY9yIQccpAqoCrltjwk9XIhRz9WX7wBX7usQbFTPMtCRAPfTs3docXGcUe13hQ

# ACCESS_TOKEN (optional)
aoaAAAAAGkRr4sEyjhyYef2Y-TVdLH0WfkNxSG2lFVXy7-aSKw7b8mn_CDugFIEiWMKMtOWqcpjN2NFhZFu8Vi7eQBkc0:MGUCMQDfBTNPXYZdXlk8VYiRlYXNRUGnPMLWtWMrwYjkB+4bPYiIbkwJvBMQXbscxE8qCMMCMEzGFoTeh+E1IJbO5vTawT1eBn3oFfq8G/7IX79bncYNYuobPSa+60/PM9YruBQRaQ
```

## Using the API

Once deployed, your worker will be available at:
```
https://amazonq-openai-bridge.<your-subdomain>.workers.dev
```

### Available Endpoints

1. **OpenAI Compatible**: `POST /v1/chat/completions`
2. **Anthropic Compatible**: `POST /v1/messages`
3. **List Models**: `GET /v1/models`
4. **Health Check**: `GET /health`
5. **Update Credentials**: `POST /credentials`

### Example Usage

**With OpenAI SDK:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://amazonq-openai-bridge.<your-subdomain>.workers.dev/v1",
    api_key="dummy"  # Not used but required by SDK
)

response = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

**With Anthropic SDK:**

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://amazonq-openai-bridge.<your-subdomain>.workers.dev",
    api_key="dummy"  # Not used but required by SDK
)

response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.content[0].text)
```

**With curl:**

```bash
curl -X POST https://amazonq-openai-bridge.<your-subdomain>.workers.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

## Monitoring

### View Logs

```bash
npm run tail
```

Or for production:

```bash
npx wrangler tail --env production
```

### Check Status

Visit the Cloudflare dashboard to see:
- Request analytics
- Error logs
- Performance metrics

## Troubleshooting

### Token Refresh Issues

If you get 403 errors:

1. Check that your secrets are set correctly:
```bash
npx wrangler secret list
```

2. Manually refresh your token using the `/credentials` endpoint:
```bash
curl -X POST https://your-worker.workers.dev/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "...",
    "client_secret": "...",
    "refresh_token": "...",
    "access_token": "..."
  }'
```

### Streaming Issues

If streaming doesn't work:
- Ensure your client supports SSE (Server-Sent Events)
- Check that `stream: true` is set in your request
- Verify CORS headers are correct

## Security Best Practices

1. **Use KV Namespace**: Store credentials in KV instead of environment variables
2. **Rotate Tokens**: Regularly refresh your access tokens
3. **Custom Domain**: Use a custom domain instead of `.workers.dev` for production
4. **Rate Limiting**: Consider adding rate limiting for production use
5. **Authentication**: Add your own authentication layer if exposing publicly

## Cost Estimation

Cloudflare Workers free tier includes:
- 100,000 requests/day
- 10ms CPU time per request

For most personal use cases, this should be sufficient and completely free.

## Advanced Configuration

### Custom Domain

1. Add a route in `wrangler.toml`:
```toml
[env.production]
routes = [
  { pattern = "api.yourdomain.com/*", zone_name = "yourdomain.com" }
]
```

2. Deploy:
```bash
npm run deploy:production
```

### Environment Variables

You can override any configuration per environment in `wrangler.toml`:

```toml
[env.production]
name = "amazonq-openai-bridge"
vars = { LOG_REQUESTS = "false", LOG_RESPONSES = "false" }
```

## Support

For issues or questions:
1. Check Cloudflare Workers documentation: https://developers.cloudflare.com/workers/
2. Review the source code in `src/index.ts`
3. Check logs with `npm run tail`

## Migration Notes

Key differences from the Python version:
- No SQLite database support (use KV namespace instead)
- All operations are stateless and edge-based
- Automatic global distribution via Cloudflare's network
- No need to manage servers or containers
- Cost-effective at scale (first 100k requests/day are free)
