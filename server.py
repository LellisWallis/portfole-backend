from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

# Your Finnhub API key
FINNHUB_API_KEY = 'd4i6sm1r01qkv40h6910d4i6sm1r01qkv40h691g'
FINNHUB_BASE_URL = 'https://finnhub.io/api/v1'

POPULAR_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA']

# Cache with 15 second lifetime
cache = {}
CACHE_TTL = 15

def get_from_cache_or_fetch(symbol):
    """Get from cache or fetch fresh"""
    now = time.time()
    
    if symbol in cache:
        data, timestamp = cache[symbol]
        if now - timestamp < CACHE_TTL:
            return data
    
    # Fetch fresh
    data = get_stock_data(symbol)
    if data:
        cache[symbol] = (data, now)
    return data

def get_stock_data(symbol):
    """Get real-time stock data from Finnhub"""
    symbol = symbol.upper()
    
    try:
        # Get quote (current price)
        quote_url = f'{FINNHUB_BASE_URL}/quote'
        quote_params = {'symbol': symbol, 'token': FINNHUB_API_KEY}
        quote_response = requests.get(quote_url, params=quote_params, timeout=5)
        
        if quote_response.status_code != 200:
            return None
            
        quote_data = quote_response.json()
        
        # Get company profile (for name)
        profile_url = f'{FINNHUB_BASE_URL}/stock/profile2'
        profile_params = {'symbol': symbol, 'token': FINNHUB_API_KEY}
        profile_response = requests.get(profile_url, params=profile_params, timeout=5)
        
        profile_data = profile_response.json() if profile_response.status_code == 200 else {}
        
        # Extract data
        current_price = quote_data.get('c', 0)  # Current price
        prev_close = quote_data.get('pc', current_price)  # Previous close
        high = quote_data.get('h', 0)  # High
        low = quote_data.get('l', 0)  # Low
        
        if current_price == 0:
            return None
        
        change = current_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
        
        return {
            'symbol': symbol,
            'name': profile_data.get('name', symbol),
            'price': round(current_price, 2),
            'change': round(change, 2),
            'changePercent': round(change_percent, 2),
            'previousClose': round(prev_close, 2),
            'dayHigh': round(high, 2) if high > 0 else None,
            'dayLow': round(low, 2) if low > 0 else None,
            'volume': None  # Finnhub doesn't provide volume in quote endpoint
        }
        
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


@app.route('/api/quote/<symbol>')
def get_quote(symbol):
    data = get_from_cache_or_fetch(symbol)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/quotes', methods=['POST'])
def get_quotes():
    symbols = request.json.get('symbols', [])
    results = []
    for symbol in symbols[:20]:
        data = get_from_cache_or_fetch(symbol)
        if data:
            results.append(data)
    return jsonify(results)


@app.route('/api/popular')
def get_popular():
    results = []
    for symbol in POPULAR_SYMBOLS:
        data = get_from_cache_or_fetch(symbol)
        if data:
            results.append(data)
    return jsonify(results)


if __name__ == '__main__':
    print('=' * 60)
    print('🚀 PORTFOLE BACKEND SERVER (FINNHUB)')
    print('=' * 60)
    print('📡 Server: http://127.0.0.1:5001')
    print('❤️  Health: http://127.0.0.1:5001/health')
    print('📊 Popular: http://127.0.0.1:5001/api/popular')
    print('=' * 60)
    print('Press CTRL+C to stop')
    print('=' * 60)
    print('')
    
    app.run(host='127.0.0.1', port=5001, debug=False)
