# Quick Command Reference

## Setup Commands

```bash
# Install dependencies
npm install

# Login to Cloudflare
npx wrangler login

# Verify login
npx wrangler whoami
```

## Development Commands

```bash
# Run locally
npm run dev

# Test locally (curl)
curl http://localhost:8787/health

# Test chat endpoint
curl -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4.5","messages":[{"role":"user","content":"Hello!"}]}'
```

## Secrets Management

```bash
# Set CLIENT_ID
npx wrangler secret put CLIENT_ID
# Paste: KwJ4zvscaSQ8ZWU7SAu-0XVzLWVhc3QtMQ

# Set CLIENT_SECRET
npx wrangler secret put CLIENT_SECRET
# Paste: eyJraWQiOiJrZXktMTU2NDAyODA5OSIsImFsZyI6IkhTMzg0In0...

# Set REFRESH_TOKEN
npx wrangler secret put REFRESH_TOKEN
# Paste: aorAAAAAGmEpW0BqAaQuIlvPsiWVqoJmkeKZnS07JKg37G0CftWC8xmapxjxAHVSWLHZsbcr3m3uTotOQFGYYhTDMBkc0:MGUCMQDO++uHKayPaKZIj9+7vNJkYn2I/UZ+0UzpG3WozrQiDZEt2F2jfaQZ1WWMghJEnEcCMGHomY9yIQccpAqoCrltjwk9XIhRz9WX7wBX7usQbFTPMtCRAPfTs3docXGcUe13hQ

# Set ACCESS_TOKEN (optional)
npx wrangler secret put ACCESS_TOKEN
# Paste: aoaAAAAAGkRr4sEyjhyYef2Y-TVdLH0WfkNxSG2lFVXy7-aSKw7b8mn_CDugFIEiWMKMtOWqcpjN2NFhZFu8Vi7eQBkc0:MGUCMQDfBTNPXYZdXlk8VYiRlYXNRUGnPMLWtWMrwYjkB+4bPYiIbkwJvBMQXbscxE8qCMMCMEzGFoTeh+E1IJbO5vTawT1eBn3oFfq8G/7IX79bncYNYuobPSa+60/PM9YruBQRaQ

# List all secrets
npx wrangler secret list

# Delete a secret
npx wrangler secret delete SECRET_NAME
```

## Deployment Commands

```bash
# Deploy to development
npm run deploy

# Deploy to production
npm run deploy:production

# View deployment URL
npx wrangler deployments list
```

## Monitoring Commands

```bash
# View live logs
npm run tail

# View live logs with filter
npx wrangler tail --format pretty

# View deployments
npx wrangler deployments list
```

## Testing Commands

```bash
# Test health endpoint
curl https://your-worker.workers.dev/health

# Test OpenAI endpoint
curl -X POST https://your-worker.workers.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4.5","messages":[{"role":"user","content":"Hello!"}]}'

# Test Anthropic endpoint (streaming)
curl -X POST https://your-worker.workers.dev/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4.5","messages":[{"role":"user","content":"Tell me a joke"}],"stream":true}'

# List models
curl https://your-worker.workers.dev/v1/models
```

## KV Commands (Optional)

```bash
# Create KV namespace
npx wrangler kv:namespace create "CREDENTIALS"

# List KV namespaces
npx wrangler kv:namespace list

# Put value in KV
npx wrangler kv:key put --namespace-id=<id> "key" "value"

# Get value from KV
npx wrangler kv:key get --namespace-id=<id> "key"

# List keys in KV
npx wrangler kv:key list --namespace-id=<id>
```

## Troubleshooting Commands

```bash
# Check Wrangler version
npx wrangler --version

# View worker status
npx wrangler deployments list

# View worker configuration
cat wrangler.toml

# Check logs for errors
npm run tail | grep -i error

# Re-authenticate
npx wrangler logout
npx wrangler login
```

## Git Commands

```bash
# Check status
git status

# Add files
git add .

# Commit (but don't commit .dev.vars!)
git commit -m "Deploy Cloudflare Worker"

# Push to remote
git push origin main
```

## One-Line Deployment

```bash
# Complete deployment in one go (after login)
npm install && \
echo "KwJ4zvscaSQ8ZWU7SAu-0XVzLWVhc3QtMQ" | npx wrangler secret put CLIENT_ID && \
echo "<YOUR_CLIENT_SECRET>" | npx wrangler secret put CLIENT_SECRET && \
echo "<YOUR_REFRESH_TOKEN>" | npx wrangler secret put REFRESH_TOKEN && \
npm run deploy
```

## Environment Variables (Local Development)

The `.dev.vars` file is automatically loaded during local development:

```bash
# Edit local environment variables
nano .dev.vars

# Variables are automatically loaded with:
npm run dev
```

## Quick Test Script

Save as `test.sh`:

```bash
#!/bin/bash
BASE_URL="${1:-http://localhost:8787}"

echo "Testing health endpoint..."
curl "$BASE_URL/health"

echo -e "\n\nTesting chat completion..."
curl -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4.5","messages":[{"role":"user","content":"Say hi"}]}'

echo -e "\n\nTesting models list..."
curl "$BASE_URL/v1/models"
```

Usage:
```bash
chmod +x test.sh
./test.sh http://localhost:8787  # Local
./test.sh https://your-worker.workers.dev  # Production
```

## Dashboard URLs

```bash
# Open Cloudflare dashboard
open https://dash.cloudflare.com/

# Open worker directly
open "https://dash.cloudflare.com/$(npx wrangler whoami | grep 'Account ID' | awk '{print $3}')/workers/overview"
```

## Useful Aliases (Add to ~/.bashrc or ~/.zshrc)

```bash
alias cfw='npx wrangler'
alias cfw-dev='npm run dev'
alias cfw-deploy='npm run deploy'
alias cfw-logs='npm run tail'
alias cfw-login='npx wrangler login'
alias cfw-status='npx wrangler deployments list'
```

## Emergency Rollback

```bash
# View deployment history
npx wrangler deployments list

# Rollback to previous version
npx wrangler rollback --message "Rolling back to previous version"
```

## Complete Setup Script

Save as `setup.sh`:

```bash
#!/bin/bash
set -e

echo "=== Cloudflare Worker Setup ==="

echo "Installing dependencies..."
npm install

echo "Logging in to Cloudflare..."
npx wrangler login

echo "Setting secrets..."
echo "Enter CLIENT_ID:"
npx wrangler secret put CLIENT_ID

echo "Enter CLIENT_SECRET:"
npx wrangler secret put CLIENT_SECRET

echo "Enter REFRESH_TOKEN:"
npx wrangler secret put REFRESH_TOKEN

echo "Deploying worker..."
npm run deploy

echo "=== Setup Complete! ==="
echo "Your worker is now live!"
npx wrangler deployments list | head -n 2
```

Usage:
```bash
chmod +x setup.sh
./setup.sh
```

---

**Pro Tip**: Bookmark this file for quick reference!
