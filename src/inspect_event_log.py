from collections import Counter
import gzip
from pathlib import Path
import xml.etree.ElementTree as ET


# Find the original dataset relative to the project folder.
DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "Sepsis Cases - Event Log.xes.gz"
)


def local_name(tag: str) -> str:
    """Return an XML tag name without its namespace."""
    return tag.rsplit("}", 1)[-1]


def main() -> None:
    """Inspect the structure of the compressed XES event log."""

    # Check whether the dataset exists.
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_PATH}"
        )

    # Open the compressed file and parse its XML content.
    with gzip.open(DATA_PATH, "rb") as file:
        root = ET.parse(file).getroot()

    # Each trace represents a patient case.
    traces = [
        element
        for element in root
        if local_name(element.tag) == "trace"
    ]

    total_events = 0
    activity_counts = Counter()
    attribute_counts = Counter()

    missing_activity = 0
    missing_timestamp = 0

    # Examine every event belonging to each patient case.
    for trace in traces:
        for event in trace:
            if local_name(event.tag) != "event":
                continue

            total_events += 1
            attributes = {}

            # Collect attributes recorded for this event.
            for element in event.iter():
                key = element.attrib.get("key")

                if key is not None:
                    value = element.attrib.get("value")
                    attributes[key] = value
                    attribute_counts[key] += 1

            # Count the clinical activity.
            activity = attributes.get("concept:name")

            if activity:
                activity_counts[activity] += 1
            else:
                missing_activity += 1

            # Check whether the event has a timestamp.
            timestamp = attributes.get("time:timestamp")

            if not timestamp:
                missing_timestamp += 1

    # Display the inspection results.
    print("\nCAREFLOW - DATASET INSPECTION")
    print("=" * 40)
    print(f"Dataset file: {DATA_PATH.name}")
    print(f"Patient cases: {len(traces):,}")
    print(f"Total events: {total_events:,}")
    print(f"Distinct activities: {len(activity_counts):,}")
    print(f"Events missing activity: {missing_activity:,}")
    print(f"Events missing timestamp: {missing_timestamp:,}")

    print("\nMost Frequent Activities")
    print("-" * 40)

    for activity, count in activity_counts.most_common(10):
        print(f"{activity}: {count:,}")

    print("\nEvent Attribute Keys")
    print("-" * 40)

    for attribute, count in sorted(attribute_counts.items()):
        print(f"{attribute}: present in {count:,} XML elements")


if __name__ == "__main__":
    main()