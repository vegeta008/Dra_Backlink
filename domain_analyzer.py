# --- Imports ---
import os
import sys
import argparse
import time
import base64
import requests
from urllib.parse import urlparse, parse_qs, unquote

# Import third-party libraries
from bs4 import BeautifulSoup
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# --- Backlink Scanner Functions ---

def get_search_results(domain, page=0, dork=""):
    """
    Performs a Bing search using a headless browser and returns the HTML content.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
    
    query = f'linkfromdomain:{domain} {dork}'.strip()
    first = page * 10 + 1
    url = f"https://www.bing.com/search?q={query}&first={first}"

    print(f"[*] Searching on Bing with Selenium: {url}")
    
    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        print("[*] Waiting for page to load...")
        time.sleep(5)
        return driver.page_source
    except Exception as e:
        print(f"{Fore.RED}[!] An error occurred with Selenium: {e}{Style.RESET_ALL}")
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
                if "bing.com/ck/a?!" in bing_redirect_link:
                    parsed_url = urlparse(bing_redirect_link)
                    query_params = parse_qs(parsed_url.query)
                    encoded_url_param = query_params.get('u', [None])[0]
                    if encoded_url_param:
                        try:
                            if encoded_url_param.startswith('a1'):
                                encoded_url_param = encoded_url_param[2:]
                            missing_padding = len(encoded_url_param) % 4
                            if missing_padding:
                                encoded_url_param += '=' * (4 - missing_padding)
                            decoded_bytes = base64.b64decode(encoded_url_param.replace('-', '+').replace('_', '/'))
                            final_url = unquote(decoded_bytes.decode('utf-8'))
                            links.append(final_url)
                        except Exception:
                            links.append(bing_redirect_link)
                else:
                    links.append(unquote(bing_redirect_link))
    return links

def run_backlink_scan(domain, num_pages, output_filepath):
    """
    Executes the full backlink scanning process and writes results to a file.
    """
    dork_templates = [
        'intext:"{domain}"', 'inurl:"{domain}"', 'intitle:"{domain}"',
        '"powered by {domain}"', '"visit {domain}"', '"source: {domain}"',
        'filetype:pdf intext:"{domain}"', 'site:.gov intext:"{domain}"',
        'site:.edu intext:"{domain}"', 'site:.org intext:"{domain}"',
    ]
    
    print(f"{Style.BRIGHT}\n--- Starting Backlink Scan for: {Fore.CYAN}{domain}{Style.RESET_ALL} ---")
    all_links = set()

    for dork_template in dork_templates:
        dork = dork_template.format(domain=domain)
        print(f"\n[*] Using dork: {dork}")
        for i in range(num_pages):
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

    with open(output_filepath, 'a', encoding='utf-8') as f:
        if all_links:
            f.write(f"--- Backlinks Found ({len(all_links)}) ---\n")
            for link in sorted(list(all_links)):
                f.write(f"{link}\n")
            f.write("\n")
            print(f"\n{Fore.GREEN}[+] Appended {len(all_links)} backlinks to {output_filepath}{Style.RESET_ALL}")
        else:
            f.write("--- Backlinks Found ---\nNo potential backlinks found.\n\n")
            print(f"\n{Fore.YELLOW}[-] No potential backlinks found for {domain}.{Style.RESET_ALL}")

# --- Wayback Machine Scanner Functions ---

def fetch_wayback_urls(domain):
    """Fetches all URLs for a domain from the Wayback Machine CDX API."""
    print(f"[*] Fetching all known URLs for {Fore.CYAN}{domain}{Style.RESET_ALL} from Wayback Machine. This may take a moment...")
    cdx_url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original&collapse=urlkey"
    
    try:
        response = requests.get(cdx_url, timeout=60)
        response.raise_for_status()
        results = response.json()[1:]
        urls = [item[0] for item in results]
        print(f"{Fore.GREEN}[+] Found {len(urls)} total unique URLs for {domain}.")
        return urls
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[!] Error connecting to Wayback Machine for {domain}: {e}{Style.RESET_ALL}", file=sys.stderr)
        return []
    except (ValueError, IndexError):
        print(f"{Fore.RED}[!] Error parsing JSON response for {domain}. No archives may exist.{Style.RESET_ALL}", file=sys.stderr)
        return []

def filter_urls_by_extension(urls, extensions):
    """Filters a list of URLs based on a list of extensions."""
    print(f"[*] Filtering URLs with {len(extensions)} extensions...")
    filtered_map = {ext: [] for ext in extensions}
    for url in urls:
        for ext in extensions:
            if url.lower().endswith(ext):
                filtered_map[ext].append(url)
                break
    
    count = sum(len(v) for v in filtered_map.values())
    print(f"{Fore.GREEN}[+] Found {count} URLs matching the specified extensions.")
    return filtered_map

def append_wayback_results(output_filepath, filtered_map):
    """Appends the filtered Wayback URLs to the consolidated output file."""
    print(f"[*] Appending Wayback Machine results to '{output_filepath}'")
    
    with open(output_filepath, 'a', encoding='utf-8') as f:
        f.write("--- Wayback Machine Results ---\n")
        total_found = 0
        for ext, urls in filtered_map.items():
            if urls:
                total_found += len(urls)
                f.write(f"\n[+] Found {len(urls)} URLs with extension {ext}:\n")
                for url in urls:
                    f.write(f"{url}\n")
        
        if total_found == 0:
            f.write("No files found matching the specified extensions.\n")
        
        f.write("\n")

def run_wayback_scan(domain, extensions, output_filepath):
    """
    Executes the full Wayback Machine scanning process and writes results to a file.
    """
    print(f"{Style.BRIGHT}\n--- Starting Wayback Machine Scan for: {Fore.CYAN}{domain}{Style.RESET_ALL} ---")
    
    if not extensions:
        print(f"{Fore.RED}[!] No extensions specified for Wayback scan. Skipping.{Style.RESET_ALL}")
        return

    all_urls = fetch_wayback_urls(domain)
    if not all_urls:
        return
        
    filtered_map = filter_urls_by_extension(all_urls, extensions)
    
    if sum(len(v) for v in filtered_map.values()) > 0:
        append_wayback_results(output_filepath, filtered_map)
    else:
        print(f"{Fore.YELLOW}[-] No files found matching the specified extensions.{Style.RESET_ALL}")
        with open(output_filepath, 'a', encoding='utf-8') as f:
            f.write("--- Wayback Machine Results ---\n")
            f.write("No files found matching the specified extensions.\n\n")

# --- Main Execution ---

def main():
    """
    Main function to run the domain analysis tool.
    """
    init(autoreset=True)
    parser = argparse.ArgumentParser(
        description="Domain Analyzer: Scans for backlinks and historical files.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("domain", nargs='?', default=None, help="A single domain to scan (e.g., example.com).")
    parser.add_argument("-f", "--file", help="Path to a file containing a list of domains to scan (one per line).")
    parser.add_argument("--scan", required=True, choices=['backlinks', 'wayback', 'all'], help="The type of scan to perform.")
    parser.add_argument("--pages", type=int, default=10, help="For backlink scan: number of pages to crawl per dork.")
    parser.add_argument("--extensions", default=".zip,.sql,.bak,.rar,.tar.gz,.7z,.old,.backup", help="For Wayback scan: comma-separated list of file extensions to look for.")
    
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
            # Adjust file path to be relative to the script's location if not absolute
            file_path = args.file
            if not os.path.isabs(file_path):
                script_dir = os.path.dirname(os.path.realpath(__file__))
                file_path = os.path.join(script_dir, file_path)

            with open(file_path, 'r') as f:
                domains_to_scan = [line.strip() for line in f if line.strip()]
            if not domains_to_scan:
                print(f"{Fore.RED}[!] The file '{args.file}' is empty or contains no valid domains.{Style.RESET_ALL}")
                return
        except FileNotFoundError:
            print(f"{Fore.RED}[!] Error: The file '{args.file}' was not found.{Style.RESET_ALL}")
            return

    extensions = [ext.strip() for ext in args.extensions.split(',')]

    for domain in domains_to_scan:
        print(f"\n\n{'='*60}")
        print(f"{Style.BRIGHT}Processing Domain: {Fore.YELLOW}{domain}{Style.RESET_ALL}")
        print(f"{'='*60}")

        # Define the single output file for this domain
        script_dir = os.path.dirname(os.path.realpath(__file__))
        output_filepath = os.path.join(script_dir, f"{domain}_analysis.txt")
        
        # Start with a clean file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(f"Analysis Report for: {domain}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        print(f"{Fore.YELLOW}[*] Results for this domain will be saved to: {output_filepath}{Style.RESET_ALL}")

        if args.scan in ['backlinks', 'all']:
            run_backlink_scan(domain, args.pages, output_filepath)
        
        if args.scan in ['wayback', 'all']:
            run_wayback_scan(domain, extensions, output_filepath)

    print(f"\n{Fore.GREEN}All processing complete.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
