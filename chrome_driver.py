import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import logging
from selenium.webdriver.support.wait import TimeoutException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_chrome():
    """Install Chrome for linux"""
    try:
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run([
            "sudo", "apt-get", "install", "-y",
            "wget",
            "gnupg2",
            "software-properties-common"
        ], check=True)

        subprocess.run([
            "wget", "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
        ], check=True)
        subprocess.run([
            "sudo", "apt", "install", "./google-chrome-stable_current_amd64.deb", "-y"
        ], check=True)

        os.remove("google-chrome-stable_current_amd64.deb")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing Chrome: {str(e)}")
        return False

def setup_chrome_driver():
    """
    Set up Chrome WebDriver
    """
    try:    
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        logger.info("Installing/updating ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("ChromeDriver setup complete")
        
        return driver
    
    except Exception as e:
        logger.error(f"Error setting up ChromeDriver: {str(e)}")
        raise e

def wait_for_js_load(driver, timeout=10):
    """
    Wait for JavaScript to finish loading on the page
    
    Args:
        driver: WebDriver instance
        timeout: Maximum time to wait in seconds
    """
    try:
        # Wait for the document to be ready
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        # Wait for jQuery if it exists
        jquery_ready = """
            return (typeof jQuery !== 'undefined') ? 
            jQuery.active === 0 : true
        """
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(jquery_ready)
        )
        
        # Wait for any AJAX requests to complete
        ajax_complete = """
            return (typeof jQuery !== 'undefined') ? 
            jQuery.active === 0 : true
        """
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(ajax_complete)
        )
        
        return True
    except TimeoutException:
        print(f"Timeout waiting for JavaScript to load after {timeout} seconds")
        return False