import os
import subprocess
import logging
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chrome_driver")

def find_chrome_binary():
    """Find the Chrome binary dynamically based on the OS."""
    system_platform = platform.system().lower()

    if system_platform == "windows":
        # Check common install locations
        possible_paths = [
            os.getenv("PROGRAMFILES") + r"\Google\Chrome\Application\chrome.exe",
            os.getenv("PROGRAMFILES(X86)") + r"\Google\Chrome\Application\chrome.exe",
            os.getenv("LOCALAPPDATA") + r"\Google\Chrome\Application\chrome.exe"
        ]
        for path in possible_paths:
            if path and os.path.exists(path):
                return path

        # Try querying the registry
        try:
            reg_query = subprocess.run(
                ['reg', 'query', r'HKCU\Software\Google\Chrome\BLBeacon', '/v', 'path'],
                capture_output=True, text=True
            )
            if reg_query.returncode == 0:
                output_lines = reg_query.stdout.splitlines()
                for line in output_lines:
                    if "path" in line:
                        return line.split()[-1]
        except Exception as e:
            logger.warning(f"Failed to query registry for Chrome path: {e}")

    elif system_platform == "darwin":  # macOS
        # Use Spotlight search
        try:
            result = subprocess.run(["mdfind", "kMDItemFSName = 'Google Chrome'"], capture_output=True, text=True)
            if result.stdout:
                return result.stdout.split("\n")[0] + "/Contents/MacOS/Google Chrome"
        except Exception as e:
            logger.warning(f"Failed to locate Chrome on macOS: {e}")

        # Fallback to default location
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    elif system_platform == "linux":
        # Use 'which' to find Chrome
        try:
            result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
            if result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Failed to locate Chrome on Linux: {e}")

        # Fallback to other possible names
        for name in ["google-chrome", "chrome", "chromium-browser", "chromium"]:
            path = f"/usr/bin/{name}"
            if os.path.exists(path):
                return path

    raise RuntimeError("Google Chrome binary not found. Please install it manually.")

def setup_chrome_driver():
    """Set up Chrome WebDriver with the correct binary path and driver."""
    try:
        chrome_binary_path = find_chrome_binary()
        logger.info(f"Found Chrome binary: {chrome_binary_path}")

        chrome_options = Options()
        chrome_options.binary_location = chrome_binary_path
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        logger.info("Installing/updating ChromeDriver...")
        service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("ChromeDriver setup complete.")

        return driver

    except Exception as e:
        logger.error(f"Error setting up ChromeDriver: {str(e)}")
        raise e

def wait_for_js_load(driver, timeout=10):
    """Wait for JavaScript to finish loading on the page."""
    try:
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Wait for jQuery and AJAX if they exist
        js_script = "return (typeof jQuery !== 'undefined') ? jQuery.active === 0 : true"
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script(js_script))

        return True
    except TimeoutException:
        logger.warning(f"Timeout waiting for JavaScript to load after {timeout} seconds")
        return False

if __name__ == "__main__":
    try:
        driver = setup_chrome_driver()
        driver.get("https://www.google.com")
        
        if wait_for_js_load(driver):
            logger.info("Page fully loaded!")

        print("Title:", driver.title)
        driver.quit()

    except Exception as err:
        logger.error(f"Fatal error: {err}")
