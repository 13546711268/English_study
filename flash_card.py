"""
flash_card.py

这是一个使用 tkinter 编写的单词练习程序。
程序从 CSV 文件中加载单词和释义，并可以记录用户记住的单词进度。
支持 9 个列表（CSV 文件：vocabulary_csv/list1.csv ~ vocabulary_csv/list9.csv），用户可以在界面上选择使用哪个列表，
进度数据在 progress.json 中按列表分别保存。

主要功能：
- 从 CSV 文件加载单词数据；
- 从 progress.json 文件加载已记住单词进度（分列表记录）；
- 保存已记住单词进度到 progress.json 文件；
- 动态调整字体大小，保证单词和释义能完整显示；
- 键盘事件处理：
    - 回车键：
         若释义未显示，则显示释义（设置 revealed 为 True）；
         若释义已显示，则切换到下一单词（获取新单词）；
    - 空格键：标记当前单词为已记住，仅更新进度，不切换到下一个单词；
    - n 键：释义已显示时跳过当前单词（不记住）；
    - r 键：重置当前列表的进度；
    - R 键：重置所有列表的进度；
- 界面上增加两个按钮：
    - “更新”：清空当前列表已记住的单词；
    - “更新所有”：清空所有列表已记住的单词；
- 用户可通过下拉框选择要练习的列表。

作者：YueLi
日期：2025-03-10
"""

import tkinter as tk
from tkinter import font as tkFont, messagebox
import csv
import json
import os
import random

# ----------------- 数据加载与保存 -----------------

progress_file = "progress.json"
progress_data = {}  # 全局字典，记录所有列表的进度，格式 { "list1": [word1, ...], "list2": [...], ... }
current_list = "list1"  # 默认选择 list1

def load_words(filename):
    """
    从 CSV 文件中加载单词和释义。
    返回一个列表，每个元素为字典 {'word': 单词, 'definition': 释义}。
    """
    words = []
    if not os.path.exists(filename):
        print(f"文件 {filename} 未找到，请确认文件路径。")
        return words
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                word = row[0].strip()
                definition = row[1].strip() if len(row) > 1 else ''
                words.append({'word': word, 'definition': definition})
    except Exception as e:
        print("加载单词时出错:", e)
    return words

def load_progress():
    """
    从 progress.json 文件中加载所有列表的进度。
    返回一个字典，若文件不存在或加载失败，则返回空字典。
    如果加载的数据不是字典，则重置为字典格式。
    """
    global progress_data
    if os.path.exists(progress_file):
        try:
            loaded = json.load(open(progress_file, "r", encoding="utf-8"))
            # 如果加载的数据不是字典，则重置为{}
            if not isinstance(loaded, dict):
                progress_data = {}
            else:
                progress_data = loaded
        except Exception as e:
            print("加载进度出错:", e)
            progress_data = {}
    else:
        progress_data = {}
    # 确保当前列表在 progress_data 中
    if current_list not in progress_data:
        progress_data[current_list] = []
    return progress_data

def save_progress():
    """
    将进度字典保存到 progress.json 文件中。
    """
    try:
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("保存进度出错:", e)

# ----------------- 字体大小调整 -----------------

def adjust_font_size(text, available_width, available_height, family="Arial", initial_size=100):
    """
    根据文本内容以及可用宽度和高度，动态计算合适的字体大小，
    保证文本换行后能完整显示。
    """
    size = initial_size
    test_font = tkFont.Font(family=family, size=size)
    
    def get_wrapped_height(text, font, max_width):
        # 根据给定最大宽度，模拟文本换行并返回总高度
        lines = []
        current_line = ""
        for char in text:
            if font.measure(current_line + char) <= max_width:
                current_line += char
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
        return len(lines) * font.metrics("linespace")
    
    while size > 1:
        test_font.config(size=size)
        wrapped_height = get_wrapped_height(text, test_font, available_width)
        if wrapped_height <= available_height:
            return size
        size -= 1
    return size

# ----------------- 单词逻辑处理 -----------------

# 全局变量定义
words = []               # 当前列表所有单词列表
remembered_words = set() # 当前列表已记住单词集合
current = None           # 当前显示的单词（字典）
round_list = []          # 当前轮次中尚未展示的未记住单词列表
revealed = False         # 当前单词释义是否显示

def get_new_word():
    """
    获取下一单词：
    1. 过滤当前轮次中已记住的单词；
    2. 若本轮单词用完，则重新构造一个新的轮次；
    3. 更新全局变量 current。
    同时设置 revealed 状态为 False。
    """
    global current, round_list, words, remembered_words, revealed
    # 过滤掉已记住的单词
    round_list = [w for w in round_list if w['word'] not in remembered_words]
    if not round_list:
        # 新一轮：取所有未记住的单词并随机打乱顺序
        round_list = [w for w in words if w['word'] not in remembered_words]
        random.shuffle(round_list)
    if not round_list:
        current = None
    else:
        current = round_list.pop(0)
    revealed = False

# ----------------- 界面更新 -----------------

def update_display():
    """
    更新界面，显示：进度、单词及释义（根据 revealed 状态决定是否显示释义）。
    """
    if current is None:
        progress_label.config(text=f"记住: {len(remembered_words)} / 总: {len(words)}")
        word_label.config(text="全部单词已记住")
        def_label.config(text="")
    else:
        progress_label.config(text=f"记住: {len(remembered_words)} / 总: {len(words)}")
        word_label.config(text=current['word'])
        def_label.config(text=current['definition'] if revealed else "")

# ----------------- 键盘事件处理 -----------------

def on_key_press(event):
    """
    处理键盘事件：
    - q 键：退出程序；
    - 回车键：
         若释义未显示，则显示释义（设置 revealed 为 True）；
         若释义已显示，则切换到下一单词；
    - 空格键：将当前单词标记为已记住，仅更新进度，不切换到下一个单词；
    - n 键：释义已显示时跳过当前单词（不记住）；
    - r 键：重置当前列表的进度；
    - R 键：重置所有列表的进度。
    """
    global current, remembered_words, revealed, round_list, words, progress_data

    if event.keysym.lower() == 'q':
        root.destroy()
    elif event.keysym == 'Return':
        if current is None:
            return
        if not revealed:
            revealed = True
        else:
            get_new_word()
        update_display()
    elif event.keysym == 'space':
        if current is None:
            return
        remembered_words.add(current['word'])
        progress_data[current_list] = list(remembered_words)
        save_progress()
        update_display()
    elif event.char.lower() == 'n':
        if current is None:
            return
        if revealed:
            get_new_word()
            update_display()
    elif event.char == 'r':
        reset_current()
    elif event.char == 'R':
        reset_all()

# ----------------- 进度重置功能 -----------------

def reset_current():
    """
    清空当前列表的已记住单词。
    """
    global remembered_words, round_list
    if messagebox.askyesno("更新", "确定要清空当前列表的进度吗？"):
        remembered_words.clear()
        progress_data[current_list] = []
        save_progress()
        round_list = words.copy()
        random.shuffle(round_list)
        get_new_word()
        update_display()

def reset_all():
    """
    清空所有列表的已记住单词。
    """
    global remembered_words, round_list
    if messagebox.askyesno("更新所有", "确定要清空所有列表的进度吗？"):
        for key in progress_data.keys():
            progress_data[key] = []
        remembered_words.clear()
        save_progress()
        round_list = words.copy()
        random.shuffle(round_list)
        get_new_word()
        update_display()

# ----------------- 列表切换处理 -----------------

def on_list_change(new_value):
    """
    当用户通过下拉框选择不同列表时的回调函数。
    加载所选 CSV 文件和对应进度，并刷新显示。
    """
    global current_list, words, remembered_words, round_list
    current_list = new_value
    words = load_words(f"vocabulary_csv/{current_list}.csv")
    if current_list not in progress_data:
        progress_data[current_list] = []
    remembered_words = set(progress_data.get(current_list, []))
    round_list = [w for w in words if w['word'] not in remembered_words]
    random.shuffle(round_list)
    get_new_word()
    update_display()

# ----------------- 窗口调整处理 -----------------

def on_configure(event):
    """
    根据窗口大小动态调整字体：
    - 英语单词字体尺寸为合适大小的 1/2；
    - 汉语释义字体固定为英语单词字体的 40% 大小。
    """
    width = root.winfo_width()
    total_height = root.winfo_height()
    prog_height = progress_label.winfo_height() if progress_label.winfo_height() > 0 else 50
    avail_height = total_height - prog_height
    word_area = avail_height / 2

    word_text = word_label.cget("text") or "单词"
    computed_size = adjust_font_size(word_text, width, word_area, family="Arial", initial_size=100)
    new_word_size = max(10, int(computed_size * 0.5))
    word_font.config(size=new_word_size)
    def_font.config(size=max(10, int(new_word_size * 0.4)))

# ----------------- 主程序入口 -----------------

def main():
    global progress_file, root, progress_label, word_label, def_label, word_font, def_font
    global words, remembered_words, current, round_list, revealed, progress_data

    load_progress()  # 加载 progress_data 全局字典

    # 默认加载当前列表的单词和进度
    words[:] = load_words(f"vocabulary_csv/{current_list}.csv")
    remembered_words.update(set(progress_data.get(current_list, [])))
    round_list[:] = [w for w in words if w['word'] not in remembered_words]
    random.shuffle(round_list)
    get_new_word()

    # 创建 Tkinter 窗口
    global root
    root = tk.Tk()
    root.title("单词练习")
    initial_geometry = "700x400"  # 窗口稍大以容纳下拉框和按钮
    root.geometry(initial_geometry)

    # 添加列表选择的 OptionMenu
    list_options = [f"list{i}" for i in range(1, 10)]
    list_var = tk.StringVar(root)
    list_var.set(current_list)
    option_menu = tk.OptionMenu(root, list_var, *list_options, command=on_list_change)
    option_menu.config(font=("Arial", 14))
    option_menu.pack(pady=5)

    # 添加更新按钮的按钮组
    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)
    update_button = tk.Button(button_frame, text="更新", font=("Arial", 14), command=reset_current)
    update_button.pack(side=tk.LEFT, padx=10)
    update_all_button = tk.Button(button_frame, text="更新所有", font=("Arial", 14), command=reset_all)
    update_all_button.pack(side=tk.LEFT, padx=10)

    # 进度标签
    progress_font = tkFont.Font(family="Arial", size=20)
    global progress_label
    progress_label = tk.Label(root, text=f"记住: {len(remembered_words)} / 总: {len(words)}",
                              font=progress_font, anchor='center')
    progress_label.pack(fill='x')

    # 定义英语单词和汉语释义的字体
    global word_font, def_font
    word_font = tkFont.Font(family="Arial", size=100)
    def_font = tkFont.Font(family="Arial", size=20, weight="bold")  # 汉语释义加粗

    # 英语单词标签（上半部分），使用 wraplength 参数预设宽度为680
    global word_label
    word_label = tk.Label(root, text="", font=word_font, anchor='center', wraplength=680)
    word_label.pack(expand=True, fill='both')

    # 汉语释义标签（下半部分）
    global def_label
    def_label = tk.Label(root, text="", font=def_font, anchor='center', wraplength=680)
    def_label.pack(expand=True, fill='both')

    update_display()

    # 绑定键盘事件及窗口调整事件
    root.bind("<Key>", on_key_press)
    root.bind("<Configure>", on_configure)

    root.mainloop()

if __name__ == '__main__':
    main()