import gzip
from pathlib import Path
import xml.etree.ElementTree as ET


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "Sepsis Cases - Event Log.xes.gz"
)

TARGET_CASE_ID = "ES"


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def get_attributes(element):
    attributes = {}

    for child in element:
        key = child.attrib.get("key")

        if key is not None:
            attributes[key] = child.attrib.get("value")

    return attributes


def main():
    with gzip.open(DATA_PATH, "rb") as file:
        root = ET.parse(file).getroot()

    for trace in root:
        if local_name(trace.tag) != "trace":
            continue

        case_attributes = get_attributes(trace)
        case_id = case_attributes.get("concept:name")

        if case_id != TARGET_CASE_ID:
            continue

        events = [
            element
            for element in trace
            if local_name(element.tag) == "event"
        ]

        print(f"Patient case: {case_id}")
        print(f"Total events in case: {len(events)}")
        print("\nEvents around the duplicate")
        print("=" * 50)

        # Display events 8 through 16, if present.
        for position, event in enumerate(events, start=1):
            if not 8 <= position <= 16:
                continue

            attributes = get_attributes(event)

            activity = attributes.get("concept:name")
            timestamp = attributes.get("time:timestamp")
            extras = {
                key: value
                for key, value in attributes.items()
                if key not in {
                    "concept:name",
                    "time:timestamp",
                }
            }

            print(f"\nEvent position: {position}")
            print(f"Activity: {activity}")
            print(f"Timestamp: {timestamp}")
            print(f"Other attributes: {extras}")

        return

    print(f"Case {TARGET_CASE_ID!r} was not found.")


if __name__ == "__main__":
    main()