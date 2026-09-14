# rcap-client

[rcap](https://github.com/mahdi-marjani/rcap) browser interactions for solving reCAPTCHA using Selenium or Playwright and rcap server.

## Installation

Install via pip:

```
pip install rcap-client
```

## Usage

### Selenium

```python
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from rcap_client.selenium import SeleniumRecaptchaSolver

driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))
driver.get("https://www.google.com/recaptcha/api2/demo")

solver = SeleniumRecaptchaSolver(driver)
solver.solve()  # Done!

print("reCAPTCHA solved!")
input("Press Enter to quit...")
driver.quit()
```

### Playwright

```python
from rcap_client.playwright import PlaywrightRecaptchaSolver
from playwright.sync_api import sync_playwright

playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)
page = browser.new_page()
page.goto("https://www.google.com/recaptcha/api2/demo")

solver = PlaywrightRecaptchaSolver(page)
solver.solve()  # Done!

print("reCAPTCHA solved!")
input("Press Enter to quit...")
page.close()
```

## Details

- Uses Selenium or Playwright for browser interaction.
- Relies on a local API (localhost:8000) for image detection.
