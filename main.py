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
parser.add_argument('-i', '--industry', help='Display all SPACs with a type of industry')
parser.add_argument('-li', '--list-industry', help='List all the types of industries', action='store_true')
parser.add_argument('-o', '--optionable', help='List all SPACs that are optionable', action='store_true')
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

def GetSPACs(spac_type=None, only_optionable=False):
    """
    Get the list of SPACs form spacehero.com

    :param spac_type - str: Type of SPAC to look for;
                            * Symbol
                            * Industry
    :param only_optionable - bool: Flag to only check for optionable SPACs

    :return: Pandas DataFrame of SPAC(s)
    """
    # Special Purpose Acquisition Companies lists
    spacs = pd.DataFrame(columns=['Symbol',
                                  'Price',
                                  'Change',
                                  'Warrant',
                                  'Volume',
                                  'Target',
                                  'Industry',
                                  'Market_Cap',
                                  'Shares_Outstanding',
                                  'Optionable',
                                  'Important_Date',
                                  'Latest_Update',
                                  'Merger_Expectation',
                                  'IPO_Date',
                                 ])

    # Set both the key and the value of the User-Agent header
    # then parse the html
    req = Request(BASE_URL, headers={'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'})
    webpage = urlopen(req).read()
    html = bs(webpage, 'html.parser')

    rows = html.find_all('tr')
    for i in range(8, len(rows)):
        # Get values from table
        td = rows[i].find_all('td')

        symbol = td[0].find('div', attrs={'class':'font-size-16'}).text.strip()
        industry = td[6].text.strip().lower()
        is_optionable = True if td[9].text.strip() == 'Yes' else False

        # Filter out unneeded SPACs
        if spac_type != None and symbol != spac_type and industry != spac_type or \
           only_optionable and not is_optionable:
            continue

        # Add SPAC to lists
        spac = {
            "Symbol": symbol,
            "Price": td[1].text.strip() + ' $',
            "Change": td[2].text.strip(),
            "Warrant": td[3].text.strip()[1:] + ' $',
            "Volume": td[4].text.strip()[1:] + ' $',
            "Target": td[5].text.strip(),
            "Industry": industry,
            "Market_Cap": td[7].text.strip(),
            "Shares_Outstanding": td[8].text.strip(),
            "Optionable": is_optionable,
            "Important_Date": td[10].text.strip(),
            "Latest_Update": td[11].text.strip(),
            "Merger_Expectation": td[12].text.strip(),
            "IPO_Date": td[13].text.strip()
        }
        spacs = spacs.append(spac, ignore_index=True)

        if symbol == spac_type:
            break

    # Rename the index to be the symbols
    spacs = spacs.set_index('Symbol')

    # Set default 'NaN' or 'NaT' values to be 'unknown' for unknown values
    spacs.loc[(spacs.Target == 'NaN'), 'Target'] = 'unknown'
    spacs.loc[(spacs.Market_Cap == 'NaN'), 'Market_Cap'] = 'unknown'
    spacs.loc[(spacs.Shares_Outstanding == 'NaN'), 'Shares_Outstanding'] = 'unknown'
    spacs.loc[(spacs.Important_Date == 'NaT'), 'Important_Date'] = 'unknown'
    spacs.loc[(spacs.Latest_Update == 'NaN'), 'Latest_Update'] = 'unknown'
    spacs.loc[(spacs.Merger_Expectation == 'NaN'), 'Merger_Expectation'] = 'unknown'
    spacs.loc[(spacs.IPO_Date == 'NaN'), 'IPO_Date'] = 'unknown'

    return spacs

def ListIndustries():
    """
    Get the list of industries that SPACs are in
    """
    spacs = GetSPACs()
    industries = spacs.Industry.tolist()
    industries = list(dict.fromkeys(industries))

    print('List of SPAC industries:')
    for industry in industries:
        print(f'  * {industry}')
    exit()

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
    spacs.Volume = spacs.Volume.str.replace(r'$', '')
    spacs.Volume = spacs.Volume.astype(float)
    volume_leaders = spacs.sort_values('Volume', ascending=False).head(limit)
    volume_leaders.Volume = volume_leaders.apply(lambda x: '{:,}'.format(x.Volume), axis=1)
    volume_leaders.Volume = volume_leaders.Volume.astype(str) + ' $'

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
    elif args.list_industry:
        ListIndustries()
    elif args.industry != None:
        spacs = GetSPACs(spac_type=args.industry.lower(), only_optionable=args.optionable)
        IsEmpty(spacs, f'No industry found for {args.industry.lower()}')
        file_name = args.industry.lower()
    else:
        spacs = GetSPACs(only_optionable=args.optionable)
        IsEmpty(spacs, f'No active spacs found')
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', 5)
        pd.set_option('display.width', None)

    print(spacs)
    if args.write_to_file != None:
        WriteToFile(args.write_to_file.lower(), spacs, file_name)
