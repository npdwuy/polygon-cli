from polygon import PROBLEM_JSON_PATH
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
    driver.set_page_load_timeout(10)
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

def grant_polygon_access(driver, slugs, grant_users_dict):
    if not grant_users_dict:
        return
        
    print("  - Checking Polygon login status...")
    login_polygon(driver)
    
    polygon_user = os.environ.get("POLYGON_USERNAME", "")
    
    with open(PROBLEM_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    problems = [p for p in data.get("problems", []) if p["local_id"] in slugs]
    
    driver.get("https://polygon.codeforces.com/problems")
    time.sleep(3)
    
    rights_map = {"Read": 0, "Write": 1}
    
    for p in problems:
        polygon_id = p.get("polygon_id")
        if not polygon_id:
            continue
            
        perms = p.get("permissions", {})
        if polygon_user and polygon_user not in perms:
            perms[polygon_user] = "Write"
            p["permissions"] = perms
            
        users_to_grant = []
        for user, target_right in grant_users_dict.items():
            target_val = rights_map.get(target_right, 0)
            current_right = perms.get(user, None)
            current_val = rights_map.get(current_right, -1)
            
            if target_val > current_val:
                users_to_grant.append((user, target_right))
                
        if not users_to_grant:
            p["permissions"] = perms
            continue
            
        print(f"\n  - Processing access for {p['local_id']}...")
        for attempt in range(3):
            try:
                row = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//tr[@problemid='{polygon_id}']"))
                )
                try:
                    link = row.find_element(By.CSS_SELECTOR, "a.START_EDIT_SESSION")
                except:
                    link = row.find_element(By.CSS_SELECTOR, "a.CONTINUE_EDIT_SESSION")
                    
                driver.get(link.get_attribute("href"))
                time.sleep(3)
                
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Manage access"))).click()
                time.sleep(1)
                
                for user, right in users_to_grant:
                    print(f"    -> Granting {right} access to {user}...")
                    try:
                        driver.find_element(By.ID, "add-user").click()
                        time.sleep(1)
                        
                        user_input = driver.find_element(By.NAME, "users_added")
                        user_input.send_keys(Keys.CONTROL, 'a')
                        user_input.send_keys(Keys.BACKSPACE)
                        user_input.send_keys(user)
                        
                        try:
                            from selenium.webdriver.support.ui import Select
                            right_select = Select(driver.find_element(By.NAME, "type"))
                            right_select.select_by_visible_text(right)
                        except:
                            pass
                            
                        user_input.send_keys(Keys.ENTER)
                        time.sleep(1)
                        perms[user] = right
                    except Exception as ex:
                        print(f"Failed to grant {right} to {user} on {p['local_id']}: {ex}")
                        
                p["permissions"] = perms
                driver.get("https://polygon.codeforces.com/problems")
                time.sleep(0.5)
                break
                
            except Exception as e:
                if attempt < 2:
                    print(f"Lag detected ({e}). Reloading problems page, waiting 10s...")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(10)
                else:
                    print(f"Error processing access for problem {p['local_id']} after 3 attempts: {e}")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(0.5)
            
    with open(PROBLEM_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_polygon_urls(driver, slugs):
    print("  - Checking Polygon login status...")
    login_polygon(driver)
    
    with open(PROBLEM_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    problems = [p for p in data.get("problems", []) if p["local_id"] in slugs]
    urls = []
    
    driver.get("https://polygon.codeforces.com/problems")
    time.sleep(3)
    
    for p in problems:
        polygon_id = p.get("polygon_id")
        if not polygon_id:
            continue
            
        print(f"\n  - Extracting Gym URL for {p['local_id']}...")
        for attempt in range(3):
            try:
                row = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//tr[@problemid='{polygon_id}']"))
                )
                try:
                    link = row.find_element(By.CSS_SELECTOR, "a.START_EDIT_SESSION")
                except:
                    link = row.find_element(By.CSS_SELECTOR, "a.CONTINUE_EDIT_SESSION")
                    
                driver.get(link.get_attribute("href"))
                time.sleep(3)
                
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "General info"))).click()
                time.sleep(1)
                
                src = driver.page_source
                match = re.search(r'(https://polygon\.codeforces\.com/p[\w\-]+/[\w\-]+/[\w\-]+)', src)
                if match:
                    extracted_url = match.group(1)
                    urls.append(extracted_url)
                    print(f"    -> Scraped URL: {extracted_url}")
                else:
                    url_el = driver.find_element(By.CLASS_NAME, "problemUrl")
                    extracted_url = url_el.get_attribute("textContent").strip().split()[0]
                    urls.append(extracted_url)
                    print(f"    -> Scraped URL: {extracted_url}")
                    
                driver.get("https://polygon.codeforces.com/problems")
                time.sleep(0.5)
                break
                
            except Exception as e:
                if attempt < 2:
                    print(f"Lag detected ({e}). Reloading problems page, waiting 10s...")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(10)
                else:
                    print(f"Error processing URL for problem {p['local_id']} after 3 attempts: {e}")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(0.5)
        
    return urls

def grant_access_only(slugs, grant_users_dict):
    if not slugs:
        print("No slugs provided for granting access.")
        return
    driver = _get_driver()
    try:
        print("Granting access on Polygon...")
        grant_polygon_access(driver, slugs, grant_users_dict)
    finally:
        driver.quit()

def automate_mashup(slugs, gym_id=None, mashup_name=None):
    if not slugs:
        print("No slugs provided for mashup automation.")
        return None
        
    driver = _get_driver()
    try:
        # Default grant access for mashup
        print("Granting default access on Polygon...")
        from polygon import GRANT_USERS
        grant_polygon_access(driver, slugs, GRANT_USERS)
        
        print("\n  - Extracting sharing URLs...")
        urls = get_polygon_urls(driver, slugs)
        
        if not urls:
            print("No valid Polygon URLs found/extracted. Aborting Mashup creation.")
            return None
            
        print("Logging into Codeforces...")
        login_codeforces(driver)
        
        if not gym_id and mashup_name:
            print(f"\n  - Creating new Codeforces Mashup: {mashup_name}...")
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
            print(f"  - Adding URL to Mashup: {url}")
            for attempt in range(3):
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
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"Lag adding {url}. Reloading mashup edit page, waiting 10s...")
                        driver.refresh()
                        time.sleep(10)
                    else:
                        print(f"Failed to add URL {url} after 3 attempts: {e}")
                
        # Save mashup
        try:
            submit_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form._MashupContestEditFrame_saveMashup input.submit"))
            )
            submit_btn.click()
            time.sleep(5)
        except Exception as e:
            print(f"Failed to save mashup: {e}")
            
        return gym_id
    finally:
        driver.quit()
