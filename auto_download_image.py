import os
import sys
import threading
import logging
from pathlib import Path
from tkinter import Tk, filedialog, messagebox, Text, Button, Entry, Label, StringVar
from gdown import download
from requests.exceptions import MissingSchema, RequestException
from typing import List


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GoogleDriveDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive Bulk Downloader")
        self.root.geometry("600x400")
        
        # Variables
        self.links_file_path = StringVar()
        self.output_directory_path = StringVar()

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        # Links file selection
        Label(self.root, text="Links File:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        Entry(self.root, textvariable=self.links_file_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        Button(self.root, text="Browse", command=self.browse_links_file).grid(row=0, column=2, padx=5, pady=5)

        # Output directory selection
        Label(self.root, text="Output Directory:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        Entry(self.root, textvariable=self.output_directory_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        Button(self.root, text="Browse", command=self.browse_output_directory).grid(row=1, column=2, padx=5, pady=5)

        # Text area for logs
        self.log_text = Text(self.root, height=15, width=70)
        self.log_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        # Download button
        Button(self.root, text="Start Download", command=self.start_download).grid(row=3, column=1, pady=10)

    def browse_links_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Links File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.links_file_path.set(file_path)

    def browse_output_directory(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory_path.set(directory)

    def log_message(self, message, level="INFO"):
        def update_log():
            levels = {
                "INFO": "INFO",
                "ERROR": "ERROR",
                "WARNING": "WARNING"
            }
            formatted_message = f"{levels.get(level, 'INFO')} - {message}\n"
            self.log_text.insert("end", formatted_message)
            self.log_text.see("end")

        self.root.after(0, update_log)

    def start_download(self):
        links_file = self.links_file_path.get()
        output_dir = self.output_directory_path.get()

        if not links_file or not output_dir:
            messagebox.showerror("Error", "Please select both the links file and output directory!")
            return

        self.log_text.delete(1.0, "end")  # Clear previous logs
        download_thread = threading.Thread(target=self.google_drive_bulk_download, args=(links_file, output_dir))
        download_thread.start()

    def google_drive_bulk_download(self, links_file_path: str, output_directory_path: str) -> None:
        # Set the working directory correctly for frozen executables (like .exe)
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS  # For frozen executables
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))  # For regular execution
        os.chdir(application_path)  # Set the working directory to the current path of the executable
        
        # Validate and open the links file
        links_path = Path(links_file_path)
        if not links_path.is_file():
            self.log_message(f"The file '{links_file_path}' does not exist!", "ERROR")
            return

        # Validate and set output directory
        output_path = Path(output_directory_path)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            os.chdir(output_path)  # Change to the output directory
        except (OSError, PermissionError) as e:
            self.log_message(f"Failed to set output directory '{output_directory_path}': {str(e)}", "ERROR")
            return

        # Read and clean the URLs
        try:
            with open(links_path, 'r', encoding='utf-8') as file:
                file_lines: List[str] = [
                    line.strip() for line in file.readlines() if line.strip()
                ]
        except (IOError, UnicodeDecodeError) as e:
            self.log_message(f"Failed to read file '{links_file_path}': {str(e)}", "ERROR")
            return

        if not file_lines:
            self.log_message("No valid URLs found in the file!", "WARNING")
            return

        file_lines_count: int = len(file_lines)
        self.log_message("Started downloading process")

        # Download each file
        for i, url_raw in enumerate(file_lines, start=1):
            download_url: str = self.fix_google_drive_url(url_raw.strip())
            self.log_message(f"Downloading [{i}/{file_lines_count}]: {download_url}")

            try:
                download(url=download_url, quiet=False, fuzzy=True)
                self.log_message("Download completed successfully")
            except MissingSchema:
                self.log_message(f"Invalid URL format: '{download_url}'", "ERROR")
            except RequestException as e:
                self.log_message(f"Network error while downloading '{download_url}': {str(e)}", "ERROR")
            except Exception as e:
                self.log_message(f"Unexpected error while downloading '{download_url}': {str(e)}", "ERROR")

        self.log_message("Finished downloading process")

    def fix_google_drive_url(self, url: str) -> str:
        """
        Fix and return the URL to be compatible with gdown download tool.
        """
        if "drive.google.com" in url:
            return url.replace("/file/d/", "/uc?id=").replace("/view", "")
        return url

if __name__ == "__main__":
    root = Tk()
    app = GoogleDriveDownloaderGUI(root)
    root.mainloop()
