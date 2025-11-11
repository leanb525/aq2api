# Quick Start Guide

Get your Amazon Q to OpenAI Bridge running on Cloudflare Workers in 5 minutes!

## Prerequisites

- Node.js 18+ installed
- A Cloudflare account (free tier works)
- Your Amazon Q credentials from the Python config

## Step 1: Install Dependencies

```bash
npm install
```

## Step 2: Login to Cloudflare

```bash
npx wrangler login
```

## Step 3: Set Your Credentials

### Option A: Use the Setup Script (Recommended)

```bash
./setup-credentials.sh
```

Follow the prompts and paste your credentials from the Python config.

### Option B: Manual Setup

```bash
# Set each secret individually
npx wrangler secret put CLIENT_ID
# Paste: KwJ4zvscaSQ8ZWU7SAu-0XVzLWVhc3QtMQ

npx wrangler secret put CLIENT_SECRET
# Paste: eyJraWQiOi... (the long JWT token)

npx wrangler secret put REFRESH_TOKEN
# Paste: aorAAAAA... (your refresh token)
```

## Step 4: Test Locally

```bash
npm run dev
```

The server will start at `http://localhost:8787`

Test it:
```bash
curl -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Step 5: Deploy to Production

```bash
npm run deploy:production
```

You'll get a URL like:
```
https://amazonq-openai-bridge.<your-subdomain>.workers.dev
```

## Usage Examples

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-worker.workers.dev/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Python (Anthropic SDK)

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://your-worker.workers.dev",
    api_key="dummy"
)

response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.content[0].text)
```

### JavaScript/TypeScript

```typescript
const response = await fetch('https://your-worker.workers.dev/v1/chat/completions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'claude-sonnet-4.5',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

## Your Credentials

Based on your Python config file, here are your values:

```bash
CLIENT_ID="KwJ4zvscaSQ8ZWU7SAu-0XVzLWVhc3QtMQ"

CLIENT_SECRET="eyJraWQiOiJrZXktMTU2NDAyODA5OSIsImFsZyI6IkhTMzg0In0.eyJzZXJpYWxpemVkIjoie1wiY2xpZW50SWRcIjp7XCJ2YWx1ZVwiOlwiS3dKNHp2c2NhU1E4WldVN1NBdS0wWFZ6TFdWaGMzUXRNUVwifSxcImlkZW1wb3RlbnRLZXlcIjpudWxsLFwidGVuYW50SWRcIjpudWxsLFwiY2xpZW50TmFtZVwiOlwiQVdTIElERSBFeHRlbnNpb25zIGZvciBWU0NvZGVcIixcImJhY2tmaWxsVmVyc2lvblwiOm51bGwsXCJjbGllbnRUeXBlXCI6XCJQVUJMSUNcIixcInRlbXBsYXRlQXJuXCI6bnVsbCxcInRlbXBsYXRlQ29udGV4dFwiOm51bGwsXCJleHBpcmF0aW9uVGltZXN0YW1wXCI6MTc3MDMxMTEwMy4wMzk5OTczOTQsXCJjcmVhdGVkVGltZXN0YW1wXCI6MTc2MjUzNTEwMy4wMzk5OTczOTQsXCJ1cGRhdGVkVGltZXN0YW1wXCI6MTc2MjUzNTEwMy4wMzk5OTczOTQsXCJjcmVhdGVkQnlcIjpudWxsLFwidXBkYXRlZEJ5XCI6bnVsbCxcInN0YXR1c1wiOm51bGwsXCJpbml0aWF0ZUxvZ2luVXJpXCI6XCJodHRwczpcL1wvdmlldy5hd3NhcHBzLmNvbVwvc3RhcnRcL1wiLFwiZW50aXRsZWRSZXNvdXJjZUlkXCI6bnVsbCxcImVudGl0bGVkUmVzb3VyY2VDb250YWluZXJJZFwiOm51bGwsXCJleHRlcm5hbElkXCI6bnVsbCxcInNvZnR3YXJlSWRcIjpudWxsLFwic2NvcGVzXCI6W3tcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjpjb21wbGV0aW9uc1wiLFwic3RhdHVzXCI6XCJJTklUSUFMXCIsXCJhcHBsaWNhdGlvbkFyblwiOm51bGwsXCJmcmllbmRseUlkXCI6XCJjb2Rld2hpc3BlcmVyXCIsXCJ1c2VDYXNlQWN0aW9uXCI6XCJjb21wbGV0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjphbmFseXNpc1wiLFwic3RhdHVzXCI6XCJJTklUSUFMXCIsXCJhcHBsaWNhdGlvbkFyblwiOm51bGwsXCJmcmllbmRseUlkXCI6XCJjb2Rld2hpc3BlcmVyXCIsXCJ1c2VDYXNlQWN0aW9uXCI6XCJhbmFseXNpc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjpjb252ZXJzYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImNvbnZlcnNhdGlvbnNcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifSx7XCJmdWxsU2NvcGVcIjpcImNvZGV3aGlzcGVyZXI6dHJhbnNmb3JtYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRyYW5zZm9ybWF0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjp0YXNrYXNzaXN0XCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRhc2thc3Npc3RcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifV0sXCJhdXRoZW50aWNhdGlvbkNvbmZpZ3VyYXRpb25cIjpudWxsLFwic2hhZG93QXV0aGVudGljYXRpb25Db25maWd1cmF0aW9uXCI6bnVsbCxcImVuYWJsZWRHcmFudHNcIjp7XCJBVVRIX0NPREVcIjp7XCJ0eXBlXCI6XCJJbW11dGFibGVBdXRob3JpemF0aW9uQ29kZUdyYW50T3B0aW9uc1wiLFwicmVkaXJlY3RVcmlzXCI6W1wiaHR0cDpcL1wvMTI3LjAuMC4xXC9vYXV0aFwvY2FsbGJhY2tcIl19LFwiUkVGUkVTSF9UT0tFTlwiOntcInR5cGVcIjpcIkltbXV0YWJsZVJlZnJlc2hUb2tlbkdyYW50T3B0aW9uc1wifX0sXCJlbmZvcmNlQXV0aE5Db25maWd1cmF0aW9uXCI6bnVsbCxcIm93bmVyQWNjb3VudElkXCI6bnVsbCxcInNzb0luc3RhbmNlQWNjb3VudElkXCI6bnVsbCxcInVzZXJDb25zZW50XCI6bnVsbCxcIm5vbkludGVyYWN0aXZlU2Vzc2lvbnNFbmFibGVkXCI6bnVsbCxcImFzc29jaWF0ZWRJbnN0YW5jZUFyblwiOm51bGwsXCJpc0JhY2tmaWxsZWRcIjpmYWxzZSxcImhhc0luaXRpYWxTY29wZXNcIjp0cnVlLFwiYXJlQWxsU2NvcGVzQ29uc2VudGVkVG9cIjpmYWxzZSxcImlzRXhwaXJlZFwiOmZhbHNlLFwic3NvU2NvcGVzXCI6W10sXCJncm91cFNjb3Blc0J5RnJpZW5kbHlJZFwiOntcImNvZGV3aGlzcGVyZXJcIjpbe1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmNvbXBsZXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImNvbXBsZXRpb25zXCIsXCJ0eXBlXCI6XCJJbW11dGFibGVBY2Nlc3NTY29wZVwiLFwic2NvcGVUeXBlXCI6XCJBQ0NFU1NfU0NPUEVcIn0se1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmFuYWx5c2lzXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImFuYWx5c2lzXCIsXCJ0eXBlXCI6XCJJbW11dGFibGVBY2Nlc3NTY29wZVwiLFwic2NvcGVUeXBlXCI6XCJBQ0NFU1NfU0NPUEVcIn0se1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmNvbnZlcnNhdGlvbnNcIixcInN0YXR1c1wiOlwiSU5JVElBTFwiLFwiYXBwbGljYXRpb25Bcm5cIjpudWxsLFwiZnJpZW5kbHlJZFwiOlwiY29kZXdoaXNwZXJlclwiLFwidXNlQ2FzZUFjdGlvblwiOlwiY29udmVyc2F0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjp0YXNrYXNzaXN0XCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRhc2thc3Npc3RcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifSx7XCJmdWxsU2NvcGVcIjpcImNvZGV3aGlzcGVyZXI6dHJhbnNmb3JtYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRyYW5zZm9ybWF0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9XX0sXCJzaG91bGRHZXRWYWx1ZUZyb21UZW1wbGF0ZVwiOmZhbHNlLFwiaGFzUmVxdWVzdGVkU2NvcGVzXCI6ZmFsc2UsXCJjb250YWluc09ubHlTc29TY29wZXNcIjpmYWxzZSxcImlzVjFCYWNrZmlsbGVkXCI6ZmFsc2UsXCJpc1YyQmFja2ZpbGxlZFwiOmZhbHNlLFwiaXNWM0JhY2tmaWxsZWRcIjpmYWxzZSxcImlzVjRCYWNrZmlsbGVkXCI6ZmFsc2V9In0.DHISHGWVPbx_BWnB4tigfmkIfdhahaLPPpLgiMDOF9LeDhgbkeJXkIF2KGyjVABI"

REFRESH_TOKEN="aorAAAAAGmEpW0BqAaQuIlvPsiWVqoJmkeKZnS07JKg37G0CftWC8xmapxjxAHVSWLHZsbcr3m3uTotOQFGYYhTDMBkc0:MGUCMQDO++uHKayPaKZIj9+7vNJkYn2I/UZ+0UzpG3WozrQiDZEt2F2jfaQZ1WWMghJEnEcCMGHomY9yIQccpAqoCrltjwk9XIhRz9WX7wBX7usQbFTPMtCRAPfTs3docXGcUe13hQ"

# Optional - will be auto-refreshed if not provided
ACCESS_TOKEN="aoaAAAAAGkRr4sEyjhyYef2Y-TVdLH0WfkNxSG2lFVXy7-aSKw7b8mn_CDugFIEiWMKMtOWqcpjN2NFhZFu8Vi7eQBkc0:MGUCMQDfBTNPXYZdXlk8VYiRlYXNRUGnPMLWtWMrwYjkB+4bPYiIbkwJvBMQXbscxE8qCMMCMEzGFoTeh+E1IJbO5vTawT1eBn3oFfq8G/7IX79bncYNYuobPSa+60/PM9YruBQRaQ"
```

## Troubleshooting

### "Error: Not logged in"
Run: `npx wrangler login`

### "Error: No account_id"
1. Get your account ID: `npx wrangler whoami`
2. Add to `wrangler.toml`: `account_id = "your-id-here"`

### 403 Errors
Your access token may be expired. The worker will automatically refresh it using your refresh_token.

### Streaming not working
Make sure your client supports Server-Sent Events (SSE) and `stream: true` is set.

## Next Steps

1. Read the full [Deployment Guide](CLOUDFLARE_DEPLOYMENT.md)
2. Set up a custom domain
3. Add rate limiting for production
4. Monitor usage in Cloudflare dashboard

## Support

- Cloudflare Workers Docs: https://developers.cloudflare.com/workers/
- Issues: Check the logs with `npm run tail`
