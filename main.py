# =============================================================================
#  CPU SCHEDULING SIMULATOR
#  Bahria University —Operating Systems
#  Language: Python 3  |  GUI: tkinter (comes built-in with Python!)
# =============================================================================
#  This simulator makes those decisions VISIBLE — you can watch the OS work!



from app import App  # Import the main application window class

if __name__ == "__main__":
    app = App()     # Create the main window and build the entire GUI
    app.mainloop()  # Start the event loop — listens for clicks, keys, etc. forever
