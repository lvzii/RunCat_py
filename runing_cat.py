
#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
# @Author  : youshu.Ji

import glob
import itertools
import os
import sys
import time

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
if getattr(sys, 'frozen', False):
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
        self.wrapped_menu_options = self.create_wrapped_menu_requirement()
        self.refresh_icon()
        self.start_schedule()
        win32gui.PumpMessages()

    def start_schedule(self):
        interval_task = self.refresh_icon
        scheduler = BackgroundScheduler()
        scheduler.add_job(interval_task, "interval", seconds=0.2)
        scheduler.start()

    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)

    def execute_menu_option(self, id):
        menu_action = self.menu_id2action[id]
        if menu_action == 'quit':
            win32gui.DestroyWindow(self.hwnd)
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
        pass

    def show_menu(self):
        option_text, option_icon, option_action, option_id = self.wrapped_menu_options[0]
        # 创建菜单
        menu = win32gui.CreatePopupMenu()
        item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                        hbmpItem=option_icon,
                                                        wID=1024)
        win32gui.InsertMenuItem(menu, 0, 1, item)
        # 。。。
        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def create_wrapped_menu_requirement(self):
        # 明确有哪些菜单需求
        quit_option = ('Quit', None, "quit")
        # 包装成后面用的
        wrapped_menu_options = []
        option_text, option_icon, option_action = quit_option
        # 退出这类菜单需要一个进程号
        self.menu_id2action[1024] = option_action
        wrapped_menu_options.append([option_text, option_icon, option_action, 1024])
        return wrapped_menu_options

    def destroy(self, hwnd, msg, wparam, lparam):
        # 这里报错了，但是还是退出了 哈哈哈哈
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # Terminate the app.

    def create(self):
        # 创建window类的实例
        window_class = win32gui.WNDCLASS()
        window_class_name = 'cat'
        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): restart,
                       win32con.WM_DESTROY: self.destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER + 20: self.notify, }
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
        hwnd = win32gui.CreateWindow(classAtom,
                                     window_class_name,
                                     style,
                                     0,
                                     0,
                                     win32con.CW_USEDEFAULT,
                                     win32con.CW_USEDEFAULT,
                                     0,
                                     0,
                                     hinst,
                                     None)
        icon_flags = 16
        # 所有变换的图标都读出来
        hicons = [win32gui.LoadImage(hinst,
                                     next(self.icos),
                                     win32con.IMAGE_ICON,
                                     0,
                                     0,
                                     icon_flags) for i in range(5)]
        # 创建的窗口  图标
        return hwnd, hicons

    def refresh_icon(self):
        hover_text = 'running cat'
        hicon = self.hicons[self.ico_cycle_idx % 5]
        self.ico_cycle_idx += 1

        if self.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER + 20,
                          hicon,
                          hover_text)

        win32gui.Shell_NotifyIcon(message, self.notify_id)


if __name__ == '__main__':
    # r'C:\Users\starseeer\Downloads\RunCat_for_windows-master\RunCat\resources\cat\white\*.ico'

    config = {
        "path": os.path.join(app_path, 'cat\\*.ico')
    }
    icos = itertools.cycle(glob.glob(config["path"]))
    cat_runner = CatRun(config)
 