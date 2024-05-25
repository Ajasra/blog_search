import requests
from bs4 import BeautifulSoup
import csv

def fetch_titles_and_links_calnewport(url, output_file):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    list_allposts = soup.find('div', id='list_allposts')
    if not list_allposts:
        print(f"No div with id 'list_allposts' found in {url}")
        return

    articles = list_allposts.find_all('a')
    with open(output_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for article in articles:
            title = article.get_text(strip=True)
            link = article['href']
            writer.writerow([title, link])

    print(f"Saved titles and links from {url} to {output_file}")

def extract_titles_and_links_from_file(html_file, output_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    grid_content = soup.find('div', class_='grid-layout__content')
    if not grid_content:
        print(f"No div with class 'grid-layout__content' found in {html_file}")
        return

    articles = grid_content.find_all('a', class_='summary-item__hed-link')
    with open(output_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for article in articles:
            title = article.get_text(strip=True)
            link = article['href']
            writer.writerow([title, link])

    print(f"Saved titles and links from {html_file} to {output_file}")

# Example usage
output_file = 'to_parse/articles.csv'
urls_and_sites = [
    ("https://calnewport.com/archive/", fetch_titles_and_links_calnewport),
    ("newyorker.html", extract_titles_and_links_from_file)
]

# Create or overwrite the CSV file and write the header
with open(output_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Title', 'Link'])

# Fetch titles and links from the URL and the saved HTML file
for url, fetch_function in urls_and_sites:
    fetch_function(url, output_file)