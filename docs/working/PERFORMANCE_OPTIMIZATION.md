# Performance Optimization - Bot Protection & Database Tuning

## 🚨 Problems Identified

### 1. Bot Traffic Overwhelming API
**Symptoms**:
- Traffic from multiple countries (Russia: 252 req/24h, Germany: 73, US: 326)
- Slow Supabase queries
- No rate limiting on API endpoints

**Impact**:
- Bots can exhaust database connections
- Legitimate users experience slow responses
- Database connection pool exhaustion

### 2. Small Database Connection Pool
**Before**:
- `pool_size=3`
- `max_overflow=2`
- **Total: Only 5 concurrent connections**

**Problem**:
- Slow queries from bots hold connections
- Pool exhausts quickly under load
- Legitimate requests wait for connections

## ✅ Solutions Implemented

### 1. Rate Limiting Middleware

Created `backend/src/middleware/rate_limiter.py`:

**Features**:
- ✅ 60 requests/minute per IP
- ✅ 1000 requests/hour per IP
- ✅ Respects `X-Forwarded-For` (Railway, Cloudflare)
- ✅ Returns 429 Too Many Requests when exceeded
- ✅ Adds rate limit headers to all responses
- ✅ Skips health check endpoints
- ✅ Auto-cleanup to prevent memory leaks

**Example Response Headers**:
```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Remaining-Hour: 873
```

**429 Response**:
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests from 1.2.3.4. Limit: 60/minute, 1000/hour",
  "retry_after": 60,
  "rate_info": {
    "requests_minute": 61,
    "limit_minute": 60,
    "requests_hour": 245,
    "limit_hour": 1000
  }
}
```

### 2. Increased Database Connection Pool

**Updated `backend/src/database.py`**:
```python
# Before
pool_size=3
max_overflow=2
# Total: 5 connections

# After
pool_size=10
max_overflow=5
# Total: 15 connections (3x increase)
```

**Benefits**:
- Handles 15 concurrent slow queries
- Better performance under load
- Still respects Supabase connection limits

### 3. Middleware Order

Added rate limiter as **outermost** middleware:
```python
app.add_middleware(RateLimiterMiddleware)  # FIRST - blocks bots early
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
```

## 📊 Expected Results

**Before**:
- 690 bot requests/24h = ~29 req/hour
- No rate limiting
- 5 database connections
- Slow responses during bot activity

**After**:
- Bots blocked after 60 req/minute
- Legitimate traffic protected
- 15 database connections
- Faster responses even with bots

## 🔍 Additional Recommendations

### 1. Check Supabase Region
Your database location affects latency. Check:
```bash
# In Railway, check:
echo $DATABASE_URL
# Look for region in hostname: aws-0-ap-northeast-2.pooler.supabase.com
```

**Current regions**:
- `ap-northeast-2` = Seoul, South Korea
- `us-east-1` = Virginia, USA
- `eu-central-1` = Frankfurt, Germany

**Recommendation**: If your users are in South Korea, `ap-northeast-2` is optimal.

### 2. Add Redis-Based Rate Limiting (Future)
Current implementation is in-memory (lost on restart). For production:
```bash
pip install slowapi redis
```

### 3. Add Cloudflare Bot Management (Optional)
Cloudflare Pages can block bots before they hit your API:
- Go to Cloudflare dashboard > Security > Bots
- Enable "Bot Fight Mode" (free)

### 4. Monitor Database Performance
In Supabase dashboard:
- Go to Database > Performance
- Check slow queries
- Add indexes if needed

### 5. Add Caching for Expensive Queries
Already have Redis configured - use it:
```python
from .services.cache_service import get_cache

# Cache expensive queries for 5 minutes
cache = get_cache()
cached_data = await cache.get("top_papers")
if not cached_data:
    cached_data = await expensive_query()
    await cache.set("top_papers", cached_data, ttl=300)
```

## 🧪 Testing Rate Limiting

Test the rate limiter works:

```bash
# Rapid requests (should get 429 after 60 requests)
for i in {1..65}; do
  curl -s https://api.hypepaper.app/api/v1/topics | head -1
  echo "Request $i"
done

# Check headers
curl -I https://api.hypepaper.app/api/v1/topics
# Should show:
# X-RateLimit-Limit-Minute: 60
# X-RateLimit-Remaining-Minute: 59
```

## 📈 Monitoring

Watch Railway logs for:
```
429 Too Many Requests
Rate limit exceeded
```

This indicates the rate limiter is protecting your API!

## 🔐 Security Benefits

Rate limiting also protects against:
- **DDoS attacks** - Limits damage from attack traffic
- **Brute force** - Slows down password guessing
- **API scraping** - Prevents data theft
- **Cost control** - Limits Supabase query usage

## ⚙️ Configuration

To adjust limits, edit `backend/src/main.py`:
```python
app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=100,  # Increase for higher traffic
    requests_per_hour=2000,   # Increase for higher traffic
)
```

**Conservative (current)**: 60/min, 1000/hour
**Moderate**: 100/min, 2000/hour
**Aggressive**: 200/min, 5000/hour

Start conservative, increase if legitimate users hit limits.
