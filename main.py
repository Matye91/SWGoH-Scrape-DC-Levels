import csv
import time
import re
import tkinter as tk
from tkinter import messagebox
import cloudscraper
from bs4 import BeautifulSoup

BASE_URL = "https://swgoh.gg"
OUTPUT_FILE = "guild_datacrons.csv"
REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://swgoh.gg/g/",
    "Upgrade-Insecure-Requests": "1",
}


class SwgohScraper:
    def __init__(self, guild_url):
        self.guild_url = guild_url
        self.session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        self.session.headers.update(HEADERS)

    def fetch_html(self, url):
        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    return BeautifulSoup(resp.text, "html.parser")
                time.sleep(2)
            except Exception:
                time.sleep(2)
        return None

    def validate_guild_page(self):
        soup = self.fetch_html(self.guild_url)
        if not soup:
            return False

        table = soup.find("table", class_="data-table data-table--small w-100")
        return table is not None

    def parse_guild_members(self):
        soup = self.fetch_html(self.guild_url)
        if not soup:
            return []

        table = soup.find("table", class_="data-table data-table--small w-100")
        if not table:
            return []

        members = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            a_tag = cols[0].find("a", href=True)
            if not a_tag or not a_tag["href"].startswith("/p/"):
                continue

            ally_code = a_tag["href"].split("/")[2]

            name_div = cols[0].find("div", class_="fw-bold text-white")
            player_name = name_div.text.strip() if name_div else "Unknown"

            gp_text = cols[1].get_text(strip=True).replace(",", "")
            try:
                player_gp = int(gp_text)
            except ValueError:
                player_gp = 0

            members.append({
                "ally_code": ally_code,
                "player_name": player_name,
                "player_gp": player_gp,
            })

        return members

    def parse_datacrons(self, ally_code):
        url = f"{BASE_URL}/p/{ally_code}/datacrons/"
        soup = self.fetch_html(url)
        if not soup:
            return [0] * 6

        container = soup.find(
            "div",
            class_="d-flex justify-content-center gap-3 flex-wrap"
        )
        if not container:
            return [0] * 6

        values = []
        for block in container.find_all("div", class_="text-center")[:6]:
            inner_divs = block.find_all("div")
            if not inner_divs:
                values.append(0)
                continue

            text = inner_divs[0].get_text(strip=True).replace(",", "")
            try:
                values.append(int(text))
            except ValueError:
                values.append(0)

        while len(values) < 6:
            values.append(0)

        return values

    def run(self):
        members = self.parse_guild_members()

        header = [
            "Ally Code",
            "Player Name",
            "Player GP",
            "Level 15",
            "Level 12-14",
            "Level 9-11",
            "Level 6-8",
            "Level 3-5",
            "Empty",
        ]

        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter="|")
            writer.writerow(header)

            for m in members:
                datacrons = self.parse_datacrons(m["ally_code"])
                writer.writerow([
                    m["ally_code"],
                    m["player_name"],
                    m["player_gp"],
                    *datacrons,
                ])
                time.sleep(1.5)


def start_gui():
    def on_start():
        guild_url = entry.get().strip()

        if not re.match(r"^https://swgoh\.gg/g/[A-Za-z0-9_-]+/?$", guild_url):
            messagebox.showerror(
                "Invalid URL",
                "Please enter a valid swgoh.gg guild URL."
            )
            return

        scraper = SwgohScraper(guild_url)
        if not scraper.validate_guild_page():
            messagebox.showerror(
                "Invalid Guild",
                "The provided link does not appear to be a valid guild page."
            )
            return

        root.destroy()
        scraper.run()
        messagebox.showinfo(
            "Done",
            f"Datacron data successfully saved to {OUTPUT_FILE}"
        )

    root = tk.Tk()
    root.title("SWGOH Guild Datacron Scraper")
    root.geometry("520x140")
    root.resizable(False, False)

    tk.Label(
        root,
        text="Enter SWGOH Guild Link:",
        font=("Segoe UI", 10)
    ).pack(pady=10)

    entry = tk.Entry(root, width=70)
    entry.pack()

    tk.Button(
        root,
        text="Start Scraping",
        command=on_start,
        width=20
    ).pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    start_gui()
