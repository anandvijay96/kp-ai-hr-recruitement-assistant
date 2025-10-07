# 🌐 Browserless Setup for Railway

## Why Browserless?

Installing Chrome/Chromium in Railway containers is problematic:
- ❌ Large dependencies slow down builds
- ❌ Version compatibility issues
- ❌ Complex setup

**Browserless solves this** by providing a separate browser service!

---

## 📦 Setup Steps

### **Step 1: Deploy Browserless Template**

1. Go to: **https://railway.app/template/browserless**
2. Click **"Deploy Now"**
3. This creates a new Browserless service in your Railway project

### **Step 2: Link Services**

In your **ai-hr-assistant** service on Railway:

1. Go to **Variables** tab
2. Add these **Reference Variables**:

```bash
BROWSER_WEBDRIVER_ENDPOINT=${{Browserless.BROWSER_WEBDRIVER_ENDPOINT}}
BROWSER_TOKEN=${{Browserless.BROWSER_TOKEN}}
```

**How to add:**
- Click **"+ New Variable"**
- Select **"Add Reference"**
- Choose `Browserless` service
- Select `BROWSER_WEBDRIVER_ENDPOINT`
- Repeat for `BROWSER_TOKEN`

### **Step 3: Deploy**

That's it! The application will automatically:
- ✅ Detect Browserless environment variables
- ✅ Connect to Browserless service
- ✅ Use remote Chrome browser
- ✅ Perform LinkedIn verification

---

## 🧪 Verification

After deployment, check logs for:

```
INFO: Initializing Chrome WebDriver for LinkedIn verification...
INFO: Using Browserless service for Chrome WebDriver
INFO: ✅ Connected to Browserless service
INFO: Navigating to DuckDuckGo: https://duckduckgo.com/?q=...
INFO: ✅ Found DuckDuckGo search results
INFO: Found LinkedIn link: https://www.linkedin.com/in/vijay-anand-bommaji
INFO: ✅ LinkedIn cross-verified (exact)
```

---

## 💡 How It Works

### **Local Development:**
```python
# Uses local Chrome/Chromium
driver = webdriver.Chrome(options=chrome_options)
```

### **Railway (with Browserless):**
```python
# Uses remote Browserless service
driver = webdriver.Remote(
    command_executor=os.environ['BROWSER_WEBDRIVER_ENDPOINT'],
    options=chrome_options
)
```

The code automatically detects the environment and uses the appropriate driver!

---

## ✅ Benefits

| Feature | Local Chrome | Browserless |
|---------|-------------|-------------|
| **Setup** | Install Chrome | Just deploy template |
| **Build Time** | Slow (large deps) | ✅ Fast |
| **Maintenance** | Manual updates | ✅ Auto-updated |
| **Reliability** | Version conflicts | ✅ Always works |
| **Cost** | Free | ~$5/month |

---

## 🔗 Resources

- **Browserless Template:** https://railway.app/template/browserless
- **Example Repo:** https://github.com/brody192/selenium-example-python
- **Browserless Docs:** https://www.browserless.io/docs

---

**With Browserless, LinkedIn verification will work perfectly on Railway!** 🚀
