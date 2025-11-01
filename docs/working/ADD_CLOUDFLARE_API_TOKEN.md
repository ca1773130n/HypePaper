# Add Cloudflare API Token to GitHub

## Quick Steps

### 1. Get Cloudflare API Token

1. **Go to Cloudflare Dashboard**
   - Open: https://dash.cloudflare.com/profile/api-tokens
   - Click **Create Token**

2. **Use "Edit Cloudflare Pages" Template**
   - Find template: **Edit Cloudflare Pages**
   - Click **Use template**

3. **Configure Permissions**
   - **Account Resources**: Select your account
   - **Zone Resources**: Include → All zones (or specific zone)
   - **Permissions**: Should auto-configure to:
     - Account → Cloudflare Pages → Edit
   - Click **Continue to summary**

4. **Create and Copy Token**
   - Review permissions
   - Click **Create Token**
   - **COPY THE TOKEN** (shown only once!)
   - Example: `abc123...xyz789`

### 2. Get Cloudflare Account ID

1. **Go to Cloudflare Dashboard**
   - Open: https://dash.cloudflare.com/
   - Select any domain

2. **Find Account ID**
   - Scroll down on right sidebar
   - Look for **Account ID** under "API"
   - Copy the ID
   - Example: `a1b2c3d4e5f6g7h8i9j0`

### 3. Add Secrets to GitHub

1. **Go to GitHub Repository Settings**
   - Open: https://github.com/ca1773130n/HypePaper/settings/secrets/actions
   - Click **New repository secret**

2. **Add CLOUDFLARE_API_TOKEN**
   - **Name**: `CLOUDFLARE_API_TOKEN`
   - **Value**: Paste your API token from Step 1
   - Click **Add secret**

3. **Add CLOUDFLARE_ACCOUNT_ID**
   - Click **New repository secret** again
   - **Name**: `CLOUDFLARE_ACCOUNT_ID`
   - **Value**: Paste your Account ID from Step 2
   - Click **Add secret**

### 4. Trigger Deployment

Push a commit to trigger GitHub Actions:

```bash
# Make a small change
echo "# Cloudflare deployment" >> README.md
git add README.md
git commit -m "chore: trigger Cloudflare Pages deployment"
git push
```

Or manually trigger workflow:
```bash
gh workflow run deploy.yml
```

### 5. Verify Deployment

1. **Check GitHub Actions**
   - Go to: https://github.com/ca1773130n/HypePaper/actions
   - Latest workflow should show:
     - ✅ Build Frontend
     - ✅ Deploy Frontend to Cloudflare Pages (instead of skipped)
     - ✅ Deploy Backend to Railway

2. **Check Cloudflare Pages**
   - Go to: https://dash.cloudflare.com/
   - Navigate to **Pages** in left sidebar
   - Should see **hypepaper** project
   - Latest deployment should be active

3. **Test Frontend**
   - Open: https://hypepaper.pages.dev (Cloudflare Pages URL)
   - Or: https://hypepaper.app (if custom domain configured)

## Expected GitHub Secrets

After adding tokens, your GitHub secrets should include:

**Required for Frontend Deployment:**
- ✅ `CLOUDFLARE_API_TOKEN` - API token from Cloudflare
- ✅ `CLOUDFLARE_ACCOUNT_ID` - Account ID from Cloudflare dashboard

**Required for Frontend Build:**
- ✅ `VITE_API_URL` - Example: `https://api.hypepaper.app`
- ✅ `VITE_SUPABASE_URL` - Your Supabase project URL
- ✅ `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key

**Optional for Railway:**
- ⏭️ `RAILWAY_TOKEN` - Only needed for CLI deployments

## Verify Secrets Are Set

```bash
# List all secrets (values hidden)
gh secret list

# Should show:
# CLOUDFLARE_API_TOKEN       Updated 2025-11-01
# CLOUDFLARE_ACCOUNT_ID      Updated 2025-11-01
# VITE_API_URL               Updated YYYY-MM-DD
# VITE_SUPABASE_URL          Updated YYYY-MM-DD
# VITE_SUPABASE_ANON_KEY     Updated YYYY-MM-DD
```

## Troubleshooting

### "Error: Input required and not supplied: apiToken"

**Cause:** `CLOUDFLARE_API_TOKEN` secret not set or named incorrectly

**Solution:**
- Verify secret name is exactly: `CLOUDFLARE_API_TOKEN` (all caps, underscores)
- Check secret exists: https://github.com/ca1773130n/HypePaper/settings/secrets/actions
- Token must have "Edit Cloudflare Pages" permissions

### "Error: Authentication failed"

**Cause:** Invalid or expired API token

**Solution:**
- Generate new API token from Cloudflare dashboard
- Update GitHub secret with new token value
- Re-run workflow

### Frontend Deployment Still Skipped

**Cause:** Workflow `if` condition not met

**Check:**
```yaml
# In .github/workflows/deploy.yml
if: github.ref == 'refs/heads/main' && secrets.CLOUDFLARE_API_TOKEN
```

**Solution:**
- Must push to `main` branch
- Secret must be named exactly `CLOUDFLARE_API_TOKEN`
- Re-run workflow after adding secret

### "Error: Failed to find Pages project"

**Cause:** Cloudflare Pages project doesn't exist or wrong name

**Solution:**
1. Create Pages project in Cloudflare dashboard
2. Name it exactly: `hypepaper`
3. Or update workflow `.github/workflows/deploy.yml` line 76:
   ```yaml
   projectName: your-actual-project-name
   ```

## Current Cloudflare Pages Project

**Project Name:** `hypepaper` (configured in workflow)

**Domain:** Check Cloudflare dashboard for:
- Default: `hypepaper.pages.dev`
- Custom: `hypepaper.app` (if configured)

## Next Steps After Adding Token

1. ✅ Add `CLOUDFLARE_API_TOKEN` secret
2. ✅ Add `CLOUDFLARE_ACCOUNT_ID` secret
3. ✅ Push commit or trigger workflow manually
4. ✅ Verify deployment succeeds in GitHub Actions
5. ✅ Test frontend at Cloudflare Pages URL
6. ⏭️ Configure Railway auto-deploy (see `RAILWAY_GITHUB_INTEGRATION_SETUP.md`)
7. ⏭️ Apply Supabase migration (see `COMPLETE_PROFILE_DEPLOYMENT.md`)

## Security Notes

- **Never commit** API tokens to git
- Tokens are stored securely in GitHub Secrets
- Only GitHub Actions workflows can access these secrets
- Rotate tokens periodically (every 90 days recommended)
- Use minimum required permissions for tokens

## References

- Cloudflare API Tokens: https://dash.cloudflare.com/profile/api-tokens
- GitHub Secrets: https://github.com/ca1773130n/HypePaper/settings/secrets/actions
- Cloudflare Pages Docs: https://developers.cloudflare.com/pages/
