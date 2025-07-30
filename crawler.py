import asyncio
import logging
from collections import deque
from urllib.parse import urlparse, urljoin
import urllib.robotparser
import requests
from page_pool import PagePool
from bs4 import BeautifulSoup

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
    
def normalize_url(url: str, base_url: str):
    """Normalize and resolve URL relative to base URL."""
    try:
        # Handle relative URLs
        full_url = urljoin(base_url, url.strip())
        
        # Parse and clean URL
        parsed = urlparse(full_url)
        
        # Remove fragment
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
            
        return clean_url
    except Exception as e:
        logger.warning(f"Could not normalize URL {url}: {e}")
        return None

def is_same_domain(url: str, domain_url: str) -> bool:
    """Check if URL belongs to the same domain."""
    try:
        url_domain = urlparse(url).netloc.lower()
        base_domain = urlparse(domain_url).netloc.lower()
        return url_domain == base_domain
    except Exception:
        return False

async def get_links(domain_url, url_accept=lambda _: True, page_pool: PagePool = None):
    if domain_url[-1] != "/":
        domain_url += "/"

    robots_path = domain_url + "robots.txt"
    disallowed_urls = get_disallowed_urls(robots_path)
    logger.info(f"Disallowed URLs: {disallowed_urls}")

    if domain_url in disallowed_urls:
        logger.info("Domain URL is disallowed by robots.txt")
        return

    internal_page_pool = False

    if page_pool is None:
        page_pool = PagePool()
        await page_pool.__aenter__()  # manually enter context
        internal_page_pool = True

    page = await page_pool.acquire()

    try:
        visited = set(disallowed_urls)
        url_dq = deque([domain_url])

        while url_dq:
            current_batch_size = len(url_dq)

            for _ in range(current_batch_size):
                url_node = url_dq.popleft()
                if url_node in visited:
                    continue

                visited.add(url_node)

                try:
                    logger.info(f"Visiting: {url_node}")

                    # Navigate to page with Playwright
                    response = await page.goto(url_node, wait_until="domcontentloaded", timeout=30000)
                    if not response or response.status >= 400:
                        logger.warning(f"Failed to load page: {url_node} (Status: {response.status if response else 'No response'})")
                        continue

                    # Get HTML content from Playwright
                    html_content = await page.content()
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract all links using BeautifulSoup
                    link_elements = soup.find_all('a', href=True)
                    hrefs = []
                    
                    for link in link_elements:
                        href = link.get('href')
                        if href:
                            # Normalize the URL
                            normalized_href = normalize_url(href, url_node)
                            if normalized_href:
                                hrefs.append(normalized_href)

                    logger.info(f"Found {len(hrefs)} links on {url_node}")

                    for href in hrefs:
                        if not href or href in visited:
                            continue

                        # Only process links from the same domain
                        if not is_same_domain(href, domain_url):
                            logger.debug(f"Skipping external link: {href}")
                            continue

                        # Check if URL is accepted by the filter
                        if not url_accept(href):
                            logger.debug(f"URL rejected by filter: {href}")
                            continue

                        # Add to queue for further crawling
                        url_dq.append(href)
                        
                        # Yield the accepted link
                        yield href

                except Exception as e:
                    logger.error(f"Error processing {url_node}: {e}")
                    continue

                # Optional: Add delay between requests to be respectful
                await asyncio.sleep(0.1)

    finally:
        await page_pool.release(page)
        if internal_page_pool:
            await page_pool.__aexit__(None, None, None)

if __name__ == "__main__":
    async def main():
        """Main function to demonstrate the web scraper."""
        try:
            domain_url = "https://accesimobil.md/"
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
                
            logger.info(f"Total links found: {link_count}")
            
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
    
    asyncio.run(main())