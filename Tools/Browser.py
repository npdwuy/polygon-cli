import os
import sys
import time
import json
import re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
except ImportError:
    pass

from .Method import ENV

def _get_driver():
    chrome_options = Options()
    # Share profile folder
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    custom_profile_dir = os.path.join(project_root, 'scratch', 'chrome_profile')
    chrome_options.add_argument(f"user-data-dir={custom_profile_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    
    # Exclude automation detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def login_polygon(driver):
    username = ENV.get("POLYGON_USERNAME", "")
    password = ENV.get("POLYGON_PASSWORD", "")
    
    if not username or not password:
        print("Missing POLYGON_USERNAME or POLYGON_PASSWORD in .env")
        return
        
    driver.get("https://polygon.codeforces.com/login")
    
    # Wait up to 60s if Cloudflare is blocking
    for _ in range(60):
        if "Just a moment" not in driver.title and "Cloudflare" not in driver.title:
            break
        time.sleep(1)
        
    
    # If we are already logged in, there won't be a login form
    if "login" not in driver.current_url.lower():
        return
        
    try:
        user_input = driver.find_element(By.NAME, "login")
        user_input.send_keys(Keys.CONTROL, 'a')
        user_input.send_keys(Keys.BACKSPACE)
        user_input.send_keys(username)
        
        pass_input = driver.find_element(By.NAME, "password")
        pass_input.send_keys(Keys.CONTROL, 'a')
        pass_input.send_keys(Keys.BACKSPACE)
        pass_input.send_keys(password)
        
        submit_btn = driver.find_element(By.NAME, "submit")
        submit_btn.click()
        
        time.sleep(3)
    except Exception as e:
        print(f"Polygon Login Form not found or error: {e}")

def login_codeforces(driver):
    username = ENV.get("CODEFORCES_USERNAME", "")
    password = ENV.get("CODEFORCES_PASSWORD", "")
    
    if not username or not password:
        print("Missing CODEFORCES_USERNAME or CODEFORCES_PASSWORD in .env")
        return
        
    driver.get("https://codeforces.com/enter")
    
    # Wait up to 60s if Cloudflare is blocking
    for _ in range(60):
        if "Just a moment" not in driver.title and "Cloudflare" not in driver.title:
            break
        time.sleep(1)
        
    
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "handleOrEmail")))
    except:
        pass
        
    if not driver.find_elements(By.NAME, "handleOrEmail"):
        return
        
    try:
        user_input = driver.find_element(By.NAME, "handleOrEmail")
        user_input.send_keys(Keys.CONTROL, 'a')
        user_input.send_keys(Keys.BACKSPACE)
        user_input.send_keys(username)
        
        pass_input = driver.find_element(By.NAME, "password")
        pass_input.send_keys(Keys.CONTROL, 'a')
        pass_input.send_keys(Keys.BACKSPACE)
        pass_input.send_keys(password)
        
        # Click submit
        submit_btn = driver.find_element(By.CLASS_NAME, "submit")
        submit_btn.click()
        time.sleep(3)
    except Exception as e:
        print(f"Codeforces Login Form not found or error: {e}")

def grant_polygon_access_and_get_urls(driver, slugs, grant_access=True):
    login_polygon(driver)
    
    with open("problem.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    problems = [p for p in data.get("problems", []) if p["local_id"] in slugs]
        
    urls = []
    
    driver.get("https://polygon.codeforces.com/problems")
    time.sleep(3)
    
    for p in problems:
        polygon_id = p.get("polygon_id")
        if not polygon_id:
            continue
            
        try:
            # 1. Start or Continue session
            row = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//tr[@problemid='{polygon_id}']"))
            )
            try:
                link = row.find_element(By.CSS_SELECTOR, "a.START_EDIT_SESSION")
            except:
                link = row.find_element(By.CSS_SELECTOR, "a.CONTINUE_EDIT_SESSION")
                
            driver.get(link.get_attribute("href"))
            time.sleep(3)
            
            # 1. Get General Info to scrape URL FIRST
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "General info"))).click()
            time.sleep(1)
            
            src = driver.page_source
            match = re.search(r'(https://polygon\.codeforces\.com/p[\w\-]+/[\w\-]+/[\w\-]+)', src)
            if match:
                urls.append(match.group(1))
            else:
                url_el = driver.find_element(By.CLASS_NAME, "problemUrl")
                urls.append(url_el.get_attribute("textContent").strip().split()[0])
                
            # 2. Grant access
            if grant_access:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Manage access"))).click()
                time.sleep(1)
                
                try:
                    # Click the "Add Users" link to show the form
                    driver.find_element(By.ID, "add-user").click()
                    time.sleep(1)
                    
                    # The input field has name "users_added"
                    user_input = driver.find_element(By.NAME, "users_added")
                    user_input.send_keys(Keys.CONTROL, 'a')
                    user_input.send_keys(Keys.BACKSPACE)
                    user_input.send_keys("codeforces")
                    user_input.send_keys(Keys.ENTER)
                    time.sleep(1)
                except Exception:
                    pass # Maybe already granted or error

            # Return to problems page for next problem
            driver.get("https://polygon.codeforces.com/problems")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing problem {p['local_id']}: {e}")
            driver.get("https://polygon.codeforces.com/problems")
            time.sleep(0.5)
            
    with open("automation_report.md", "a", encoding="utf-8") as f:
        f.write(f"## Polygon Automation Report at {time.ctime()}\n")
        f.write(f"Extracted {len(urls)} Gym URLs for slugs: {', '.join(slugs)}\n")
        for u in urls:
            f.write(f"- {u}\n")
        f.write("\n")
        
    return urls

def automate_mashup(slugs, gym_id=None, mashup_name=None, grant_access=True):
    if not slugs:
        print("No slugs provided for mashup automation.")
        return None
        
    driver = _get_driver()
    try:
        print("Granting access on Polygon and extracting sharing URLs...")
        urls = grant_polygon_access_and_get_urls(driver, slugs, grant_access=grant_access)
        
        if not urls:
            print("No valid Polygon URLs found/extracted. Aborting Mashup creation.")
            return None
            
        print("Logging into Codeforces...")
        login_codeforces(driver)
        
        if not gym_id and mashup_name:
            driver.get("https://codeforces.com/mashup/new")
            try:
                name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "contestName"))
                )
                name_input.send_keys(Keys.CONTROL, 'a')
                name_input.send_keys(Keys.BACKSPACE)
                name_input.send_keys(mashup_name)
                
                duration_input = driver.find_element(By.NAME, "contestDuration")
                duration_input.send_keys(Keys.CONTROL, 'a')
                duration_input.send_keys(Keys.BACKSPACE)
                duration_input.send_keys("40320")
                
                driver.find_element(By.CLASS_NAME, "submit").click()
                
                # Wait for URL change
                WebDriverWait(driver, 15).until(lambda d: "mashup/new" not in d.current_url)
                
                # Extract Gym ID from current URL
                match = re.search(r'(?:gym|mashup)/(\d+)', driver.current_url)
                if match:
                    gym_id = match.group(1)
            except Exception as e:
                print(f"Failed to create new mashup: {e}")
                return
                
        if not gym_id:
            print("No Gym ID available.")
            return
            
        driver.get(f"https://codeforces.com/gym/{gym_id}/problems/new")
        time.sleep(3)
        
        for url in urls:
            try:
                input_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "problemQuery"))
                )
                input_el.send_keys(Keys.CONTROL, 'a')
                input_el.send_keys(Keys.BACKSPACE)
                input_el.send_keys(url)
                time.sleep(0.5)
                
                add_link = driver.find_element(By.CLASS_NAME, "_MashupContestEditFrame_addProblemLink")
                add_link.click()
                
                WebDriverWait(driver, 30).until(
                    lambda d: d.find_element(By.NAME, "problemQuery").is_enabled()
                )
                time.sleep(1)
            except Exception as e:
                print(f"Failed to add URL {url}: {e}")
                
        # Save mashup
        try:
            submit_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form._MashupContestEditFrame_saveMashup input.submit"))
            )
            submit_btn.click()
            time.sleep(5)
        except Exception as e:
            print(f"Failed to save mashup: {e}")
            
        with open("automation_report.md", "a", encoding="utf-8") as f:
            f.write(f"## Codeforces Automation Report at {time.ctime()}\n")
            f.write(f"Added problems to Mashup Gym ID: {gym_id}\n")
            f.write(f"Slugs: {', '.join(slugs)}\n\n")
            
        return gym_id
    finally:
        driver.quit()
