# GitHub Actions Setup Guide

This document explains how to configure GitHub Actions secrets for automated deployments.

## Current Workflow Status

The GitHub Actions workflow has been configured to:
- ✅ **Always run**: Build and validate the frontend code
- ⚠️ **Conditionally run**: Deploy only when secrets are configured

## Required Secrets (Optional)

Deployments are **optional**. The workflow will build and test your code even without these secrets. Configure them only if you want automated deployments.

### For Cloudflare Pages Deployment

To enable frontend deployment to Cloudflare Pages:

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add the following repository secrets:

| Secret Name | Description | How to Get It |
|------------|-------------|---------------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with Pages access | 1. Go to Cloudflare Dashboard<br>2. My Profile → API Tokens<br>3. Create Token → "Edit Cloudflare Workers" template<br>4. Add "Cloudflare Pages:Edit" permission |
| `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare account ID | 1. Go to Cloudflare Dashboard<br>2. Workers & Pages → Overview<br>3. Copy Account ID from the right sidebar |
| `VITE_API_URL` | Your production API URL | Example: `https://your-backend.railway.app` |
| `VITE_SUPABASE_URL` | Your Supabase project URL | From Supabase project settings |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anonymous key | From Supabase project settings |

### For Railway Backend Deployment

To enable backend deployment to Railway:

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add the following repository secret:

| Secret Name | Description | How to Get It |
|------------|-------------|---------------|
| `RAILWAY_TOKEN` | Railway deployment token | 1. Install Railway CLI: `npm i -g @railway/cli`<br>2. Login: `railway login`<br>3. Generate token: `railway tokens` |

## Testing Without Deployment

You can test the workflow without configuring deployment secrets:

1. Push code to `main` or any `claude/**` branch
2. The workflow will:
   - ✅ Checkout code
   - ✅ Setup Node.js with npm caching
   - ✅ Install dependencies
   - ✅ Build the frontend
   - ✅ Upload build artifacts
   - ⏭️ Skip deployment steps (no secrets configured)

## Workflow Files

- `.github/workflows/deploy.yml` - Main deployment workflow
- `.github/workflows/claude-flow-tasks.yml` - Claude Flow automation

## Troubleshooting

### "Some specified paths were not resolved, unable to cache dependencies"
✅ Fixed - `package-lock.json` is now committed to the repository

### "Unauthorized. Please login with railway login"
⚠️ Expected when `RAILWAY_TOKEN` secret is not configured. The job will be skipped.

### "Input required and not supplied: apiToken"
⚠️ Expected when `CLOUDFLARE_API_TOKEN` secret is not configured. The job will be skipped.

## Benefits of Configuring Secrets

Once secrets are configured, every push to `main` or `claude/**` branches will:
- 🚀 Automatically deploy frontend to Cloudflare Pages
- 🚀 Automatically deploy backend to Railway
- ✅ Provide deployment URLs in PR comments
- 📊 Track deployment history

## Default Behavior Without Secrets

Without deployment secrets, the workflow still provides value:
- ✅ Validates code builds successfully
- ✅ Catches build errors before merging
- ✅ Ensures dependencies are installable
- ✅ Provides build artifacts for manual deployment

---

**Need help?** Check the [GitHub Actions documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets) for more information on secrets management.
