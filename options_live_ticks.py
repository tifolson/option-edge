from tick_trade_aggregation import aggregate_trades
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestBarRequest, OptionChainRequest
from alpaca.data.live.option import OptionDataStream
from alpaca.data.enums import OptionsFeed
from alpaca.data.models import Trade, Quote
from config_alpaca import *
import asyncio
import datetime
from datetime import datetime, timedelta
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.common.exceptions import APIError

import time
import winsound

# Your API keys (replace with your actual keys or create a config file and import the file contents as noted above: from config import *)
api_key = API_KEY
api_secret = API_SECRET
base_url = 'https://paper-api.alpaca.markets'  # This is for paper trading, replace with live URL for live trading
option_stream_data_wss = None

# Initialize Alpaca clients
stock_client = StockHistoricalDataClient(api_key, api_secret)
options_client = OptionHistoricalDataClient(api_key, api_secret)
option_stream = OptionDataStream(api_key, api_secret, feed=OptionsFeed.OPRA) # OPRA feed requires a paid Alpaca subscription. Delayed trades are available with a free subscription. Note the delay is 15 minutes.
trade_api = TradingClient(api_key, api_secret)

# Global variable to store latest quotes for options
latest_quotes = {}

# Predefine the columns and their data types
columns = ['symbol', 'price', 'size', 'ask_price', 'timestamp']
trades_df = pd.DataFrame(columns=columns)
trade_batch = []

last_write_time = time.time()
write_interval = 8  # seconds


# Step 1: Get the underlying price of QQQ
def get_underlying_price(symbol='QQQ'):
    request = StockLatestBarRequest(symbol_or_symbols=[symbol])
    response = stock_client.get_stock_latest_bar(request)

    # Debugging: Print the API response for the underlying stock price
    print(f"Underlying Price API Response: {response}")

    if response and symbol in response:
        bar = response[symbol]
        print(f"Retrieved Close Price: {bar.close}")
        return bar.close  # Use the 'close' price
    else:
        print("Error: Could not retrieve underlying price.")
    return None


# Step 2: Load the options chain for QQQ 0DTE and 1DTE
def load_options_chain(underlying_symbol='QQQ'):
    # Get today's date in the format YYYY-MM-DD
    today = datetime.now().strftime('%y%m%d')
    # Get tomorrow's date in the format YYYY-MM-DD
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%y%m%d')

    option_chain_request = OptionChainRequest(underlying_symbol=underlying_symbol)
    option_chain = options_client.get_option_chain(option_chain_request)

    # Debugging: Print the API response for the options chain
    print(f"Options Chain API Response: {option_chain}")

    # Filter the option chain for today's expiration
    filtered_chain = {
        symbol: details for symbol, details in option_chain.items()
        if extract_expiry_from_symbol(symbol) in [today, tomorrow]  # == today
    }

    # Debugging: Print how many options are expiring today
    print(f"Loaded {len(filtered_chain)} option contracts expiring today and tomorrow.")

    if filtered_chain:
        return filtered_chain
    else:
        print("Error: No option contracts loaded for today or tomorrow's expiration.")
        return None

# Helper function to extract the expiry date from the option symbol
def extract_expiry_from_symbol(symbol):
    # Assuming the format is 'QQQYYMMDDXXXX' where YYMMDD is the expiration
    return symbol[3:9]

# Step 3: Filter options within $20 of the underlying price
def filter_options_within_range(option_chain, underlying_price, price_offset=20):
    filtered_symbols = []
    for symbol, details in option_chain.items():
        # Extract the strike price from the option symbol (last 8 characters)
        strike_price = extract_strike_price(symbol) #float(symbol[10:15])  # Assuming a fixed symbol format

        # Debugging: Print each option symbol and its strike price
        print(f"Option Symbol: {symbol}, Strike Price: {strike_price:.2f}")

        # Filter based on proximity to the underlying price
        if abs(underlying_price - strike_price) <= price_offset:
            filtered_symbols.append(symbol)
            print(f"Symbol {symbol} within range of ${price_offset}.")

    print(f"Filtered {len(filtered_symbols)} option symbols within ${price_offset} of underlying price.")
    return filtered_symbols


def extract_strike_price(symbol):
    # Extract the substring representing the strike price (assume it's always 8 characters long)
    strike_price_str = symbol[10:18]  # Adjust the slice according to the symbol format

    # Convert the substring to an integer
    strike_price_int = int(strike_price_str)

    # Convert to float and divide by 100 to get the correct price with two decimal places
    strike_price = strike_price_int / 1000

    return strike_price
    

# Async handler for option quotes
async def handle_option_quotes(msg):
    '''if 0.03 <= msg.ask_price <= 0.30:  # Ask price threshold
        print(f"Option Quote Passed Filter: {msg}")'''
    if 0.03 <= msg.ask_price <= 0.30:
        # Update the latest quote
        latest_quotes[msg.symbol] = msg
        #print(f"Updated Option Quote: {msg}")
        #winsound.Beep(1000, 200)

# Async handler for option trades
async def handle_option_trades(msg):
    ''' example: if msg.size >= 30:  # Minimum trade volume threshold
        print(f"Option Trade Passed Filter: {msg}")'''
    # Check if the trade meets the volume and price criteria
    if 0.03 <= msg.price <= 0.14 and msg.size > 50:
        # Ensure the trade price is greater than or equal to the latest quote's ask price
        quote = latest_quotes.get(msg.symbol)
        if quote and msg.price >= quote.ask_price:
            # Store the trade in the DataFrame
            global trades_df
            global last_write_time

            trade_data = {
                'symbol': msg.symbol,
                'price': msg.price,
                'size': msg.size,
                'ask_price': latest_quotes.get(msg.symbol).ask_price,  #quote.ask_price,
                'timestamp': msg.timestamp
            }


            # Convert trade_data to DataFrame and ensure correct types
            trade_row = pd.DataFrame([trade_data], columns=trades_df.columns)
            # Concatenate to the existing trades_df
            trades_df = pd.concat([trades_df, trade_row], ignore_index=True)
            # trades_df = pd.concat([trades_df, pd.DataFrame([trade_data])], ignore_index=True)
            print(f"Option Trade Passed Filter: {msg}")

            # Play a beep sound when a new trade is printed
            winsound.Beep(1000, 200)

            # Get current time
            current_time = time.time()

            if current_time - last_write_time >= write_interval:  #len(trade_batch) >= 10 or (time.time() - last_write_time > 5):  Write if batch is large or 5s passed
                # Write batch to HDF5 file
                print(f"It's been {write_interval} seconds")

                file_name = 'alerts.h5'
                try:
                    print("Writing batch to HDF5 file")
                    trades_df.to_hdf(file_name, key='trades', mode='a', format='table', append=True)
                    trades_df = pd.DataFrame(columns=columns)  # Reset the DataFrame after writing
                    last_write_time = current_time

                    # Optional: Verify that data was saved correctly
                    with pd.HDFStore(file_name) as store:
                        print(store['trades'].tail())
                except Exception as e:
                    print(f"Error writing to HDF5: {e}")


# Step 4: Start the WebSocket stream
async def start_option_stream(option_symbols):
    # Subscribe to option data
    option_stream.subscribe_quotes(handle_option_quotes, *option_symbols)
    option_stream.subscribe_trades(handle_option_trades, *option_symbols)

    # Debugging: Print subscribed symbols
    print(f"Subscribed to option symbols: {option_symbols}")

    # Run the option stream
    await option_stream._run_forever()

# Step 5. Add audio when new trade occurs
def on_new_row_printed(row):
    print(row)
    # Play a simple beep sound (frequency: 1000 Hz, duration: 200 ms)
    winsound.Beep(1000, 200)

# Main script execution
def main():
    # Step 1: Get the underlying price once
    underlying_price = get_underlying_price('QQQ')
    if not underlying_price:
        print("Error: Unable to retrieve underlying price. Exiting.")
        return

    # Step 2: Load the options chain
    option_chain = load_options_chain()
    if not option_chain:
        print("Error: Unable to load options chain. Exiting.")
        return

    # Step 3: Filter options within $20 of the underlying price
    option_symbols = filter_options_within_range(option_chain, underlying_price, price_offset=20)
    if not option_symbols:
        print("Error: No option symbols found within range. Exiting.")
        return

    # Step 4: Start the event loop for option stream
    try:
        asyncio.run(start_option_stream(option_symbols))
    except Exception as e:
        print(f"Error running option stream: {e}")


if __name__ == "__main__":
    main()





