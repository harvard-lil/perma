import asyncio
from playwright.async_api import async_playwright


from fabric.decorators import task

@task
def screenshots(base_url='http://perma.test:8000', output_path='/playwright/screenshots', browser='chrome'):
    async def screenshot(page, upper_left_selector, lower_right_selector, file_name, upper_left_offset=(0,0), lower_right_offset=(0,0)):
        print(f"Capturing {file_name}")
        upper_left_locator = page.locator(upper_left_selector)
        lower_right_locator = page.locator(lower_right_selector)
        upper_left_box = await upper_left_locator.bounding_box()
        lower_right_box = await lower_right_locator.bounding_box()
        x = upper_left_box['x'] + upper_left_offset[0]
        y = upper_left_box['y'] + upper_left_offset[1]
        width = lower_right_box['x'] + lower_right_box['width'] + lower_right_offset[0] - x
        height = lower_right_box['y'] + lower_right_box['height'] + lower_right_offset[1] - y
        await page.screenshot(path=file_name, clip={"x": x, "y": y, "width": width,"height": height })


    async def do_snaps(browser_instance, url, save_path):
        page = await browser_instance.new_page()
        await page.goto(url)
        await page.set_viewport_size({"width":1300, "height":800})

        await screenshot(page, 'header', '#landing-introduction', save_path + 'screenshot_home.png')

        # login screen
        await page.goto(url + '/login')
        await screenshot(page, 'header', '#main-content', save_path + 'screenshot_create_account.png')

        # logged in user - drop-down menu
        username = page.locator('#id_username')
        await username.focus()
        await username.type('test_user@example.com')
        password = page.locator('#id_password')
        await password.focus()
        await password.type('pass')
        await page.locator("button.btn.login").click()
        await page.locator("a.navbar-link").click()
        await screenshot(page, 'header', 'ul.dropdown-menu', save_path + 'screenshot_dropdown.png', lower_right_offset=(15,15))

        await browser_instance.close()

    async def run():
        async with async_playwright() as p:
            browser_instance = None
            if browser=='firefox':
                browser_instance = p.firefox
            elif browser == 'webkit':
                browser_instance = p.webkit
            else:
                browser_instance = p.chromium
            browser_l = await browser_instance.launch()
            await do_snaps(browser_l, base_url, output_path + '/')

    asyncio.run(run())
