# coding: utf8

from tkinter import *
from tkinter import ttk
import tello
import cv2
from PIL import Image
from PIL import ImageTk

COLOR_BG = 'grey10'
COLOR_BUTTON = 'grey20'
COLOR_FONT = 'grey80'
FONT = ('Helvetica', 10, 'bold')


class GUI:
    def __init__(self):
        self.tello = tello.Tello()

        self.root = Tk()
        self.root.config(bg=COLOR_BG)

        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TButton', relief='flat', width=8, background=COLOR_BUTTON, foreground=COLOR_FONT, font=FONT)

        panel_width = self.tello.video_width
        panel_height = self.tello.video_heigth
        self.panel = Canvas(self.root,
                            width=panel_width,
                            height=panel_height,
                            highlightthickness=0)
        self.panel.grid(row=0, column=1, pady=5)
        self.img = self.panel.create_image(0, 0, image=None, anchor=NW)
        self.battery_text = self.panel.create_text(10, 10, text="", anchor=NW, font=FONT)
        self.baro_text = self.panel.create_text(10, 40, text="", anchor=NW, font=FONT)

        self.placeButtonXY()
        self.placeButtonZ()
        self.placeButtonLand()
        self.bindAction()
        ttk.Button(self.root, text="ALIGN", command=self.tello.align_with_face).grid()
        ttk.Button(self.root, text="STOP", command=self.tello.stop_align).grid()
        ttk.Button(self.root, text="QUIT", command=self.quit).grid()

        if not self.tello.isConnected:
            print("Drone is not connected")
            return

        self.update_video()

        self.root.mainloop()

    def update_video(self):
        self.panel.itemconfigure(self.battery_text, text="BATTERY : " + str(self.tello.battery) + '%')
        self.panel.itemconfigure(self.baro_text, text="BAROMETTER : " + str(self.tello.barometer))
        frame = self.tello.video_frame
        if frame is not None:
            img = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.panel.itemconfigure(self.img, image=img)
        self.panel.update()
        self.root.after(0, self.update_video)

    def placeButtonLand(self):
        ttk.Button(self.root, text="TAKEOFF", command=self.tello.takeoff).grid(column=1, sticky=EW, ipady=5, pady=5)
        ttk.Button(self.root, text="LAND", command=self.tello.land).grid(column=1, sticky=EW, ipady=5, pady=5)

    def placeButtonXY(self):
        frame = Frame(self.root, bg=COLOR_BG, bd=20)
        frame.grid(column=0, row=0)
        ttk.Button(frame, text="Forward", command=self.tello.forward).grid(column=1, ipady=22, padx=5, pady=5)
        ttk.Button(frame, text="Left", command=self.tello.right).grid(row=1, ipady=22, padx=5, pady=5)
        ttk.Button(frame, text="Right", command=self.tello.left).grid(row=1, column=3, ipady=22, padx=5, pady=5)
        ttk.Button(frame, text="Back", command=self.tello.back).grid(row=2, column=1, ipady=22, padx=5, pady=5)

    def placeButtonZ(self):
        frame = Frame(self.root, bg=COLOR_BG, bd=20)
        frame.grid(column=2, row=0)
        ttk.Button(frame, text="Up", command=self.tello.up).grid(column=1, ipady=22, padx=5, pady=5)
        ttk.Button(frame, text="Down", command=self.tello.down).grid(row=2, column=1, ipady=22, padx=5, pady=5)
        ttk.Button(frame, text="CW", command=self.tello.turn_right).grid(row=1, column=3, ipady=22, padx=5, pady=5)
        ttk.Button(frame, text="CCW", command=self.tello.turn_left).grid(row=1, ipady=22, padx=5, pady=5)

    def bindAction(self):
        self.root.bind('<space>', lambda event: self.tello.takeoff())
        self.root.bind('<Return>', lambda event: self.tello.land())

        self.root.bind('<Up>', lambda event: self.tello.up())
        self.root.bind('<Down>', lambda event: self.tello.down())
        self.root.bind('<Left>', lambda event: self.tello.turn_left())
        self.root.bind('<Right>', lambda event: self.tello.turn_right())

        self.root.bind('z', lambda event: self.tello.forward())
        self.root.bind('s', lambda event: self.tello.back())
        self.root.bind('q', lambda event: self.tello.left())
        self.root.bind('d', lambda event: self.tello.right())

    def quit(self):
        self.root.destroy()
        self.tello.disconect()


if __name__ == '__main__':
    Interface = GUI()
