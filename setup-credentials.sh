#!/bin/bash

# Setup script for Amazon Q credentials
# This script helps you set up your credentials for Cloudflare Workers

set -e

echo "================================================"
echo "Amazon Q to OpenAI Bridge - Credential Setup"
echo "================================================"
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "Error: wrangler is not installed"
    echo "Please run: npm install"
    exit 1
fi

# Check if logged in
if ! wrangler whoami &> /dev/null; then
    echo "You need to log in to Cloudflare first"
    echo "Running: wrangler login"
    wrangler login
fi

echo "Setting up secrets for Cloudflare Workers..."
echo ""

# Ask for environment
echo "Which environment? (default: production)"
echo "  1) production (default)"
echo "  2) dev"
read -p "Enter choice [1]: " env_choice
env_choice=${env_choice:-1}

ENV_FLAG=""
if [ "$env_choice" == "2" ]; then
    ENV_FLAG="--env dev"
    echo "Using development environment"
else
    echo "Using production environment"
fi

echo ""
echo "Please provide your Amazon Q credentials:"
echo ""

# CLIENT_ID
echo "CLIENT_ID (from your config):"
read -p "> " CLIENT_ID
echo "$CLIENT_ID" | wrangler secret put CLIENT_ID $ENV_FLAG

echo ""

# CLIENT_SECRET
echo "CLIENT_SECRET (from your config):"
read -p "> " CLIENT_SECRET
echo "$CLIENT_SECRET" | wrangler secret put CLIENT_SECRET $ENV_FLAG

echo ""

# REFRESH_TOKEN
echo "REFRESH_TOKEN (from your config):"
read -p "> " REFRESH_TOKEN
echo "$REFRESH_TOKEN" | wrangler secret put REFRESH_TOKEN $ENV_FLAG

echo ""

# ACCESS_TOKEN (optional)
read -p "Do you want to set ACCESS_TOKEN? (optional, can be auto-refreshed) [y/N]: " set_access_token
if [[ $set_access_token =~ ^[Yy]$ ]]; then
    echo "ACCESS_TOKEN:"
    read -p "> " ACCESS_TOKEN
    echo "$ACCESS_TOKEN" | wrangler secret put ACCESS_TOKEN $ENV_FLAG
fi

echo ""
echo "================================================"
echo "Credentials setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Test locally: npm run dev"
echo "  2. Deploy: npm run deploy:production"
echo ""
