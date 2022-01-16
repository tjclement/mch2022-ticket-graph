import sys
import time
import json
from datetime import datetime

import asyncio

from matplotlib import cycler
from pandas import *
from asyncio_mqtt import Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def get_updated_counters(tickets):
    new_data = {key: [tickets[key]["sold"]] for key in tickets.keys()}
    new_data["utc_epoch_time"] = time.time()

    # Earlybirds were removed from MQTT on Jan 14th, but we do want them in this graph
    new_data["Early-BirdTickets"] = [512]

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
    hidden_list = ["utc_epoch_time", "CamperTicket", "Harbour"]
    list_data = {key: data[key].to_list() for key in data.keys() if not any([hidden in key for hidden in hidden_list])}

    fig, ax = plt.subplots()
    fig.set_facecolor("#491d88")
    ax.set_facecolor("#fec859")
    ax.set_prop_cycle(cycler(color=["#fa448c", "#43b5a0", "#331a38"]))
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.tick_params(axis="x", which="both", colors="white")
    ax.tick_params(axis="y", which="both", colors="white")

    ax.stackplot(timestamps, list_data.values(),
                 labels=list_data.keys(), alpha=0.8)
    ax.axhline(y=1500, color="limegreen", linestyle="--", label="Required tickets w/ donations")
    ax.legend(loc="upper left")
    ax.set_title("MCH Tickets", color="white")
    ax.set_ylabel("Number of tickets sold")
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=[mdates.MO, mdates.FR], tz=mdates.UTC))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=[mdates.MO, mdates.TU, mdates.WE, mdates.TH, mdates.FR, mdates.SA, mdates.SU], tz=mdates.UTC))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %m/%d"))

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
                name_tokens = message.topic.split("/")
                if len(name_tokens) < 3:
                    print(f"Invalid ticket name '{message.topic}', skipping")
                    continue
                name = name_tokens[-1]
                tickets[name] = json.loads(message.payload.decode())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
