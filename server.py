from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)

POPULAR_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA']

def get_stock_data(symbol):
    """Get real-time stock data with proper daily change"""
    symbol = symbol.upper()
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Set shorter timeout
        info = ticker.info
        
        # Get price from multiple sources
        price = (
            info.get('regularMarketPrice') or 
            info.get('currentPrice') or 
            info.get('ask') or 
            info.get('bid')
        )
        
        # Fallback to history with timeout
        if price is None:
            try:
                hist = ticker.history(period='2d', timeout=10)
                if len(hist) > 0:
                    price = float(hist['Close'].iloc[-1])
                else:
                    print(f"⚠️ No price data for {symbol}")
                    return None
            except Exception as e:
                print(f"⚠️ History fetch failed for {symbol}: {e}")
                return None
        
        # Get previous close
        prev_close = (
            info.get('previousClose') or 
            info.get('regularMarketPreviousClose')
        )
        
        if prev_close is None:
            prev_close = price
        
        # Calculate change
        price = float(price)
        prev_close = float(prev_close)
        change = price - prev_close
        pct = (change / prev_close) * 100 if prev_close != 0 else 0
        
        return {
            'symbol': symbol,
            'name': info.get('longName') or info.get('shortName') or symbol,
            'price': round(price, 2),
            'change': round(change, 2),
            'changePercent': round(pct, 2),
            'previousClose': round(prev_close, 2),
            'dayHigh': info.get('dayHigh') or info.get('regularMarketDayHigh'),
            'dayLow': info.get('dayLow') or info.get('regularMarketDayLow'),
            'volume': info.get('volume') or info.get('regularMarketVolume')
        }
        
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {str(e)[:100]}")
        return None


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


@app.route('/api/quote/<symbol>')
def get_quote(symbol):
    data = get_stock_data(symbol)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/quotes', methods=['POST'])
def get_quotes():
    symbols = request.json.get('symbols', [])
    results = []
    for symbol in symbols[:20]:
        data = get_stock_data(symbol)
        if data:
            results.append(data)
    return jsonify(results)


@app.route('/api/popular')
def get_popular():
    results = []
    for symbol in POPULAR_SYMBOLS:
        data = get_stock_data(symbol)
        if data:
            results.append(data)
    return jsonify(results)


@app.route('/api/history/<symbol>')
def get_history(symbol):
    """Get historical price data for charts"""
    period = request.args.get('period', '1mo')
    
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)
        
        if len(hist) == 0:
            return jsonify({'error': 'No historical data'}), 404
        
        # Convert to list of data points
        data = []
        for date, row in hist.iterrows():
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume'])
            })
        
        return jsonify({
            'symbol': symbol.upper(),
            'period': period,
            'data': data
        })
        
    except Exception as e:
        print(f"❌ Error fetching history for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('=' * 60)
    print('🚀 PORTFOLE BACKEND SERVER')
    print('=' * 60)
    print('📡 Server: http://127.0.0.1:5001')
    print('❤️  Health: http://127.0.0.1:5001/health')
    print('📊 Popular: http://127.0.0.1:5001/api/popular')
    print('=' * 60)
    print('')
    print('⚠️  NOTE: Stock prices only move when markets are OPEN!')
    print('   US Markets: Mon-Fri, 9:30 AM - 4:00 PM EST')
    print('   (That\'s 3:30 PM - 10:00 PM Swedish time)')
    print('')
    print('   Today is a weekend = markets closed = prices frozen')
    print('   The CHANGE shown is Friday vs Thursday close')
    print('')
    print('=' * 60)
    print('Press CTRL+C to stop')
    print('=' * 60)
    print('')
    
    app.run(host='127.0.0.1', port=5001, debug=False)
