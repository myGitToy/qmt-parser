
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import tkinter as tk
from tkinter import Menu    # 导入菜单类


win = tk.Tk()
win.title("Python GUI")    # 添加标题


def _quit():
    """结束主事件循环"""
    win.quit()      # 关闭窗口
    win.destroy()   # 将所有的窗口小部件进行销毁，应该有内存回收的意思
    exit()

# 创建菜单栏功能
menuBar = Menu(win)
win.config(menu=menuBar)


# 创建一个名为File的菜单项
fileMenu = Menu(menuBar, tearoff=0)
menuBar.add_cascade(label="File", menu=fileMenu)

# 在菜单项File下面添加一个名为New的选项
fileMenu.add_command(label="New")

# 在两个菜单选项中间添加一条横线
fileMenu.add_separator()

# 在菜单项下面添加一个名为Exit的选项
fileMenu.add_command(label="Exit", command=_quit)

# 在菜单栏中创建一个名为Help的菜单项
helpMenu = Menu(menuBar, tearoff=0)
menuBar.add_cascade(label="Help", menu=helpMenu)

# 在菜单栏Help下添加一个名为About的选项
helpMenu.add_command(label="About")

win.mainloop()      # 进入主事件循环，当调用mainloop()时,窗口才会显示出来