#!/usr/bin/env python3
"""
Parser for Step Counter Data

This tool parses binary data from the watch for further processing.
It supports both raw binary and base64 encoded binary files.
See stepcounter_logging_face.c in second movement.
"""

import argparse
import base64
import csv
import re
import struct
from datetime import datetime
from pathlib import Path


def is_base64(file_path):
    """Check if file contains b64 encoded data"""
    try:
        with open(file_path, "r") as f:
            first_lines = [f.readline().strip() for _ in range(10)]

        # Check if lines contain only base64 characters
        base64_pattern = re.compile(r"^[A-Za-z0-9+/]*={0,2}$")

        for line in first_lines:
            if line and not base64_pattern.match(line):
                return False

        return True
    except Exception:
        return False


def decode_base64(file_path):
    """Decode a base64 encoded file to binary data"""
    try:
        with open(file_path, "r") as f:
            b64_data = f.read().strip()

        # Remove any whitespace and newlines
        b64_data = "".join(b64_data.split())

        # Decode base64
        binary_data = base64.b64decode(b64_data)
        return binary_data

    except Exception as e:
        raise ValueError(f"Failed to decode base64 file {file_path}: {e}")


def parse_header(data: bytes, offset=0):
    """Parse the header section"""
    # Validate magic bytes
    magic = struct.unpack("<H", data[offset : offset + 2])[0]
    if magic != 0x4223:
        raise ValueError("Invalid magic bytes")
    offset += 2

    # Parse all header fields
    header = {
        "version": struct.unpack("B", data[offset : offset + 1])[0],
        "device_state": {
            "mode": struct.unpack("B", data[offset + 1 : offset + 2])[0],
            "data_rate": struct.unpack("B", data[offset + 2 : offset + 3])[0],
            "low_power": struct.unpack("B", data[offset + 3 : offset + 4])[0],
            "bwf_mode": struct.unpack("B", data[offset + 4 : offset + 5])[0],
            "range": struct.unpack("B", data[offset + 5 : offset + 6])[0],
            "filter": struct.unpack("B", data[offset + 6 : offset + 7])[0],
            "low_noise": struct.unpack("B", data[offset + 7 : offset + 8])[0],
        },
        "data_type": struct.unpack("B", data[offset + 8 : offset + 9])[0],
        "index": struct.unpack("B", data[offset + 9 : offset + 10])[0],
        "start_ts": struct.unpack("<I", data[offset + 10 : offset + 14])[0],
    }

    return header, offset + 14


def print_header(header):
    """Print a human readable version of the header"""
    # Mapping dictionaries
    mode_map = {0b00: "Low power", 0b01: "High performance", 0b10: "On demand"}
    rate_map = {
        0: "Power down",
        0b0001: "Low",
        0b0010: "12.5 Hz",
        0b0011: "25 Hz",
        0b0100: "50 Hz",
    }
    lp_map = {
        0b00: "Mode 1 (12-bit)",
        0b01: "Mode 2 (14-bit)",
        0b10: "Mode 3 (14-bit)",
        0b11: "Mode 4 (14-bit)",
    }
    bwf_map = {0b00: "Div2", 0b01: "Div4", 0b10: "Div10", 0b11: "Div20"}
    range_map = {0b11: "±16g", 0b10: "±8g", 0b01: "±4g", 0b00: "±2g"}
    filter_map = {0: "Low pass", 1: "High pass"}
    low_noise_map = {0: "Disabled", 1: "Enabled"}

    # Print header info
    print("Header:")
    print(f"  Version: {header['version']}")
    print("  Device State:")

    state = header["device_state"]
    print(f"    Mode: {mode_map.get(state['mode'], 'Unknown')}")
    print(f"    Data Rate: {rate_map.get(state['data_rate'], 'Unknown')}")
    print(f"    Low Power Mode: {lp_map.get(state['low_power'], 'Unknown')}")
    print(f"    Bandwidth Filter: {bwf_map.get(state['bwf_mode'], 'Unknown')}")
    print(f"    Range: {range_map.get(state['range'], 'Unknown')}")
    print(f"    Filter: {filter_map.get(state['filter'], 'Unknown')}")
    print(f"    Low Noise: {low_noise_map.get(state['low_noise'], 'Unknown')}")

    # Print data type flags
    data_types = []
    if header["data_type"] & 0x01:
        data_types.append("XYZ coordinates")
    if header["data_type"] & 0x02:
        data_types.append("Magnitude")
    if header["data_type"] & 0x04:
        data_types.append("L1 norm")

    print(f"  Data Type: {', '.join(data_types) if data_types else 'Unknown'}")
    print(f"  Index: {header['index']}")
    ts = header["start_ts"]
    print(
        f"  Start Timestamp: {ts} "
        f"({datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')})"
    )


def get_rate(header):
    """Get the rate from the header"""

    # 1.6 Hz is only available in low power mode
    if header["device_state"]["data_rate"] == 0b0001:
        if header["device_state"]["low_power"] == 0b00:
            return 1.6
        else:
            return 12.5
    else:
        # All other rates are available in all modes
        return {
            0b0010: 12.5,
            0b0011: 25,
            0b0100: 50,
        }[header["device_state"]["data_rate"]]


def parse_chunk(data, offset, header, index):
    """Parse a single chunk of data"""
    chunk = []

    # Read number of measurements in this chunk
    count = struct.unpack("B", data[offset : offset + 1])[0]
    offset += 1

    # Get rate and start timestamp
    rate = get_rate(header)
    ts = header["start_ts"] + index

    for i in range(count):
        # Parse XYZ coordinates if present
        if header["data_type"] & 0x01:
            reading = struct.unpack("<hhh", data[offset : offset + 6])
            offset += 6

        # Parse magnitude if present (L1 or L2 norm)
        if header["data_type"] & 0x02:
            # Magnitude is stored as 24-bit little endian
            mag_bytes = data[offset : offset + 3]
            reading = [mag_bytes[0] | (mag_bytes[1] << 8) | (mag_bytes[2] << 16)]
            offset += 3

        chunk.append((ts + i / rate, *reading))

    return chunk, offset


def check_marker(data, offset):
    """Check if the data contains a marker"""
    marker = struct.unpack("B", data[offset : offset + 1])[0]
    if marker == 0xFF:
        return True, offset + 1
    else:
        return False, offset


def parse_steps(data, offset):
    """Parse the steps data"""
    steps = struct.unpack("<H", data[offset : offset + 2])[0]
    return steps, offset + 2


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Parse binary step counter data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", type=Path, help="Input binary file")
    parser.add_argument(
        "-c", "--csv-export", help="Export to CSV file", type=Path, default=None
    )

    return parser.parse_args()


def parse_readings(data, offset, header):
    # Parse all data chunks until marker
    readings, index = [], 0
    while offset < len(data):
        marker, offset = check_marker(data, offset)
        if marker:
            break
        chunk, offset = parse_chunk(data, offset, header, index)
        readings.extend(chunk)
        index += 1

    # Parse final step count
    steps, _ = parse_steps(data, offset)
    return readings, steps


def print_readings(readings, steps):
    """Print the readings in a human readable format"""
    # Calculate statistics
    timestamps = [r[0] for r in readings]
    duration = max(timestamps) - min(timestamps)

    print("Readings:")
    print(f"  Time range: {duration:.2f}s")
    print(f"  Samples: {len(readings)}")

    if len(readings[0]) == 2:
        x = [r[1] for r in readings]
        print(f"  Magnitudes: {min(x)}/{sum(x)/len(x):.0f}/{max(x)} (min/avg/max)")
    else:
        # Ignore xyz data
        pass

    print(f"  Steps: {steps}")


def export_readings(header, readings, steps, args):
    """Export the readings to a CSV file"""
    with open(args.csv_export, "w", newline="") as f:
        writer = csv.writer(f)

        # Set headers based on data type
        if header["data_type"] & 0x01:
            headers = ["Timestamp", "X", "Y", "Z", "Steps"]
        else:
            headers = ["Timestamp", "Magnitude", "Steps"]
        writer.writerow(headers)

        # Write first row with total steps, remaining rows with 0 steps
        writer.writerow(list(readings[0]) + [steps])
        writer.writerows(list(reading) + [0] for reading in readings[1:])


def main():
    """Parse step counter data from input file"""
    args = parse_args()

    if not args.input.exists():
        print(f"Error: Input file does not exist: {args.input}")
        return

    if is_base64(args.input):
        data = decode_base64(args.input)
    else:
        data = args.input.read_bytes()

    # Parse header and print info
    header, offset = parse_header(data)
    print_header(header)

    # Parse readings and step count
    readings, steps = parse_readings(data, offset, header)
    print_readings(readings, steps)

    if args.csv_export:
        export_readings(header, readings, steps, args)


if __name__ == "__main__":
    main()
