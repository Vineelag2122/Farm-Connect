import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

def scrape_agri_news():
    try:
        # List of agriculture news sources with their specific selectors
        sources = [
            {
                'url': 'https://www.thehindu.com/business/agri-business/',
                'title_selector': 'h3.title',
                'link_selector': 'h3.title a',
                'source': 'The Hindu'
            },
            {
                'url': 'https://krishijagran.com/news/',
                'title_selector': '.news-title',
                'link_selector': '.news-title a',
                'source': 'Krishi Jagran'
            },
            {
                'url': 'https://www.downtoearth.org.in/category/agriculture',
                'title_selector': '.news-title',
                'link_selector': '.news-title a',
                'source': 'Down To Earth'
            }
        ]
        
        news_items = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for source in sources:
            try:
                logging.info(f"Scraping news from {source['source']}")
                response = requests.get(source['url'], headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find news articles
                articles = soup.select(source['title_selector'])
                links = soup.select(source['link_selector'])
                
                for i, (article, link) in enumerate(zip(articles[:10], links[:10])):
                    title = article.text.strip()
                    url = link.get('href')
                    if not url.startswith('http'):
                        # Handle relative URLs
                        if url.startswith('/'):
                            base_url = '/'.join(source['url'].split('/')[:3])
                            url = base_url + url
                        else:
                            url = source['url'] + url
                    
                    news_items.append({
                        'title': title,
                        'link': url,
                        'source': source['source'],
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
                
                logging.info(f"Successfully scraped {len(articles[:5])} articles from {source['source']}")
                
            except Exception as e:
                logging.error(f"Error scraping {source['source']}: {str(e)}")
                continue
        
        if not news_items:
            # Fallback news items if scraping fails
            news_items = [
                {
                    'title': 'Government Announces New Agricultural Policies',
                    'link': '#',
                    'source': 'Fallback News',
                    'date': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'title': 'Latest Updates on Crop Insurance Schemes',
                    'link': '#',
                    'source': 'Fallback News',
                    'date': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'title': 'Weather Forecast for the Upcoming Season',
                    'link': '#',
                    'source': 'Fallback News',
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            logging.warning("Using fallback news items due to scraping failures")
        
        return news_items
        
    except Exception as e:
        logging.error(f"Critical error in news scraping: {str(e)}")
        return []

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    # Test the scraper
    news = scrape_agri_news()
    for item in news:
        print(f"\nTitle: {item['title']}")
        print(f"Source: {item['source']}")
        print(f"Link: {item['link']}")
        print(f"Date: {item['date']}")
