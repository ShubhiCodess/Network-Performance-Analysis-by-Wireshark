import pyshark
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

CAPTURE_FOLDER = "captures"
OUTPUT_FOLDER = "output"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

files = glob.glob(f"{CAPTURE_FOLDER}/*.pcap*")

all_results = []

for file in files:

    print(f"\nProcessing {file}")

    capture = pyshark.FileCapture(
        file,
        keep_packets=False
    )

    rows = []

    for packet in capture:

        try:
            timestamp = float(packet.sniff_timestamp)
            size = int(packet.length)

            src = ""
            dst = ""

            if hasattr(packet, "ip"):
                src = packet.ip.src
                dst = packet.ip.dst

            rows.append([
                timestamp,
                size,
                src,
                dst
            ])

        except:
            continue

    capture.close()

    if len(rows) == 0:
        continue

    df = pd.DataFrame(
        rows,
        columns=[
            "time",
            "bytes",
            "src",
            "dst"
        ]
    )

    start = df.time.min()

    df["second"] = (
        df.time - start
    ).astype(int)

    # upload = outgoing
    upload = (
        df[
            df["src"].str.startswith(
                ("192.","10.","172."),
                na=False
            )
        ]
        .groupby("second")
        ["bytes"]
        .sum()
        /1024
    )

    # download = incoming
    download = (
        df[
            df["dst"].str.startswith(
                ("192.","10.","172."),
                na=False
            )
        ]
        .groupby("second")
        ["bytes"]
        .sum()
        /1024
    )

    total = (
        df.groupby("second")
        ["bytes"]
        .sum()
        /1024
    )

    summary = {

        "file":
        os.path.basename(file),

        "avg_total_kbps":
        round(total.mean(),2),

        "peak_total_kbps":
        round(total.max(),2),

        "avg_download_kbps":
        round(download.mean(),2),

        "avg_upload_kbps":
        round(upload.mean(),2),

        "total_data_mb":
        round(
            df.bytes.sum()/1024/1024,
            2
        ),

        "packets":
        len(df)
    }

    all_results.append(summary)

    plt.figure(figsize=(12,6))

    plt.plot(
        total.index,
        total.values,
        label="Total"
    )

    plt.plot(
        upload.index,
        upload.values,
        label="Upload"
    )

    plt.plot(
        download.index,
        download.values,
        label="Download"
    )

    plt.xlabel("Time (s)")
    plt.ylabel("KB/s")

    plt.title(
        os.path.basename(file)
    )

    plt.grid()

    plt.legend()

    plt.savefig(
        f"{OUTPUT_FOLDER}/"
        f"{os.path.basename(file)}.png"
    )

    plt.close()

summary_df = pd.DataFrame(
    all_results
)

summary_df.to_csv(
    f"{OUTPUT_FOLDER}/summary.csv",
    index=False
)

print("\n===== RESULTS =====")

print(summary_df)
