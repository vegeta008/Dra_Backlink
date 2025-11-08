import requests
from bs4 import BeautifulSoup
import argparse
import time
from urllib.parse import urlparse, parse_qs, unquote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import base64

def get_search_results(domain, page=0, dork=""):
    """
    Performs a Bing search using a headless browser and returns the HTML content.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
    
    # Combine the main query with the optional dork
    query = f'linkfromdomain:{domain} {dork}'.strip()
    # Bing's pagination is 1-based and uses 'first'
    first = page * 10 + 1
    url = f"https://www.bing.com/search?q={query}&first={first}"

    print(f"[*] Searching on Bing with Selenium: {url}")
    
    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        
        # Wait for the page to load. A simple sleep is used for simplicity.
        # A more robust solution would use WebDriverWait.
        print("[*] Waiting for page to load...")
        time.sleep(5)
        
        html_content = driver.page_source
        
        return html_content
    except Exception as e:
        print(f"[!] An error occurred with Selenium: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def parse_links(html_content):
    """
    Parses the Bing search results page to extract and clean backlink URLs.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    for li in soup.find_all('li', class_='b_algo'):
        h2_tag = li.find('h2')
        if h2_tag:
            a_tag = h2_tag.find('a')
            if a_tag and a_tag.get('href'):
                bing_redirect_link = a_tag.get('href')
                
                # Check if it's a Bing redirect link
                if "bing.com/ck/a?!" in bing_redirect_link:
                    parsed_url = urlparse(bing_redirect_link)
                    query_params = parse_qs(parsed_url.query)
                    
                    # The actual URL is usually in the 'u' parameter
                    encoded_url_param = query_params.get('u', [None])[0]
                    
                    if encoded_url_param:
                        try:
                            # Bing sometimes adds 'a1' prefix, remove it
                            if encoded_url_param.startswith('a1'):
                                encoded_url_param = encoded_url_param[2:]
                            
                            # Base64 strings sometimes omit padding. Add it if necessary.
                            missing_padding = len(encoded_url_param) % 4
                            if missing_padding:
                                encoded_url_param += '=' * (4 - missing_padding)
                            
                            # Base64 decode (replace URL-safe chars with standard ones)
                            decoded_bytes = base64.b64decode(encoded_url_param.replace('-', '+').replace('_', '/'))
                            decoded_url = decoded_bytes.decode('utf-8')
                            
                            # URL decode again in case it was double encoded
                            final_url = unquote(decoded_url)
                            links.append(final_url)
                        except Exception as e:
                            print(f"[!] Error decoding Bing URL '{encoded_url_param}': {e}")
                            # Fallback to the original Bing redirect link if decoding fails
                            links.append(bing_redirect_link)
                    else:
                        links.append(bing_redirect_link)
                else:
                    # If not a Bing redirect, add the link directly
                    links.append(unquote(bing_redirect_link))

    return links

def main():
    """
    Main function to run the automated backlink checker for single or multiple domains.
    """
    parser = argparse.ArgumentParser(description="Automated Backlink Checker using Bing Search and common dorks.")
    parser.add_argument("domain", nargs='?', default=None, help="A single domain to check for backlinks (e.g., example.com).")
    parser.add_argument("-f", "--file", help="Path to a file containing a list of domains to scan (one per line).")
    parser.add_argument("--pages", type=int, default=1, help="Number of Bing search pages to crawl for EACH dork. Default is 1.")
    args = parser.parse_args()

    if not args.domain and not args.file:
        parser.error("You must provide either a single domain or a file with the -f flag.")
    if args.domain and args.file:
        parser.error("You cannot provide both a single domain and a file. Please choose one.")

    domains_to_scan = []
    if args.domain:
        domains_to_scan.append(args.domain)
    else:
        try:
            with open(args.file, 'r') as f:
                domains_to_scan = [line.strip() for line in f if line.strip()]
            if not domains_to_scan:
                print(f"[!] The file '{args.file}' is empty or contains no valid domains.")
                return
        except FileNotFoundError:
            print(f"[!] Error: The file '{args.file}' was not found.")
            return

    dork_templates = [
        'intext:"{domain}"',
        'inurl:"{domain}"',
        'intitle:"{domain}"',
        '"powered by {domain}"',
        '"visit {domain}"',
        '"source: {domain}"',
        'filetype:pdf intext:"{domain}"',
        'site:.gov intext:"{domain}"',
        'site:.edu intext:"{domain}"',
        'site:.org intext:"{domain}"',
    ]
    
    for domain in domains_to_scan:
        print(f"\n\n--- Starting automated backlink check for: {domain} ---")
        all_links = set()

        for dork_template in dork_templates:
            dork = dork_template.format(domain=domain)
            print(f"\n[*] Using dork: {dork}")
            print(f"[*] Crawling {args.pages} page(s) of Bing results for this dork...")

            for i in range(args.pages):
                html = get_search_results(domain, page=i, dork=dork)
                if html:
                    found_links = parse_links(html)
                    if not found_links:
                        print("[*] No more results found for this dork.")
                        break
                    
                    new_links_found = 0
                    for link in found_links:
                        parsed_link_domain = urlparse(link).netloc
                        if domain not in parsed_link_domain and "bing.com" not in parsed_link_domain:
                            if link not in all_links:
                                all_links.add(link)
                                new_links_found += 1
                    
                    if new_links_found > 0:
                        print(f"[*] Found {new_links_found} new potential backlink(s) on page {i+1}.")

                    time.sleep(2) 
                else:
                    break

        if all_links:
            print(f"\n[+] Found a total of {len(all_links)} potential backlinks for {domain}:")
            for link in sorted(list(all_links)):
                print(f"  - {link}")
        else:
            print(f"\n[-] No potential backlinks found for {domain}.")

if __name__ == "__main__":
    main()
