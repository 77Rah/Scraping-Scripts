from bs4 import BeautifulSoup, element
import requests
import urllib.request
import pandas as pd
import numpy as np

# Number of pages to scrape
total_pages = 63

# Initialize containers for data
records = {
    'Rank': [],
    'Name': [],
    'Platform': [],
    'Year': [],
    'Genre': [],
    'Publisher': [],
    'Developer': [],
    'Critic_Score': [],
    'User_Score': [],
    'NA_Sales': [],
    'PAL_Sales': [],
    'JP_Sales': [],
    'Other_Sales': [],
    'Global_Sales': []
}

base_url = 'http://www.vgchartz.com/gamedb/?page='
query_params = '&console=&region=All&developer=&publisher=&genre=&boxart=Both&ownership=Both'
query_params += '&results=1000&order=Sales&showtotalsales=1&showpublisher=1&shownasales=1'
query_params += '&showdeveloper=1&showcriticscore=1&showpalsales=1&showreleasedate=1'
query_params += '&showuserscore=1&showjapansales=1&showothersales=1&showgenre=1&sort=GL'

# Start page-by-page scraping
for page in range(1, total_pages):
    print(f"Processing Page {page}")
    url = f"{base_url}{page}{query_params}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    # Extract game entry links from HTML
    links = soup.find_all('a', href=True)[10:]
    game_links = [tag for tag in links if tag['href'].startswith('https://www.vgchartz.com/game/')]

    for idx, tag in enumerate(game_links, start=len(records['Name']) + 1):
        try:
            game_name = " ".join(tag.string.split())
            print(f"{idx}: Retrieving data for '{game_name}'")
            records['Name'].append(game_name)

            details = tag.find_parent('tr').find_all("td")

            records['Rank'].append(int(details[0].text.strip()))
            records['Platform'].append(details[3].img['alt'].strip())
            records['Publisher'].append(details[4].text.strip())
            records['Developer'].append(details[5].text.strip())

            # Handle scores and sales with NA checks
            parse_val = lambda x: float(x[:-1]) if x and not x.startswith("N/A") else np.nan
            parse_score = lambda x: float(x) if x and not x.startswith("N/A") else np.nan

            records['Critic_Score'].append(parse_score(details[6].text.strip()))
            records['User_Score'].append(parse_score(details[7].text.strip()))
            records['Global_Sales'].append(parse_val(details[8].text.strip()))
            records['NA_Sales'].append(parse_val(details[9].text.strip()))
            records['PAL_Sales'].append(parse_val(details[10].text.strip()))
            records['JP_Sales'].append(parse_val(details[11].text.strip()))
            records['Other_Sales'].append(parse_val(details[12].text.strip()))

            # Parse year
            year_str = details[13].text.strip().split()[-1]
            if "N/A" in year_str:
                records['Year'].append("N/A")
            else:
                records['Year'].append(int("19" + year_str) if int(year_str) >= 22 else int("20" + year_str))

            # Follow individual game link for Genre info
            genre_url = tag['href']
            genre_page = urllib.request.urlopen(genre_url).read()
            genre_soup = BeautifulSoup(genre_page, "html.parser")
            h2_tags = genre_soup.find("div", id="gameGenInfoBox").find_all('h2')

            genre_text = next((h2.next_sibling.strip() for h2 in h2_tags if h2.text == "Genre"), "Unknown")
            records['Genre'].append(genre_text)

        except Exception as e:
            print(f"Error processing game at index {idx}: {e}")
            continue

    # Save per-page backup
    temp_df = pd.DataFrame(records)
    temp_df.to_csv(f"vgchartz_page_{page}.csv", index=False)

# Final full dataset save
df_final = pd.DataFrame(records)
df_final = df_final[['Rank', 'Name', 'Platform', 'Year', 'Genre', 'Publisher', 'Developer',
                     'Critic_Score', 'User_Score', 'NA_Sales', 'PAL_Sales',
                     'JP_Sales', 'Other_Sales', 'Global_Sales']]
df_final.to_csv("vgchartz_full_data.csv", index=False)
print("Scraping complete. Data saved to 'vgchartz_full_data.csv'")
