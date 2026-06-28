import asyncio
import os
import sys
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\TS-PC-022\.gemini\antigravity\brain\747e7568-de34-41bd-9686-773a057b88eb"

async def run_verification():
    print("Launching Playwright browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a browser context with large viewport
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Handle browser alert dialogs automatically
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

        # 1. Navigate to frontend dashboard
        print("Navigating to http://localhost:3000...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)  # Wait for page to load fully and ping backend
        
        initial_path = os.path.join(ARTIFACT_DIR, "1_initial_dashboard.png")
        await page.screenshot(path=initial_path)
        print(f"Captured initial dashboard state: {initial_path}")

        # 2. Place a new order
        print("Filling out order form...")
        await page.fill("#productName", "AI Tensor Processor H100")
        await page.fill("#quantity", "5")
        
        # Click submit button
        print("Submitting order...")
        await page.click("button[type='submit']")
        await page.wait_for_timeout(4000)  # Wait for order to register and poll
        
        order_placed_path = os.path.join(ARTIFACT_DIR, "2_order_placed.png")
        await page.screenshot(path=order_placed_path)
        print(f"Captured order placement state: {order_placed_path}")

        # 3. Trigger Payment Webhook (HMAC verified)
        print("Triggering secure payment webhook...")
        # Find the trigger button in the table
        await page.click("text=Trigger Webhook")
        await page.wait_for_timeout(4000)  # Wait for webhook processing and polling
        
        webhook_triggered_path = os.path.join(ARTIFACT_DIR, "3_payment_completed.png")
        await page.screenshot(path=webhook_triggered_path)
        print(f"Captured webhook completion state: {webhook_triggered_path}")

        # 4. View AI Diagnostic Summary
        print("Opening glassmorphic diagnostic drawer...")
        await page.click("text=View Diagnostic")
        await page.wait_for_timeout(2000)  # Wait for transition animation
        
        drawer_path = os.path.join(ARTIFACT_DIR, "4_diagnostic_drawer.png")
        await page.screenshot(path=drawer_path)
        print(f"Captured AI diagnostic drawer: {drawer_path}")

        await browser.close()
        print("Playwright UI verification finished successfully.")

if __name__ == "__main__":
    asyncio.run(run_verification())
