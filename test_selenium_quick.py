"""Quick test to verify Selenium is working"""
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import shutil
    
    print("✅ Selenium imported successfully")
    
    # Find Chrome/Chromium binary
    chrome_binary = None
    for binary in ['chromium-browser', 'chromium', 'google-chrome', 'chrome']:
        path = shutil.which(binary)
        if path:
            chrome_binary = path
            print(f"✅ Found Chrome binary: {chrome_binary}")
            break
    
    if not chrome_binary:
        raise Exception("Chrome/Chromium not found!")
    
    # Configure Chrome options
    options = Options()
    options.binary_location = chrome_binary
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    print("🔧 Initializing Chrome WebDriver...")
    
    # Try to create driver
    driver = webdriver.Chrome(options=options)
    print("✅ Chrome WebDriver created successfully")
    
    # Test navigation
    print("🌐 Testing Google navigation...")
    driver.get('https://www.google.com')
    print(f"✅ Page title: {driver.title}")
    
    # Close driver
    driver.quit()
    print("\n✅ SUCCESS! Selenium is fully functional!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
