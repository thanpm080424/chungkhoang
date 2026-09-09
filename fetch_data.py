import urllib.request
import json
import time

SYMBOLS = {
    'FPT': 'FPT.VN', 'HPG': 'HPG.VN', 'VCB': 'VCB.VN', 'VIC': 'VIC.VN', 'VNM': 'VNM.VN',
    'MWG': 'MWG.VN', 'TCB': 'TCB.VN', 'SSI': 'SSI.VN', 'VHM': 'VHM.VN', 'VPB': 'VPB.VN',
    'MSN': 'MSN.VN', 'ACB': 'ACB.VN', 'GAS': 'GAS.VN', 'SAB': 'SAB.VN', 'CTG': 'CTG.VN',
    'BID': 'BID.VN', 'MBB': 'MBB.VN', 'PLX': 'PLX.VN', 'VRE': 'VRE.VN', 'TPB': 'TPB.VN',
    'HDB': 'HDB.VN', 'STB': 'STB.VN', 'POW': 'POW.VN', 'BCM': 'BCM.VN', 'GVR': 'GVR.VN',
    'VJC': 'VJC.VN', 'SHB': 'SHB.VN', 'LPB': 'LPB.VN', 'EIB': 'EIB.VN', 'VIB': 'VIB.VN',
    'SSB': 'SSB.VN', 'MSB': 'MSB.VN', 'OCB': 'OCB.VN', 'VND': 'VND.VN', 'HCM': 'HCM.VN',
    'VCI': 'VCI.VN', 'PDR': 'PDR.VN', 'DIG': 'DIG.VN', 'DXG': 'DXG.VN', 'HSG': 'HSG.VN', 'NKG': 'NKG.VN'
}

def fetch_data():
    tickers = list(SYMBOLS.values())
    batches = [tickers[i:i + 20] for i in range(0, len(tickers), 20)]
    all_results = []
    
    for batch in batches:
        url = f"https://query2.finance.yahoo.com/v7/finance/spark?symbols={','.join(batch)}&range=3mo&interval=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if 'spark' in data and 'result' in data['spark']:
                    all_results.extend(data['spark']['result'])
        except Exception as e:
            print(f"Error fetching batch: {e}")
        time.sleep(1)
        
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False)
        
if __name__ == "__main__":
    fetch_data()
