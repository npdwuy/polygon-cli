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
    driver.set_page_load_timeout(30)
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
    urls = []
    if not grant_users_dict:
        return urls
        
    print("  - Checking Polygon login status...")
    login_polygon(driver)
    
    polygon_user = os.environ.get("POLYGON_USERNAME", "")
    
    with open(PROBLEM_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    problems = [p for p in data.get("problems", []) if p["local_id"] in slugs]
    
    rights_map = {"Read": 0, "Write": 1}
    
    needs_browsing = False
    for p in problems:
        perms = p.get("permissions", {})
        users_to_grant = []
        if polygon_user and polygon_user not in perms:
            users_to_grant.append((polygon_user, "Write"))
        for user, target_right in grant_users_dict.items():
            if rights_map.get(target_right, 0) > rights_map.get(perms.get(user, None), -1):
                users_to_grant.append((user, target_right))
        if users_to_grant or "polygon_url" not in p:
            needs_browsing = True
            break
            
    if needs_browsing:
        driver.get("https://polygon.codeforces.com/problems")
        time.sleep(3)
    
    for p in problems:
        polygon_id = p.get("polygon_id")
        if not polygon_id:
            continue
            
        perms = p.get("permissions", {})
        if polygon_user and polygon_user not in perms:
            perms[polygon_user] = "Write"
            
        users_to_grant = []
        for user, target_right in grant_users_dict.items():
            target_val = rights_map.get(target_right, 0)
            current_right = perms.get(user, None)
            current_val = rights_map.get(current_right, -1)
            
            if target_val > current_val:
                users_to_grant.append((user, target_right))
                
        if not users_to_grant and "polygon_url" in p:
            print(f"\n  - {p['local_id']} already has required permissions and cached URL. Zero-navigation applied.")
            urls.append(p["polygon_url"])
            continue
            
        print(f"\n  - Processing access & URL for {p['local_id']}...")
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
                
                if users_to_grant:
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
                
                # Extract URL from General info
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "General info"))).click()
                time.sleep(1)
                
                src = driver.page_source
                extracted_url = ""
                match = re.search(r'(https://polygon\.codeforces\.com/p[\w\-]+/[\w\-]+/[\w\-]+)', src)
                if match:
                    extracted_url = match.group(1)
                else:
                    url_el = driver.find_element(By.CLASS_NAME, "problemUrl")
                    extracted_url = url_el.get_attribute("textContent").strip().split()[0]
                    
                if extracted_url:
                    print(f"    -> Scraped URL: {extracted_url}")
                    urls.append(extracted_url)
                    p["polygon_url"] = extracted_url

                driver.get("https://polygon.codeforces.com/problems")
                time.sleep(0.5)
                break
                
            except Exception as e:
                if attempt < 2:
                    print(f"Lag detected ({e}). Reloading problems page, waiting 10s...")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(10)
                else:
                    print(f"Error processing {p['local_id']} after 3 attempts: {e}")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(0.5)
            
    with open(PROBLEM_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return urls


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
        # Default grant access and get URLs for mashup
        print("Granting default access & Extracting sharing URLs on Polygon...")
        from polygon import GRANT_USERS
        urls = grant_polygon_access(driver, slugs, GRANT_USERS)
        
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

def delete_polygon_solutions(driver, slugs, filenames_to_delete):
    print("  - Checking Polygon login status...")
    login_polygon(driver)
    
    with open(PROBLEM_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    problem_dict = {p["local_id"]: p for p in data.get("problems", [])}
    problems = [problem_dict[slug] for slug in slugs if slug in problem_dict]
    
    driver.get("https://polygon.codeforces.com/problems")
    time.sleep(3)
    
    for p in problems:
        polygon_id = p.get("polygon_id")
        if not polygon_id:
            continue
            
        print(f"\n  - Processing deletion for {p['local_id']}...")
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
                time.sleep(2)
                
                # Go to solutions tab
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Solution files"))).click()
                time.sleep(2)
                
                deleted_any = False
                for filename in filenames_to_delete:
                    try:
                        delete_link = driver.find_element(By.XPATH, f"//a[@class='delete-link' and @file='{filename}']")
                        print(f"    -> Clicking delete for {filename}...")
                        delete_link.click()
                        time.sleep(1)
                        
                        alert = driver.switch_to.alert
                        alert.accept()
                        
                        # Wait for page reload
                        WebDriverWait(driver, 10).until(EC.staleness_of(delete_link))
                        time.sleep(1)
                        deleted_any = True
                        print(f"    -> Successfully deleted {filename}.")
                    except Exception as ex:
                        pass # File not found or already deleted
                        
                if not deleted_any:
                    print("    -> No matching files found to delete.")
                
                driver.get("https://polygon.codeforces.com/problems")
                time.sleep(1)
                break
                
            except Exception as e:
                if attempt < 2:
                    print(f"Lag detected ({e}). Reloading problems page, waiting 10s...")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(10)
                else:
                    print(f"Error processing deletion for problem {p['local_id']} after 3 attempts: {e}")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(1)

def delete_polygon_statements(driver, slugs, language_to_delete):
    print("  - Checking Polygon login status...")
    login_polygon(driver)
    
    with open(PROBLEM_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    problem_dict = {p["local_id"]: p for p in data.get("problems", [])}
    problems = [problem_dict[slug] for slug in slugs if slug in problem_dict]
    
    driver.get("https://polygon.codeforces.com/problems")
    time.sleep(3)
    
    for p in problems:
        polygon_id = p.get("polygon_id")
        if not polygon_id:
            continue
            
        print(f"\n  - Processing statement deletion for {p['local_id']}...")
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
                time.sleep(2)
                
                # Go to Statement tab
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Statement"))).click()
                time.sleep(2)
                
                # Select the language
                try:
                    lang_link = driver.find_element(By.LINK_TEXT, language_to_delete)
                    print(f"    -> Selecting language: {language_to_delete}...")
                    lang_link.click()
                    time.sleep(2)
                except Exception:
                    print(f"    -> Language {language_to_delete} not found for this problem.")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(1)
                    break
                
                # Click Delete
                try:
                    delete_btn = driver.find_element(By.ID, "delete-statement-link")
                    print("    -> Clicking 'Delete Current'...")
                    delete_btn.click()
                    time.sleep(1)
                    
                    alert = driver.switch_to.alert
                    alert.accept()
                    
                    # Wait for page reload
                    WebDriverWait(driver, 10).until(EC.staleness_of(delete_btn))
                    time.sleep(1)
                    print(f"    -> Successfully deleted {language_to_delete} statement.")
                except Exception as ex:
                    print(f"    -> Could not click Delete for {language_to_delete}: {ex}")
                
                driver.get("https://polygon.codeforces.com/problems")
                time.sleep(1)
                break
                
            except Exception as e:
                if attempt < 2:
                    print(f"Lag detected ({e}). Reloading problems page, waiting 10s...")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(10)
                else:
                    print(f"Error processing statement deletion for problem {p['local_id']} after 3 attempts: {e}")
                    driver.get("https://polygon.codeforces.com/problems")
                    time.sleep(1)

def delete_mashup_problems(driver, gym_id, short_names):
    print("  - Checking Codeforces login status...")
    login_codeforces(driver)
    
    gym_url = f"https://codeforces.com/gym/{gym_id}"
    
    deleted_count = 0
    for short_name in short_names:
        print(f"\n  - Starting deletion process for '{short_name}'...")
        try:
            driver.get(gym_url)
        except Exception as ge:
            print(f"  - Navigation to Gym URL timed out or failed: {ge}. Proceeding anyway...")
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "problems"))
            )
        except Exception as e:
            print(f"Failed to find the problems table on Gym dashboard: {e}")
            continue
            
        rows = driver.find_elements(By.CSS_SELECTOR, "table.problems tr")
        target_row = None
        for row in rows:
            try:
                td_id = row.find_element(By.CSS_SELECTOR, "td.id")
                if td_id.text.strip() == short_name:
                    target_row = row
                    break
            except Exception:
                continue
                
        if not target_row:
            print(f"Problem with short name '{short_name}' not found in Gym {gym_id}. Skipping.")
            continue
            
        try:
            edit_link = target_row.find_element(By.XPATH, ".//a[contains(@href, '/problems/edit/')]")
            edit_url = edit_link.get_attribute("href")
        except Exception as e:
            print(f"Failed to extract edit URL for problem '{short_name}': {e}")
            continue
            
        print(f"  - Extracted edit URL for problem '{short_name}': {edit_url}")
        print(f"  - Navigating to edit page...")
        try:
            driver.get(edit_url)
        except Exception as ge:
            print(f"  - Navigation to edit page URL timed out or failed: {ge}. Proceeding anyway...")
        
        try:
            delete_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "deleteProblem"))
            )
            print("  - Clicking delete button...")
            delete_btn.click()
            
            # Wait for the confirmation alert
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"  - Confirm alert text: '{alert_text}'")
            alert.accept()
            print(f"  - Accepted confirmation alert.")
            
            # Wait for action to complete and page redirection
            time.sleep(3)
            print(f"  - Problem '{short_name}' deleted successfully from Gym {gym_id}.")
            deleted_count += 1
        except Exception as e:
            print(f"Error while deleting problem on the edit page: {e}")
            
    print(f"\nDeletion sequence finished. Successfully deleted {deleted_count}/{len(short_names)} problems.")
    return deleted_count == len(short_names)

def restore_mashup_problems(driver, gym_id):
    print("  - Checking Codeforces login status...")
    login_codeforces(driver)
    
    gym_url = f"https://codeforces.com/gym/{gym_id}"
    
    restored_count = 0
    while True:
        print(f"\n  - Navigating to Gym {gym_id}: {gym_url}")
        try:
            driver.get(gym_url)
        except Exception as ge:
            print(f"  - Navigation to Gym URL timed out or failed: {ge}. Proceeding anyway...")
            
        try:
            # Click "Show deleted problems" if visible
            try:
                show_link = driver.find_element(By.CSS_SELECTOR, "a[id^='show-deleted-problems-link-']")
                if show_link.is_displayed():
                    print("  - Clicking 'Show deleted problems' link...")
                    show_link.click()
                    time.sleep(1)
            except Exception:
                pass
                
            # Locate the deleted problems section
            try:
                deleted_section = driver.find_element(By.CSS_SELECTOR, "div[class*='deletedProblems']")
                if not deleted_section.is_displayed():
                    print("  - Deleted problems section is not visible. Stopping.")
                    break
            except Exception:
                print("  - Deleted problems section not found or not visible. No more problems to restore.")
                break
                
            # Locate rows in the deleted problems table
            rows = deleted_section.find_elements(By.CSS_SELECTOR, "table.problems tr")
            
            # The first row is the header, look for subsequent rows
            target_row = None
            for row in rows:
                try:
                    # Ensure it has a cell with an edit link
                    edit_link = row.find_element(By.XPATH, ".//a[contains(@href, '/problems/edit/')]")
                    target_row = row
                    break # We want the FIRST deleted problem row
                except Exception:
                    continue
                    
            if not target_row:
                print("  - No more deleted problem rows found. Restore completed.")
                break
                
            # Extract problem name and edit URL
            try:
                prob_name_el = target_row.find_element(By.CSS_SELECTOR, "td.left a")
                prob_name = prob_name_el.text.strip()
                edit_link = target_row.find_element(By.XPATH, ".//a[contains(@href, '/problems/edit/')]")
                edit_url = edit_link.get_attribute("href")
            except Exception as e:
                safe_e = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"  - Failed to extract details for the next deleted problem: {safe_e}")
                break
                
            print(f"  - Next problem to restore: '{prob_name}'")
            print(f"  - Navigating to edit page: {edit_url}")
            try:
                driver.get(edit_url)
            except Exception as ge:
                print(f"  - Navigation to edit page URL timed out or failed: {ge}. Proceeding anyway...")
                
            try:
                restore_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "restoreProblem"))
                )
                print("  - Clicking 'Restore problem' button...")
                try:
                    restore_btn.click()
                except Exception as ce:
                    print(f"  - Click action timed out or encountered an issue: {ce}. Proceeding anyway...")
                time.sleep(3)
                print(f"  - Problem '{prob_name}' restored successfully.")
                restored_count += 1
            except Exception as e:
                safe_e = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"  - Failed to locate or restore problem '{prob_name}': {safe_e}")
                break
        except Exception as e:
            safe_e = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"  - Stale element or other DOM error occurred: {safe_e}. Retrying in 2 seconds...")
            time.sleep(2)
            
    print(f"\nRestore sequence finished. Successfully restored {restored_count} problems.")
    return restored_count

def reindex_mashup_problems(driver, gym_id):
    print("  - Checking Codeforces login status...")
    login_codeforces(driver)
    
    gym_url = f"https://codeforces.com/gym/{gym_id}"
    print(f"\n  - Navigating to Gym {gym_id}: {gym_url}")
    try:
        driver.get(gym_url)
    except Exception as ge:
        print(f"  - Navigation to Gym URL timed out or failed: {ge}. Proceeding anyway...")
        
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "problems"))
        )
    except Exception as e:
        print(f"Failed to find the problems table on Gym dashboard: {e}")
        return False
        
    # Get active table rows
    rows = driver.find_elements(By.CSS_SELECTOR, "div#pageContent div.datatable:not([class*='deletedProblems']) table.problems tr")
    
    problem_details = []
    for row in rows:
        try:
            td_id = row.find_element(By.CSS_SELECTOR, "td.id")
            old_index = td_id.text.strip()
            
            # Extract edit URL
            edit_link = row.find_element(By.XPATH, ".//a[contains(@href, '/problems/edit/')]")
            edit_url = edit_link.get_attribute("href")
            
            problem_details.append({
                "old_index": old_index,
                "edit_url": edit_url
            })
        except Exception:
            continue
            
    if not problem_details:
        print("No active problems found to re-index.")
        return False
        
    print(f"Found {len(problem_details)} active problems.")
    
    max_numeric_index = 0
    problems_to_reindex = []
    
    for prob in problem_details:
        old_index = prob["old_index"]
        if old_index.isdigit():
            max_numeric_index = max(max_numeric_index, int(old_index))
        else:
            problems_to_reindex.append(prob)
            
    if not problems_to_reindex:
        print("All problems are already numerically indexed. Nothing to do.")
        return True
        
    print(f"Found {len(problems_to_reindex)} problems with non-numeric indices.")
    print(f"Max existing numeric index is {max_numeric_index:03d}. Will start re-indexing from {max_numeric_index + 1:03d}.")
    
    updated_count = 0
    next_index_num = max_numeric_index + 1
    for prob in problems_to_reindex:
        new_index = f"{next_index_num:03d}"
        old_index = prob["old_index"]
        next_index_num += 1
            
        print(f"\n  - Re-indexing '{old_index}' -> '{new_index}'...")
        print(f"  - Navigating to edit page: {prob['edit_url']}")
        try:
            driver.get(prob["edit_url"])
        except Exception as ge:
            print(f"  - Navigation to edit page URL timed out or failed: {ge}. Proceeding anyway...")
            
        try:
            index_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "index"))
            )
            index_input.clear()
            index_input.send_keys(new_index)
            
            save_btn = driver.find_element(By.CSS_SELECTOR, "input.submitProblem[type='submit']")
            print("  - Clicking 'Save changes' button...")
            try:
                save_btn.click()
            except Exception as ce:
                print(f"  - Click action timed out or encountered an issue: {ce}. Proceeding anyway...")
            time.sleep(3)
            print(f"  - Problem '{old_index}' successfully updated to index '{new_index}'.")
            updated_count += 1
        except Exception as e:
            safe_e = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"  - Failed to change index for '{old_index}': {safe_e}")
            
    print(f"\nRe-indexing sequence finished. Updated {updated_count} problems.")
    return True




