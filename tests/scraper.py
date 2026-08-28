import requests
from bs4 import BeautifulSoup
import csv
import json

def scrape_articles(url: str):
    """
    Fetches and parses news articles from the given URL.

    Args:
        url: The URL of the news page to scrape.

    Returns:
        list[dict]: A list of dictionaries, where each dict represents a scraped article.
    """
    print(f"Starting scrape on URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # --- T2 Logic: Scrape all article links from the homepage ---
        # Instead of relying on a volatile class, we find all links and filter them
        # to only include those that point to specific articles (i.e., contain '/news/').
        
        # We search for all anchor tags.
        all_links = soup.find_all('a')
        
        for link_tag in all_links:
            link = link_tag.get('href')
            title_tag = link_tag.find('h3') or link_tag.parent.find('h3') # Look for h3 inside or parent
            
            if link and link.startswith('/news/') and title_tag:
                title = title_tag.text.strip()
                
                # Ensure the link is absolute
                if not link.startswith('http'):
                    link = "https://www.bbc.com" + link
                
                articles.append({
                    'title': title,
                    'link': link,
                    'source': 'BBC News Homepage' # Static source for this initial scrape
                })
        
        print(f"Found {len(articles)} potential articles on the homepage.")
        
        return articles
        
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return []

def save_articles(articles: list[dict], filename: str):
    """
    Saves the list of articles to a CSV file.
    """
    if not articles:
        print("No articles to save.")
        return

    keys = articles[0].keys()
    
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(articles)
        
    print(f"Successfully saved {len(articles)} articles to {filename}")


if __name__ == "__main__":
    # Target URL for testing (BBC News homepage)
    TARGET_URL = "https://www.bbc.com/news"
    OUTPUT_FILE = "news_articles.csv"

    # Phase 1: Get the articles
    scraped_data = scrape_articles(TARGET_URL)

    # Phase 3: Save the articles
    save_articles(scraped_data, OUTPUT_FILE)