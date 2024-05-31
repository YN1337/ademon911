import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from PIL import Image, ImageTk
import requests
import threading
from io import BytesIO

class URLFetcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Fetcher Tool")
        self.root.geometry("800x600")

        # Download background image from URL
        image_url = "https://wallpaperaccess.com/full/3078197.jpg"
        response = requests.get(image_url)
        image_data = BytesIO(response.content)
        self.bg_image = Image.open(image_data)
        self.bg_image = self.bg_image.resize((800, 600))  # Resizing without specifying the resampling filter
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        # Set the background image on canvas
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        self.label = tk.Label(root, text="Enter Domain:", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12))
        self.canvas.create_window(400, 50, window=self.label)

        self.domain_entry = tk.Entry(root, width=70, font=("Helvetica", 12))
        self.canvas.create_window(400, 100, window=self.domain_entry)

        self.fetch_button = ttk.Button(root, text="Fetch URLs", command=self.start_fetching)
        self.canvas.create_window(400, 150, window=self.fetch_button)

        self.result_area = scrolledtext.ScrolledText(root, width=80, height=20, font=("Helvetica", 10), wrap=tk.WORD)
        self.canvas.create_window(400, 350, window=self.result_area)

        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.canvas.create_window(400, 550, window=self.progress)

    def start_fetching(self):
        domain = self.domain_entry.get()
        if domain:
            self.result_area.delete(1.0, tk.END)
            self.result_area.insert(tk.END, f"Fetching URLs for {domain}...\n\n")
            self.progress.start()
            fetch_thread = threading.Thread(target=self.fetch_urls, args=(domain,))
            fetch_thread.start()

    def fetch_urls(self, domain):
        try:
            urls = self.get_urls(domain)
            self.result_area.insert(tk.END, "\n".join(urls) + "\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.progress.stop()

    def get_urls(self, domain):
        urls = []
        threads = []

        fetchers = [
            self.fetch_from_otx,
            self.fetch_from_wayback,
            self.fetch_from_common_crawl,
            self.fetch_from_urlscan,
        ]

        results = [[] for _ in fetchers]

        def run_fetcher(fetcher, index):
            results[index].extend(fetcher(domain))

        for i, fetcher in enumerate(fetchers):
            thread = threading.Thread(target=run_fetcher, args=(fetcher, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for result in results:
            urls.extend(result)

        return urls

    def fetch_from_otx(self, domain):
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return [url_data['url'] for url_data in data['url_list']]
        except Exception as e:
            print(f"Error fetching from OTX: {e}")
        return []

    def fetch_from_wayback(self, domain):
        try:
            url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&collapse=urlkey"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return [entry[0] for entry in data[1:]]
        except Exception as e:
            print(f"Error fetching from Wayback Machine: {e}")
        return []

    def fetch_from_common_crawl(self, domain):
        try:
            cc_url = f"https://index.commoncrawl.org/CC-MAIN-2023-09-index?url={domain}&output=json"
            response = requests.get(cc_url)
            if response.status_code == 200:
                return [entry['url'] for entry in response.json()]
        except Exception as e:
            print(f"Error fetching from Common Crawl: {e}")
        return []

    def fetch_from_urlscan(self, domain):
        try:
            url = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
            headers = {'API-Key': 'YOUR_API_KEY_HERE'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return [result['task']['url'] for result in data['results']]
        except Exception as e:
            print(f"Error fetching from URLScan: {e}")
        return []

if __name__ == "__main__":
    root = tk.Tk()
    app = URLFetcherApp(root)
    root.mainloop()
