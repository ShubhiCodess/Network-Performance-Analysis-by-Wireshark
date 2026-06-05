import pyshark
import pandas as pd
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# List of PCAP files (Update with actual filenames)
PCAP_FILES = ["lib_1.pcap", "lib_2.pcap", "lib_3.pcap"]

# Function to extract network speed (download & upload)
def extract_network_speed(pcap_file):
    asyncio.set_event_loop(asyncio.new_event_loop())  # Fix for async issues

    capture = pyshark.FileCapture(pcap_file, display_filter="tcp or udp", only_summaries=True)
    data_list = []
    
    for i, packet in enumerate(capture):
        if i >= 100000:  # Limit processing to 100,000 packets for speed
            break
        
        try:
            timestamp = datetime.fromtimestamp(float(packet.sniff_time.timestamp()))
            length = int(packet.length)  # Packet size in Bytes
            src_ip = packet.source
            dst_ip = packet.destination

            data_list.append({"Timestamp": timestamp, "File": pcap_file, 
                              "Source IP": src_ip, "Destination IP": dst_ip, 
                              "Packet Size (KB)": length / 1024})  # Convert Bytes to KB
        except AttributeError:
            continue  # Skip packets without required attributes

    capture.close()
    return pd.DataFrame(data_list)

# Process all files in parallel
def process_pcap_files():
    with ThreadPoolExecutor() as executor:
        results = executor.map(extract_network_speed, PCAP_FILES)

    return pd.concat(results, ignore_index=True)  # Merge all data into a single DataFrame

# Run processing
df = process_pcap_files()

# Aggregate speed (Download & Upload) per second
df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.groupby(["File", pd.Grouper(key="Timestamp", freq="1S")])["Packet Size (KB)"].sum().reset_index()

# Print Network Speed Data
print("\n==== Network Speed (Download & Upload) Per Second ====\n")
for _, row in df.iterrows():
    print(f"File: {row['File']} | Time: {row['Timestamp']} | Speed: {row['Packet Size (KB)']:.2f} KB/s")