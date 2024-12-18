from datetime import datetime
import pandas as pd
import time
import tables  # Needed for HDF5 exceptions
from apscheduler.schedulers.background import BackgroundScheduler


# Function to copy raw trades and aggregate them in a separate HDF5 file
def aggregate_trades(source_file, destination_file):
    max_retries = 3
    retries = 0

    while retries < max_retries:
        try:
            # Open the source HDF5 file (alerts.h5) in read-only mode to avoid conflicts
            with pd.HDFStore(source_file, mode='r') as store_read:
                # Load the entire dataset of raw trades from the source
                df = store_read['trades']

            # Ensure the timestamp is in datetime format
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Filter for today's trades only
            today = datetime.utcnow().date()
            df_today = df[df['timestamp'].dt.date == today]

            if df_today.empty:
                print("No trades found for today.")
                return

            # Copy raw data into the destination HDF5 file (copy_alerts.h5)
            with pd.HDFStore(destination_file, mode='a') as store_write:
                store_write.put('trades', df_today, format='table', append=False)  # Overwrite raw trades

                # Group by 'timestamp' and 'symbol' for different contracts and aggregate per 1-minute interval
                df_today.set_index('timestamp', inplace=True)
                trades_resampled = df_today.groupby('symbol').resample('1min').agg({
                    'price': 'mean',  # Average price per minute
                    'size': 'sum'  # Total volume per minute
                }).reset_index()

                # Store the aggregated trades in a separate key in the destination file
                store_write.append('minute1', trades_resampled, format='table', append=True)

            print("Aggregated trades written to copy_alerts.h5 successfully.")
            break

        except tables.exceptions.HDF5ExtError as e:
            print(f"Error in HDF5 writer: {e}")
            retries += 1
            time.sleep(2)  # Wait before retrying
            if retries == max_retries:
                print("Max retries reached for this run. Will try again at the next scheduled time.")


# Scheduler function to run the aggregation task periodically
def schedule_aggregation():
    scheduler = BackgroundScheduler()

    # Schedule the aggregation to run every minute
    scheduler.add_job(aggregate_trades, 'interval', minutes=1, args=['alerts.h5', 'copy_alerts.h5'])

    scheduler.start()

    print("Scheduler started. Aggregating trades every minute.")

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    schedule_aggregation()
