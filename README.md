# Web Crawller 

This project utilizes Selenium and ChromeDriver to scrape links from a specified domain. It sets up a headless Chrome instance and extracts all unique links from the website while respecting `robots.txt` rules.

## Features

- **JavaScript Support**: It waits for the page to fully load, including JavaScript-rendered content.
- **Respecting robots.txt**: The scraper checks the site's `robots.txt` file to avoid scraping disallowed URLs.
- **Automatic Chrome & WebDriver Setup**: Chrome and the ChromeDriver are installed and set up automatically, ensuring compatibility and ease of use.

## Requirements

Make sure to install these dependencies before running the project. You can install them using the `requirements.txt` file provided.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/VMM-MMV/url_crawler
   cd url_crawler
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. **Automatic Installation of Google Chrome (Linux)**:

   The script includes an automatic method to install Google Chrome for Linux if it is not already installed.

4. **Manual Installation of Chrome** (if needed):

   If you prefer to install Chrome manually, you can follow these steps:

   ```bash
   sudo apt-get update
   sudo apt-get install -y wget gnupg2 software-properties-common
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo apt install ./google-chrome-stable_current_amd64.deb -y
   ```

## Usage

### Scraping Links

To start scraping, simply run the script:

```bash
python scraper.py
```

This will:

- Set up the ChromeDriver with the appropriate options.
- Begin scraping the specified URL (default: `https://fcim.utm.md/`).
- Respect `robots.txt` by excluding disallowed links.
- Print all the links found on the site.

You can modify the `domain_url` variable in the script to target a different website.