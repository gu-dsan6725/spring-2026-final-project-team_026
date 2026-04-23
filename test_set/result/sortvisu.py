#!/usr/bin/env python

"""Sorting algorithms visualizer using tkinter.

This module is comprised of three ``components'':

- an array visualizer with methods that implement basic sorting
operations (compare, swap) as well as methods for ``annotating'' the
sorting algorithm (e.g. to show the pivot element);

- a number of sorting algorithms (currently quicksort, insertion sort,
selection sort and bubble sort, as well as a randomization function),
all using the array visualizer for its basic operations and with calls
to its annotation methods;

- and a ``driver'' class which can be used as a Grail applet or as a
stand-alone application.

"""

import tkinter as tk
from tkinter import ttk
import random

XGRID = 10
YGRID = 10
WIDTH = 6


class Array:

    def __init__(self, master, data=None):
        self.master = master
        self.frame = tk.Frame(self.master)
        self.frame.pack(fill=tk.X)
        self.label = tk.Label(self.frame)
        self.label.pack()
        self.canvas = tk.Canvas(self.frame)
        self.canvas.pack()
        self.report = tk.Label(self.frame)
        self.report.pack()
        self.left = tk.Canvas(self.canvas, width=2, height=20)
        self.left.place(x=0, y=0)
        self.right = tk.Canvas(self.canvas, width=2, height=20)
        self.right.place(x=0, y=0)
        self.pivot = tk.Canvas(self.canvas, width=2, height=20)
        self.pivot.place(x=0, y=0)
        self.items = []
        self.size = self.maxvalue = 0
        if data:
            self.setdata(data)

    def setdata(self, data):
        olditems = self.items
        self.items = []
        for item in olditems:
            item.delete()
        self.size = len(data)
        self.maxvalue = max(data)
        self.canvas.config(width=(self.size+1)*XGRID,
                           height=(self.maxvalue+1)*YGRID)
        for i in range(self.size):
            self.items.append(ArrayItem(self, i, data[i]))
        self.reset("Sort demo, size %d" % self.size)

    speed = "normal"

    def setspeed(self, speed):
        self.speed = speed

    def destroy(self):
        self.frame.destroy()

    in_mainloop = 0
    stop_mainloop = 0

    def cancel(self):
        self.stop_mainloop = 1
        if self.in_mainloop:
            self.master.quit()

    def step(self):
        if self.in_mainloop:
            self.master.quit()

    Cancelled = "Array.Cancelled"  # Exception

    def wait(self, msecs):
        if self.speed == "fastest":
            msecs = 0
        elif self.speed == "fast":
            msecs = msecs / 10
        elif self.speed == "single-step":
            msecs = 1000000000
        if not self.stop_mainloop:
            self.master.update()
            id = self.master.after(msecs, self.master.quit)
            self.in_mainloop = 1
            self.master.mainloop()
            self.master.after_cancel(id)
            self.in_mainloop = 0
        if self.stop_mainloop:
            self.stop_mainloop = 0
            self.message("Cancelled")
            raise Array.Cancelled

    def getsize(self):
        return self.size

    def show_partition(self, first, last):
        for i in range(self.size):
            item = self.items[i]
            if first <= i < last:
                item.item.config(fill='red')
            else:
                item.item.config(fill='orange')
        self.hide_left_right_pivot()

    def hide_partition(self):
        for i in range(self.size):
            item = self.items[i]
            item.item.config(fill='red')
        self.hide_left_right_pivot()

    def show_left(self, left):
        if not 0 <= left < self.size:
            self.hide_left()
            return
        x1, y1, x2, y2 = self.items[left].position()
        self.left.coords([(x1 - 2, 0), (x1 - 2, 9999)])
        self.master.update()

    def show_right(self, right):
        if not 0 <= right < self.size:
            self.hide_right()
            return
        x1, y1, x2, y2 = self.items[right].position()
        self.right.coords(((x2 + 2, 0), (x2 + 2, 9999)))
        self.master.update()

    def hide_left_right_pivot(self):
        self.hide_left()
        self.hide_right()
        self.hide_pivot()

    def hide_left(self):
        self.left.coords(((0, 0), (0, 0)))

    def hide_right(self):
        self.right.coords(((0, 0), (0, 0)))

    def show_pivot(self, pivot):
        x1, y1, x2, y2 = self.items[pivot].position()
        self.pivot.coords(((0, y1 - 2), (9999, y1 - 2)))

    def hide_pivot(self):
        self.pivot.coords(((0, 0), (0, 0)))

    def swap(self, i, j):
        if i == j: return
        self.countswap()
        item = self.items[i]
        other = self.items[j]
        self.items[i], self.items[j] = other, item
        item.swapwith(other)

    def compare(self, i, j):
        self.countcompare()
        item = self.items[i]
        other = self.items[j]
        return item.compareto(other)

    def reset(self, msg):
        self.ncompares = 0
        self.nswaps = 0
        self.message(msg)
        self.updatereport()
        self.hide_partition()

    def message(self, msg):
        self.label.config(text=msg)

    def countswap(self):
        self.nswaps = self.nswaps + 1
        self.updatereport()

    def countcompare(self):
        self.ncompares = self.ncompares + 1
        self.updatereport()

    def updatereport(self):
        text = "%d cmps, %d swaps" % (self.ncompares, self.nswaps)
        self.report.config(text=text)


class ArrayItem:

    def __init__(self, array, index, value):
        self.array = array
        self.index = index
        self.value = value
        x1, y1, x2, y2 = self.position()
        self.item = tk.Canvas(self.array.canvas, width=WIDTH, height=YGRID)
        self.item.place(x=x1, y=y1)
        self.item.bind('<Button-1>', self.mouse_down)
        self.item.bind('<Button1-Motion>', self.mouse_move)
        self.item.bind('<ButtonRelease-1>', self.mouse_up)

    def delete(self):
        item = self.item
        self.array = None
        self.item = None
        item.destroy()

    def mouse_down(self, event):
        self.lastx = event.x
        self.lasty = event.y
        self.origx = event.x
        self.origy = event.y
        self.item.lift()

    def mouse_move(self, event):
        self.item.move(event.x - self.lastx, event.y - self.lasty)
        self.lastx = event.x
        self.lasty = event.y

    def mouse_up(self, event):
        i = self.nearestindex(event.x)
        if i >= self.array.getsize():
            i = self.array.getsize() - 1
        if i < 0:
            i = 0
        other = self.array.items[i]
        here = self.index
        self.array.items[here], self.array.items[i] = other, self
        self.index = i
        x1, y1, x2, y2 = self.position()
        self.item.place(x=x1, y=y1)
        other.setindex(here)

    def setindex(self, index):
        nsteps = steps(self.index, index)
        if not nsteps: return
        if self.array.speed == "fastest":
            nsteps = 0
        oldpts = self.position()
        self.index = index
        newpts = self.position()
        trajectory = interpolate(oldpts, newpts, nsteps)
        self.item.lift()
        for pts in trajectory:
            self.item.place(x=pts[0], y=pts[1])
            self.array.wait(50)

    def swapwith(self, other):
        nsteps = steps(self.index, other.index)
        if not nsteps: return
        if self.array.speed == "fastest":
            nsteps = 0
        myoldpts = self.position()
        otheroldpts = other.position()
        self.index, other.index = other.index, self.index
        mynewpts = self.position()
        othernewpts = other.position()
        myfill = self.item['fill']
        otherfill = other.item['fill']
        self.item.config(fill='green')
        other.item.config(fill='yellow')
        self.array.master.update()
        if self.array.speed == "single-step":
            self.item.place(x=mynewpts[0], y=mynewpts[1])
            other.item.place(x=othernewpts[0], y=othernewpts[1])
            self.array.master.update()
            self.item.config(fill=myfill)
            other.item.config(fill=otherfill)
            self.array.wait(0)
            return
        mytrajectory = interpolate