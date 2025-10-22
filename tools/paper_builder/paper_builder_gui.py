#!/usr/bin/env python3
"""GUI tool for generating exam papers using repository templates."""
from __future__ import annotations

import html
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


def load_template(name: str) -> str:
    from .template_library import TEMPLATE_REGISTRY

    try:
        return TEMPLATE_REGISTRY[name]
    except KeyError as exc:
        raise FileNotFoundError(
            f"Template '{name}' not found. Available templates: {sorted(TEMPLATE_REGISTRY)}"
        ) from exc


@dataclass
class Question:
    title: str
    prompt: str
    score: int

    def to_display(self) -> str:
        raise NotImplementedError

    def question_type(self) -> str:
        raise NotImplementedError

    def export(self, output_dir: Path, index: int) -> None:
        raise NotImplementedError


@dataclass
class SingleChoiceQuestion(Question):
    options: List[str]

    def question_type(self) -> str:
        return "single"

    def to_display(self) -> str:
        return f"单选题：{self.title or '未命名单选题'}（{self.score} 分）"

    def export(self, output_dir: Path, index: int) -> None:
        template = load_template("single.html")
        content = render_template(
            template,
            question_number=f"{index:02d}",
            title=self.title,
            prompt_html=format_multiline(self.prompt),
            score=str(self.score),
            options_json=json.dumps(self.options, ensure_ascii=False),
        )
        target = output_dir / f"{index:02d}.html"
        target.write_text(content, encoding="utf-8")


@dataclass
class FillInQuestion(Question):
    blanks: int

    def question_type(self) -> str:
        return "choice"

    def to_display(self) -> str:
        return f"填空题：{self.title or '未命名填空题'}（{self.score} 分）"

    def export(self, output_dir: Path, index: int) -> None:
        template = load_template("fill.html")
        content = render_template(
            template,
            question_number=f"{index:02d}",
            title=self.title,
            prompt_html=format_multiline(self.prompt),
            blanks=str(self.blanks),
            score=str(self.score),
        )
        target = output_dir / f"{index:02d}.html"
        target.write_text(content, encoding="utf-8")
        (output_dir / f"{index:02d}-config.dat").write_text(
            f"{self.score} {self.blanks}\n", encoding="utf-8"
        )


@dataclass
class FileTaskQuestion(Question):
    instructions: str
    deliverables: List[str]

    def question_type(self) -> str:
        return "file"

    def to_display(self) -> str:
        return f"文件题：{self.title or '未命名文件题'}（{self.score} 分）"

    def export(self, output_dir: Path, index: int) -> None:
        template = load_template("file.html")
        content = render_template(
            template,
            question_number=f"{index:02d}",
            title=self.title,
            prompt_html=format_multiline(self.prompt),
            instructions_html=format_multiline(self.instructions, use_br=False),
            deliverables_json=json.dumps(self.deliverables, ensure_ascii=False, indent=2),
        )
        target = output_dir / f"{index:02d}.html"
        target.write_text(content, encoding="utf-8")
        config_path = output_dir / f"{index:02d}-config.dat"
        config_path.write_text("\n".join(self.deliverables) + "\n", encoding="utf-8")
        task_dir = output_dir / f"{index:02d}"
        task_dir.mkdir(exist_ok=True)
        for name in self.deliverables:
            file_path = task_dir / name
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("", encoding="utf-8")


def format_multiline(text: str, *, use_br: bool = True) -> str:
    """Convert multiline plain text into safe HTML."""
    if not text:
        return ""
    lines = [html.escape(line) for line in text.strip().splitlines()]
    if not lines:
        return ""
    if use_br:
        return "<br>\n".join(lines)
    return "\n".join(lines)


def render_template(template: str, **replacements: str) -> str:
    for key, value in replacements.items():
        template = template.replace("{" + key + "}", value)
    return template


class PaperBuilderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("试卷创建工具")
        self.questions: List[Question] = []

        self.output_dir_var = tk.StringVar()
        self.exam_title_var = tk.StringVar()
        self.duration_var = tk.StringVar(value="60")

        self.setup_widgets()

    def setup_widgets(self) -> None:
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Exam info
        info_frame = ttk.LabelFrame(main_frame, text="考试信息", padding=10)
        info_frame.grid(row=0, column=0, sticky="ew")
        info_frame.columnconfigure(1, weight=1)

        ttk.Label(info_frame, text="试卷标题:").grid(row=0, column=0, sticky="w")
        ttk.Entry(info_frame, textvariable=self.exam_title_var).grid(
            row=0, column=1, sticky="ew"
        )

        ttk.Label(info_frame, text="时长(分钟):").grid(row=1, column=0, sticky="w")
        ttk.Entry(info_frame, textvariable=self.duration_var, width=10).grid(
            row=1, column=1, sticky="w"
        )

        ttk.Label(info_frame, text="输出目录:").grid(row=2, column=0, sticky="w")
        output_entry = ttk.Entry(info_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=2, column=1, sticky="ew")
        ttk.Button(info_frame, text="浏览", command=self.choose_output_dir).grid(
            row=2, column=2, padx=5
        )

        # Question controls
        controls = ttk.LabelFrame(main_frame, text="题目管理", padding=10)
        controls.grid(row=1, column=0, pady=10, sticky="nsew")
        controls.columnconfigure(0, weight=1)

        self.question_list = tk.Listbox(controls, height=8)
        self.question_list.grid(row=0, column=0, columnspan=3, sticky="nsew")
        controls.rowconfigure(0, weight=1)

        ttk.Button(controls, text="新增单选题", command=self.add_single_choice).grid(
            row=1, column=0, pady=5, sticky="ew"
        )
        ttk.Button(controls, text="新增填空题", command=self.add_fill_in).grid(
            row=1, column=1, pady=5, sticky="ew"
        )
        ttk.Button(controls, text="新增文件题", command=self.add_file_task).grid(
            row=1, column=2, pady=5, sticky="ew"
        )

        ttk.Button(controls, text="删除选中题目", command=self.remove_selected).grid(
            row=2, column=0, columnspan=3, pady=(5, 0), sticky="ew"
        )

        ttk.Button(main_frame, text="生成试卷结构", command=self.generate_exam).grid(
            row=2, column=0, sticky="ew"
        )

    def choose_output_dir(self) -> None:
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)

    def add_single_choice(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("新增单选题")
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title_var = tk.StringVar()
        score_var = tk.StringVar(value="5")
        prompt_text = tk.Text(frame, width=40, height=5)
        option_vars = [tk.StringVar() for _ in range(4)]

        _build_basic_fields(frame, title_var, score_var, prompt_text)

        options_frame = ttk.LabelFrame(frame, text="选项")
        options_frame.pack(fill=tk.X, pady=(10, 0))
        for idx, var in enumerate(option_vars):
            ttk.Label(options_frame, text=f"选项 {chr(ord('A') + idx)}:").grid(
                row=idx, column=0, sticky="w"
            )
            entry = ttk.Entry(options_frame, textvariable=var, width=40)
            entry.grid(row=idx, column=1, sticky="ew")
            options_frame.columnconfigure(1, weight=1)

        def submit() -> None:
            options = [var.get().strip() for var in option_vars if var.get().strip()]
            if len(options) < 2:
                messagebox.showerror("输入错误", "至少需要填写两个选项。", parent=dialog)
                return
            try:
                score = int(score_var.get() or 0)
            except ValueError:
                messagebox.showerror("输入错误", "分值必须是整数。", parent=dialog)
                return
            question = SingleChoiceQuestion(
                title=title_var.get().strip() or "未命名单选题",
                prompt=read_text(prompt_text),
                options=options,
                score=score,
            )
            self.questions.append(question)
            self.question_list.insert(tk.END, question.to_display())
            dialog.destroy()

        ttk.Button(frame, text="确定", command=submit).pack(pady=10)

    def add_fill_in(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("新增填空题")
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title_var = tk.StringVar()
        score_var = tk.StringVar(value="10")
        blanks_var = tk.StringVar(value="5")
        prompt_text = tk.Text(frame, width=40, height=5)

        _build_basic_fields(frame, title_var, score_var, prompt_text)

        blanks_frame = ttk.Frame(frame)
        blanks_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(blanks_frame, text="空格数量:").pack(side=tk.LEFT)
        blanks_entry = ttk.Entry(blanks_frame, textvariable=blanks_var, width=5)
        blanks_entry.pack(side=tk.LEFT)

        def submit() -> None:
            try:
                score = int(score_var.get() or 0)
                blanks = int(blanks_var.get())
            except ValueError:
                messagebox.showerror("输入错误", "分值和空格数量必须是整数。", parent=dialog)
                return
            if blanks <= 0:
                messagebox.showerror("输入错误", "空格数量必须大于 0。", parent=dialog)
                return
            question = FillInQuestion(
                title=title_var.get().strip() or "未命名填空题",
                prompt=read_text(prompt_text),
                blanks=blanks,
                score=score,
            )
            self.questions.append(question)
            self.question_list.insert(tk.END, question.to_display())
            dialog.destroy()

        ttk.Button(frame, text="确定", command=submit).pack(pady=10)

    def add_file_task(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("新增文件题")
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title_var = tk.StringVar()
        score_var = tk.StringVar(value="40")
        prompt_text = tk.Text(frame, width=40, height=5)
        instruction_text = tk.Text(frame, width=40, height=6)
        deliverable_box = tk.Listbox(frame, height=4)
        deliverable_var = tk.StringVar()

        _build_basic_fields(frame, title_var, score_var, prompt_text)

        instructions_frame = ttk.LabelFrame(frame, text="操作说明")
        instructions_frame.pack(fill=tk.BOTH, pady=(10, 0))
        instruction_text.pack(in_=instructions_frame, fill=tk.BOTH, expand=True)

        deliverable_frame = ttk.LabelFrame(frame, text="需提交文件")
        deliverable_frame.pack(fill=tk.BOTH, pady=(10, 0))
        entry = ttk.Entry(deliverable_frame, textvariable=deliverable_var)
        entry.grid(row=0, column=0, sticky="ew")
        deliverable_frame.columnconfigure(0, weight=1)

        def add_deliverable() -> None:
            value = deliverable_var.get().strip()
            if value:
                deliverable_box.insert(tk.END, value)
                deliverable_var.set("")

        ttk.Button(deliverable_frame, text="添加", command=add_deliverable).grid(
            row=0, column=1, padx=5
        )
        deliverable_box.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 0))

        def submit() -> None:
            deliverables = [deliverable_box.get(i) for i in range(deliverable_box.size())]
            if not deliverables:
                messagebox.showerror("输入错误", "请至少添加一个需提交的文件。", parent=dialog)
                return
            try:
                score = int(score_var.get() or 0)
            except ValueError:
                messagebox.showerror("输入错误", "分值必须是整数。", parent=dialog)
                return
            question = FileTaskQuestion(
                title=title_var.get().strip() or "未命名文件题",
                prompt=read_text(prompt_text),
                instructions=read_text(instruction_text),
                deliverables=deliverables,
                score=score,
            )
            self.questions.append(question)
            self.question_list.insert(tk.END, question.to_display())
            dialog.destroy()

        ttk.Button(frame, text="确定", command=submit).pack(pady=10)

    def remove_selected(self) -> None:
        selection = self.question_list.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的题目。")
            return
        index = selection[0]
        self.question_list.delete(index)
        del self.questions[index]

    def generate_exam(self) -> None:
        if not self.questions:
            messagebox.showerror("错误", "请先添加至少一道题目。")
            return
        output_dir = Path(self.output_dir_var.get())
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录。")
            return
        output_dir.mkdir(parents=True, exist_ok=True)

        copy_static(output_dir)
        write_exam_info(output_dir, self.exam_title_var.get(), self.duration_var.get())

        question_types: List[str] = []
        for idx, question in enumerate(self.questions, start=1):
            question.export(output_dir, idx)
            question_types.append(question.question_type())

        (output_dir / "question-type.dat").write_text(
            "\n".join(question_types) + "\n", encoding="utf-8"
        )
        groups_info = generate_groups_info(self.questions)
        (output_dir / "groups-info.dat").write_text(groups_info, encoding="utf-8")
        messagebox.showinfo("完成", "试卷模板已生成。")


def copy_static(output_dir: Path) -> None:
    target_static = output_dir / "static"
    if target_static.exists():
        return
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, target_static)


def write_exam_info(output_dir: Path, title: str, duration: str) -> None:
    content = [
        f"考试名称: {title or '未命名考试'}",
        f"考试时长: {duration or '60'} 分钟",
        "本目录由试卷创建工具自动生成。",
    ]
    (output_dir / "tips.txt").write_text("\n".join(content) + "\n", encoding="utf-8")


GROUP_LABELS = {
    "single": "单选题",
    "choice": "填空题",
    "file": "文件题",
}

CHINESE_NUMERALS = "一二三四五六七八九十"


def generate_groups_info(questions: List[Question]) -> str:
    grouped: List[Dict[str, object]] = []
    for question in questions:
        qtype = question.question_type()
        if not grouped or grouped[-1]["type"] != qtype:
            grouped.append({"type": qtype, "count": 0})
        grouped[-1]["count"] = int(grouped[-1]["count"]) + 1

    lines: List[str] = []
    for idx, group in enumerate(grouped, start=1):
        numeral = CHINESE_NUMERALS[idx - 1] if idx <= len(CHINESE_NUMERALS) else str(idx)
        label = GROUP_LABELS.get(group["type"], group["type"])
        lines.append(f"{numeral}、{label}----{group['count']}")
    return "\n".join(lines) + ("\n" if lines else "")


def _build_basic_fields(
    frame: ttk.Frame,
    title_var: tk.StringVar,
    score_var: tk.StringVar,
    prompt_text: tk.Text,
) -> None:
    title_frame = ttk.Frame(frame)
    title_frame.pack(fill=tk.X)
    ttk.Label(title_frame, text="标题:").pack(side=tk.LEFT)
    ttk.Entry(title_frame, textvariable=title_var, width=40).pack(
        side=tk.LEFT, fill=tk.X, expand=True
    )

    score_frame = ttk.Frame(frame)
    score_frame.pack(fill=tk.X, pady=(5, 0))
    ttk.Label(score_frame, text="分值:").pack(side=tk.LEFT)
    ttk.Entry(score_frame, textvariable=score_var, width=6).pack(side=tk.LEFT)

    prompt_frame = ttk.LabelFrame(frame, text="题干")
    prompt_frame.pack(fill=tk.BOTH, pady=(5, 0))
    prompt_text.pack(in_=prompt_frame, fill=tk.BOTH, expand=True)


def read_text(widget: tk.Text) -> str:
    return widget.get("1.0", tk.END).strip()


def main() -> None:
    root = tk.Tk()
    PaperBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
