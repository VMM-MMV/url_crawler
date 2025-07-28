import asyncio
import logging
from collections import deque
from urllib.parse import urlparse
import urllib.robotparser
import requests
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_disallowed_urls(robots_url):
    """Parse robots.txt and return disallowed URLs."""
    rp = urllib.robotparser.RobotFileParser()
    
    try:
        response = requests.get(robots_url, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Invalid response when querying for robots.txt from: {robots_url}")
            return []  # No file? Allow crawling everything
        
        rp.parse(response.text.splitlines())
        
        disallowed_urls = [] 
        
        for entry in rp.entries:
            if entry.useragent != '*':  # For all User-agents
                with open("not_allowed_to_query.txt", "a") as f:
                    f.write(robots_url + "\n")
                domain_name = urlparse(robots_url).netloc
                return [domain_name]  # Return the domain since no URLs are allowed
            
            for disallow_path in entry.disallow:
                disallowed_urls.append(disallow_path)
        
        return disallowed_urls
    
    except Exception as e:
        logger.warning(f"Error parsing robots.txt from {robots_url}: {e}")
        return []

async def setup_playwright_browser():
    """Set up Playwright browser with optimal settings for web scraping."""
    playwright = await async_playwright().start()
    
    # Launch browser with headless mode and optimized settings
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
    )
    
    # Create context with reasonable settings
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    return playwright, browser, context

async def wait_for_page_load(page, timeout=10000):
    """Wait for page to fully load including JavaScript and network requests."""
    try:
        # Wait for the page to load
        await page.wait_for_load_state('networkidle', timeout=timeout)
        
        # Additional check for document ready state
        await page.wait_for_function('document.readyState === "complete"', timeout=timeout)
        
        # Wait for any jQuery AJAX calls to complete if jQuery is present
        try:
            await page.wait_for_function(
                'typeof jQuery === "undefined" || jQuery.active === 0',
                timeout=5000
            )
        except:
            pass  # jQuery might not be present, which is fine
        
        return True
    except Exception as e:
        logger.warning(f"Timeout waiting for page to load: {e}")
        return False

async def get_links(domain_url, url_accept=lambda _: True):
    """
    Extract all unique links from the given domain using Playwright.

    Args:
        domain_url (str): The starting URL of the domain to extract links from.
        url_accept (callable, optional): A callback for accepting URLs

    Yields:
        str: Extracted URLs from the domain.
    """
    if domain_url[-1] != "/":
        domain_url += "/"
    
    robots_path = domain_url + "robots.txt"
    disallowed_urls = get_disallowed_urls(robots_path)
    logger.info(f"Disallowed URLs: {disallowed_urls}")

    if domain_url in disallowed_urls:
        logger.info("Domain URL is disallowed by robots.txt")
        return

    playwright, browser, context = await setup_playwright_browser()
    page = await context.new_page()
    
    try:
        visited = set(disallowed_urls)
        url_dq = deque([domain_url])

        while url_dq:
            current_batch_size = len(url_dq)
            
            for _ in range(current_batch_size):
                url_node = url_dq.popleft()
                
                try:
                    logger.info(f"Visiting: {url_node}")
                    
                    # Navigate to the page
                    response = await page.goto(url_node, timeout=30000)
                    
                    if not response or response.status >= 400:
                        logger.warning(f"Failed to load page: {url_node} (Status: {response.status if response else 'No response'})")
                        continue
                    
                    # Wait for page to fully load
                    if not await wait_for_page_load(page):
                        logger.warning(f"Timeout for page: {url_node}")
                        continue

                    # Extract all href attributes from anchor tags
                    hrefs = await page.evaluate('''
                        () => {
                            const links = Array.from(document.querySelectorAll('a[href]'));
                            return links.map(link => link.href).filter(href => href && href.trim());
                        }
                    ''')
                    
                    logger.info(f"Found {len(hrefs)} links on {url_node}")
                    
                    for href in hrefs:
                        if not href or href in visited:
                            continue
                        
                        visited.add(href)
                        
                        if not url_accept(href):
                            continue
                        
                        url_dq.append(href)
                        yield href

                except Exception as e:
                    logger.error(f"Error processing {url_node}: {e}")
                    continue
    
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    async def main():
        """Main function to demonstrate the web scraper."""
        try:
            domain_url = "https://fcim.utm.md/"
            base_domain = urlparse(domain_url).netloc
            logger.info(f"Base domain: {base_domain}")

            def url_accept_strategy(href):
                parsed_href = urlparse(href)
                if parsed_href.netloc != base_domain:
                    logger.info(f"Not domain URL: {href}")
                    return False
                
                path = parsed_href.path.lower()
                skip_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.xml', '.ico'}
                if any(path.endswith(ext) for ext in skip_extensions):
                    return False
                
                return True

            link_count = 0
            async for link in get_links(domain_url, url_accept_strategy):
                print(f"Found link: {link}")
                link_count += 1
                
                # Optional: Add a limit to prevent infinite crawling
                if link_count >= 100:  # Adjust as needed
                    logger.info("Reached link limit, stopping...")
                    break
            
            logger.info(f"Total links found: {link_count}")
            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    
    asyncio.run(main())