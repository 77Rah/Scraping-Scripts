from bs4 import BeautifulSoup, element
import requests
import urllib
import urllib.request
import pandas as pd
import numpy as np

# Total number of pages to loop through
total_pages = 63
entry_counter = 0

# Define storage lists for all relevant fields
ranks, names, platforms, release_years, genres = [], [], [], [], []
critics, users = [], []
publishers, developers = [], []
na_sales, pal_sales, jp_sales, other_sales, global_sales = [], [], [], [], []

# Build the dynamic portion of the URL
url_prefix = 'http://www.vgchartz.com/gamedb/?page='
url_params = (
    '&console=&region=All&developer=&publisher=&genre=&boxart=Both&ownership=Both'
    '&results=1000&order=Sales&showtotalsales=1&showpublisher=1'
    '&showvgchartzscore=0&shownasales=1&showdeveloper=1&showcriticscore=1'
    '&showpalsales=1&showreleasedate=1&showuserscore=1&showjapansales=1'
    '&showlastupdate=0&showothersales=1&showgenre=1&sort=GL'
)

# Iterate through all the specified pages
for page in range(1, total_pages):
    current_url = url_prefix + str(page) + url_params
    response = requests.get(current_url)
    soup = BeautifulSoup(response.text, "lxml")
    print(f"Processing Page: {page}")

    # Get all <a> elements with an href attribute
    anchor_tags = soup.find_all('a', href=True)[10:]

    # Retain only game links that begin with the appropriate domain
    game_links = list(filter(lambda x: x['href'].startswith('https://www.vgchartz.com/game/'), anchor_tags))

    for tag in game_links:
        try:
            # Store game title
            names.append(" ".join(tag.string.split()))
            print(f"{entry_counter + 1}. Scraping: {names[-1]}")

            # Navigate up to row and extract all <td> elements
            row = tag.parent.parent.find_all("td")

            # Extract and store each attribute
            ranks.append(np.int32(row[0].string))
            platforms.append(row[3].find('img')['alt'])
            publishers.append(row[4].string)
            developers.append(row[5].string)

            # Handle missing review scores
            critics.append(float(row[6].string) if not row[6].string.startswith("N/A") else np.nan)
            users.append(float(row[7].string) if not row[7].string.startswith("N/A") else np.nan)

            # Regional sales parsing
            global_sales.append(float(row[8].string[:-1]) if not row[8].string.startswith("N/A") else np.nan)
            na_sales.append(float(row[9].string[:-1]) if not row[9].string.startswith("N/A") else np.nan)
            pal_sales.append(float(row[10].string[:-1]) if not row[10].string.startswith("N/A") else np.nan)
            jp_sales.append(float(row[11].string[:-1]) if not row[11].string.startswith("N/A") else np.nan)
            other_sales.append(float(row[12].string[:-1]) if not row[12].string.startswith("N/A") else np.nan)

            # Extract release year from formatted string
            year_fragment = row[13].string.split()[-1]
            if year_fragment.startswith("N/A"):
                release_years.append("N/A")
            else:
                release_years.append(int("19" + year_fragment) if int(year_fragment) >= 22 else int("20" + year_fragment))

            # Access individual game page for genre information
            game_page = urllib.request.urlopen(tag['href']).read()
            game_soup = BeautifulSoup(game_page, "html.parser")

            genre_header = game_soup.find("div", {"id": "gameGenInfoBox"}).find_all('h2')
            genre_value = 'N/A'
            for h2 in genre_header:
                if h2.string == 'Genre':
                    genre_value = h2.find_next_sibling(text=True).strip()
                    break
            genres.append(genre_value)

            entry_counter += 1
        except Exception as e:
            print(f"Skipping entry due to error: {e}")
            continue

    # Compile and export per-page CSV (optional, for debugging)
    data_dict = {
        'Rank': ranks, 'Name': names, 'Platform': platforms, 'Year': release_years, 'Genre': genres,
        'Publisher': publishers, 'Developer': developers,
        'Critic_Score': critics, 'User_Score': users,
        'NA_Sales': na_sales, 'PAL_Sales': pal_sales, 'JP_Sales': jp_sales,
        'Other_Sales': other_sales, 'Global_Sales': global_sales
    }

    df = pd.DataFrame(data_dict)
    print(f"✔ Records collected so far: {entry_counter}")
    print(df.columns)

    # Reorder and save output
    df = df[['Rank', 'Name', 'Platform', 'Year', 'Genre',
             'Publisher', 'Developer', 'Critic_Score', 'User_Score',
             'NA_Sales', 'PAL_Sales', 'JP_Sales', 'Other_Sales', 'Global_Sales']]

    df.to_csv(f"page{page}.csv", index=False, encoding='utf-8')
