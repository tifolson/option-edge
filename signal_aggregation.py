import pandas as pd
from datetime import datetime, timedelta

# Open the HDF5 file and view the stored keys
file_name = 'alerts.h5'

with pd.HDFStore(file_name) as store:
    print(store.keys())  # This will list the stored datasets (keys)

# Load the data for a specific key
df = pd.read_hdf(file_name, key='trades')

df = df.drop_duplicates()

df = df.reset_index(drop=True)

# Optionally, check the full dataframe structure
print(df.info())

# Ensure the timestamp column is a datetime type
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Filter the DataFrame to contain only today's data
today = datetime.today().date()  # Get today's date
df_today = df[df['timestamp'].dt.date == today]

# Print the first few rows to inspect the data
print(df_today.head())
print(df_today.tail())

# Group by 'symbol' and calculate the number of trades and total trade size per symbol
symbol_summary = df_today.groupby('symbol').agg(
    trade_count=('symbol', 'size'),  # Count the number of trades
    total_trade_size=('size', 'sum')  # Sum up the trade sizes
).reset_index()

print(symbol_summary)

# Sort by trade_count in descending order
sorted_df = symbol_summary.sort_values(by='total_trade_size', ascending=False)
print(sorted_df)



'''
OTHER WAYS TO SLICE AND DICE THE DATA:

1. Filter the DataFrame to contain only a previous day's data
previous = (datetime.now() - timedelta(days=1)).date()  # in this instance, yesterday or t-1
print(previous)
df_previous = df[df['timestamp'].dt.date == previous]
print(df_previous.head())
print(df_previous.tail())

2. Filter the DataFrame to contain only tomorrow's data
tomorrow = (datetime.now() + timedelta(days=1)).date() # in this instance, tomorrow or t+1
print(tomorrow)
df_tomorrow = df[df['timestamp'].dt.date == tomorrow]
print(df_tomorrow.head())
print(df_tomorrow.tail())

3. Check trades for a specific contract symbol
In this case, we are checking trades for that contract, regardless of execution date (not limited to today's trades)
df_symbol = df.query("symbol == 'QQQ240916P00470000'")
print(df_symbol)'''



