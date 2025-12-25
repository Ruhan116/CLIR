import requests
from bs4 import BeautifulSoup

url = "https://www.bssnews.net/news/100-days-of-interim-government"

try:
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    prettified_html = soup.prettify()
    
    with open('all_scraped_experiment.txt', 'w', encoding='utf-8') as f:
        f.write(prettified_html)
    
    print("HTML saved to tbs_experiment.txt")
except requests.exceptions.RequestException as e:
    print(f"Error fetching the URL: {e}")
except Exception as e:
    print(f"Error: {e}")