import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import queue
import ctypes
import json
import requests
import uuid
from datetime import datetime
from mappings import script_mappings  # Import the script mappings

def get_mac_address():
    """Get the MAC address of the computer."""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0, 11, 2)])

def validate_key(key):
    """Send the key and MAC address to the server for validation."""
    mac_address = get_mac_address()

    url = "https://aviator.nextgendynamicsnaija.com/aviator/validate_key.php"
    data = {
        "key": key,
        "mac_address": mac_address
    }
    print(data)
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()

def check_key():
    """Function to check the entered key and show the main window if the key is valid."""
    key = key_entry.get()
    result = validate_key(key)
    if "success" in result:
        key_dialog.destroy()
        show_main_window(result["data"].get("expiry_date", ""))
    else:
        messagebox.showerror("Invalid Key", result.get("error", "The entered key is not valid."))

def run_script():
    # Get the values from the GUI elements
    country = country_combo.get()
    betting_site = bookie_combo.get()
    turnover_value = turnover_combo.get()
    
    # Retrieve the corresponding script based on the selected country and betting site
    script = script_mappings.get((country, betting_site), None)
    
    if script:
        output_text.insert(tk.END, f"Connecting to {betting_site}\n")

        def run_in_thread(script, country, betting_site, turnover_value, queue):
            try:
                process = subprocess.Popen(
                    ['python', script, country, betting_site, turnover_value],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True, bufsize=1
                )

                # Poll process.stdout to read output in real-time
                for stdout_line in iter(process.stdout.readline, ""):
                    queue.put(stdout_line)
                    # Ensure buffer is flushed to get real-time output
                    process.stdout.flush()

                process.stdout.close()
                process.wait()

                stderr_output = process.stderr.read()
                if stderr_output:
                    queue.put(stderr_output)
                
                process.stderr.close()
            except Exception as e:
                queue.put(f"An error occurred: {str(e)}\n")

        def update_gui(queue):
            try:
                while not queue.empty():
                    line = queue.get_nowait()
                    output_text.insert(tk.END, line)
                    output_text.see(tk.END)  # Auto-scroll to the end of the text area
            except queue.Empty:
                pass
            finally:
                # Re-schedule the update_gui function
                main_window.after(100, update_gui, queue)

        # Create a queue to hold the output lines
        output_queue = queue.Queue()

        # Start the thread to run the subprocess
        thread = threading.Thread(target=run_in_thread, args=(script, country, betting_site, turnover_value, output_queue))
        thread.start()

        # Start updating the GUI with the output
        main_window.after(100, update_gui, output_queue)
    else:
        output_text.insert(tk.END, f"No script found for {country} and {betting_site}.\n")

def update_bookie_list(event):
    """Function to update the bookie list based on the selected country."""
    country = country_combo.get()
    bookies = {
        "Ghana": ["SportyBet Gh", "Betway Gh", "BetPawa Gh"],
        "Nigeria": ["SportyBet Ng", "Betway Ng", "BetPawa Ng", "PariPesa Ng"],
        "Cameroon": ["BetPawa Cm", "BetwayNG"],
        "Kenya": ["BetPawa Ke", "Betway Ke", "SportyBet Ke"],
        "Uganda": ["BetPawa Ug", "Betway Ug", "SportyBet Ug"],
        "South Africa": ["BetPawa Za"],
        "Tanzania": ["BetPawa Tz", "Betway Tz", "SportyBet Tz"],
        "Zambia": ["BetPawa Zm", "BolaBet Zm", "BongoBongo Zm", "Betlion Zm", "PariPesa Zm", "888Aviator Zm", "GSB Zm", "MWOS Zm"],
        "Malawi": ["BetPawa Mw", "Betika Mw", "Betway Mw"]
    }
    
    bookie_combo['values'] = bookies.get(country, ["No Bookies"])
    bookie_combo.set("Betting Site")

def show_main_window(expiry_date):
    """Function to show the main window."""
    global country_combo, bookie_combo, turnover_combo, output_text, main_window

    # Convert expiry date format from yyyy-mm-dd to dd/mm/yyyy
    try:
        expiry_date_formatted = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
    except ValueError:
        expiry_date_formatted = expiry_date

    main_window = tk.Tk()
    main_window.title("Main Window")
    main_window.geometry("1126x845")  # Increased by 10%
    main_window.minsize(800, 600)
    main_window.maxsize(1126, 845)

    # Set high-quality font
    default_font = ('Segoe UI', 12)
    main_window.option_add("*TCombobox*Listbox*Font", default_font)
    main_window.option_add("*Font", default_font)

    # Adding labels and combo boxes
    tk.Label(main_window, text="Select Country").place(x=30, y=40)
    tk.Label(main_window, text="Bookie").place(x=30, y=90)
    tk.Label(main_window, text="Turnover").place(x=30, y=140)
    tk.Label(main_window, text="Key Valid till:").place(x=730, y=10)
    tk.Label(main_window, text=expiry_date_formatted).place(x=890, y=10)

    country_combo = ttk.Combobox(main_window)
    country_combo['values'] = ("Ghana", "Nigeria", "Cameroon", "Kenya", "Uganda", "South Africa", "Tanzania", "Zambia", "Malawi")
    country_combo.place(x=220, y=40)  # Moved to the right
    country_combo.set("Country...")
    country_combo.bind("<<ComboboxSelected>>", update_bookie_list)

    bookie_combo = ttk.Combobox(main_window)
    bookie_combo.place(x=220, y=90)  # Moved to the right
    bookie_combo.set("Betting Site")

    turnover_combo = ttk.Combobox(main_window)
    turnover_combo['values'] = ("x2", "x4", "x6", "x8")
    turnover_combo.place(x=220, y=140)  # Moved to the right
    turnover_combo.set("Turnover Value")

    # Output text area
    output_text = scrolledtext.ScrolledText(main_window, bg='black', fg='white', font=('Consolas', 12))
    output_text.place(x=30, y=290, width=1066, height=511)  # Adjusted for increased size

    # Start button
    start_button = tk.Button(main_window, text="Start", bg='green', fg='white', command=run_script)
    start_button.place(x=200, y=200, width=724, height=41)  # Increased width and moved down

    main_window.mainloop()

# Enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception as e:
    print(e)

# Product Key Dialog
key_dialog = tk.Tk()
key_dialog.title("Aviator Bot")
key_dialog.geometry("550x440")  # Increased by 10%

# Centralize elements
container = tk.Frame(key_dialog)
container.place(relx=0.5, rely=0.4, anchor=tk.CENTER)  # Adjusted vertical position

# Label, entry, and submit button
tk.Label(container, text="Please Enter your Product Key", font=('Segoe UI', 12)).pack(pady=(0, 20))
key_entry = tk.Entry(container, font=('Segoe UI', 12), width=30)  # Set width
key_entry.pack(pady=(0, 20), ipadx=10, ipady=5)

submit_button = tk.Button(container, text="Start Bot", command=check_key, font=('Segoe UI', 12), bg='green', fg='white')
submit_button.pack(ipadx=10,  fill='x')  # Match width with key_entry by using fill='x'

key_dialog.mainloop()
