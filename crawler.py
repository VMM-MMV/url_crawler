from selenium.webdriver.common.by import By
from chrome_driver import setup_chrome_driver
from chrome_driver import wait_for_js_load
import logging
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_links(domain_url, driver):
    """
    Extract all links from a page
    
    Args:
        driver: WebDriver instance
    
    Returns:
        list: List of dictionaries containing link text and href
    """

    visited = set()
    url_dq = deque([domain_url])

    while url_dq:
        for _ in range(len(url_dq)):
            url_node = url_dq.popleft()
            if url_node in visited:
                continue
            
            yield url_node
            driver.get(domain_url)
    
            if not wait_for_js_load(driver):
                logger.warning("Timeout for page: ", url_node)
                continue

            # Find all <a> elements
            elements = driver.find_elements(By.TAG_NAME, "a")
            
            for element in elements:
                try:
                    url_dq.append(element.get_attribute("href"))
                except Exception as e:
                    print(f"Error extracting link: {str(e)}")
                    continue

if __name__ == "__main__":
    try:
        driver = setup_chrome_driver()
        
        for link in get_links("https://accesimobil.md", driver):
            print(link)
        
        driver.quit()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if 'driver' in locals():
            driver.quit()