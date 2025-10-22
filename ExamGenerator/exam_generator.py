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
        
        # 创建界面
        self.create_widgets()
        
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
        ttk.Radiobutton(type_frame, text="C语言操作题", variable=self.question_type, 
                       value="c_file", command=self.on_type_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="PS操作题", variable=self.question_type, 
                       value="ps_file", command=self.on_type_change).pack(side=tk.LEFT, padx=5)
        
        # 题目编号
        ttk.Label(middle_frame, text="题目编号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.question_number = tk.StringVar()
        ttk.Entry(middle_frame, textvariable=self.question_number, width=10).grid(
            row=1, column=1, sticky=tk.W, pady=5)
        
        # 题干输入
        ttk.Label(middle_frame, text="题干内容:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        self.question_text = scrolledtext.ScrolledText(middle_frame, width=60, height=8)
        self.question_text.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 选项容器（动态显示）
        self.options_frame = ttk.LabelFrame(middle_frame, text="选项设置", padding="5")
        self.options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.option_vars = {}
        self.create_option_fields()
        
        # 代码区域（可选）
        ttk.Label(middle_frame, text="代码区域:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        code_frame = ttk.Frame(middle_frame)
        code_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.code_text = scrolledtext.ScrolledText(code_frame, width=60, height=6)
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(code_frame, text="（可选）单选题可添加代码示例", 
                 foreground="gray").pack(anchor=tk.W)
        
        # 添加/更新按钮
        btn_frame2 = ttk.Frame(middle_frame)
        btn_frame2.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame2, text="添加题目", command=self.add_question,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="更新题目", command=self.update_question).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="清空表单", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        
        # 右侧面板 - 分组设置和生成
        right_frame = ttk.LabelFrame(main_frame, text="试卷设置", padding="10")
        right_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 试卷信息
        ttk.Label(right_frame, text="考试说明:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        self.tips_text = scrolledtext.ScrolledText(right_frame, width=35, height=10)
        self.tips_text.pack(fill=tk.BOTH, pady=5)
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
        self.group_listbox = tk.Listbox(right_frame, height=8)
        self.group_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Button(right_frame, text="删除分组", command=self.delete_group).pack(fill=tk.X, pady=2)
        
        # 生成按钮
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(right_frame, text="📁 选择输出目录", command=self.select_output_dir,
                  style="Accent.TButton").pack(fill=tk.X, pady=5)
        
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
            
        elif question_type in ["c_file", "ps_file"]:
            # 操作题
            ttk.Label(self.options_frame, text="素材文件夹:").grid(
                row=0, column=0, sticky=tk.W, pady=2, padx=5)
            self.material_folder = tk.StringVar()
            entry_frame = ttk.Frame(self.options_frame)
            entry_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            ttk.Entry(entry_frame, textvariable=self.material_folder).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(entry_frame, text="浏览", command=self.browse_material).pack(side=tk.LEFT, padx=5)
            
            if question_type == "ps_file":
                ttk.Label(self.options_frame, text="样图文件:").grid(
                    row=1, column=0, sticky=tk.W, pady=2, padx=5)
                self.sample_image = tk.StringVar()
                entry_frame2 = ttk.Frame(self.options_frame)
                entry_frame2.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
                ttk.Entry(entry_frame2, textvariable=self.sample_image).pack(side=tk.LEFT, fill=tk.X, expand=True)
                ttk.Button(entry_frame2, text="浏览", command=self.browse_sample).pack(side=tk.LEFT, padx=5)
    
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
            'code': self.code_text.get("1.0", tk.END).strip()
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
            
        elif question_type in ["c_file", "ps_file"]:
            question['material_folder'] = self.material_folder.get()
            if question_type == "ps_file":
                question['sample_image'] = self.sample_image.get()
        
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
            'code': self.code_text.get("1.0", tk.END).strip()
        }
        
        if question_type == "single":
            question['options'] = {k: v.get() for k, v in self.option_vars.items()}
        elif question_type == "choice":
            question['blank_count'] = self.blank_count.get()
            question['blank_score'] = self.blank_score.get()
            question['choice_options'] = self.choice_options.get("1.0", tk.END).strip()
        elif question_type in ["c_file", "ps_file"]:
            question['material_folder'] = self.material_folder.get()
            if question_type == "ps_file":
                question['sample_image'] = self.sample_image.get()
        
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
                'c_file': 'C语言',
                'ps_file': 'PS'
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
        elif q['type'] in ['c_file', 'ps_file']:
            self.material_folder.set(q.get('material_folder', ''))
            if q['type'] == 'ps_file':
                self.sample_image.set(q.get('sample_image', ''))
    
    def clear_form(self):
        """清空表单"""
        self.question_number.set('')
        self.question_text.delete("1.0", tk.END)
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
            int(count)
        except:
            messagebox.showerror("错误", "题目数量必须是数字！")
            return
        
        self.groups.append({'name': name, 'count': count})
        self.update_group_list()
        self.group_name.set('')
        self.group_count.set('')
    
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
    
    def browse_sample(self):
        """浏览样图文件"""
        file = filedialog.askopenfilename(title="选择样图文件",
                                         filetypes=[("图片文件", "*.jpg *.png *.jpeg")])
        if file:
            self.sample_image.set(file)
    
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
            
            # 生成HTML文件
            template = HTMLTemplate()
            for i, q in enumerate(self.questions, 1):
                html_file = output_dir / f"{i:02d}.html"
                
                if q['type'] == 'single':
                    html_content = template.generate_single_choice(
                        number=q['number'],
                        question_text=q['text'],
                        options=q['options'],
                        code=q.get('code', '')
                    )
                elif q['type'] == 'choice':
                    html_content = template.generate_fill_blank(
                        number=q['number'],
                        question_text=q['text'],
                        code=q.get('code', ''),
                        choice_options=q.get('choice_options', '')
                    )
                elif q['type'] == 'c_file':
                    html_content = template.generate_c_operation(
                        question_text=q['text']
                    )
                    # 复制素材
                    if q.get('material_folder'):
                        material_src = Path(q['material_folder'])
                        material_dst = output_dir / f"{i:02d}"
                        if material_src.exists():
                            shutil.copytree(material_src, material_dst, dirs_exist_ok=True)
                elif q['type'] == 'ps_file':
                    html_content = template.generate_ps_operation(
                        question_text=q['text']
                    )
                    # 复制素材
                    if q.get('material_folder'):
                        material_src = Path(q['material_folder'])
                        material_dst = output_dir / f"{i:02d}"
                        if material_src.exists():
                            shutil.copytree(material_src, material_dst, dirs_exist_ok=True)
                    # 复制样图
                    if q.get('sample_image'):
                        sample_src = Path(q['sample_image'])
                        if sample_src.exists():
                            shutil.copy2(sample_src, static_dst / "example.jpg")
                
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 生成config文件（如果需要）
                if q['type'] == 'choice':
                    config_file = output_dir / f"{i:02d}-config.dat"
                    with open(config_file, 'w', encoding='utf-8') as f:
                        f.write(f"{q.get('blank_count', '5')}\n")
                        f.write(f"{q.get('blank_score', '2')}\n")
                elif q['type'] == 'c_file':
                    config_file = output_dir / f"{i:02d}-config.dat"
                    with open(config_file, 'w', encoding='utf-8') as f:
                        f.write("prog.c\n")
                elif q['type'] == 'ps_file':
                    config_file = output_dir / f"{i:02d}-config.dat"
                    material_folder = Path(q.get('material_folder', ''))
                    with open(config_file, 'w', encoding='utf-8') as f:
                        f.write("样图.jpg\n")
                        f.write("作品.psd\n")
                        if material_folder.exists():
                            for file in material_folder.glob('*'):
                                if file.is_file():
                                    f.write(f"素材\\{file.name}\n")
            
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
                    elif q['type'] in ['c_file', 'ps_file']:
                        f.write("file\n")
            
            # 生成tips.txt
            tips_file = output_dir / "tips.txt"
            with open(tips_file, 'w', encoding='utf-8') as f:
                f.write(self.tips_text.get("1.0", tk.END))
            
            messagebox.showinfo("成功", f"试卷已成功生成到：\n{output_dir}")
            
            # 打开输出目录
            if messagebox.askyesno("提示", "是否打开输出目录？"):
                os.startfile(output_dir) if os.name == 'nt' else os.system(f'xdg-open "{output_dir}"')
                
        except Exception as e:
            messagebox.showerror("错误", f"生成试卷失败：\n{str(e)}")
    
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
                
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # 简单解析（这里只是示例，实际需要更复杂的解析）
                question = {
                    'type': qtype if qtype != 'file' else 'c_file',
                    'number': str(i),
                    'text': '(导入的题目，请手动编辑)',
                    'code': ''
                }
                
                if qtype == 'single':
                    question['options'] = {'A': '', 'B': '', 'C': '', 'D': ''}
                
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
