
import requests
import re
import json
import urllib.parse

def test_youtube_extraction():
    video_id = "jNQXAC9IVRw" # Me at the zoo (short, popular, has captions)
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    proxies = [
        'https://api.codetabs.com/v1/proxy?quest=',
        'https://corsproxy.io/?',
        'https://api.allorigins.win/get?url='
    ]

    print(f"Testing extraction for video: {video_url}")

    caption_url = None

    # 1. Fetch Page
    for proxy in proxies:
        target_url = f"{proxy}{urllib.parse.quote(video_url)}"
        print(f"Trying proxy: {proxy}")

        try:
            response = requests.get(target_url, timeout=10)
            if response.status_code != 200:
                print(f"  Failed with status {response.status_code}")
                continue

            html = ""
            if 'allorigins' in proxy:
                try:
                    data = response.json()
                    html = data.get('contents', '')
                except:
                    print("  Failed to parse JSON from allorigins")
            else:
                html = response.text

            if not html:
                print("  Empty HTML received")
                continue

            # Search for captionTracks
            match = re.search(r'"captionTracks"\s*:\s*(\[.*?\])', html)
            if match:
                print("  FOUND captionTracks!")
                tracks = json.loads(match.group(1))
                if tracks:
                    caption_url = tracks[0]['baseUrl']
                    print(f"  Caption URL found: {caption_url[:50]}...")
                    break
            else:
                print("  captionTracks not found in HTML")

        except Exception as e:
            print(f"  Error: {e}")

    if not caption_url:
        print("FAILED to get caption URL from any proxy.")
        return False

    # 2. Fetch Transcript
    print("Attempting to fetch transcript...")
    for proxy in proxies:
        target_url = f"{proxy}{urllib.parse.quote(caption_url)}"
        try:
            response = requests.get(target_url, timeout=10)
            if response.status_code != 200:
                continue

            content = ""
            if 'allorigins' in proxy:
                data = response.json()
                content = data.get('contents', '')
            else:
                content = response.text

            if content and "<text" in content:
                print("SUCCESS: Transcript XML fetched!")
                return True
        except:
            pass

    print("FAILED to fetch transcript XML.")
    return False

if __name__ == "__main__":
    success = test_youtube_extraction()
    if success:
        print("VERIFICATION PASSED")
    else:
        print("VERIFICATION FAILED")
