"""
Base class all page objects inherit from. Holds the one thing every page
object needs: a reference to the Playwright page object itself.
"""

from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page
