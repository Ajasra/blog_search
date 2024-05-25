import requests
from bs4 import BeautifulSoup
import markdownify
import csv
import os
import re
import time
import random

def sanitize_filename(filename):
    # Replace any character that is not alphanumeric, a space, or an underscore with an underscore
    filename = re.sub(r'[^\w\s-]', '_', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename

def fetch_and_save_article(source, title, link, output_dir):
    # Sanitize the file name and add the source at the beginning
    file_name = f"{source}_{sanitize_filename(title)}.md"

    file_path = os.path.join(output_dir, file_name)

    # Check if file already exists
    if os.path.exists(file_path):
        # print(f"File {file_name} already exists. Checking for URL.")
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.read()
            if link not in content:
                file.write(f"\n\nOriginal URL: {link}")
                print(f"Added URL to {file_name}")
        return

    response = requests.get(link)
    if response.status_code != 200:
        print(f"Failed to fetch {link}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    article_section = soup.find('article')  # Adjust the tag based on the site's structure
    if not article_section:
        print(f"No article section found in {link}")
        return

    markdown_content = markdownify.markdownify(str(article_section), heading_style="ATX")
    markdown_content += f"\n\nOriginal URL: {link}"

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(markdown_content)

    print(f"Saved {file_name}")
    # Add a random delay between 1 and 5 seconds
    time.sleep(random.uniform(1, 5))

def process_csv_file(csv_file, source, output_dir):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            title, link = row
            try:
                fetch_and_save_article(source, title, link, output_dir)
            except Exception as e:
                print(f"An error occurred while processing {title}: {e}")

# Example usage
output_directory = 'essays'
os.makedirs(output_directory, exist_ok=True)

csv_files_sources = [
    ('to_parse/articles.csv', 'blog'),
    ('to_parse/articles2.csv', 'newyorker')
]

for csv_file, source in csv_files_sources:
    process_csv_file(csv_file, source, output_directory)