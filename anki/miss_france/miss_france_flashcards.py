#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Miss France Anki Flashcard Generator

This script parses the miss_france.html file to extract information about Miss France winners
(names, regions, years, images), downloads the images to the images directory, and creates
an Anki flashcard deck using genanki with multiple card types.

Card types:
1. Name to region
2. Name to year
3. Year to name
4. Picture to name
"""

import os
import re
import time
import random
import hashlib
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import genanki

# Constants
IMAGES_DIR = "images"
WIKIPEDIA_URL = "https://fr.wikipedia.org/wiki/Miss_France"
OUTPUT_DECK = "miss_france_deck.apkg"
# Use requests.__version__ to include the actual version in the User-Agent
USER_AGENT = f'Miss-France-Flashcards/1.0 (Educational project; https://github.com/lfavole) Python-Requests/{requests.__version__}'

# Ensure the images directory exists
os.makedirs(IMAGES_DIR, exist_ok=True)

# Define the model for the flashcards
# We'll use a single model with different templates for different card types
MODEL_ID = random.randrange(1 << 30, 1 << 31)
DECK_ID = random.randrange(1 << 30, 1 << 31)

class MissFranceNote(genanki.Note):
    """Custom note class to generate ID based on data"""

    @property
    def guid(self):
        # Use the name and year as a unique identifier
        return hashlib.sha256(f"{self.fields[0]}_{self.fields[1]}".encode('utf-8')).hexdigest()

# Define the model for our flashcards
# Fields: Name, Year, Region, ImagePath
miss_france_model = genanki.Model(
    MODEL_ID,
    'Miss France',
    fields=[
        {'name': 'Nom'},
        {'name': 'Année'},
        {'name': 'Région'},
        {'name': 'Image'},
    ],
    templates=[
        {
            'name': 'Nom -> région',
            'qfmt': '<p>De quelle <span class="question-word">région</span> vient <span class="question">{{Nom}} <small>(Miss France {{Année}})</small></span>&nbsp;?</p>',
            'afmt': '<p><span class="question">{{Nom}} (Miss France {{Année}})</span> vient de la <span class="question-word">région</span> <span class="answer">{{Région}}</span>.</p>',
        },
        {
            'name': 'Nom -> année',
            'qfmt': '<p>En quelle <span class="question-word">année</span> <span class="question">{{Nom}}</span> a-t-elle remporté Miss France&nbsp;?</p>',
            'afmt': '<p><span class="question">{{Nom}}</span> a remporté Miss France en <span class="answer">{{Année}}</span>.</p>',
        },
        {
            'name': 'Année -> nom',
            'qfmt': '<p><span class="question-word">Qui</span> a remporté Miss France en <span class="question">{{Année}}</span>&nbsp;?</p>',
            'afmt': '<p><span class="answer">{{Nom}} <small>(Miss {{Région}})</small></span> a remporté Miss France en <span class="question">{{Année}}</span>.</p>',
        },
        {
            'name': 'Image -> nom',
            'qfmt': '{{#Image}}<p class="above-map"><span class="question-word">Qui</span> est cette Miss France&nbsp;?</p><p>{{Image}}</p>{{/Image}}',
            'afmt': '<p class="above-map"><span class="answer">{{Nom}} <small>(Miss France {{Année}} - {{Région}})</small></span></p><p>{{Image}}</p>',
        },
    ],
    css='@import "_style.css";',
)

def download_wikipedia_content() -> str:
    """
    Download HTML content from the Miss France Wikipedia page.

    Returns:
        HTML content as a string
    """
    print(f"Downloading content from {WIKIPEDIA_URL}...")

    # Add a proper User-Agent header
    headers = {
        'User-Agent': USER_AGENT
    }

    try:
        response = requests.get(WIKIPEDIA_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error downloading Wikipedia content: {e}")
        raise

def parse_miss_france_html(html_content: str) -> List[Dict[str, str]]:
    """
    Parse the Miss France HTML content to extract information about winners.

    Args:
        html_content: HTML content as a string

    Returns:
        List of dictionaries containing information about each Miss France
    """
    print("Parsing Wikipedia content...")
    soup = BeautifulSoup(html_content, 'html.parser')

    miss_france_list = []

    # Find the main table with Miss France winners
    # Based on inspection, the table has class "wikitable centre"
    tables = soup.find_all('table', class_='wikitable')

    if not tables:
        print("No tables found with wikitable class.")
        return miss_france_list
    # Look for the right table that contains Miss France winners
    miss_france_table = None
    for table in tables:
        headers = [th.get_text().strip().lower() for th in table.find_all('th')]
        # Look for the specific headers found in the Miss France table (Table 3)
        # Headers should include "Année", "Portrait", "Prénom, Nom", "Région représentée"
        if ('année' in headers or any('année' in h for h in headers)) and \
           ('portrait' in headers or any('portrait' in h for h in headers)) and \
           any('prénom' in h or 'nom' in h for h in headers) and \
           any('région' in h for h in headers):
            miss_france_table = table
            break

    if not miss_france_table:
        print("Could not find the table with Miss France winners.")
        return miss_france_list

    # Process the table rows
    for row in miss_france_table.find_all('tr')[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])

        # Skip rows that don't have enough cells
        if len(cells) < 4:  # Need at least année, portrait, prénom/nom, région
            continue

        # Identify the columns based on the table structure
        # In Table 3: Année (0), Portrait (1), Prénom/Nom (2), Région (3)
        year = cells[0].get_text().strip()
        portrait_cell = cells[1]
        name_cell = cells[2]
        region_cell = cells[3]

        # Extract name and clean it
        name = name_cell.get_text().strip()
        name = re.sub(r'\[\d+\]', '', name)  # Remove reference numbers like [1]

        # Extract region and clean it
        region = region_cell.get_text().strip()
        region = re.sub(r'\[\d+\]', '', region)  # Remove reference numbers
        region = re.sub(r'^Miss ', '', region)

        # Look for an image in the portrait cell
        image_url = None
        img_tag = portrait_cell.find('img')
        if img_tag and 'src' in img_tag.attrs:
            img_src = img_tag.get('src')
            # Handle both thumbnail and full-size images
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            image_url = urljoin(WIKIPEDIA_URL, img_src) if not img_src.startswith('http') else img_src

        # Some cells might have a link to a more detailed article
        link = name_cell.find('a')
        article_url = None
        if link and 'href' in link.attrs:
            article_url = urljoin(WIKIPEDIA_URL, link.get('href'))
            # If we didn't find an image in the portrait cell, check if the name has one
            if not image_url:
                name_img = link.find('img')
                if name_img and 'src' in name_img.attrs:
                    img_src = name_img.get('src')
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    image_url = urljoin(WIKIPEDIA_URL, img_src) if not img_src.startswith('http') else img_src
        # Add the extracted information to our list
        miss_france_list.append({
            'year': year,
            'name': name,
            'region': region,
            'image_url': image_url,
            'article_url': article_url
        })

    print(f"Found {len(miss_france_list)} Miss France winners")
    return miss_france_list

def download_image(url: str, save_path: str, headers: dict | None = None) -> bool:
    """
    Download an image from a URL and save it to the specified path.

    Args:
        url: URL of the image
        save_path: Path to save the image
        headers: Optional request headers

    Returns:
        True if download successful, False otherwise
    """
    if headers is None:
        headers = {}

    # Check if file already exists
    if os.path.exists(save_path):
        # Consider small files (typically < 2KB) as placeholder images
        file_size = os.path.getsize(save_path)
        if file_size > 2000:  # Skip only if it's not a placeholder
            print(f"Image already exists at {save_path} ({file_size} bytes)")
            return True

        print(f"Existing image at {save_path} appears to be a placeholder ({file_size} bytes). Redownloading...")

    try:
        print(f"Downloading image from {url}")
        response = requests.get(url, stream=True, timeout=10, headers=headers)
        response.raise_for_status()

        # Check content size before saving
        content_length = int(response.headers.get('Content-Length', 0))
        if content_length < 2000:
            print(f"Warning: Downloaded image is very small ({content_length} bytes). Might be a placeholder.")

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Successfully downloaded to {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error downloading image: {e}")
        return False

def modify_wikimedia_url_for_higher_resolution(url: str, desired_width: int = 400) -> str:
    """
    Modify a Wikimedia thumbnail URL to request a higher resolution.

    Args:
        url: Original Wikimedia URL
        desired_width: Desired width in pixels (default: 400)

    Returns:
        Modified URL with higher resolution if applicable, otherwise original URL
    """
    if not url:
        return url

    # Ensure URL uses https:// when starting with //
    if url.startswith('//'):
        url = 'https:' + url

    # Simple case: if not a thumbnail URL, return as is
    if '/thumb/' not in url:
        return url

    try:
        # For Wikimedia thumbnail URLs, the pattern is typically:
        # https://upload.wikimedia.org/wikipedia/commons/thumb/path/to/file.jpg/XXXpx-file.jpg
        # We need to replace XXX with our desired width but preserve the domain

        # Split the URL into parts before and after the width specification
        parts = url.split('/')

        # Find the part with the pixel width (e.g., "80px-filename.jpg")
        for i, part in enumerate(parts):
            if re.match(r'^\d+px-', part):
                # Replace just the width number, keeping the domain and path intact
                width_match = re.match(r'^(\d+)(px-.+)$', part)
                if width_match:
                    parts[i] = f"{desired_width}{width_match.group(2)}"
                    return '/'.join(parts)

    except Exception as e:
        print(f"Error modifying URL {url}: {e}")

    # If all else fails, try a more robust regex approach that preserves the domain
    try:
        # Find the last occurrence of /XXXpx- in the URL
        match = re.search(r'^(.*)/(\d+)(px-.+)$', url)
        if match:
            domain_and_path = match.group(1)  # Everything before the width
            width = match.group(2)           # The width number
            suffix = match.group(3)          # Everything after the width (px-filename.jpg)

            # Replace just the width number
            return f"{domain_and_path}/{desired_width}{suffix}"
    except Exception as e:
        print(f"Secondary URL modification attempt failed for {url}: {e}")

    return url  # Return original URL if modification failed

def download_miss_france_images(miss_france_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Download images for Miss France winners.

    Args:
        miss_france_data: List of dictionaries with Miss France data

    Returns:
        Updated list with local image paths
    """
    updated_data = []

    # Define placeholder image patterns to skip
    placeholder_patterns = ['Defaut.svg', 'Default.svg', 'Placeholder', 'placeholder']

    # Define headers for Wikimedia requests
    headers = {
        'User-Agent': USER_AGENT
    }

    for i, miss in enumerate(miss_france_data):
        # Skip contestants without image URLs
        if not miss.get('image_url'):
            print(f"No image URL for {miss['name']} ({miss['year']}), skipping")
            updated_data.append(miss)
            continue

        # Get the original image URL
        image_url = miss['image_url']

        # Check if this is a default/placeholder image
        if any(pattern in image_url for pattern in placeholder_patterns):
            print(f"Skipping default/placeholder image for {miss['name']} ({miss['year']}): {image_url}")
            updated_data.append(miss)
            continue

        # Create a filename based on year and name
        filename = f"{miss['year']}_{miss['name'].lower().replace(' ', '_')}.jpg"
        save_path = os.path.join(IMAGES_DIR, filename)

        # Modify the URL to get a higher resolution version
        high_res_url = modify_wikimedia_url_for_higher_resolution(image_url)
        print(f"Original URL: {image_url}")
        print(f"Modified URL: {high_res_url}")

        # Download the image with proper headers
        success = download_image(high_res_url, save_path, headers)
        if success:
            # Add the local image path to the dictionary
            miss['image_path'] = save_path

        # Add a short delay between downloads to be respectful to the server
        if i < len(miss_france_data) - 1:
            time.sleep(0.5)

        updated_data.append(miss)

    return updated_data

def create_anki_deck(miss_france_data: List[Dict[str, str]]) -> genanki.Deck:
    """
    Create an Anki deck with Miss France flashcards.

    Args:
        miss_france_data: List of dictionaries containing Miss France data

    Returns:
        An Anki deck object
    """
    deck = genanki.Deck(
        DECK_ID,
        'Miss France Flashcards',
        description='Flashcards to learn about Miss France winners'
    )

    for miss in miss_france_data:
        # Skip if missing essential data
        if not all(key in miss for key in ['name', 'year', 'region']):
            continue

        # Use a default image path if none is available
        image_path = os.path.basename(miss.get('image_path', ''))

        # Create the Image field HTML if an image path exists
        # Setting it to an empty string will trigger the Mustache conditional to not display any image
        image_html = f'<img src="{image_path}">' if image_path else ''

        # Create a note (a set of flashcards) for this Miss France
        note = MissFranceNote(
            model=miss_france_model,
            fields=[
                miss['name'],
                miss['year'],
                miss['region'],
                image_html,
            ]
        )
        deck.add_note(note)

    return deck

def remove_placeholder_images():
    """
    Remove 1983-byte placeholder images from the images folder.
    These are likely indicators of missing images.
    """
    print("Checking for placeholder images to remove...")
    count = 0
    for filename in os.listdir(IMAGES_DIR):
        file_path = os.path.join(IMAGES_DIR, filename)
        try:
            # Check if file is exactly 1983 bytes (placeholder size)
            if os.path.isfile(file_path) and os.path.getsize(file_path) == 1983:
                print(f"Removing placeholder image: {filename}")
                os.remove(file_path)
                count += 1
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"Removed {count} placeholder images")

def main():
    """Main function to execute the script"""
    # Remove placeholder images before processing
    remove_placeholder_images()

    # Download content from Wikipedia
    try:
        html_content = download_wikipedia_content()
    except Exception as e:
        print(f"Failed to download from Wikipedia: {e}")
        print("Please check your internet connection and try again.")
        return

    # Parse the downloaded HTML content
    miss_france_data = parse_miss_france_html(html_content)

    if not miss_france_data:
        print("No Miss France data found. Exiting.")
        return

    # Download images
    miss_france_data = download_miss_france_images(miss_france_data)

    # Create the Anki deck
    deck = create_anki_deck(miss_france_data)

    # Prepare the list of media files (images) to include in the package
    media_files = []
    for miss in miss_france_data:
        if 'image_path' in miss and os.path.exists(miss['image_path']):
            media_files.append(miss['image_path'])

    # Generate the Anki package
    print(f"Creating Anki package with {len(deck.notes)} notes and {len(media_files)} images...")
    genanki.Package(deck, media_files).write_to_file(OUTPUT_DECK)

    print(f"Successfully created Anki deck: {OUTPUT_DECK}")
    print(f"Deck contains {len(deck.notes)} flashcard notes with 4 card types each")

if __name__ == "__main__":
    main()
