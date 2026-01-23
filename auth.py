"""
Authentication module for Microsoft SSO login.
"""

import time
import gc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from security import validate_totp_secret, generate_totp_code


def auto_login(driver, url, username, password, totp_secret):
    """
    Automatically log in via Microsoft SSO.
    Uses secure TOTP generation with no secret logging.
    """
    print("  Attempting auto-login via Microsoft SSO...")
    driver.get(url)
    time.sleep(5)
    
    if not username or not password or username == "your_psu_username":
        print("  Credentials not configured")
        return False
    
    try:
        wait = WebDriverWait(driver, 15)
        
        # Step 1: Enter email
        try:
            email_field = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "input[type='email'], input[name='loginfmt'], #i0116"
            )))
            email_field.clear()
            email_field.send_keys(username)
            print(f"  Entered email: {username}")
            
            time.sleep(1)
            next_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], #idSIButton9")
            next_btn.click()
            print("  Clicked Next")
            time.sleep(3)
        except Exception as e:
            print(f"  Email step failed: {str(e)[:50]}")
        
        # Step 2: Enter password (never logged)
        try:
            password_field = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "input[type='password'], input[name='passwd'], #i0118"
            )))
            password_field.clear()
            password_field.send_keys(password)
            print("  Entered password")
            
            time.sleep(1)
            signin_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], #idSIButton9")
            signin_btn.click()
            print("  Clicked Sign In")
            time.sleep(3)
        except Exception as e:
            print(f"  Password step failed: {str(e)[:50]}")
        
        # Step 3: Handle "Stay signed in?" prompt
        try:
            stay_signed_in = driver.find_element(By.CSS_SELECTOR, "#idBtn_Back, #idSIButton9")
            if "stay signed in" in driver.page_source.lower():
                stay_signed_in.click()
                print("  Handled 'Stay signed in' prompt")
                time.sleep(2)
        except:
            pass
        
        # Step 4: Handle TOTP/MFA
        if totp_secret and validate_totp_secret(totp_secret):
            time.sleep(3)
            
            try:
                totp_field = driver.find_element(By.CSS_SELECTOR, 
                    "input[name='otc'], input[id='idTxtBx_SAOTCC_OTC'], input[name='passcode'], input[id='idTxtBx_SAOTCS_OTC']"
                )
                
                code = generate_totp_code(totp_secret)
                if code:
                    print("  Generated TOTP code (secure)")
                    
                    totp_field.clear()
                    totp_field.send_keys(code)
                    print("  Entered TOTP code")
                    
                    code = None
                    gc.collect()
                    
                    time.sleep(1)
                    verify_btn = driver.find_element(By.CSS_SELECTOR, 
                        "input[type='submit'], #idSubmit_SAOTCC_Continue, #idSubmit_SAOTCS_Continue"
                    )
                    verify_btn.click()
                    print("  Clicked Verify")
            except Exception as e:
                print(f"  TOTP step: {str(e)[:50]}")
                print("  (You may need to approve a push notification)")
        
        # Wait for redirect
        print("  Waiting for login to complete...")
        try:
            WebDriverWait(driver, 60).until(
                lambda d: "login.microsoftonline.com" not in d.current_url 
                and "25live.collegenet.com" in d.current_url
            )
            print("  Redirect detected!")
            
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".grid--item, .ngHome, .navbar-nav, .ngNav"))
            )
            print("  Login successful!")
            return True
        except Exception as e:
            print(f"  Timeout waiting for login: {str(e)[:50]}")
            if "login.microsoftonline.com" in driver.current_url:
                print("  Still on Microsoft login page - may need manual intervention")
                return False
            print("  Login may have succeeded - continuing...")
            return True
            
    except Exception as e:
        print(f"  Auto-login error: {str(e)[:100]}")
        return False
