"""
Security module for credential management and TOTP generation.
Implements RFC 6238 compliant TOTP with secure storage.
"""

import os
import re
import gc
import sys
from dotenv import load_dotenv
from config import KEYRING_SERVICE

# Try to use keyring for secure storage
USE_KEYRING = False
try:
    import keyring
    USE_KEYRING = True
except ImportError:
    pass

try:
    import pyotp
except ImportError:
    print("ERROR: pyotp not installed. Run: pip install pyotp")
    sys.exit(1)


def validate_totp_secret(secret):
    """
    Validate TOTP secret format per RFC 6238 / RFC 4648.
    Returns True if valid base32 format, False otherwise.
    """
    if not secret or secret == "your_totp_secret_key":
        return False
    
    # Remove spaces and convert to uppercase
    secret = secret.replace(" ", "").upper()
    
    # Check valid base32 characters (A-Z, 2-7, with = padding)
    if not re.match(r'^[A-Z2-7]+=*$', secret):
        return False
    
    # Check reasonable length (minimum 16 chars for security)
    if len(secret) < 16:
        print("  WARNING: TOTP secret is shorter than recommended (16+ chars)")
        return False
    
    return True


def generate_totp_code(secret):
    """
    Securely generate a TOTP code.
    Uses SHA-1 per RFC 6238 for Microsoft Authenticator compatibility.
    """
    if not validate_totp_secret(secret):
        return None
    
    try:
        totp = pyotp.TOTP(secret, digits=6, interval=30)
        code = totp.now()
        return code
    except Exception:
        return None


def get_credentials():
    """
    Securely retrieve credentials from keyring or .env file.
    Keyring uses OS-level encryption.
    """
    username = None
    password = None
    totp_secret = None
    
    if USE_KEYRING:
        try:
            username = keyring.get_password(KEYRING_SERVICE, "username")
            password = keyring.get_password(KEYRING_SERVICE, "password")
            totp_secret = keyring.get_password(KEYRING_SERVICE, "totp_secret")
            
            if username and password:
                print("  Loaded credentials from OS keyring (encrypted)")
                return username, password, totp_secret
        except Exception:
            pass
    
    # Fallback to .env file
    load_dotenv()
    username = os.getenv("PSU_USERNAME")
    password = os.getenv("PSU_PASSWORD")
    totp_secret = os.getenv("TOTP_SECRET")
    
    if username and password:
        print("  Loaded credentials from .env file")
        if USE_KEYRING:
            print("  TIP: Run 'python main.py --setup' to store in secure keyring")
    
    return username, password, totp_secret


def setup_keyring():
    """Interactive setup to store credentials in OS keyring"""
    if not USE_KEYRING:
        print("ERROR: keyring module not installed. Run: pip install keyring")
        return
    
    print("\n" + "=" * 60)
    print("  SECURE CREDENTIAL SETUP")
    print("  Credentials will be stored in your OS keyring (encrypted)")
    print("=" * 60)
    
    import getpass
    
    username = input("\nPenn State Username: ").strip()
    password = getpass.getpass("Penn State Password: ")
    totp_secret = getpass.getpass("TOTP Secret Key (base32): ").strip().upper()
    
    if not validate_totp_secret(totp_secret):
        print("\nWARNING: TOTP secret appears invalid. Storing anyway.")
    
    try:
        keyring.set_password(KEYRING_SERVICE, "username", username)
        keyring.set_password(KEYRING_SERVICE, "password", password)
        keyring.set_password(KEYRING_SERVICE, "totp_secret", totp_secret)
        print("\n  Credentials stored securely in OS keyring!")
        print("  You can now run the script without --setup")
    except Exception as e:
        print(f"\nERROR storing credentials: {e}")
    
    # Clear sensitive variables
    password = '\x00' * len(password)
    totp_secret = '\x00' * len(totp_secret) if totp_secret else None
    del password, totp_secret
    gc.collect()


def clear_credentials(password, totp_secret):
    """Securely clear credentials from memory"""
    if password:
        password = '\x00' * len(password)
    if totp_secret:
        totp_secret = '\x00' * len(totp_secret)
    del password, totp_secret
    gc.collect()
