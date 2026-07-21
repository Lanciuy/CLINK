import urllib.request

urls = [
    ("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrnet-x4plus.param", "d:/Project/CLINK/tools/realesrgan/models/realesrnet-x4plus.param"),
    ("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrnet-x4plus.bin", "d:/Project/CLINK/tools/realesrgan/models/realesrnet-x4plus.bin")
]

for url, path in urls:
    print(f"Downloading {url}...")
    urllib.request.urlretrieve(url, path)
    print("Done")
