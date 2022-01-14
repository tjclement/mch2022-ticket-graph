import sys
import time
import json
from datetime import datetime

import asyncio
from pandas import *
from asyncio_mqtt import Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def get_updated_counters(tickets):
    new_data = {key: [tickets[key]["sold"]] for key in tickets.keys()}
    new_data["utc_epoch_time"] = time.time()

    # RegularTickets includes Earlybirds, so need to subtract them for an accurate graph
    if "Early-BirdTickets" in new_data and "RegularTickets" in new_data:
        new_data["RegularTickets"][0] -= new_data["Early-BirdTickets"][0]

    filename = "tickets.csv"
    data = read_csv(filename)
    data = data.append(DataFrame(new_data), ignore_index=True)
    data.to_csv(filename, index=False)
    return data


def plot_counters(data):
    timestamps = [datetime.fromtimestamp(stamp) for stamp in data["utc_epoch_time"].to_list()]
    list_data = {key: data[key].to_list() for key in data.keys() if key != "utc_epoch_time"}

    fig, ax = plt.subplots()
    ax.stackplot(timestamps, list_data.values(),
                 labels=list_data.keys(), alpha=0.8)
    ax.legend(loc='upper left')
    ax.set_title('MCH Ticket Sales')
    ax.set_xlabel('Time')
    ax.set_ylabel('Number of tickets sold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))

    plt.gcf().autofmt_xdate()
    plt.savefig("mch2022tickets.png")


async def process_tickets(tickets):
    await asyncio.sleep(2)
    data = get_updated_counters(tickets)
    plot_counters(data)
    print("Successfully added tickets:", tickets)
    sys.exit(0)


async def main(loop):
    tickets = {}
    async with Client(hostname="mqtt.mch2022.org", port=1883) as client:
        async with client.filtered_messages("mch2022/ticketshop/#") as messages:
            await client.subscribe("mch2022/ticketshop/#")
            asyncio.create_task(process_tickets(tickets))
            async for message in messages:
                name_tokens = message.topic.split('/')
                if len(name_tokens) < 3:
                    print(f"Invalid ticket name '{message.topic}', skipping")
                    continue
                name = name_tokens[-1]
                tickets[name] = json.loads(message.payload.decode())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
