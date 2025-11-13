# Amazon Q to OpenAI/Anthropic API Bridge - Cloudflare Worker Deployment Guide

## Overview

This guide will help you deploy your Amazon Q to OpenAI/Anthropic API bridge on Cloudflare Workers. The TypeScript implementation is already complete and ready to deploy!

## What's Been Done

The Python Flask application has been successfully converted to a Cloudflare Worker with the following features:

- **OpenAI API compatibility** - `/v1/chat/completions` endpoint
- **Anthropic API compatibility** - `/v1/messages` endpoint
- **Streaming support** - Real-time SSE streaming for both formats
- **Automatic token refresh** - Handles token expiration automatically
- **Auto-scaling** - Deployed to 270+ edge locations worldwide
- **Zero maintenance** - No servers to manage

## Prerequisites

1. **Node.js** (v16 or higher) - Already available in your sandbox
2. **Cloudflare Account** - Sign up at https://dash.cloudflare.com/sign-up (Free tier available)
3. **Amazon Q Credentials** - Already configured in `.dev.vars`

## Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
npm install
```

### Step 2: Test Locally

Run the worker locally to test it:

```bash
npm run dev
```

The worker will start at `http://localhost:8787`

Test it with curl:

```bash
# Test health endpoint
curl http://localhost:8787/health

# Test chat completion (OpenAI format)
curl -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test streaming (Anthropic format)
curl -X POST http://localhost:8787/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Tell me a joke"}],
    "stream": true
  }'
```

### Step 3: Login to Cloudflare

```bash
npx wrangler login
```

This will open a browser window to authenticate with Cloudflare.

### Step 4: Set Your Secrets

For production deployment, you need to set your credentials as secrets (not in `.dev.vars`):

```bash
# Set CLIENT_ID
npx wrangler secret put CLIENT_ID
# Paste: KwJ4zvscaSQ8ZWU7SAu-0XVzLWVhc3QtMQ

# Set CLIENT_SECRET
npx wrangler secret put CLIENT_SECRET
# Paste: eyJraWQiOiJrZXktMTU2NDAyODA5OSIsImFsZyI6IkhTMzg0In0.eyJzZXJpYWxpemVkIjoie1wiY2xpZW50SWRcIjp7XCJ2YWx1ZVwiOlwiS3dKNHp2c2NhU1E4WldVN1NBdS0wWFZ6TFdWaGMzUXRNUVwifSxcImlkZW1wb3RlbnRLZXlcIjpudWxsLFwidGVuYW50SWRcIjpudWxsLFwiY2xpZW50TmFtZVwiOlwiQVdTIElERSBFeHRlbnNpb25zIGZvciBWU0NvZGVcIixcImJhY2tmaWxsVmVyc2lvblwiOm51bGwsXCJjbGllbnRUeXBlXCI6XCJQVUJMSUNcIixcInRlbXBsYXRlQXJuXCI6bnVsbCxcInRlbXBsYXRlQ29udGV4dFwiOm51bGwsXCJleHBpcmF0aW9uVGltZXN0YW1wXCI6MTc3MDMxMTEwMy4wMzk5OTczOTQsXCJjcmVhdGVkVGltZXN0YW1wXCI6MTc2MjUzNTEwMy4wMzk5OTczOTQsXCJ1cGRhdGVkVGltZXN0YW1wXCI6MTc2MjUzNTEwMy4wMzk5OTczOTQsXCJjcmVhdGVkQnlcIjpudWxsLFwidXBkYXRlZEJ5XCI6bnVsbCxcInN0YXR1c1wiOm51bGwsXCJpbml0aWF0ZUxvZ2luVXJpXCI6XCJodHRwczpcL1wvdmlldy5hd3NhcHBzLmNvbVwvc3RhcnRcL1wiLFwiZW50aXRsZWRSZXNvdXJjZUlkXCI6bnVsbCxcImVudGl0bGVkUmVzb3VyY2VDb250YWluZXJJZFwiOm51bGwsXCJleHRlcm5hbElkXCI6bnVsbCxcInNvZnR3YXJlSWRcIjpudWxsLFwic2NvcGVzXCI6W3tcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjpjb21wbGV0aW9uc1wiLFwic3RhdHVzXCI6XCJJTklUSUFMXCIsXCJhcHBsaWNhdGlvbkFyblwiOm51bGwsXCJmcmllbmRseUlkXCI6XCJjb2Rld2hpc3BlcmVyXCIsXCJ1c2VDYXNlQWN0aW9uXCI6XCJjb21wbGV0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjphbmFseXNpc1wiLFwic3RhdHVzXCI6XCJJTklUSUFMXCIsXCJhcHBsaWNhdGlvbkFyblwiOm51bGwsXCJmcmllbmRseUlkXCI6XCJjb2Rld2hpc3BlcmVyXCIsXCJ1c2VDYXNlQWN0aW9uXCI6XCJhbmFseXNpc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjpjb252ZXJzYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImNvbnZlcnNhdGlvbnNcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifSx7XCJmdWxsU2NvcGVcIjpcImNvZGV3aGlzcGVyZXI6dHJhbnNmb3JtYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRyYW5zZm9ybWF0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjp0YXNrYXNzaXN0XCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRhc2thc3Npc3RcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifV0sXCJhdXRoZW50aWNhdGlvbkNvbmZpZ3VyYXRpb25cIjpudWxsLFwic2hhZG93QXV0aGVudGljYXRpb25Db25maWd1cmF0aW9uXCI6bnVsbCxcImVuYWJsZWRHcmFudHNcIjp7XCJBVVRIX0NPREVcIjp7XCJ0eXBlXCI6XCJJbW11dGFibGVBdXRob3JpemF0aW9uQ29kZUdyYW50T3B0aW9uc1wiLFwicmVkaXJlY3RVcmlzXCI6W1wiaHR0cDpcL1wvMTI3LjAuMC4xXC9vYXV0aFwvY2FsbGJhY2tcIl19LFwiUkVGUkVTSF9UT0tFTlwiOntcInR5cGVcIjpcIkltbXV0YWJsZVJlZnJlc2hUb2tlbkdyYW50T3B0aW9uc1wifX0sXCJlbmZvcmNlQXV0aE5Db25maWd1cmF0aW9uXCI6bnVsbCxcIm93bmVyQWNjb3VudElkXCI6bnVsbCxcInNzb0luc3RhbmNlQWNjb3VudElkXCI6bnVsbCxcInVzZXJDb25zZW50XCI6bnVsbCxcIm5vbkludGVyYWN0aXZlU2Vzc2lvbnNFbmFibGVkXCI6bnVsbCxcImFzc29jaWF0ZWRJbnN0YW5jZUFyblwiOm51bGwsXCJpc0JhY2tmaWxsZWRcIjpmYWxzZSxcImhhc0luaXRpYWxTY29wZXNcIjp0cnVlLFwiYXJlQWxsU2NvcGVzQ29uc2VudGVkVG9cIjpmYWxzZSxcImlzRXhwaXJlZFwiOmZhbHNlLFwic3NvU2NvcGVzXCI6W10sXCJncm91cFNjb3Blc0J5RnJpZW5kbHlJZFwiOntcImNvZGV3aGlzcGVyZXJcIjpbe1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmNvbXBsZXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImNvbXBsZXRpb25zXCIsXCJ0eXBlXCI6XCJJbW11dGFibGVBY2Nlc3NTY29wZVwiLFwic2NvcGVUeXBlXCI6XCJBQ0NFU1NfU0NPUEVcIn0se1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmFuYWx5c2lzXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcImFuYWx5c2lzXCIsXCJ0eXBlXCI6XCJJbW11dGFibGVBY2Nlc3NTY29wZVwiLFwic2NvcGVUeXBlXCI6XCJBQ0NFU1NfU0NPUEVcIn0se1wiZnVsbFNjb3BlXCI6XCJjb2Rld2hpc3BlcmVyOmNvbnZlcnNhdGlvbnNcIixcInN0YXR1c1wiOlwiSU5JVElBTFwiLFwiYXBwbGljYXRpb25Bcm5cIjpudWxsLFwiZnJpZW5kbHlJZFwiOlwiY29kZXdoaXNwZXJlclwiLFwidXNlQ2FzZUFjdGlvblwiOlwiY29udmVyc2F0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9LHtcImZ1bGxTY29wZVwiOlwiY29kZXdoaXNwZXJlcjp0YXNrYXNzaXN0XCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRhc2thc3Npc3RcIixcInR5cGVcIjpcIkltbXV0YWJsZUFjY2Vzc1Njb3BlXCIsXCJzY29wZVR5cGVcIjpcIkFDQ0VTU19TQ09QRVwifSx7XCJmdWxsU2NvcGVcIjpcImNvZGV3aGlzcGVyZXI6dHJhbnNmb3JtYXRpb25zXCIsXCJzdGF0dXNcIjpcIklOSVRJQUxcIixcImFwcGxpY2F0aW9uQXJuXCI6bnVsbCxcImZyaWVuZGx5SWRcIjpcImNvZGV3aGlzcGVyZXJcIixcInVzZUNhc2VBY3Rpb25cIjpcInRyYW5zZm9ybWF0aW9uc1wiLFwidHlwZVwiOlwiSW1tdXRhYmxlQWNjZXNzU2NvcGVcIixcInNjb3BlVHlwZVwiOlwiQUNDRVNTX1NDT1BFXCJ9XX0sXCJzaG91bGRHZXRWYWx1ZUZyb21UZW1wbGF0ZVwiOmZhbHNlLFwiaGFzUmVxdWVzdGVkU2NvcGVzXCI6ZmFsc2UsXCJjb250YWluc09ubHlTc29TY29wZXNcIjpmYWxzZSxcImlzVjFCYWNrZmlsbGVkXCI6ZmFsc2UsXCJpc1YyQmFja2ZpbGxlZFwiOmZhbHNlLFwiaXNWM0JhY2tmaWxsZWRcIjpmYWxzZSxcImlzVjRCYWNrZmlsbGVkXCI6ZmFsc2V9In0.DHISHGWVPbx_BWnB4tigfmkIfdhahaLPPpLgiMDOF9LeDhgbkeJXkIF2KGyjVABI

# Set REFRESH_TOKEN
npx wrangler secret put REFRESH_TOKEN
# Paste: aorAAAAAGmEpW0BqAaQuIlvPsiWVqoJmkeKZnS07JKg37G0CftWC8xmapxjxAHVSWLHZsbcr3m3uTotOQFGYYhTDMBkc0:MGUCMQDO++uHKayPaKZIj9+7vNJkYn2I/UZ+0UzpG3WozrQiDZEt2F2jfaQZ1WWMghJEnEcCMGHomY9yIQccpAqoCrltjwk9XIhRz9WX7wBX7usQbFTPMtCRAPfTs3docXGcUe13hQ

# Set ACCESS_TOKEN (optional, will auto-refresh)
npx wrangler secret put ACCESS_TOKEN
# Paste: aoaAAAAAGkRr4sEyjhyYef2Y-TVdLH0WfkNxSG2lFVXy7-aSKw7b8mn_CDugFIEiWMKMtOWqcpjN2NFhZFu8Vi7eQBkc0:MGUCMQDfBTNPXYZdXlk8VYiRlYXNRUGnPMLWtWMrwYjkB+4bPYiIbkwJvBMQXbscxE8qCMMCMEzGFoTeh+E1IJbO5vTawT1eBn3oFfq8G/7IX79bncYNYuobPSa+60/PM9YruBQRaQ
```

### Step 5: Deploy to Production

```bash
npm run deploy
```

That's it! Your worker is now live on Cloudflare's global network.

You'll see output like:

```
Published amazonq-openai-bridge (X.XX sec)
  https://amazonq-openai-bridge.<your-subdomain>.workers.dev
```

## API Endpoints

Once deployed, your worker exposes these endpoints:

### OpenAI Compatible

```bash
POST https://your-worker.workers.dev/v1/chat/completions
POST https://your-worker.workers.dev/v1/models
```

### Anthropic Compatible

```bash
POST https://your-worker.workers.dev/v1/messages
```

### Management

```bash
GET  https://your-worker.workers.dev/health
POST https://your-worker.workers.dev/credentials
GET  https://your-worker.workers.dev/
```

## Usage Examples

### OpenAI SDK (Python)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-worker.workers.dev/v1",
    api_key="dummy"  # Not used, but required by SDK
)

response = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### Anthropic SDK (Python)

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://your-worker.workers.dev",
    api_key="dummy"  # Not used, but required by SDK
)

response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.content[0].text)
```

### Curl

```bash
# OpenAI format
curl -X POST https://your-worker.workers.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Write a haiku about clouds"}]
  }'

# Anthropic format with streaming
curl -X POST https://your-worker.workers.dev/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Tell me a joke"}],
    "stream": true
  }'
```

## Monitoring and Debugging

### View Real-time Logs

```bash
npm run tail
```

This shows live logs from your deployed worker.

### View in Dashboard

Visit https://dash.cloudflare.com/ and navigate to:
- Workers & Pages > Your Worker > Metrics (for analytics)
- Workers & Pages > Your Worker > Logs (for historical logs)

## Advanced Configuration

### Custom Domain

You can map a custom domain to your worker:

1. Go to Cloudflare Dashboard > Workers & Pages
2. Click on your worker
3. Go to Settings > Triggers
4. Add a custom domain

### KV Storage (Optional)

For persistent credential storage across requests:

```bash
# Create KV namespace
npx wrangler kv:namespace create "CREDENTIALS"

# Add to wrangler.toml
[[kv_namespaces]]
binding = "CREDENTIALS"
id = "your-kv-namespace-id"
```

### Environment Variables

Edit `wrangler.toml` to customize:

```toml
[vars]
AMAZONQ_ENDPOINT = "https://codewhisperer.us-east-1.amazonaws.com"
SSO_OIDC_ENDPOINT = "https://oidc.us-east-1.amazonaws.com"
LOG_REQUESTS = "true"
LOG_RESPONSES = "true"
TOKEN_REFRESH_MARGIN = "300"
```

## Pricing

Cloudflare Workers Free Tier includes:
- **100,000 requests per day**
- **10ms CPU time per request**
- **Unlimited bandwidth**

Paid plan ($5/month):
- **10 million requests per month**
- **50ms CPU time per request**
- **Unlimited bandwidth**

## Troubleshooting

### Issue: "Failed to publish"

**Solution**: Make sure you're logged in:
```bash
npx wrangler login
npx wrangler whoami
```

### Issue: "403 Forbidden" from Amazon Q

**Solution**: Your access token may have expired. The worker will automatically refresh it, or you can update it manually:
```bash
npx wrangler secret put REFRESH_TOKEN
```

### Issue: "No response from worker"

**Solution**: Check logs:
```bash
npm run tail
```

### Issue: "CORS errors in browser"

**Solution**: CORS is already configured. Make sure you're using the correct worker URL.

## Security Best Practices

1. **Never commit `.dev.vars`** - It's already in `.gitignore`
2. **Use secrets for production** - Always use `wrangler secret put` for sensitive data
3. **Rotate tokens regularly** - Update your Amazon Q tokens periodically
4. **Monitor usage** - Check Cloudflare dashboard for unusual activity
5. **Use custom domains** - Map a custom domain for professional use

## Next Steps

- Read `README_CLOUDFLARE.md` for detailed feature documentation
- Read `QUICK_START.md` for additional examples
- Read `CLOUDFLARE_DEPLOYMENT.md` for advanced deployment scenarios
- Check `PROJECT_STRUCTURE.txt` for codebase overview

## Support

- **Cloudflare Workers**: https://developers.cloudflare.com/workers/
- **Wrangler CLI**: https://developers.cloudflare.com/workers/wrangler/
- **Cloudflare Community**: https://community.cloudflare.com/

---

**Congratulations!** Your Amazon Q to OpenAI/Anthropic API bridge is now running on Cloudflare's global edge network! 🚀
