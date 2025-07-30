import asyncio
from playwright.async_api import async_playwright


class PagePool:
    def __init__(self, max_pages: int = 5):
        self.max_pages = max_pages
        self.pool = asyncio.Queue()
        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        for _ in range(self.max_pages):
            page = await self.context.new_page()
            await self.pool.put(page)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        while not self.pool.empty():
            page = await self.pool.get()
            await page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def acquire(self):
        return await self.pool.get()

    async def release(self, page):
        await self.pool.put(page)
