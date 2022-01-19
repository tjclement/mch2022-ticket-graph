# Small script to drop duplicate rows

from pandas import read_csv

filename = "tickets.csv"
data = read_csv(filename)

last = None
for idx, row in data.iterrows():
    if last is None:
        last = row
        continue

    differences = [key for key in row.keys() if key != 'utc_epoch_time' and (
        (last[key] != row[key]).any()
    )]
    last = row
    if not differences:
        data = data[data.utc_epoch_time != row.utc_epoch_time]

data.to_csv(filename, index=False)
