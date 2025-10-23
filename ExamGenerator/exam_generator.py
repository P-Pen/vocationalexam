"""
电子试卷生成工具 - 主程序
支持生成单选题、选择填空题、操作题等多种题型
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import json
import shutil
from pathlib import Path
from html_template import HTMLTemplate


class ExamGeneratorGUI:
    """电子试卷生成工具GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("电子试卷生成工具 v1.0")
        self.root.geometry("1200x800")
        
        # 题目列表
        self.questions = []
        self.groups = []
        
        # 当前项目文件路径（用于自动保存）
        self.current_project_file = None
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        """创建界面组件"""
        
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="电子试卷生成工具", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # 左侧面板 - 题目列表
        left_frame = ttk.LabelFrame(main_frame, text="题目列表", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 题目列表框
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.question_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                          width=30, height=25)
        self.question_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.question_listbox.yview)
        
        self.question_listbox.bind('<<ListboxSelect>>', self.on_question_select)
        
        # 列表操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="▲ 上移", command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="▼ 下移", command=self.move_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除", command=self.delete_question).pack(side=tk.LEFT, padx=2)
        
        # 中间面板 - 题目编辑
        middle_frame = ttk.LabelFrame(main_frame, text="题目编辑", padding="10")
        middle_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        middle_frame.columnconfigure(1, weight=1)
        
        # 题目类型选择
        ttk.Label(middle_frame, text="题目类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.question_type = tk.StringVar(value="single")
        type_frame = ttk.Frame(middle_frame)
        type_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(type_frame, text="单选题", variable=self.question_type, 
                       value="single", command=self.on_type_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="选择填空题", variable=self.question_type, 
                       value="choice", command=self.on_type_change).pack(side=tk.LEFT, padx=5)
        # 合并C语言和PS为通用的文件操作题（file）
        ttk.Radiobutton(type_frame, text="文件操作题", variable=self.question_type,
                       value="file", command=self.on_type_change).pack(side=tk.LEFT, padx=5)
        
        # 题目编号
        ttk.Label(middle_frame, text="题目编号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.question_number = tk.StringVar()
        ttk.Entry(middle_frame, textvariable=self.question_number, width=10).grid(
            row=1, column=1, sticky=tk.W, pady=5)
        
        # 题干输入
        ttk.Label(middle_frame, text="题干内容:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        self.question_text = scrolledtext.ScrolledText(middle_frame, width=60, height=8)
        self.question_text.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 题干图片（可选）
        ttk.Label(middle_frame, text="题干图片:").grid(row=3, column=0, sticky=tk.W, pady=5)
        image_frame = ttk.Frame(middle_frame)
        image_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.question_image = tk.StringVar()
        ttk.Entry(image_frame, textvariable=self.question_image).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_frame, text="浏览", command=self.browse_question_image).pack(side=tk.LEFT, padx=5)
        ttk.Label(image_frame, text="（可选）图片将保存到static目录", 
                 foreground="gray").pack(side=tk.LEFT, padx=5)
        
        # 选项容器（动态显示）
        self.options_frame = ttk.LabelFrame(middle_frame, text="选项设置", padding="5")
        self.options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.option_vars = {}
        self.create_option_fields()
        
        # 代码区域（可选）
        ttk.Label(middle_frame, text="代码区域:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        code_frame = ttk.Frame(middle_frame)
        code_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.code_text = scrolledtext.ScrolledText(code_frame, width=60, height=6)
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(code_frame, text="（可选）单选题可添加代码示例", 
                 foreground="gray").pack(anchor=tk.W)
        
        # 添加/更新按钮
        btn_frame2 = ttk.Frame(middle_frame)
        btn_frame2.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame2, text="添加题目", command=self.add_question).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="更新题目", command=self.update_question).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="清空表单", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        
        # 右侧面板 - 分组设置和生成
        right_frame = ttk.LabelFrame(main_frame, text="试卷设置", padding="10")
        right_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 试卷信息
        ttk.Label(right_frame, text="考试说明:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        self.tips_text = scrolledtext.ScrolledText(right_frame, width=35, height=8)
        self.tips_text.pack(fill=tk.X, pady=5)
        self.tips_text.insert("1.0", "1.考试时长：60分钟。\n2.考试模块：C语言程序设计、图形图像设计\n")
        
        # 分组设置
        ttk.Label(right_frame, text="题目分组:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        group_frame = ttk.Frame(right_frame)
        group_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(group_frame, text="分组名称:").pack(anchor=tk.W)
        self.group_name = tk.StringVar()
        ttk.Entry(group_frame, textvariable=self.group_name, width=30).pack(fill=tk.X, pady=2)
        
        ttk.Label(group_frame, text="题目数量:").pack(anchor=tk.W)
        self.group_count = tk.StringVar()
        ttk.Entry(group_frame, textvariable=self.group_count, width=30).pack(fill=tk.X, pady=2)
        
        ttk.Button(group_frame, text="添加分组", command=self.add_group).pack(fill=tk.X, pady=5)
        
        # 分组列表
        self.group_listbox = tk.Listbox(right_frame, height=6)
        self.group_listbox.pack(fill=tk.X, pady=5)
        
        ttk.Button(right_frame, text="删除分组", command=self.delete_group).pack(fill=tk.X, pady=2)
        
        # 生成按钮
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(right_frame, text="📁 选择输出目录", command=self.select_output_dir).pack(fill=tk.X, pady=5)
        
        self.output_dir = tk.StringVar(value="./output")
        ttk.Label(right_frame, textvariable=self.output_dir, 
                 wraplength=250, foreground="blue").pack(fill=tk.X, pady=2)
        
        ttk.Button(right_frame, text="🚀 生成试卷", command=self.generate_exam, 
                  style="Accent.TButton").pack(fill=tk.X, pady=10)
        
        # 文件操作按钮
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(file_frame, text="💾 保存项目", command=self.save_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="📂 加载项目", command=self.load_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="📋 导入现有试卷", command=self.import_exam).pack(side=tk.LEFT, padx=5)
        
    def create_option_fields(self):
        """创建选项输入字段"""
        # 清空现有字段
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        question_type = self.question_type.get()
        
        if question_type == "single":
            # 单选题：4个选项
            self.option_vars = {}
            for i, opt in enumerate(['A', 'B', 'C', 'D']):
                ttk.Label(self.options_frame, text=f"选项{opt}:").grid(
                    row=i, column=0, sticky=tk.W, pady=2, padx=5)
                var = tk.StringVar()
                self.option_vars[opt] = var
                ttk.Entry(self.options_frame, textvariable=var, width=50).grid(
                    row=i, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
                    
        elif question_type == "choice":
            # 选择填空题
            ttk.Label(self.options_frame, text="填空数量:").grid(
                row=0, column=0, sticky=tk.W, pady=2, padx=5)
            self.blank_count = tk.StringVar(value="5")
            ttk.Entry(self.options_frame, textvariable=self.blank_count, width=10).grid(
                row=0, column=1, sticky=tk.W, pady=2, padx=5)
            
            ttk.Label(self.options_frame, text="每空分值:").grid(
                row=1, column=0, sticky=tk.W, pady=2, padx=5)
            self.blank_score = tk.StringVar(value="2")
            ttk.Entry(self.options_frame, textvariable=self.blank_score, width=10).grid(
                row=1, column=1, sticky=tk.W, pady=2, padx=5)
            
            ttk.Label(self.options_frame, text="备选项:").grid(
                row=2, column=0, sticky=tk.NW, pady=2, padx=5)
            self.choice_options = scrolledtext.ScrolledText(self.options_frame, width=50, height=8)
            self.choice_options.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            self.choice_options.insert("1.0", "A、选项1\nB、选项2\nC、选项3\n")
            
        elif question_type == "file":
            # 通用文件操作题（可用于C语言或PS类操作题）
            ttk.Label(self.options_frame, text="要打开的文件:").grid(
                row=0, column=0, sticky=tk.W, pady=2, padx=5)
            self.open_file = tk.StringVar()
            entry_frame0 = ttk.Frame(self.options_frame)
            entry_frame0.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            ttk.Entry(entry_frame0, textvariable=self.open_file).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(entry_frame0, text="浏览", command=self.browse_open_file).pack(side=tk.LEFT, padx=5)
            ttk.Label(entry_frame0, text="（如：prog.c、作品.psd、文档.docx）", 
                     foreground="gray").pack(side=tk.LEFT, padx=5)
            
            ttk.Label(self.options_frame, text="素材文件夹 (可选):").grid(
                row=1, column=0, sticky=tk.W, pady=2, padx=5)
            self.material_folder = tk.StringVar()
            entry_frame = ttk.Frame(self.options_frame)
            entry_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            ttk.Entry(entry_frame, textvariable=self.material_folder).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(entry_frame, text="浏览", command=self.browse_material).pack(side=tk.LEFT, padx=5)

            # 可选：样图（PS）
            ttk.Label(self.options_frame, text="样图文件 (可选):").grid(
                row=2, column=0, sticky=tk.W, pady=2, padx=5)
            self.sample_image = tk.StringVar()
            entry_frame2 = ttk.Frame(self.options_frame)
            entry_frame2.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            ttk.Entry(entry_frame2, textvariable=self.sample_image).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(entry_frame2, text="浏览", command=self.browse_sample).pack(side=tk.LEFT, padx=5)

            # 可选：prog.c 模板（C语言）
            ttk.Label(self.options_frame, text="prog.c 模板 (可选):").grid(
                row=3, column=0, sticky=tk.W, pady=2, padx=5)
            self.prog_template = tk.StringVar()
            entry_frame3 = ttk.Frame(self.options_frame)
            entry_frame3.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            ttk.Entry(entry_frame3, textvariable=self.prog_template).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(entry_frame3, text="浏览", command=self.browse_prog_template).pack(side=tk.LEFT, padx=5)
    
    def on_type_change(self):
        """题目类型改变时重新创建选项字段"""
        self.create_option_fields()
    
    def add_question(self):
        """添加题目"""
        question_type = self.question_type.get()
        number = self.question_number.get().strip()
        text = self.question_text.get("1.0", tk.END).strip()
        
        if not number or not text:
            messagebox.showwarning("警告", "请填写题目编号和题干内容！")
            return
        
        question = {
            'type': question_type,
            'number': number,
            'text': text,
            'code': self.code_text.get("1.0", tk.END).strip(),
            'question_image': self.question_image.get().strip()
        }
        
        if question_type == "single":
            question['options'] = {k: v.get() for k, v in self.option_vars.items()}
            if not all(question['options'].values()):
                messagebox.showwarning("警告", "请填写所有选项！")
                return
                
        elif question_type == "choice":
            question['blank_count'] = self.blank_count.get()
            question['blank_score'] = self.blank_score.get()
            question['choice_options'] = self.choice_options.get("1.0", tk.END).strip()
            
        elif question_type == "file":
            question['open_file'] = getattr(self, 'open_file', tk.StringVar()).get().strip()
            question['material_folder'] = self.material_folder.get()
            question['sample_image'] = getattr(self, 'sample_image', tk.StringVar()).get()
            question['prog_template'] = getattr(self, 'prog_template', tk.StringVar()).get()
        
        self.questions.append(question)
        self.update_question_list()
        self.clear_form()
        messagebox.showinfo("成功", "题目已添加！")
    
    def update_question(self):
        """更新选中的题目"""
        selection = self.question_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要更新的题目！")
            return
        
        idx = selection[0]
        question_type = self.question_type.get()
        number = self.question_number.get().strip()
        text = self.question_text.get("1.0", tk.END).strip()
        
        if not number or not text:
            messagebox.showwarning("警告", "请填写题目编号和题干内容！")
            return
        
        question = {
            'type': question_type,
            'number': number,
            'text': text,
            'code': self.code_text.get("1.0", tk.END).strip(),
            'question_image': self.question_image.get().strip()
        }
        
        if question_type == "single":
            question['options'] = {k: v.get() for k, v in self.option_vars.items()}
        elif question_type == "choice":
            question['blank_count'] = self.blank_count.get()
            question['blank_score'] = self.blank_score.get()
            question['choice_options'] = self.choice_options.get("1.0", tk.END).strip()
        elif question_type == "file":
            question['open_file'] = getattr(self, 'open_file', tk.StringVar()).get().strip()
            question['material_folder'] = self.material_folder.get()
            question['sample_image'] = getattr(self, 'sample_image', tk.StringVar()).get()
            question['prog_template'] = getattr(self, 'prog_template', tk.StringVar()).get()
        
        self.questions[idx] = question
        self.update_question_list()
        messagebox.showinfo("成功", "题目已更新！")
    
    def delete_question(self):
        """删除选中的题目"""
        selection = self.question_listbox.curselection()
        if not selection:
            return
        
        if messagebox.askyesno("确认", "确定删除选中的题目吗？"):
            idx = selection[0]
            del self.questions[idx]
            self.update_question_list()
    
    def move_up(self):
        """上移题目"""
        selection = self.question_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        idx = selection[0]
        self.questions[idx], self.questions[idx-1] = self.questions[idx-1], self.questions[idx]
        self.update_question_list()
        self.question_listbox.selection_set(idx-1)
    
    def move_down(self):
        """下移题目"""
        selection = self.question_listbox.curselection()
        if not selection or selection[0] == len(self.questions) - 1:
            return
        
        idx = selection[0]
        self.questions[idx], self.questions[idx+1] = self.questions[idx+1], self.questions[idx]
        self.update_question_list()
        self.question_listbox.selection_set(idx+1)
    
    def update_question_list(self):
        """更新题目列表显示"""
        self.question_listbox.delete(0, tk.END)
        for q in self.questions:
            type_name = {
                'single': '单选',
                'choice': '填空',
                'file': '文件'
            }.get(q['type'], '未知')
            self.question_listbox.insert(tk.END, f"({q['number']}) [{type_name}] {q['text'][:30]}...")
    
    def on_question_select(self, event):
        """题目选中时加载到编辑区"""
        selection = self.question_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        q = self.questions[idx]
        
        self.question_type.set(q['type'])
        self.on_type_change()
        
        self.question_number.set(q['number'])
        self.question_text.delete("1.0", tk.END)
        self.question_text.insert("1.0", q['text'])
        
        self.question_image.set(q.get('question_image', ''))
        
        self.code_text.delete("1.0", tk.END)
        if q.get('code'):
            self.code_text.insert("1.0", q['code'])
        
        if q['type'] == 'single':
            for k, v in q['options'].items():
                if k in self.option_vars:
                    self.option_vars[k].set(v)
        elif q['type'] == 'choice':
            self.blank_count.set(q.get('blank_count', ''))
            self.blank_score.set(q.get('blank_score', ''))
            self.choice_options.delete("1.0", tk.END)
            self.choice_options.insert("1.0", q.get('choice_options', ''))
        elif q['type'] == 'file':
            self.open_file.set(q.get('open_file', ''))
            self.material_folder.set(q.get('material_folder', ''))
            self.sample_image.set(q.get('sample_image', ''))
            self.prog_template.set(q.get('prog_template', ''))
    
    def clear_form(self):
        """清空表单"""
        self.question_number.set('')
        self.question_text.delete("1.0", tk.END)
        self.question_image.set('')
        self.code_text.delete("1.0", tk.END)
        
        if hasattr(self, 'option_vars'):
            for var in self.option_vars.values():
                var.set('')
    
    def add_group(self):
        """添加分组"""
        name = self.group_name.get().strip()
        count = self.group_count.get().strip()
        
        if not name or not count:
            messagebox.showwarning("警告", "请填写分组名称和题目数量！")
            return
        
        try:
            count_int = int(count)
            if count_int <= 0:
                raise ValueError("题目数量必须大于0")
        except ValueError as e:
            messagebox.showerror("错误", f"题目数量必须是正整数！\n{str(e)}")
            return
        
        self.groups.append({'name': name, 'count': count})
        self.update_group_list()
        self.group_name.set('')
        self.group_count.set('')
        messagebox.showinfo("成功", f"已添加分组：{name}")
    
    def delete_group(self):
        """删除分组"""
        selection = self.group_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        del self.groups[idx]
        self.update_group_list()
    
    def update_group_list(self):
        """更新分组列表显示"""
        self.group_listbox.delete(0, tk.END)
        for g in self.groups:
            self.group_listbox.insert(tk.END, f"{g['name']}----{g['count']}")
    
    def browse_material(self):
        """浏览素材文件夹"""
        folder = filedialog.askdirectory(title="选择素材文件夹")
        if folder:
            self.material_folder.set(folder)
    
    def browse_question_image(self):
        """浏览题干图片"""
        file = filedialog.askopenfilename(title="选择题干图片",
                                         filetypes=[("图片文件", "*.jpg *.png *.jpeg *.gif *.bmp")])
        if file:
            self.question_image.set(file)
    
    def browse_open_file(self):
        """浏览要打开的文件"""
        file = filedialog.askopenfilename(title="选择要打开的文件",
                                         filetypes=[
                                             ("所有文件", "*.*"),
                                             ("C文件", "*.c"),
                                             ("PSD文件", "*.psd"),
                                             ("Word文档", "*.doc *.docx"),
                                             ("Excel文件", "*.xls *.xlsx"),
                                             ("PPT文件", "*.ppt *.pptx")
                                         ])
        if file:
            self.open_file.set(file)
    
    def browse_sample(self):
        """浏览样图文件"""
        file = filedialog.askopenfilename(title="选择样图文件",
                                         filetypes=[("图片文件", "*.jpg *.png *.jpeg")])
        if file:
            self.sample_image.set(file)
    
    def browse_prog_template(self):
        """浏览prog.c模板文件"""
        file = filedialog.askopenfilename(title="选择prog.c模板文件",
                                         filetypes=[("C文件", "*.c"), ("所有文件", "*.*")])
        if file:
            self.prog_template.set(file)
    
    def select_output_dir(self):
        """选择输出目录"""
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_dir.set(folder)
    
    def generate_exam(self):
        """生成试卷"""
        if not self.questions:
            messagebox.showwarning("警告", "请先添加题目！")
            return
        
        output_dir = Path(self.output_dir.get())
        
        try:
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制static文件夹
            static_src = Path(__file__).parent / "static_template"
            static_dst = output_dir / "static"
            if static_src.exists():
                shutil.copytree(static_src, static_dst, dirs_exist_ok=True)
            else:
                messagebox.showwarning("警告", f"找不到static_template文件夹：{static_src}\n将继续生成，但可能缺少静态资源。")
            
            # 生成HTML文件
            template = HTMLTemplate()
            for i, q in enumerate(self.questions, 1):
                html_file = output_dir / f"{i:02d}.html"
                
                # 处理题干图片
                question_image_path = q.get('question_image', '')
                if question_image_path and Path(question_image_path).exists():
                    # 复制题干图片到static目录
                    if static_dst.exists():
                        img_ext = Path(question_image_path).suffix
                        img_name = f"question_{i:02d}{img_ext}"
                        shutil.copy2(question_image_path, static_dst / img_name)
                        # 在题干中添加图片HTML标签
                        question_text_with_img = q['text'] + f'\n\n<div class="row" style="margin-top: 10px;"><div class="col-md-6"><img class="img-responsive center-block" src="./static/{img_name}" alt="题干图片"></div></div>'
                    else:
                        question_text_with_img = q['text']
                else:
                    question_text_with_img = q['text']
                
                if q['type'] == 'single':
                    html_content = template.generate_single_choice(
                        number=q['number'],
                        question_text=question_text_with_img,
                        options=q['options'],
                        code=q.get('code', '')
                    )
                elif q['type'] == 'choice':
                    html_content = template.generate_fill_blank(
                        number=q['number'],
                        question_text=question_text_with_img,
                        code=q.get('code', ''),
                        choice_options=q.get('choice_options', '')
                    )
                elif q['type'] == 'file':
                    # 获取文件操作题的配置
                    material_folder = q.get('material_folder', '')
                    prog_template = q.get('prog_template', '')
                    sample_image = q.get('sample_image', '')
                    open_file_path = q.get('open_file', '').strip()  # 要自动打开的文件路径
                    
                    # 判断操作题类型
                    is_ps_operation = sample_image and Path(sample_image).exists()
                    is_c_operation = prog_template and Path(prog_template).exists()
                    
                    # 生成HTML
                    if is_ps_operation:
                        html_content = template.generate_ps_operation(question_text=question_text_with_img)
                    else:
                        html_content = template.generate_c_operation(question_text=question_text_with_img)
                    
                    # 创建题目文件夹
                    question_folder = output_dir / f"{i:02d}"
                    question_folder.mkdir(exist_ok=True)
                    
                    # 复制要打开的文件到题目文件夹
                    open_file_name = ""
                    if open_file_path and Path(open_file_path).exists():
                        open_file_name = Path(open_file_path).name
                        shutil.copy2(open_file_path, question_folder / open_file_name)
                    
                    # 如果是PS操作题
                    if is_ps_operation:
                        # 创建素材子文件夹
                        material_subfolder = question_folder / "素材"
                        material_subfolder.mkdir(exist_ok=True)
                        
                        # 复制样图到static文件夹
                        if static_dst.exists():
                            shutil.copy2(sample_image, static_dst / "example.jpg")
                        
                        # 复制素材文件到素材子文件夹
                        if material_folder and Path(material_folder).exists():
                            for file in Path(material_folder).iterdir():
                                if file.is_file():
                                    shutil.copy2(file, material_subfolder / file.name)
                    else:
                        # C语言或其他操作题：复制素材文件到题目文件夹根目录
                        if material_folder and Path(material_folder).exists():
                            for file in Path(material_folder).iterdir():
                                if file.is_file() and file.name != open_file_name:
                                    shutil.copy2(file, question_folder / file.name)
                    
                    # 生成config.dat文件
                    config_file = output_dir / f"{i:02d}-config.dat"
                    config_lines = []
                    
                    # 第一行：要自动打开的文件名（不是路径）
                    if open_file_name:
                        config_lines.append(f"{open_file_name}\n")
                    
                    # 添加素材文件列表（注意：样图在static目录，不需要在这里列出）
                    if material_folder and Path(material_folder).exists():
                        for file in Path(material_folder).iterdir():
                            if file.is_file() and file.name != open_file_name:
                                if is_ps_operation:
                                    config_lines.append(f"素材\\{file.name}\n")
                                else:
                                    config_lines.append(f"{file.name}\n")
                    
                    # 写入config文件
                    if config_lines:
                        with open(config_file, 'w', encoding='utf-8') as f:
                            f.writelines(config_lines)
                
                # 写入HTML文件
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 生成config文件（如果需要）
                if q['type'] == 'choice':
                    config_file = output_dir / f"{i:02d}-config.dat"
                    with open(config_file, 'w', encoding='utf-8') as f:
                        f.write(f"{q.get('blank_count', '5')}\n")
                        f.write(f"{q.get('blank_score', '2')}\n")
            
            # 生成groups-info.dat
            if self.groups:
                groups_file = output_dir / "groups-info.dat"
                with open(groups_file, 'w', encoding='utf-8') as f:
                    for g in self.groups:
                        f.write(f"{g['name']}----{g['count']}\n")
            
            # 生成question-type.dat
            types_file = output_dir / "question-type.dat"
            with open(types_file, 'w', encoding='utf-8') as f:
                for q in self.questions:
                    if q['type'] == 'single':
                        f.write("single\n")
                    elif q['type'] == 'choice':
                        f.write("choice\n")
                    elif q['type'] == 'file':
                        f.write("file\n")
            
            # 生成tips.txt
            tips_file = output_dir / "tips.txt"
            with open(tips_file, 'w', encoding='utf-8') as f:
                f.write(self.tips_text.get("1.0", tk.END))
            
            messagebox.showinfo("成功", f"试卷已成功生成到：\n{output_dir}")
            
            # 打开输出目录（跨平台）
            if messagebox.askyesno("提示", "是否打开输出目录？"):
                import platform
                system = platform.system()
                try:
                    if system == 'Windows':
                        os.startfile(output_dir)
                    elif system == 'Darwin':  # macOS
                        os.system(f'open "{output_dir}"')
                    else:  # Linux and others
                        os.system(f'xdg-open "{output_dir}"')
                except Exception as e:
                    messagebox.showwarning("提示", f"无法自动打开目录：{str(e)}\n请手动打开：{output_dir}")
                
        except Exception as e:
            messagebox.showerror("错误", f"生成试卷失败：\n{str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def save_project(self):
        """保存项目"""
        file = filedialog.asksaveasfilename(
            title="保存项目",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if not file:
            return
        
        project = {
            'questions': self.questions,
            'groups': self.groups,
            'tips': self.tips_text.get("1.0", tk.END)
        }
        
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
        
        messagebox.showinfo("成功", "项目已保存！")
    
    def load_project(self):
        """加载项目"""
        file = filedialog.askopenfilename(
            title="加载项目",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if not file:
            return
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                project = json.load(f)
            
            self.questions = project.get('questions', [])
            self.groups = project.get('groups', [])
            
            self.tips_text.delete("1.0", tk.END)
            self.tips_text.insert("1.0", project.get('tips', ''))
            
            self.update_question_list()
            self.update_group_list()
            
            messagebox.showinfo("成功", "项目已加载！")
        except Exception as e:
            messagebox.showerror("错误", f"加载项目失败：\n{str(e)}")
    
    def import_exam(self):
        """导入现有试卷"""
        folder = filedialog.askdirectory(title="选择现有试卷目录")
        if not folder:
            return
        
        try:
            folder_path = Path(folder)
            
            # 读取question-type.dat
            types_file = folder_path / "question-type.dat"
            if not types_file.exists():
                messagebox.showerror("错误", "找不到question-type.dat文件！")
                return
            
            with open(types_file, 'r', encoding='utf-8') as f:
                types = [line.strip() for line in f.readlines()]
            
            # 读取每个HTML文件
            self.questions = []
            for i, qtype in enumerate(types, 1):
                html_file = folder_path / f"{i:02d}.html"
                if not html_file.exists():
                    continue
                
                # 简单解析（这里只是示例，实际需要更复杂的解析）
                question = {
                    'type': qtype,
                    'number': str(i),
                    'text': '(导入的题目，请手动编辑)',
                    'code': ''
                }
                
                if qtype == 'single':
                    question['options'] = {'A': '', 'B': '', 'C': '', 'D': ''}
                elif qtype == 'choice':
                    # 读取config文件
                    config_file = folder_path / f"{i:02d}-config.dat"
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            question['blank_count'] = lines[0].strip() if len(lines) > 0 else '5'
                            question['blank_score'] = lines[1].strip() if len(lines) > 1 else '2'
                    question['choice_options'] = ''
                elif qtype == 'file':
                    # 检查是否有素材文件夹
                    material_folder = folder_path / f"{i:02d}"
                    if material_folder.exists():
                        question['material_folder'] = str(material_folder)
                    question['sample_image'] = ''
                    question['prog_template'] = ''
                
                self.questions.append(question)
            
            # 读取分组信息
            groups_file = folder_path / "groups-info.dat"
            if groups_file.exists():
                self.groups = []
                with open(groups_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '----' in line:
                            name, count = line.strip().split('----')
                            self.groups.append({'name': name, 'count': count})
            
            # 读取提示信息
            tips_file = folder_path / "tips.txt"
            if tips_file.exists():
                with open(tips_file, 'r', encoding='utf-8') as f:
                    self.tips_text.delete("1.0", tk.END)
                    self.tips_text.insert("1.0", f.read())
            
            self.update_question_list()
            self.update_group_list()
            
            messagebox.showinfo("成功", f"已导入 {len(self.questions)} 道题目！\n请检查并编辑题目内容。")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：\n{str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def on_closing(self):
        """窗口关闭时的处理"""
        if self.questions and messagebox.askyesno("确认", "是否在退出前保存项目？"):
            self.save_project()
        self.root.destroy()
    
    def validate_question(self, question):
        """验证题目数据的完整性"""
        if not question.get('number') or not question.get('text'):
            return False, "题目编号和题干不能为空"
        
        if question['type'] == 'single':
            if not all(question.get('options', {}).values()):
                return False, "单选题必须填写所有选项"
        elif question['type'] == 'choice':
            if not question.get('blank_count') or not question.get('blank_score'):
                return False, "选择填空题必须填写填空数量和分值"
            try:
                int(question['blank_count'])
                int(question['blank_score'])
            except ValueError:
                return False, "填空数量和分值必须是数字"
        elif question['type'] == 'file':
            if not question.get('material_folder') and not question.get('prog_template') and not question.get('sample_image'):
                return False, "文件操作题至少需要提供素材文件夹、prog.c模板或样图之一"
        
        return True, "验证通过"


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置主题样式
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ExamGeneratorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
