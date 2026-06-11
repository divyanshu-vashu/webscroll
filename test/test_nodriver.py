
import asyncio
import nodriver as uc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_nodriver")

async def test_bypass():
    import os
    url = "https://www.mediamarkt.at/de/product/_gorenje-rb-492-pw-kuhlschrank-e-845-mm-hoch-weiss-142380563.html"
    
    # Absolute path for the profile to avoid issues
    user_data_dir = os.path.abspath("storage/profiles/mediamarkt_test")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir, exist_ok=True)
    
    logger.info(f"Starting browser with profile at: {user_data_dir}")
    # Added no_sandbox=True and simplified start
    browser = await uc.start(
        headless=False, 
        user_data_dir=user_data_dir,
        no_sandbox=True
    )
    
    try:
        logger.info(f"Navigating to {url}")
        page = await browser.get(url)
        
        # --- ROBUST WAIT FOR CLOUDFLARE ---
        logger.info("Waiting for bypass... (up to 60s)")
        for i in range(60): 
            title = await page.evaluate("document.title")
            
            if "MediaMarkt" in title:
                logger.info(f"✅ SUCCESS! Reached target page: {title}")
                break
            
            # If we are stuck on "Just a moment...", try to interact
            if any(term in title for term in ["Just a moment", "Attention Required", "Cloudflare", "Verifying"]):
                if i % 10 == 0:
                    logger.info(f"Attempt {i+1}: Still on challenge page. Sending 'human' signals...")
                    # Click in the general area where a Turnstile checkbox usually is
                    await page.mouse_move(400, 400)
                    await page.mouse_click(400, 400)
                
                if i % 5 == 0:
                    await page.scroll_down(150)
                    await page.sleep(0.5)
                    await page.scroll_up(50)
            
            await page.sleep(1)
        else:
            logger.warning("❌ Failed to bypass challenge within 60 seconds.")
        
        # Final validation
        final_html = await page.evaluate("document.documentElement.outerHTML")
        if "Gorenje" in final_html or "Produktinformationen" in final_html:
            logger.info("🎉 DATA FOUND! Extraction successful.")
        else:
            logger.warning("🤔 Title changed, but specific product data not found in HTML.")
            
        print("\n--- FINAL TITLE ---")
        print(await page.evaluate("document.title"))
        
    finally:
        browser.stop()

if __name__ == "__main__":
    uc.loop().run_until_complete(test_bypass())
