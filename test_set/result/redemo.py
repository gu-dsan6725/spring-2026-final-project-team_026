import tkinter as tk
from tkinter import ttk
import re

class ReDemo:
    def __init__(self, master):
        self.master = master
        self.prompt_display = tk.Label(master, anchor=tk.W, text="Enter a Perl-style regular expression:")
        self.prompt_display.pack(side=tk.TOP, fill=tk.X)

        self.regex_display = tk.Entry(master)
        self.regex_display.pack(fill=tk.X)
        self.regex_display.focus_set()

        self.add_options()

        self.status_display = tk.Label(master, text="", anchor=tk.W)
        self.status_display.pack(side=tk.TOP, fill=tk.X)

        self.label_display = tk.Label(master, anchor=tk.W, text="Enter a string to search:")
        self.label_display.pack(fill=tk.X)

        self.show_frame = tk.Frame(master)
        self.show_frame.pack(fill=tk.X, anchor=tk.W)

        self.show_var = tk.StringVar(master)
        self.show_var.set("first")

        self.show_first_radio = ttk.Radiobutton(self.show_frame, text="Highlight first match", variable=self.show_var, value="first", command=self.recompile)
        self.show_first_radio.pack(side=tk.LEFT)

        self.show_all_radio = ttk.Radiobutton(self.show_frame, text="Highlight all matches", variable=self.show_var, value="all", command=self.recompile)
        self.show_all_radio.pack(side=tk.LEFT)

        self.string_display = tk.Text(master, width=60, height=4)
        self.string_display.pack(fill=tk.BOTH, expand=1)
        self.string_display.tag_configure("hit", background="yellow")

        self.group_label = tk.Label(master, text="Groups:", anchor=tk.W)
        self.group_label.pack(fill=tk.X)

        self.group_list = tk.Listbox(master)
        self.group_list.pack(expand=1, fill=tk.BOTH)

        self.regex_display.bind('<Key>', self.recompile)
        self.string_display.bind('<Key>', self.reevaluate)

        self.compiled = None
        self.recompile()

        btags = self.regex_display.bindtags()
        self.regex_display.bindtags(btags[1:] + btags[:1])

        btags = self.string_display.bindtags()
        self.string_display.bindtags(btags[1:] + btags[:1])

    def add_options(self):
        self.frames = []
        self.boxes = []
        self.vars = []
        for name in ('IGNORECASE', 'LOCALE', 'MULTILINE', 'DOTALL', 'VERBOSE'):
            if len(self.boxes) % 3 == 0:
                frame = tk.Frame(self.master)
                frame.pack(fill=tk.X)
                self.frames.append(frame)
            val = getattr(re, name)
            var = tk.IntVar()
            box = ttk.Checkbutton(frame, variable=var, text=name, offvalue=0, onvalue=val, command=self.recompile)
            box.pack(side=tk.LEFT)
            self.boxes.append(box)
            self.vars.append(var)

    def get_flags(self):
        flags = 0
        for var in self.vars:
            flags = flags | var.get()
        return flags

    def recompile(self, event=None):
        try:
            self.compiled = re.compile(self.regex_display.get(), self.get_flags())
            bg = self.prompt_display['background']
            self.status_display.config(text="", background=bg)
        except re.error as msg:
            self.compiled = None
            self.status_display.config(text="re.error: %s" % str(msg), background="red")
        self.reevaluate()

    def reevaluate(self, event=None):
        try:
            self.string_display.tag_remove("hit", "1.0", tk.END)
        except tk.TclError:
            pass
        try:
            self.string_display.tag_remove("hit0", "1.0", tk.END)
        except tk.TclError:
            pass
        self.group_list.delete(0, tk.END)
        if not self.compiled:
            return
        self.string_display.tag_configure("hit", background="yellow")
        self.string_display.tag_configure("hit0", background="orange")
        text = self.string_display.get("1.0", tk.END)
        last = 0
        nmatches = 0
        while last <= len(text):
            m = self.compiled.search(text, last)
            if m is None:
                break
            first, last = m.span()
            if last == first:
                last = first+1
                tag = "hit0"
            else:
                tag = "hit"
            pfirst = "1.0 + %d chars" % first
            plast = "1.0 + %d chars" % last
            self.string_display.tag_add(tag, pfirst, plast)
            if nmatches == 0:
                self.string_display.yview_pickplace(pfirst)
                groups = list(m.groups())
                groups.insert(0, m.group())
                for i in range(len(groups)):
                    g = "%2d: %s" % (i, `groups[i]`)
                    self.group_list.insert(tk.END, g)
            nmatches = nmatches + 1
            if self.show_var.get() == "first":
                break

        if nmatches == 0:
            self.status_display.config(text="(no match)", background="yellow")
        else:
            self.status_display.config(text="")

# Main function, run when invoked as a stand-alone Python program.

def main():
    root = tk.Tk()
    demo = ReDemo(root)
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.mainloop()

if __name__ == '__main__':
    main()