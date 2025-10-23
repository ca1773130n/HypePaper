# ⚠️ Important: Cloudflare Pages Build Configuration

## Build Settings

Since `package-lock.json` is not in the repository, you need to configure Cloudflare Pages to use `npm install` instead of the default `npm ci`.

### In Cloudflare Pages Dashboard:

**Settings > Builds & Deployments > Build configurations**

```
Framework preset: None (or select Vite but we'll override)
Build command: cd frontend && npm install && npm run build
Build output directory: frontend/dist
Root directory: (leave empty)

OR if Root directory is set to "frontend":
Build command: npm install && npm run build
Build output directory: dist
Root directory: frontend
```

### Why This Change?

- `npm ci` requires `package-lock.json` to exist
- `npm install` works without a lockfile
- It will generate lockfile locally but won't commit it (gitignored)

### Alternative: Use package-lock.json (Recommended for Production)

If you prefer reproducible builds, you can:
1. Remove `package-lock.json` from `.gitignore`
2. Commit it to the repository
3. Use `npm ci` for faster, more reliable builds

But since you explicitly don't want it in the repo, use `npm install` as shown above.
