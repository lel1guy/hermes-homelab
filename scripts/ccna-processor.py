#!/usr/bin/env python3
"""Fetch a YouTube transcript and write a detailed CCNA concept note to the vault."""
import sys, os, json, re, textwrap
sys.path.insert(0, '/home/vitor/.hermes/skills/media/youtube-content/scripts')
from fetch_transcript import fetch_transcript

VAULT = "/home/vitor/vault/Knowledge/CCNA"

VIDEOS = [
    # (video_id, title, filename, day_label)
    ("S7MNX_UD7vY", "FREE CCNA // What is a Network? // Day 0", "01-what-is-a-network", "Day 0"),
    ("9eH16Fxeb9o", "What is a SWITCH? // FREE CCNA // Day 1", "02-what-is-a-switch", "Day 1"),
    ("p9ScLm9S3B4", "What is a ROUTER? // FREE CCNA // EP 2", "03-what-is-a-router", "EP 2"),
    ("CRdL1PcherM", "what is TCP/IP and OSI? // FREE CCNA // EP 3", "04-tcpip-and-osi", "EP 3"),
    ("3kfO61Mensg", "REAL LIFE example!! (TCP/IP and OSI layers) // FREE CCNA // EP 4", "05-osi-real-life-example", "EP 4"),
    ("oIRkXulqJA4", "how the OSI model works on YouTube (Application and Transport Layers) // FREE CCNA // EP 5", "06-osi-application-transport", "EP 5"),
    ("wwwAXlE4OtU", "DO NOT design your network like this!! // FREE CCNA // EP 6", "07-network-design", "EP 6"),
    ("6-66D9J5PkY", "Data Center NETWORKS (what do they look like??) // FREE CCNA // EP 7", "08-data-center-networks", "EP 7"),
    ("xPi4uZu4uF0", "WAN....it's not the internet!! (sometimes) // FREE CCNA // EP 8", "09-wan", "EP 8"),
    ("80vIin4xGp8", "let's hack your home network // FREE CCNA // EP 9", "10-hack-home-network", "EP 9"),
    ("37tyxaQbtN4", "you need to learn Hybrid-Cloud RIGHT NOW!! // FREE CCNA // EP 10", "11-hybrid-cloud", "EP 10"),
    ("y8h5qY3zwic", "forcing my kids to make Ethernet cables // FREE CCNA // EP 11", "12-ethernet-cables", "EP 11"),
    ("MLxgmkRzgIQ", "why Power over Ethernet (PoE) is amazing!! // FREE CCNA // EP 12", "13-poe-power-over-ethernet", "EP 12"),
    ("E3DEJ7odWq0", "fiber optic cables (what you NEED to know) // FREE CCNA // EP 13", "14-fiber-optic-cables", "EP 13"),
    ("0W4JZIWtjLQ", "you NEED to learn Port Security…….RIGHT NOW!! // FREE CCNA // EP 14", "15-port-security", "EP 14"),
    ("5WfiTHiU4x8", "what is an IP Address? // You SUCK at Subnetting // EP 1", "16-ip-addresses", "Subnetting EP 1"),
    ("tcae4TSSMo8", "we ran OUT of IP Addresses!!", "17-ip-exhaustion", "Subnetting EP 2"),
    ("8bhvn9tQk8o", "we're out of IP Addresses….but this saved us (Private IP Addresses)", "18-private-ip-addresses", "Subnetting EP 3"),
    ("2-i5x8KCfII", "i bet you can't do this (because you still suck at subnetting)", "19-subnetting-basics", "Subnetting EP 4"),
    ("oZGZRtaGyG8", "What is a Subnet Mask??? (you NEED to know it!!)", "20-subnet-mask", "Subnetting EP 5"),
    ("mJ_5qeqGOaI", "let's subnet your home network // You SUCK at subnetting // EP 6", "21-subnet-home-network", "Subnetting EP 6"),
    ("B1vqKQIPxr0", "subnetting my coffee shop", "22-subnet-coffee-shop", "Subnetting EP 7"),
    ("6zopTcQFhqM", "Subnetting…..but in reverse", "23-subnetting-in-reverse", "Subnetting EP 8"),
    ("OD2vG5st4zI", "Do you STILL suck at subnetting?? (THE FINAL TEST) // EP 9", "24-subnetting-final-test", "Subnetting EP 9"),
]

def slugify(s):
    s = re.sub(r'[^a-zA-Z0-9\s-]', '', s.lower())
    return re.sub(r'\s+', '-', s.strip())

def create_note(vid, title, filename, label):
    print(f"Processing: {title} ({vid})...")
    transcript_data = fetch_transcript(vid, text_only=False)
    if not transcript_data or not transcript_data.get('transcript'):
        print(f"  WARNING: No transcript for {vid}, writing placeholder")
        text_content = f"No transcript available for this video."
        transcript_json = []
    else:
        transcript_json = transcript_data['transcript']
        text_content = " ".join(seg['text'] for seg in transcript_json)
    
    content = f"""---
created: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
source: "https://youtube.com/watch?v={vid}"
type: ccna-video
day: {label}
playlist: "FREE CCNA 200-301 // Complete Course // NetworkChuck"
channel: NetworkChuck
tags: [ccna, networking, networkchuck]
---

# {label}: {title}

**Video:** https://youtube.com/watch?v={vid}

## Core Concepts

[To be filled from transcript analysis]

## Transcript

{text_content[:500]}...

## Key Takeaways

-

## Related Notes

- [[CCNA Course Index]]
"""
    
    path = os.path.join(VAULT, f"{filename}.md")
    with open(path, 'w') as f:
        f.write(content)
    print(f"  -> Saved {filename}.md")
    return path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=len(VIDEOS))
    args = parser.parse_args()
    
    batch = VIDEOS[args.start:args.end]
    for vid, title, filename, label in batch:
        try:
            create_note(vid, title, filename, label)
        except Exception as e:
            print(f"  ERROR processing {title}: {e}", file=sys.stderr)
    
    print(f"\nDone! Processed {len(batch)} videos.")
