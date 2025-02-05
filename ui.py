import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import csv

CONFIG_FILE = "config.json"
LOG_FILES = ["error.log", "google.log", "script.log"]
LOG_TAIL_LINES = 20  # Number of lines to display from the end of the log
LAST_INDEX_FILE = "last_index.txt"  # File containing the Google display value

class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Config Editor")

        # Load config
        self.config = self.load_config()

        # UI Elements
        self.create_ui()
        self.start_auto_update()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error", "Config file not found.")
            self.root.quit()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, ensure_ascii=False, indent=4)
            messagebox.showinfo("Success", "Config saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def create_ui(self):
        # Sessions Frame
        session_frame = ttk.LabelFrame(self.root, text="Sessions")
        session_frame.pack(fill="x", padx=10, pady=5)

        self.session_list = tk.Listbox(session_frame, height=5, selectmode=tk.SINGLE)
        self.session_list.pack(side="left", fill="x", expand=True)
        self.update_session_list()

        session_buttons = tk.Frame(session_frame)
        session_buttons.pack(side="right", padx=5)

        tk.Button(session_buttons, text="Enable", command=self.enable_session).pack(fill="x", pady=2)
        tk.Button(session_buttons, text="Disable", command=self.disable_session).pack(fill="x", pady=2)
        tk.Button(session_buttons, text="Remove", command=self.remove_session).pack(fill="x", pady=2)
        tk.Button(session_buttons, text="Add", command=self.add_session).pack(fill="x", pady=2)
        tk.Button(session_buttons, text="Edit", command=self.edit_session).pack(fill="x", pady=2)

        # Input/Output Files
        file_frame = ttk.LabelFrame(self.root, text="Input/Output Files")
        file_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.input_file_entry = tk.Entry(file_frame, width=40)
        self.input_file_entry.grid(row=0, column=1, padx=5, pady=2)
        self.input_file_entry.insert(0, self.config.get("input_file", ""))
        tk.Button(file_frame, text="Browse", command=self.browse_input_file).grid(row=0, column=2, padx=5, pady=2)

        tk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.output_file_entry = tk.Entry(file_frame, width=40)
        self.output_file_entry.grid(row=1, column=1, padx=5, pady=2)
        self.output_file_entry.insert(0, self.config.get("output_file", ""))
        tk.Button(file_frame, text="Browse", command=self.browse_output_file).grid(row=1, column=2, padx=5, pady=2)

        # Other Settings
        settings_frame = ttk.LabelFrame(self.root, text="Settings")
        settings_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(settings_frame, text="Delay (seconds):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.delay_spinbox = tk.Spinbox(settings_frame, from_=0, to=60, width=5)
        self.delay_spinbox.grid(row=0, column=1, padx=5, pady=2)
        self.delay_spinbox.delete(0, "end")
        self.delay_spinbox.insert(0, self.config.get("delay", 5))

        tk.Label(settings_frame, text="Count:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.count_spinbox = tk.Spinbox(settings_frame, from_=1, to=100, width=5)
        self.count_spinbox.grid(row=1, column=1, padx=5, pady=2)
        self.count_spinbox.delete(0, "end")
        self.count_spinbox.insert(0, self.config.get("count", 10))

        tk.Label(settings_frame, text="Last Processed Index:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.last_processed_label = tk.Label(settings_frame, text=self.config.get("last_processed_index", 0))
        self.last_processed_label.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(settings_frame, text="Google Value:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.google_value_label = tk.Label(settings_frame, text=self.load_google_value())
        self.google_value_label.grid(row=3, column=1, padx=5, pady=2)

        # Log Viewer
        log_frame = ttk.LabelFrame(self.root, text="Log Viewer")
        log_frame.pack(fill="both", padx=10, pady=5, expand=True)

        self.log_selector = tk.Listbox(log_frame, height=3, selectmode=tk.SINGLE)
        self.log_selector.pack(fill="x", padx=5, pady=5)
        for log_file in LOG_FILES:
            self.log_selector.insert(tk.END, log_file)

        self.log_text = tk.Text(log_frame, wrap="none", height=10)
        self.log_text.pack(fill="both", expand=True)
        self.log_selector.bind("<<ListboxSelect>>", self.display_selected_log)
        self.display_selected_log()

        # Save Button
        save_button = tk.Button(self.root, text="Save Config", command=self.save)
        save_button.pack(pady=5)

    def update_session_list(self):
        self.session_list.delete(0, tk.END)
        for session in self.config.get("sessions", []):
            status = "Enabled" if not session["session_id"].startswith("#") else "Disabled"
            self.session_list.insert(tk.END, f"{session['tag']} - {status}")

    def enable_session(self):
        selected = self.session_list.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a session to enable.")
            return

        index = selected[0]
        self.config["sessions"][index]["session_id"] = self.config["sessions"][index]["session_id"].lstrip("#")
        self.update_session_list()
        self.save_config()

    def disable_session(self):
        selected = self.session_list.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a session to disable.")
            return

        index = selected[0]
        self.config["sessions"][index]["session_id"] = f"#{self.config['sessions'][index]['session_id']}"
        self.update_session_list()
        self.save_config()

    def remove_session(self):
        selected = self.session_list.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a session to remove.")
            return

        index = selected[0]
        del self.config["sessions"][index]
        self.update_session_list()
        self.save_config()

    def add_session(self):
        self.open_session_editor(new=True)

    def edit_session(self):
        selected = self.session_list.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a session to edit.")
            return

        index = selected[0]
        self.open_session_editor(new=False, index=index)

    def open_session_editor(self, new=True, index=None):
        editor_window = tk.Toplevel(self.root)
        editor_window.title("Add Session" if new else "Edit Session")

        tk.Label(editor_window, text="Session ID:").grid(row=0, column=0, padx=5, pady=5)
        session_id_entry = tk.Entry(editor_window, width=30)
        session_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(editor_window, text="Tag:").grid(row=1, column=0, padx=5, pady=5)
        tag_entry = tk.Entry(editor_window, width=30)
        tag_entry.grid(row=1, column=1, padx=5, pady=5)

        if not new and index is not None:
            session_id_entry.insert(0, self.config["sessions"][index]["session_id"])
            tag_entry.insert(0, self.config["sessions"][index]["tag"])

        def save_session():
            session_id = session_id_entry.get().strip()
            tag = tag_entry.get().strip()
            if not session_id or not tag:
                messagebox.showwarning("Warning", "Both fields are required.")
                return

            if new:
                self.config["sessions"].append({"session_id": session_id, "tag": tag})
            else:
                self.config["sessions"][index] = {"session_id": session_id, "tag": tag}

            self.update_session_list()
            self.save_config()
            editor_window.destroy()

        tk.Button(editor_window, text="Save", command=save_session).grid(row=2, column=0, columnspan=2, pady=10)

    def browse_input_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.input_file_entry.delete(0, "end")
            self.input_file_entry.insert(0, file_path)

    def browse_output_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[["CSV Files", "*.csv"]])
        if file_path:
            self.output_file_entry.delete(0, "end")
            self.output_file_entry.insert(0, file_path)

    def save(self):
        self.config["input_file"] = self.input_file_entry.get()
        self.config["output_file"] = self.output_file_entry.get()
        self.config["delay"] = int(self.delay_spinbox.get())
        self.config["count"] = int(self.count_spinbox.get())
        self.save_config()

    def load_log(self):
        selected_log = self.get_selected_log()
        if not selected_log:
            return

        try:
            with open(selected_log, 'r', encoding='utf-8') as log_file:
                lines = log_file.readlines()
                tail_lines = lines[-LOG_TAIL_LINES:] if len(lines) > LOG_TAIL_LINES else lines
                self.log_text.delete("1.0", tk.END)
                self.log_text.insert("1.0", "".join(tail_lines))
        except FileNotFoundError:
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", f"Log file '{selected_log}' not found.")

    def display_selected_log(self, event=None):
        self.load_log()

    def get_selected_log(self):
        selected = self.log_selector.curselection()
        if not selected:
            return None
        return LOG_FILES[selected[0]]

    def start_auto_update(self):
        self.auto_update()

    def auto_update(self):
        self.load_config_data()
        self.load_log()
        self.update_google_value()
        self.root.after(5000, self.auto_update)  # Update every 5 seconds

    def load_config_data(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                self.config = json.load(file)
                self.update_session_list()
                self.input_file_entry.delete(0, "end")
                self.input_file_entry.insert(0, self.config.get("input_file", ""))
                self.output_file_entry.delete(0, "end")
                self.output_file_entry.insert(0, self.config.get("output_file", ""))
                self.delay_spinbox.delete(0, "end")
                self.delay_spinbox.insert(0, self.config.get("delay", 5))
                self.count_spinbox.delete(0, "end")
                self.count_spinbox.insert(0, self.config.get("count", 10))
                self.last_processed_label.config(text=self.config.get("last_processed_index", 0))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def load_google_value(self):
        try:
            with open(LAST_INDEX_FILE, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except FileNotFoundError:
            return "File not found"
        except Exception as e:
            return f"Error: {e}"

    def update_google_value(self):
        self.google_value_label.config(text=self.load_google_value())

class ExtendedConfigEditor(ConfigEditor):
    def __init__(self, root):
        super().__init__(root)
        self.progress_frame = ttk.LabelFrame(self.root, text="Progress")
        self.progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(self.progress_frame, length=300, mode="determinate")
        self.progress_bar.pack(pady=5)

        self.progress_label = tk.Label(self.progress_frame, text="Progress: 0%")
        self.progress_label.pack()

        self.load_progress_button = tk.Button(self.progress_frame, text="Load Progress", command=self.load_csv_progress)
        self.load_progress_button.pack(pady=5)

    def load_csv_progress(self):
        file_path = filedialog.askopenfilename(filetypes=[["CSV Files", "*.csv"]])
        if not file_path:
            return

        try:
            total_rows = self.get_csv_row_count(file_path)
            google_value = int(self.load_google_value()) if self.load_google_value().isdigit() else 0

            self.progress_bar["maximum"] = total_rows
            self.progress_bar["value"] = google_value

            progress_percentage = (google_value / total_rows) * 100 if total_rows else 0
            self.progress_label.config(text=f"Progress: {progress_percentage:.2f}%")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")

    def get_csv_row_count(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                return sum(1 for _ in reader)  # Count rows in the CSV
        except Exception as e:
            raise e

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtendedConfigEditor(root)
    root.mainloop()
