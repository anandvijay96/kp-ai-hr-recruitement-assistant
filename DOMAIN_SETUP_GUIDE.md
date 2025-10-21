# 🌐 Domain Setup Guide - hrms.kloudportal.com

Complete guide to connecting your custom domain to the Dokploy-deployed application.

---

## **📋 Your Configuration (Screenshot 2)**

**Perfect Configuration! ✅**

Your Dokploy settings are correct:

```
Host: hrms.kloudportal.com
Path: /
Internal Path: /
Container Port: 3000
HTTPS: ✅ Enabled
Certificate Provider: Let's Encrypt ✅
```

**This is exactly right!** No changes needed in Dokploy.

---

## **🔐 SSL Certificate (Let's Encrypt)**

### **Is it Free?**
✅ **YES! Completely FREE!**

**Let's Encrypt provides:**
- Free SSL certificates
- Auto-renewal every 90 days
- Trusted by all browsers
- No configuration needed

**Dokploy handles everything automatically:**
1. Requests certificate from Let's Encrypt
2. Installs it on your domain
3. Auto-renews before expiration
4. No manual intervention required

**Cost: $0.00** 🎉

---

## **📝 GoDaddy DNS Configuration**

### **Step-by-Step Instructions:**

#### **1. Login to GoDaddy**
- Go to: https://godaddy.com
- Login to your account
- Click "My Products"
- Find `kloudportal.com` domain
- Click "DNS" or "Manage DNS"

---

#### **2. Add A Record for Subdomain**

**Add this DNS record:**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **A** | **hrms** | **158.69.219.206** | **600** |

**Detailed Steps:**
1. Click "Add" or "Add Record"
2. **Type:** Select "A"
3. **Name/Host:** Enter `hrms`
4. **Points to/Value:** Enter `158.69.219.206` (your Dokploy IP)
5. **TTL:** 600 seconds (or default)
6. Click "Save"

---

#### **3. Alternative: CNAME Record (If Preferred)**

If you prefer CNAME instead of A record:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| **CNAME** | **hrms** | **158.69.219.206** | **600** |

**Note:** A record is recommended for better performance.

---

#### **4. Verify DNS Record**

**Wait 5-10 minutes** for DNS propagation, then verify:

**Method 1: Online Tool**
- Go to: https://dnschecker.org/
- Enter: `hrms.kloudportal.com`
- Check if it resolves to `158.69.219.206`

**Method 2: Command Line**
```bash
# Windows
nslookup hrms.kloudportal.com

# Linux/Mac
dig hrms.kloudportal.com
```

**Expected output:**
```
Name:    hrms.kloudportal.com
Address: 158.69.219.206
```

---

## **🚀 Dokploy SSL Setup**

### **After DNS is Configured:**

1. **Wait for DNS Propagation** (5-30 minutes)
2. **Dokploy Auto-Detects Domain**
   - Dokploy monitors your configured domain
   - When DNS resolves correctly, it triggers SSL
3. **Let's Encrypt Certificate Request**
   - Dokploy requests certificate automatically
   - Verifies domain ownership
   - Installs certificate
4. **HTTPS Enabled**
   - Your site becomes accessible via HTTPS
   - HTTP automatically redirects to HTTPS

### **No Manual Steps Required!**

Dokploy handles everything once DNS is configured.

---

## **⏱️ Timeline**

| Step | Duration | Status |
|------|----------|--------|
| Add DNS record in GoDaddy | 2 minutes | ⏳ Manual |
| DNS propagation | 5-30 minutes | ⏳ Automatic |
| SSL certificate request | 2-5 minutes | ✅ Automatic |
| HTTPS activation | Instant | ✅ Automatic |
| **Total Time** | **10-40 minutes** | |

---

## **✅ Verification Checklist**

### **1. DNS Configuration**
```bash
# Check DNS
nslookup hrms.kloudportal.com

# Should return: 158.69.219.206
```

### **2. HTTP Access**
```bash
# Try HTTP (will redirect to HTTPS)
curl -I http://hrms.kloudportal.com

# Should return: 301 Redirect to HTTPS
```

### **3. HTTPS Access**
```bash
# Try HTTPS
curl -I https://hrms.kloudportal.com

# Should return: 200 OK
```

### **4. SSL Certificate**
- Open: https://hrms.kloudportal.com
- Click padlock icon in browser
- Verify: "Let's Encrypt" certificate
- Check expiry: ~90 days from now

---

## **🔧 Troubleshooting**

### **Issue 1: DNS Not Resolving**

**Symptoms:**
- `nslookup` returns "can't find"
- Browser shows "DNS_PROBE_FINISHED_NXDOMAIN"

**Solutions:**
1. Wait longer (up to 48 hours for full propagation)
2. Check DNS record in GoDaddy:
   - Correct name: `hrms`
   - Correct IP: `158.69.219.206`
   - Record type: `A`
3. Clear DNS cache:
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Linux/Mac
   sudo systemd-resolve --flush-caches
   ```

---

### **Issue 2: SSL Certificate Not Issued**

**Symptoms:**
- HTTPS shows "Not Secure"
- Certificate error in browser

**Solutions:**
1. Verify DNS is resolving correctly
2. Check Dokploy logs:
   - Go to Dokploy → Your App → Logs
   - Look for Let's Encrypt errors
3. Ensure port 80 is open (required for verification)
4. Try manual certificate request in Dokploy

---

### **Issue 3: Site Not Loading**

**Symptoms:**
- DNS resolves but site doesn't load
- Connection timeout

**Solutions:**
1. Check if app is running:
   - Dokploy → Your App → Status
   - Should show "Running"
2. Verify container port: `3000`
3. Check firewall rules on server
4. Test direct IP access: `http://158.69.219.206:3000`

---

## **📊 DNS Record Examples**

### **Correct Configuration:**

```
Type: A
Name: hrms
Value: 158.69.219.206
TTL: 600
```

**Result:** `hrms.kloudportal.com` → `158.69.219.206`

---

### **Common Mistakes to Avoid:**

❌ **Wrong Name:**
```
Name: hrms.kloudportal.com  # Don't include full domain
```

✅ **Correct Name:**
```
Name: hrms  # Just the subdomain
```

---

❌ **Wrong Type:**
```
Type: CNAME
Value: 158.69.219.206  # Can't use IP with CNAME
```

✅ **Correct Type:**
```
Type: A
Value: 158.69.219.206  # Use A record for IP
```

---

## **🎯 Final Configuration Summary**

### **GoDaddy DNS:**
- **Record Type:** A
- **Name:** hrms
- **Value:** 158.69.219.206
- **TTL:** 600

### **Dokploy:**
- **Host:** hrms.kloudportal.com
- **HTTPS:** Enabled
- **Certificate:** Let's Encrypt (Auto)
- **Port:** 3000

### **Result:**
- **URL:** https://hrms.kloudportal.com
- **SSL:** ✅ Free & Auto-Renewed
- **Redirect:** HTTP → HTTPS (Automatic)

---

## **🚀 After Setup**

Once domain is working:

1. **Update Environment Variables:**
   ```env
   FRONTEND_URL=https://hrms.kloudportal.com
   ```

2. **Update OAuth Redirects:**
   - Google OAuth: Add `https://hrms.kloudportal.com/auth/google/callback`
   - Any other OAuth providers

3. **Update Email Templates:**
   - Change links from IP to domain
   - Update verification URLs

4. **Test All Features:**
   - Login/Logout
   - Email verification
   - OAuth (if used)
   - File uploads
   - All API endpoints

---

## **📞 Support**

If you encounter issues:

1. **Check Dokploy Logs:**
   - Application logs
   - SSL certificate logs
   - Nginx/proxy logs

2. **Verify DNS:**
   - Use dnschecker.org
   - Check multiple locations

3. **Test Connectivity:**
   - Try from different networks
   - Use mobile data vs WiFi
   - Test from different locations

---

**Your configuration is perfect! Just add the DNS record in GoDaddy and wait for propagation.** 🎉

**SSL is completely FREE with Let's Encrypt via Dokploy!** 🔐

