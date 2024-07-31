import tkinter as tk

root = tk.Tk()

label = tk.Label(root, text="Hello, Tkinter!")
label.grid(row=0, column=0)
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

root.mainloop()
