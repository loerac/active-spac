import argparse
import enum
import pandas as pd
from bs4 import BeautifulSoup as bs
from urllib.request import Request, urlopen

# URL to scrape data from
BASE_URL = 'https://www.spachero.com/'

# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--symbol', help='SPACs symbol name')
parser.add_argument('-i', '--industry', help='Type of industry: health, ev, tech, consumer, energy, cannabis, sustainability')
parser.add_argument('-tg', '--top-gainers', help='Display the top 5 gainers', action='store_true')
parser.add_argument('-tl', '--top-losers', help='Display the top 5 losers', action='store_true')
parser.add_argument('-vl', '--volume-leaders', help='Display the top volume leaders', action='store_true')
parser.add_argument('-w', '--write-to-file', help='Write the results to a file; json or csv')
args = parser.parse_args()

def IsEmpty(spac, msg):
    """
    Checks to see if the SPAC DataFrame is empty

    :param spac - DataFrame: Dataframe of SPAC(s)
    """
    if spacs.empty:
        print(msg)
        exit()

def GetSPACs(spac_type=None):
    """
    Get the list of SPACs form spacehero.com

    :param spac_type - str: Type of SPAC to look for;
                            * Symbol
                            * Industry

    :return: Pandas DataFrame of SPAC(s)
    """
    # Special Purpose Acquisition Companies lists
    spacs = pd.DataFrame(columns=['Symbol',
                                  'Price',
                                  'Change',
                                  'Volume',
                                  'Target',
                                  'Industry',
                                  'News_Sentiment',
                                  'Market_Cap',
                                  'Optionable',
                                  'Key_Date',
                                  'Date_Desc',
                                  'Expected_Close',
                                 ])

    # Set both the key and the value of the User-Agent header
    # then parse the html
    req = Request(BASE_URL, headers={'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'})
    webpage = urlopen(req).read()
    html = bs(webpage, 'html.parser')

    body = html.find_all('tbody')
    rows = body[0].find_all('tr')
    for row in rows:
        symbol = row.find('div', attrs={'class':'font-size-14'}).text.strip()   # 0
        price = row.find('span').text.strip()                                   # 1
        price_change = row.find('label', attrs={'class':'label'}).text.strip()  # 2
        td = row.find_all('td')

        # Get industry to check if that is the SPAC we're looking for
        industry = td[5].text.strip().lower()
        if spac_type != None and symbol != spac_type and industry != spac_type:
            continue

        # Some rows are labeled as '2.24*1000' or '-'
        # Changing it to be 2,240.0 and 0, respectively
        market_cap = td[7].text.strip().split('*')
        if len(market_cap) != 1:
            market_cap = float(market_cap[0]) * float(market_cap[1])
        else:
            try:
                market_cap = float(market_cap[0])
            except Exception as e:
                market_cap = 'unknown'

        # Add SPAC to lists
        spac = {
            "Symbol": symbol,
            "Price": price,
            "Change": price_change,
            "Volume": td[3].text.strip(),
            "Target": td[4].text.strip(),
            "Industry": industry,
            "News_Sentiment": td[6].text.strip(),
            "Market_Cap": market_cap,
            "Optionable": td[8].text.strip(),
            "Key_Date": td[9].text.strip(),
            "Date_Desc": td[10].text.strip(),
            "Expected_Close": td[11].text.strip()
        }
        spacs = spacs.append(spac, ignore_index=True)

    # Rename the index to be the symbols
    spacs = spacs.set_index('Symbol')

    # Set default '0' value to be 'unknown' for unknown values
    spacs.loc[(spacs.Target == '0'), 'Target'] = 'unknown'
    spacs.loc[(spacs.Key_Date == '0'), 'Key_Date'] = 'unknown'
    spacs.loc[(spacs.Date_Desc == '0'), 'Date_Desc'] = 'unknown'
    spacs.loc[(spacs.Expected_Close == '0'), 'Expected_Close'] = 'unknown'

    return spacs

def TopGainers(limit=5):
    """
    Get the top SPACs with the biggest increase in price

    :param limit - int: How many SPACs to show

    :return: DataFrame with the biggest increase in price
    """
    spacs = GetSPACs()
    spacs.Change = spacs.Change.str.replace(r' %', '')
    spacs.Change = spacs.Change.astype(float)

    top_gainers = spacs.sort_values('Change', ascending=False).head(limit)
    top_gainers.Change = top_gainers.Change.astype(str) + ' %'

    return top_gainers[['Price', 'Change', 'Volume']]

def TopLosers(limit=5):
    """
    Get the top SPACs with the biggest decrease in price

    :param limit - int: How many SPACs to show

    :return: DataFrame with the biggest decrease in price
    """
    spacs = GetSPACs()
    spacs.Change = spacs.Change.str.replace(r' %', '')
    spacs.Change = spacs.Change.astype(float)

    top_losers = spacs.sort_values('Change').head(limit)
    top_losers.Change = top_losers.Change.astype(str) + ' %'

    return top_losers[['Price', 'Change', 'Volume']]

def VolumeLeaders(limit=5):
    """
    Get the top SPACs with the most volume

    :param limit - int: How many SPACs to show

    :return: DataFrame with the most volume
    """
    spacs = GetSPACs()
    spacs.Volume = spacs.Volume.str.replace(r',', '')
    spacs.Volume = spacs.Volume.astype(float)
    volume_leaders = spacs.sort_values('Volume', ascending=False).head(limit)
    volume_leaders.Volume = volume_leaders.apply(lambda x: '{:,}'.format(x.Volume), axis=1)

    return volume_leaders[['Price', 'Change', 'Volume']]

def WriteToFile(ftype, spacs, file_name):
    """
    Write SPAC(s) to a file

    :param ftype - str: File type to write to
    :param spacs - DataFrame: DataFrame of SPAC(s) to write
    :param file_name - str: File name that the DataFrame is being written to
    """
    if ftype == 'json':
        spacs.to_json(path_or_buf=f'{file_name}.json', orient='index', indent=4)
    elif ftype == 'csv':
        spacs.to_csv(f'{file_name}.csv')


if __name__=='__main__':
    file_name = 'spacs'
    if args.top_gainers:
        spacs = TopGainers()
        file_name = 'top_gainers'
    elif args.top_losers:
        spacs = TopLosers()
        file_name = 'top_losers'
    elif args.volume_leaders:
        spacs = VolumeLeaders()
        file_name = 'volume_leaders'
    elif args.symbol != None:
        spacs = GetSPACs(spac_type=args.symbol.upper())
        IsEmpty(spacs, f'No SPAC found for {args.symbol.upper()}')
        spacs = spacs.loc[args.symbol.upper()]
        file_name = args.symbol.upper()
    elif args.industry != None:
        spacs = GetSPACs(spac_type=args.industry.lower())
        IsEmpty(spacs, f'No industry found for {args.industry.lower()}')
        file_name = args.industry.lower()
    else:
        spacs = GetSPACs()
        IsEmpty(spacs, f'No active spacs found')
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', 5)
        pd.set_option('display.width', None)

    print(spacs)
    if args.write_to_file != None:
        WriteToFile(args.write_to_file.lower(), spacs, file_name)
