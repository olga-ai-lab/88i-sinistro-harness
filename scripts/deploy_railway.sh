#!/bin/bash

set -e

echo "🚀 Deploying to Railway..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "Logging in to Railway..."
railway login

# Link project
echo "Linking Railway project..."
railway link

# Set environment variables
echo "Setting environment variables..."
railway variables set ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
railway variables set SUPABASE_URL=$SUPABASE_URL
railway variables set SUPABASE_KEY=$SUPABASE_KEY
railway variables set INNGEST_API_KEY=$INNGEST_API_KEY
railway variables set LANGFUSE_PUBLIC_KEY=$LANGFUSE_PUBLIC_KEY
railway variables set LANGFUSE_SECRET_KEY=$LANGFUSE_SECRET_KEY
railway variables set ENVIRONMENT=production

# Deploy
echo "Deploying application..."
railway up

echo "✅ Deployment complete!"
echo "Application URL: $(railway status)"
