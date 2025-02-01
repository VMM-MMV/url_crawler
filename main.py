import logging
from chrome_driver import setup_chrome_driver
from crawler import get_links
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        driver = setup_chrome_driver()
        
        domain_url = "https://www.youtube.com/"
        base_domain = urlparse(domain_url).netloc
        logger.info(f"Base domain: {base_domain}")

        def url_accept_strategy(href):
            if urlparse(href).netloc != base_domain:
                logger.info(f"Not domain url: {href}")
                return False
            return True

        for link in get_links(domain_url, driver, url_accept_strategy):
            print(f"Found link: {link}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    main()