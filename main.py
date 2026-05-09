import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
RESUME_FILENAME = "my-resume.pdf"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"
COOKIES_JSON = os.getenv("NAUKRI_COOKIES")

def update_naukri_profile():
    if not COOKIES_JSON:
        print("Error: NAUKRI_COOKIES secret not found!")
        return

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Anti-bot detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30) # Increased timeout to 30s
    
    try:
        print("Opening Naukri for cookie injection...")
        driver.get("https://www.naukri.com/")
        
        print("Injecting cookies...")
        cookie_list = json.loads(COOKIES_JSON)
        for cookie in cookie_list:
            c = {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie.get("domain", ".naukri.com"),
                "path": cookie.get("path", "/")
            }
            driver.add_cookie(c)
        
        print("Refreshing to Profile page...")
        driver.get(PROFILE_URL)
        
        # Check if we are redirected to login (means cookies expired)
        if "login" in driver.current_url.lower():
            print("CRITICAL: Cookies expired! Redirected to login page.")
            driver.save_screenshot("login_redirect.png")
            return

        print("Searching for upload input using multiple strategies...")
        
        # Naukri uses 'attachCV' ID for the hidden file input
        search_queries = [
            "//input[@id='attachCV']",
            "//input[@type='file']",
            "//input[contains(@class, 'fileInput')]"
        ]
        
        upload_input = None
        for query in search_queries:
            try:
                upload_input = wait.until(EC.presence_of_element_located((By.XPATH, query)))
                if upload_input:
                    print(f"Found input using: {query}")
                    break
            except:
                continue

        if not upload_input:
            print("Fallback: Scrolling to bottom and trying one last time...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            upload_input = driver.find_element(By.XPATH, "//input[@type='file']")

        resume_path = os.path.abspath(RESUME_FILENAME)
        print(f"Uploading file from: {resume_path}")
        
        # Using JS to make sure the input is interactable
        driver.execute_script("arguments[0].style.display = 'block';", upload_input)
        upload_input.send_keys(resume_path)
        
        print("Upload command sent. Waiting for processing...")
        time.sleep(15) 
        
        driver.save_screenshot("final_status.png")
        print("Process Finished.")

    except Exception as e:
        print(f"Failed: {str(e)}")
        driver.save_screenshot("error_state.png")
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    update_naukri_profile()
