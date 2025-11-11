from playwright.sync_api import sync_playwright
import time

def order_pizzas(address, city, state, zip_code, pizzas):
    """
    pizzas: list of tuples [(pizza_name, quantity), ...]
    Example: [("Ultimate Pepperoni", 2), ("Cheese Lovers", 1)]
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
        context = browser.new_context(
            permissions=["geolocation"],
            geolocation={"latitude": 30.6280, "longitude": -96.3344},
        )
        page = context.new_page()

        # Go to Domino's homepage
        page.goto('https://www.dominos.com/')

        # Accept cookies (if popup appears)
        try:
            page.click('button.button-agree')
        except:
            pass

        # Delivery
        page.click("text=Delivery")

        # Fill address form
        page.get_by_label("Street Address").type(address, delay=100)
        page.get_by_label("City").type(city, delay=100)
        page.get_by_role("combobox", name="State").click()
        page.get_by_role("option", name=state).click()
        page.get_by_label("Zip Code").type(zip_code, delay=100)

        # Continue
        page.get_by_role("button", name="Continue").click()
        page.get_by_role("button", name="Confirm").click()

        # Wait for menu
        page.wait_for_selector('text=Browse Menu')
        page.click('a[href="/menu/specialty"]')
        page.wait_for_selector('text="Specialty Pizzas"')
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(1500)

        # Add pizzas
        for pizza_name, qty in pizzas:
            card = page.locator(f'div.clickable-card:has(h2:text-is("{pizza_name}"))')
            add_button = card.locator(f'button[aria-label="Add {pizza_name} to Cart"]')
            plus_button = card.locator(f'button[aria-label="Add one {pizza_name}"]')

            # Add N pizzas
            for i in range(qty):
                try:
                    if i == 0:
                        # First pizza: click Add button
                        add_button.click(force=True)
                    else:
                        # Subsequent pizzas: click + button
                        plus_button.click(force=True)
                    time.sleep(1)  # allow UI to update
                except Exception as e:
                    print(f"⚠️ Could not add pizza #{i+1}: {e}")
        print(f"Successfully added 2 {pizza_name} pizzas to cart.")
        page.wait_for_timeout(150000)


# Example usage
# order_pizzas(
#     address="161 Wellborn Road",
#     city="College Station",
#     state="TX",
#     zip_code="77840",
#     pizzas=[("Ultimate Pepperoni", 2)]
# )
