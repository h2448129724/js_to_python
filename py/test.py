import tkinter as tk
class MyApp(tk.Frame):
    def init (self, master=None):
        super().init (master)
        self.master =master
        self.label = tk.Label(self.master, text="Hello, World!", bg="gray")
        self.label.place(relx=0.5,rely=0.5, anchor="center")
        self.pack()
        self.bind("<Configure>",self.on_resize)
    def on_resize(self, event):
        w= event.width
        h = event.heightself.label.place_configure(relx=0.5, rely=0.5, anchor="center", width=w*.8, height=h*0.8)

root = tk.Tk()
app = MyApp(root)
app.mainloop()