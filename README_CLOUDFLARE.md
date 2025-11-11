# Amazon Q to OpenAI/Anthropic API Bridge - Cloudflare Worker Edition

Transform Amazon Q API into OpenAI and Anthropic compatible endpoints, deployed globally on Cloudflare's edge network.

## Features

- **OpenAI Compatible**: Drop-in replacement for OpenAI API
- **Anthropic Compatible**: Native Anthropic Messages API support
- **Streaming Support**: Real-time Server-Sent Events (SSE)
- **Global Edge Network**: Deployed to 270+ cities worldwide
- **Auto-Scaling**: Handles any load automatically
- **Token Management**: Automatic OAuth token refresh
- **Zero Infrastructure**: No servers to manage
- **Free Tier**: 100,000 requests per day included

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Setup Credentials

```bash
# Login to Cloudflare
npx wrangler login

# Setup your Amazon Q credentials
./setup-credentials.sh
```

### 3. Deploy

```bash
# Test locally
npm run dev

# Deploy to production
npm run deploy:production
```

That's it! Your API bridge is now running globally.

## Usage

### With OpenAI SDK (Python)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-worker.workers.dev/v1",
    api_key="dummy"  # Not used but required
)

response = client.chat.completions.create(
    model="claude-sonnet-4.5",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

print(response.choices[0].message.content)
```

### With Anthropic SDK (Python)

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://your-worker.workers.dev",
    api_key="dummy"  # Not used but required
)

response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
)

print(response.content[0].text)
```

### With cURL

```bash
curl -X POST https://your-worker.workers.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

## Available Endpoints

- `POST /v1/chat/completions` - OpenAI compatible chat endpoint
- `POST /v1/messages` - Anthropic compatible messages endpoint
- `GET /v1/models` - List available models
- `GET /health` - Health check
- `POST /credentials` - Update credentials
- `GET /` - API information

## Available Models

- `claude-sonnet-4.5` (default)
- `claude-sonnet-4`
- `amazon-q`

## Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[Deployment Guide](CLOUDFLARE_DEPLOYMENT.md)** - Comprehensive deployment instructions
- **[Migration Summary](MIGRATION_SUMMARY.md)** - Python to Cloudflare Worker migration details

## Project Structure

```
.
├── src/
│   └── index.ts              # Main worker application
├── wrangler.toml             # Cloudflare Worker configuration
├── package.json              # Node.js dependencies
├── tsconfig.json             # TypeScript configuration
├── setup-credentials.sh      # Interactive setup script
├── QUICK_START.md           # Quick start guide
├── CLOUDFLARE_DEPLOYMENT.md # Full deployment guide
└── MIGRATION_SUMMARY.md     # Migration details
```

## Configuration

### Environment Variables

Set via Cloudflare dashboard or `wrangler.toml`:

- `AMAZONQ_ENDPOINT` - Amazon Q API endpoint (default: https://codewhisperer.us-east-1.amazonaws.com)
- `SSO_OIDC_ENDPOINT` - AWS SSO OIDC endpoint (default: https://oidc.us-east-1.amazonaws.com)
- `LOG_REQUESTS` - Log incoming requests (default: true)
- `LOG_RESPONSES` - Log responses (default: true)

### Secrets

Set via `wrangler secret put <NAME>` or setup script:

- `CLIENT_ID` - Amazon Q OAuth client ID (required)
- `CLIENT_SECRET` - Amazon Q OAuth client secret (required)
- `REFRESH_TOKEN` - Amazon Q OAuth refresh token (required)
- `ACCESS_TOKEN` - Amazon Q access token (optional, auto-refreshed)

## Development

### Local Development

```bash
npm run dev
```

Server runs at `http://localhost:8787`

### View Logs

```bash
npm run tail
```

### Deploy

```bash
# Deploy to production
npm run deploy:production

# Deploy to development
npm run deploy
```

## Monitoring

Monitor your worker in the Cloudflare dashboard:
- Request analytics
- Error rates
- Performance metrics
- Global traffic distribution

Access at: https://dash.cloudflare.com/

## Cost

**Free Tier (Included):**
- 100,000 requests per day
- 10ms CPU time per request
- More than sufficient for most personal and small business use

**Paid Plans:**
- Unlimited requests ($5/month)
- 50ms CPU time per request
- 15-minute maximum duration (vs 30 seconds free)

## Advantages Over Self-Hosted

| Feature | Self-Hosted | Cloudflare Worker |
|---------|-------------|-------------------|
| Setup Time | Hours | Minutes |
| Global Deployment | Manual/Expensive | Automatic |
| Scaling | Manual | Automatic |
| Cost | $5-50+/month | Free - $5/month |
| Latency | Single location | 270+ edge locations |
| DDoS Protection | Manual | Built-in |
| SSL/TLS | Manual setup | Automatic |
| Maintenance | Regular updates | Zero maintenance |

## Security

- Credentials stored as encrypted secrets
- Automatic HTTPS for all requests
- Built-in DDoS protection
- No exposed infrastructure
- Regular security updates by Cloudflare

## Troubleshooting

### 403 Errors
Your access token may be expired. The worker automatically refreshes it using your refresh token.

### Not Found
Make sure you're using the correct endpoint URL from your deployment output.

### Streaming Not Working
Ensure your client supports Server-Sent Events (SSE) and `stream: true` is set in the request.

### View Detailed Logs
```bash
npm run tail
```

## Support

- **Documentation**: See the docs folder
- **Cloudflare Workers**: https://developers.cloudflare.com/workers/
- **Issues**: Check logs with `npm run tail`

## License

MIT

## Acknowledgments

- Built on Cloudflare Workers platform
- Compatible with OpenAI and Anthropic SDKs
- Powered by Amazon Q API

---

**Get Started Now**: See [QUICK_START.md](QUICK_START.md) for step-by-step instructions!
