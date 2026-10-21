import gzip
from pathlib import Path
import xml.etree.ElementTree as ET


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "Sepsis Cases - Event Log.xes.gz"
)


def local_name(tag: str) -> str:
    """Return an XML tag without its namespace."""
    return tag.rsplit("}", 1)[-1]


def get_attributes(element):
    """Read the direct attributes of an XES element."""
    result = {}

    for child in element:
        key = child.attrib.get("key")

        if key is not None:
            result[key] = child.attrib.get("value")

    return result


def main():
    """Find and describe exact duplicate events."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    with gzip.open(DATA_PATH, "rb") as file:
        root = ET.parse(file).getroot()

    total_duplicates = 0

    for trace in root:
        if local_name(trace.tag) != "trace":
            continue

        trace_attributes = get_attributes(trace)
        case_id = trace_attributes.get(
            "concept:name", "<missing case ID>"
        )

        events = [
            item
            for item in trace
            if local_name(item.tag) == "event"
        ]

        # Remember the first position of each event signature.
        seen = {}

        for position, event in enumerate(events, start=1):
            attributes = get_attributes(event)
            signature = tuple(sorted(attributes.items()))

            if signature in seen:
                total_duplicates += 1

                print("\nExact duplicate found")
                print("-" * 35)
                print(f"Case ID: {case_id}")
                print(f"First event position: {seen[signature]}")
                print(f"Repeated event position: {position}")
                print(
                    "Activity:",
                    attributes.get("concept:name")
                )
                print(
                    "Timestamp:",
                    attributes.get("time:timestamp")
                )

                print("\nMatching event attributes:")
                for key, value in sorted(attributes.items()):
                    print(f"  {key}: {value}")

            else:
                seen[signature] = position

    print("\n" + "=" * 35)
    print(f"Total exact duplicate events: {total_duplicates}")


if __name__ == "__main__":
    main()