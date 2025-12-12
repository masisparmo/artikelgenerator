
import requests
import json

VIDEO_ID = "NrpncvUJZFk"

INSTANCES = [
    # Piped
    {"url": "https://pipedapi.kavin.rocks", "type": "piped"},
    {"url": "https://api.piped.privacy.com.de", "type": "piped"},
    {"url": "https://pipedapi.drgns.space", "type": "piped"},
    {"url": "https://pipedapi.smnz.de", "type": "piped"},
    {"url": "https://api.piped.projectsegfau.lt", "type": "piped"},

    # Invidious
    {"url": "https://invidious.drgns.space", "type": "invidious"},

    # Raw Proxy Test (Codetabs)
    {"url": "https://api.codetabs.com/v1/proxy?quest=https://www.youtube.com/watch?v=" + VIDEO_ID, "type": "proxy"}
]

def test_alternatives():
    for instance in INSTANCES:
        base_url = instance["url"]
        api_type = instance["type"]
        print(f"Testing {api_type}: {base_url}")

        try:
            if api_type == "invidious":
                url = f"{base_url}/api/v1/videos/{VIDEO_ID}"
                response = requests.get(url, timeout=10)
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    captions = data.get('captions', [])
                    print(f"  [SUCCESS] Invidious found video. Captions: {len(captions)}")

            elif api_type == "piped":
                url = f"{base_url}/streams/{VIDEO_ID}"
                response = requests.get(url, timeout=10)
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    subtitles = data.get('subtitles', [])
                    print(f"  [SUCCESS] Piped found video. Subtitles: {len(subtitles)}")

            elif api_type == "proxy":
                response = requests.get(base_url, timeout=15)
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    text = response.text
                    if "captionTracks" in text:
                        print("  [SUCCESS] Proxy retrieved HTML with captionTracks!")
                    else:
                        print("  [FAIL] Proxy retrieved HTML but no captions found.")

        except Exception as e:
            print(f"  [FAIL] Error: {e}")

if __name__ == "__main__":
    test_alternatives()
