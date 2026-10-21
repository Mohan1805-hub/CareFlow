from collections import Counter
from datetime import datetime, timezone
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
    """Return an XML tag name without its namespace."""
    return tag.rsplit("}", 1)[-1]


def get_attributes(element):
    """Read the direct attributes of an XES element."""
    result = {}

    for child in element:
        key = child.attrib.get("key")

        if key is not None:
            result[key] = child.attrib.get("value")

    return result


def parse_timestamp(value):
    """Parse an ISO timestamp and normalize it to UTC."""
    if not value:
        return None

    try:
        timestamp = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )
        else:
            timestamp = timestamp.astimezone(
                timezone.utc
            )

        return timestamp

    except ValueError:
        return None


def is_blank(value) -> bool:
    """Check whether an attribute value is empty."""
    return value is None or not str(value).strip()


def main() -> None:
    """Run basic data-quality checks on the XES dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    with gzip.open(DATA_PATH, "rb") as file:
        root = ET.parse(file).getroot()

    traces = [
        item
        for item in root
        if local_name(item.tag) == "trace"
    ]

    case_ids_seen = set()
    activity_counts = Counter()
    event_attribute_counts = Counter()
    trace_attribute_counts = Counter()

    total_events = 0
    missing_case_ids = 0
    duplicate_case_ids = 0
    empty_cases = 0
    missing_activities = 0
    missing_timestamps = 0
    invalid_timestamps = 0
    out_of_order_events = 0
    exact_duplicate_events = 0
    blank_event_values = 0
    blank_trace_values = 0

    for trace in traces:
        trace_attributes = get_attributes(trace)
        case_id = trace_attributes.get("concept:name")

        for key, value in trace_attributes.items():
            trace_attribute_counts[key] += 1

            if is_blank(value):
                blank_trace_values += 1

        if is_blank(case_id):
            missing_case_ids += 1
        elif case_id in case_ids_seen:
            duplicate_case_ids += 1
        else:
            case_ids_seen.add(case_id)

        events = [
            item
            for item in trace
            if local_name(item.tag) == "event"
        ]

        if not events:
            empty_cases += 1

        previous_timestamp = None
        signatures_seen = set()

        for event in events:
            total_events += 1
            attributes = get_attributes(event)

            for key, value in attributes.items():
                event_attribute_counts[key] += 1

                if is_blank(value):
                    blank_event_values += 1

            activity = attributes.get("concept:name")

            if is_blank(activity):
                missing_activities += 1
            else:
                activity_counts[activity] += 1

            timestamp_value = attributes.get(
                "time:timestamp"
            )

            if is_blank(timestamp_value):
                missing_timestamps += 1
                timestamp = None
            else:
                timestamp = parse_timestamp(
                    timestamp_value
                )

                if timestamp is None:
                    invalid_timestamps += 1

            if timestamp is not None:
                if (
                    previous_timestamp is not None
                    and timestamp < previous_timestamp
                ):
                    out_of_order_events += 1

                previous_timestamp = timestamp

            # Check for exact duplicates within this case.
            signature = tuple(sorted(attributes.items()))

            if signature in signatures_seen:
                exact_duplicate_events += 1

            signatures_seen.add(signature)

    print("\nCAREFLOW - DATA QUALITY AUDIT")
    print("=" * 45)
    print(f"Patient cases: {len(traces):,}")
    print(f"Total events: {total_events:,}")
    print(f"Distinct activities: {len(activity_counts):,}")

    print("\nData Quality Checks")
    print("-" * 45)
    print(f"Cases missing case ID: {missing_case_ids}")
    print(f"Repeated case IDs: {duplicate_case_ids}")
    print(f"Cases without events: {empty_cases}")
    print(f"Events missing activity: {missing_activities}")
    print(f"Events missing timestamp: {missing_timestamps}")
    print(f"Invalid timestamps: {invalid_timestamps}")
    print(f"Out-of-order event transitions: {out_of_order_events}")
    print(f"Exact duplicate events: {exact_duplicate_events}")
    print(f"Blank event attribute values: {blank_event_values}")
    print(f"Blank case attribute values: {blank_trace_values}")

    print("\nLeast Frequently Present Event Attributes")
    print("-" * 45)

    for key, count in sorted(
        event_attribute_counts.items(),
        key=lambda item: item[1]
    )[:10]:
        absent = total_events - count
        print(
            f"{key}: present {count:,}, "
            f"absent {absent:,}"
        )

    print("\nLeast Frequently Present Case Attributes")
    print("-" * 45)

    for key, count in sorted(
        trace_attribute_counts.items(),
        key=lambda item: item[1]
    )[:10]:
        absent = len(traces) - count
        print(
            f"{key}: present {count:,}, "
            f"absent {absent:,}"
        )

    print("\nAudit completed. Original data was not modified.")


if __name__ == "__main__":
    main()