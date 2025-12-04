import os
import subprocess
import sys
from pathlib import Path


class ScreenshotService:
    """Service to take screenshots of web applications using Playwright"""

    # Default paths
    DEFAULT_OUTPUT_DIR = "/lab/user"
    DEFAULT_SCREENSHOT_FILENAME = "app_screenshot.png"
    DEFAULT_CONSOLE_LOG_FILENAME = "console_logs.txt"

    @staticmethod
    def ensure_playwright_installed() -> bool:
        """
        Check if playwright is installed and install it if not.
        Returns True if playwright is available, False otherwise.
        """
        try:
            import playwright

            print("Playwright is already installed.")
        except ImportError:
            print("Playwright not found. Installing playwright...")
            try:
                # Install playwright package
                subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
                print("Playwright package installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install playwright: {e}")
                return False

        # Install playwright browsers and system dependencies
        try:
            print("Installing playwright browsers and system dependencies...")

            # Install system dependencies using apt (requires sudo)
            print("Installing system dependencies (requires sudo)...")
            apt_packages = [
                "libglib2.0-0",
                "libnspr4",
                "libnss3",
                "libdbus-1-3",
                "libatk1.0-0",
                "libatk-bridge2.0-0",
                "libcups2",
                "libxkbcommon0",
                "libatspi2.0-0",
                "libxcomposite1",
                "libxdamage1",
                "libxfixes3",
                "libxrandr2",
                "libgbm1",
                "libcairo2",
                "libpango-1.0-0",
                "libasound2",
            ]

            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y"] + apt_packages, capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"Warning: System dependencies installation had issues: {result.stderr}")
                print("Attempting to continue with browser installation...")
            else:
                print("System dependencies installed successfully.")

            # Install playwright browsers
            print("Installing playwright browsers...")
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            print("Playwright browsers installed successfully.")

            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install playwright browsers: {e}")
            return False

    @staticmethod
    def take_screenshot(
        url: str = "http://localhost:8511",
        route: str = "/",
        output_path: str = None,
        save_console_logs: bool = True,
        headless: bool = True,
    ) -> int:
        """
        Take a screenshot of a web application.

        Args:
            url: Base URL of the application (default: http://localhost:8511)
            route: Route to navigate to (default: /)
            output_path: Path where to save the screenshot (default: current directory)
            save_console_logs: Whether to save browser console logs (default: True)
            headless: Whether to run browser in headless mode (default: False)

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Ensure playwright is installed
        if not ScreenshotService.ensure_playwright_installed():
            return 1

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Failed to import playwright after installation.")
            return 1

        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=headless)

                # Create a new page
                page = browser.new_page()

                # Setup console log listener
                console_logs = []
                page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

                # Navigate to the application
                full_url = f"{url}{route}"
                print(f"Navigating to {full_url}")
                page.goto(full_url)

                # Wait for page to load fully
                page.wait_for_load_state("networkidle")

                # Determine screenshot path
                if output_path is None:
                    output_path = os.path.join(
                        ScreenshotService.DEFAULT_OUTPUT_DIR,
                        ScreenshotService.DEFAULT_SCREENSHOT_FILENAME,
                    )
                else:
                    # Ensure the output path is absolute
                    output_path = os.path.abspath(output_path)

                    # Create directory if it doesn't exist
                    output_dir = os.path.dirname(output_path)
                    if output_dir:
                        Path(output_dir).mkdir(parents=True, exist_ok=True)

                # Take screenshot
                page.screenshot(path=output_path)
                print(f"Screenshot saved to {output_path}")

                # Print collected console logs
                if console_logs:
                    print("\nBrowser Console Logs:")
                    for log in console_logs:
                        print(log)

                # Save console logs to a file
                if save_console_logs and console_logs:
                    log_path = os.path.join(
                        os.path.dirname(output_path), ScreenshotService.DEFAULT_CONSOLE_LOG_FILENAME
                    )
                    with open(log_path, "w") as f:
                        f.write("\n".join(console_logs))
                    print(f"Console logs saved to {log_path}")

                # Close browser
                browser.close()

                return 0

        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return 1
