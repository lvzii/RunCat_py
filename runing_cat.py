#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
# @Author  : youshu.Ji

import glob
import itertools
import os
import psutil
import sys
import time

try:
    import GPUtil
    has_gpu = True
except ImportError:
    has_gpu = False

import win32con
import win32gui
import win32gui_struct
from apscheduler.schedulers.background import BackgroundScheduler

# 一套实现逻辑是不用阻塞，通过sleep实现刷新，这个没法添加quit功能
# 另一套逻辑是阻塞，用定时任务实现刷新
"""
变量名缩写   wnd=window

"""

# if hasattr(sys, '_MEIPASS'):
#   app_path = os.path.dirname(os.path.realpath(sys.executable))
# else:
#   app_path, filename = os.path.split(os.path.abspath( __file__))

# 打包成exe需要这样
if getattr(sys, "frozen", False):
    app_path = sys._MEIPASS
else:
    app_path = os.path.dirname(os.path.abspath(__file__))


# app_path = os.path.dirname(__file__)
def restart():
    pass


def destroy():
    win32gui.PostQuitMessage(0)  # Terminate the app.


class CatRun(object):
    def __init__(self, config):
        self.notify_id = None
        self.icos = itertools.cycle(glob.glob(config["path"]))
        self.ico_cycle_idx = 0
        self.hwnd, self.hicons = self.create()
        self.menu_id2action = {}
        self.mode = "cpu"  # 新增，默认模式为cpu
        self.wrapped_menu_options = self.create_wrapped_menu_requirement()
        self.refresh_interval = 0.2  # 初始刷新间隔
        self.scheduler = BackgroundScheduler()
        self.refresh_icon_job = None
        self.refresh_icon()
        self.start_schedule()
        win32gui.PumpMessages()

    def start_schedule(self):
        self.scheduler.add_job(self.update_refresh_interval, "interval", seconds=1)
        self.refresh_icon_job = self.scheduler.add_job(self.refresh_icon, "interval", seconds=self.refresh_interval)
        self.scheduler.start()

    def update_refresh_interval(self):
        if self.mode == "cpu":
            util = psutil.cpu_percent(interval=None)
        elif self.mode == "gpu" and has_gpu:
            gpus = GPUtil.getGPUs()
            util = max([gpu.load * 100 for gpu in gpus]) if gpus else 0
        else:
            util = 0
        # 设定刷新间隔，利用率高时更快，低时更慢
        interval = 1.0 - (util * 0.009)
        interval = max(0.1, min(1.0, interval)) / 5
        print(f"{self.mode.upper()}利用率: {util:.1f}%, interval: {interval:.3f}")

        if abs(interval - self.refresh_interval) > 1e-3:
            self.refresh_interval = interval
            self.refresh_icon_job.reschedule(trigger="interval", seconds=self.refresh_interval)

    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)

    def execute_menu_option(self, id):
        menu_action = self.menu_id2action[id]
        if menu_action == "quit":
            win32gui.DestroyWindow(self.hwnd)
        elif menu_action == "switch_cpu":
            self.mode = "cpu"
            print("已切换为CPU模式")
        elif menu_action == "switch_gpu":
            self.mode = "gpu"
            print("已切换为GPU模式")
        else:
            menu_action(self)

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONDBLCLK:
            self.execute_menu_option(1024)
        elif lparam == win32con.WM_RBUTTONUP:
            self.show_menu()
        elif lparam == win32con.WM_LBUTTONUP:
            pass
        return True

    def create_menu(self):
        menu = win32gui.CreatePopupMenu()
        # Quit
        item_quit, _ = win32gui_struct.PackMENUITEMINFO(text="Quit", wID=1024)
        win32gui.InsertMenuItem(menu, 0, 1, item_quit)
        # 切换CPU
        item_cpu, _ = win32gui_struct.PackMENUITEMINFO(text="切换为CPU占用", wID=1025)
        win32gui.InsertMenuItem(menu, 1, 1, item_cpu)
        # 切换GPU
        if has_gpu:
            item_gpu, _ = win32gui_struct.PackMENUITEMINFO(text="切换为GPU占用", wID=1026)
            win32gui.InsertMenuItem(menu, 2, 1, item_gpu)
        return menu

    def show_menu(self):
        menu = self.create_menu()
        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def create_wrapped_menu_requirement(self):
        wrapped_menu_options = []
        self.menu_id2action[1024] = "quit"
        self.menu_id2action[1025] = "switch_cpu"
        if has_gpu:
            self.menu_id2action[1026] = "switch_gpu"
        return wrapped_menu_options

    def destroy(self, hwnd, msg, wparam, lparam):
        # 这里报错了，但是还是退出了 哈哈哈哈
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # Terminate the app.

    def create(self):
        # 创建window类的实例
        window_class = win32gui.WNDCLASS()
        window_class_name = "cat"
        message_map = {
            win32gui.RegisterWindowMessage("TaskbarCreated"): restart,
            win32con.WM_DESTROY: self.destroy,
            win32con.WM_COMMAND: self.command,
            win32con.WM_USER + 20: self.notify,
        }
        # 实例的一系列属性
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map  # could also specify a wndproc.
        # 用window实例，注册一个window类
        classAtom = win32gui.RegisterClass(window_class)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        # 创建窗口
        hwnd = win32gui.CreateWindow(
            classAtom, window_class_name, style, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, hinst, None
        )
        icon_flags = 16
        # 所有变换的图标都读出来
        hicons = [win32gui.LoadImage(hinst, next(self.icos), win32con.IMAGE_ICON, 0, 0, icon_flags) for i in range(5)]
        # 创建的窗口  图标
        return hwnd, hicons

    def refresh_icon(self):
        hover_text = "running cat"
        hicon = self.hicons[self.ico_cycle_idx % 5]
        self.ico_cycle_idx += 1

        if self.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD
        self.notify_id = (
            self.hwnd,
            0,
            win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
            win32con.WM_USER + 20,
            hicon,
            hover_text,
        )

        win32gui.Shell_NotifyIcon(message, self.notify_id)


if __name__ == "__main__":
    # r'C:\Users\starseeer\Downloads\RunCat_for_windows-master\RunCat\resources\cat\white\*.ico'

    config = {"path": os.path.join(app_path, "cat\\*.ico")}
    icos = itertools.cycle(glob.glob(config["path"]))
    cat_runner = CatRun(config)
