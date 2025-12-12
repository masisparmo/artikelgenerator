
import requests
import json

VIDEO_ID = "NrpncvUJZFk"

# Extensive list of Piped instances
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.tokhmi.xyz",
    "https://pipedapi.moomoo.me",
    "https://pipedapi.syncpundit.io",
    "https://api.piped.privacy.com.de",
    "https://api.martion.de",
    "https://pipedapi.ngn.tf",
    "https://pipedapi.systemless.io",
    "https://api.piped.projectsegfau.lt", # Often has captcha/html
    "https://pipedapi.r4fo.com",
    "https://api.piped.yt",
    "https://piped-api.lunar.icu",
    "https://pipedapi-libre.kavin.rocks",
]

def test_piped_instances():
    working_instances = []

    for base_url in PIPED_INSTANCES:
        print(f"Testing: {base_url}")
        try:
            url = f"{base_url}/streams/{VIDEO_ID}"
            response = requests.get(url, timeout=5)

            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    subtitles = data.get('subtitles', [])
                    print(f"  [SUCCESS] Subtitles found: {len(subtitles)}")
                    if len(subtitles) > 0:
                        working_instances.append(base_url)
                except json.JSONDecodeError:
                    print("  [FAIL] Response was not JSON (likely HTML error page)")
            else:
                print(f"  [FAIL] HTTP {response.status_code}")

        except Exception as e:
            print(f"  [FAIL] Error: {e}")

    print("\n--- Working Instances ---")
    for instance in working_instances:
        print(f'"{instance}",')

if __name__ == "__main__":
    test_piped_instances()
