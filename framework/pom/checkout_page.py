from framework.pom.base_page import BasePage


class CheckoutPage(BasePage):
    def goto(self, base_url: str):
        self.page.goto(f"{base_url}/checkout-page")

    def pay(self):
        self.page.click("#pay-button")

    def is_confirmed(self) -> bool:
        return self.page.locator("#confirmation").is_visible()
