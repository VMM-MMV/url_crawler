import logging
from chrome_driver import setup_chrome_driver
from crawler import get_links

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        driver = setup_chrome_driver()
        
        for link in get_links("https://accesimobil.md", driver):
            print(link)
        
        driver.quit()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if 'driver' in locals():
            driver.quit()