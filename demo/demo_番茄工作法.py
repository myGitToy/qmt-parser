import tkinter as tk
from tkinter import messagebox
import time
import winsound
class PomodoroTimer:
    def __init__(self, master):
        self.master = master
        self.master.title("番茄工作法计时器")
        self.time_left = 1 * 60  # 25分钟
        self.timer_running = False

        self.label = tk.Label(master, text=self.time_to_str(), font=("Helvetica", 48))
        self.label.pack()

        self.start_button = tk.Button(master, text="开始", command=self.start_timer)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="停止", command=self.stop_timer)
        self.stop_button.pack()

    def time_to_str(self):
        return f"{self.time_left // 60:02d}:{self.time_left % 60:02d}"

    def update_timer(self):
        if self.timer_running and self.time_left > 0:
            self.time_left -= 1
            self.label.config(text=self.time_to_str())
            self.master.after(1000, self.update_timer)
        elif self.time_left == 0:
            #播放指定的音乐
            winsound.Beep(1000, 5000) 
            messagebox.showinfo("时间到", "休息一下吧！")

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()

    def stop_timer(self):
        self.timer_running = False

root = tk.Tk()
timer = PomodoroTimer(root)
root.mainloop()