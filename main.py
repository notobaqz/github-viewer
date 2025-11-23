import asyncio
import random
from playwright.async_api import async_playwright

agents = [
    "mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/129.0 safari/537.36",
    "mozilla/5.0 (macintosh; intel mac os x 13_2) applewebkit/605.1.15 (khtml, like gecko) version/16.3 safari/605.1.15",
    "mozilla/5.0 (x11; linux x86_64) applewebkit/537.36 (khtml, like gecko) chrome/115.0 safari/537.36",
    "mozilla/5.0 (windows nt 10.0; win64; x64; rv:117.0) gecko/20100101 firefox/117.0",
]

user = str(input("user? "))
url = f"https://github.com/{user}"
print(f"  using {url}")

async def mousemove(page):
    box = await page.evaluate(
        """() => {
            const body = document.body;
            return {width: body.clientWidth, height: body.clientHeight};
        }"""
    )

    for _ in range(random.randint(2, 5)):
        x = random.randint(0, box["width"])
        y = random.randint(0, box["height"])
        await page.mouse.move(x, y, steps=random.randint(2, 5))
        await asyncio.sleep(random.uniform(0.05, 0.1))

async def blockres(route):
    if route.request.resource_type in {"image", "stylesheet", "font"}:
        await route.abort()
    else:
        await route.continue_()

async def visit(browser, index, semaphore):
    async with semaphore:
        user_agent = random.choice(agents)
        print(f"  {index} using user-agent: {user_agent}")

        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        await page.route("**/*", blockres)
        await page.goto(f"{url}", wait_until="networkidle", timeout=120000)

        await mousemove(page)
        await asyncio.sleep(random.uniform(1, 2))

        title = await page.title()
        print(f"  {index} page title {title}")

        await context.close()

async def main():
    semaphore = asyncio.Semaphore(5) # 5 = number running at once (concurrency)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        tasks = [visit(browser, i, semaphore) for i in range(1, 101)]
        await asyncio.gather(*tasks)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
