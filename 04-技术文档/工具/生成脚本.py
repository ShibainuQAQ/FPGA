# -*- coding: utf-8 -*-
"""
技术文档生成脚本 —— 2026 嵌入式芯片与系统设计竞赛（AMD 赛道）
按《技术文档模板.docx》结构生成 Word 文档 + 配套插图。
运行： python 生成脚本.py
输出： 04-技术文档/ 下的 docx 与 图/ 目录
"""
import os
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Pt, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

# 本脚本位于 <项目>/04-技术文档/工具/，故 BASE 取上一级
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(BASE, "图")
os.makedirs(FIGDIR, exist_ok=True)

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"


# ============================================================
# 一、生成插图（Pillow）
# ============================================================
def _f(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except Exception:
        return ImageFont.truetype(FONT, size)


def _box(d, x, y, w, h, text, fill, outline="#20323f", fs=22, bold=True, radius=10):
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill,
                        outline=outline, width=2)
    lines = text.split("\n")
    f = _f(fs, bold)
    total = len(lines) * (fs + 8)
    ty = y + (h - total) // 2
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text((x + (w - tw) / 2, ty), ln, font=f, fill="#12222e")
        ty += fs + 8


def _arrow(d, p1, p2, color="#2f6f9f", width=3, head=11):
    d.line([p1, p2], fill=color, width=width)
    import math
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    for da in (math.radians(155), math.radians(-155)):
        d.line([p2, (p2[0] + head * math.cos(ang + da), p2[1] + head * math.sin(ang + da))],
               fill=color, width=width)


def fig_fpga_arch():
    """图 2-13 FPGA 侧系统框图与数据通路（按 A 线 §2.1 重绘）"""
    W, H = 1240, 700
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 18), "图 2-13  FPGA 侧系统框图与数据通路", font=_f(30, True), fill="#12222e")

    # 时钟链
    _box(d, 40, 90, 180, 76, "板载\n50 MHz", "#e8e8ef", fs=18)
    _box(d, 260, 90, 180, 76, "MMCM\n(Clock Wizard)", "#e8e8ef", fs=17)
    _box(d, 480, 90, 200, 76, "200 MHz 主时钟\n周期 5 ns", "#dbe9f7", fs=17)
    _arrow(d, (224, 128), (256, 128))
    _arrow(d, (444, 128), (476, 128))
    _arrow(d, (220, 170), (220, 246), color="#2f6f9f", width=3)
    _arrow(d, (580, 170), (580, 246), color="#2f6f9f", width=3)
    _arrow(d, (676, 130), (972, 174), color="#2f6f9f", width=3)
    _arrow(d, (972, 174), (972, 246), color="#2f6f9f", width=3)

    _box(d, 60, 250, 320, 120, "ADC 采样接口（adc_if）\n\n2 MHz = 200 MHz ÷ 100\n"
                               "安静窗采样 · 位序 · OTR · 预热", "#e6f0e2", fs=17)
    _box(d, 440, 250, 300, 120, "DPWM 核心\n\n200 kHz（PERIOD_CY=1000）\n"
                                "死区 40×5 ns=200 ns · 严格互补", "#dbe9f7", fs=17)
    _box(d, 800, 250, 340, 120, "2P2Z 数字补偿器\n\nQ14 定点 · 48 位累加\n"
                                "10 拍流水 MAC · 限幅 [100,900]", "#fff6da", fs=17)

    _box(d, 60, 490, 320, 88, "AD9226  12 bit / 65 MSPS\n（模块，由 FPGA 供 ADC_CLK）", "#e6f0e2", fs=16)
    _box(d, 440, 490, 300, 88, "IR2110 驱动级 → Q1 / Q2 功率级", "#fdeadf", fs=16)
    _box(d, 800, 490, 340, 88, "LM393 硬件保护\nOCP(3.5 A) / OVP(5.7 V)", "#fdeadf", fs=16)

    # 数据通路（画在两条带之间的走廊 y=430 上，避免交叉）
    _arrow(d, (220, 374), (220, 430), color="#2e8b57", width=3)          # adc_if ↓
    _arrow(d, (220, 430), (970, 430), color="#2e8b57", width=3)          # adc_code →
    _arrow(d, (970, 430), (970, 374), color="#2e8b57", width=3)          # → 2P2Z
    _text_at(d, 470, 404, "adc_code（12 位反馈码）", 15, "#2e8b57")
    _arrow(d, (796, 310), (744, 310), color="#2f6f9f", width=3)          # duty ←
    _text_at(d, 750, 282, "duty", 15, "#2f6f9f")
    _arrow(d, (220, 374), (220, 430), color="#2e8b57", width=0)
    _arrow(d, (300, 374), (300, 486), color="#2e8b57", width=3)          # ADC_CLK ↓
    _text_at(d, 306, 380, "ADC_CLK / D[11:0]", 14, "#2e8b57")
    _arrow(d, (590, 374), (590, 486), color="#2f6f9f", width=3)          # PWM ↓
    _text_at(d, 596, 380, "PWM_H / PWM_L", 14, "#2f6f9f")

    _box(d, 60, 610, 1080, 74,
         "故障保护通路：FAULT_N → 2 级触发器同步（抗亚稳态） → 一级【逐周期封锁，故障消失即恢复】"
         " ＋ 二级【闩锁并置 SD=1 关断 IR2110，需 PL KEY1 人工复位】",
         "#f3e8f7", fs=15)
    _arrow(d, (970, 582), (970, 606), color="#c0392b", width=3)
    _text_at(d, 978, 560, "FAULT_N", 15, "#c0392b")
    _arrow(d, (590, 618), (590, 582), color="#c0392b", width=3)
    _text_at(d, 596, 590, "SD", 15, "#c0392b")

    im.save(os.path.join(FIGDIR, "图2-14-FPGA侧系统框图.png"))
    return "图2-14-FPGA侧系统框图.png"


def fig_sample_phase():
    """图 2-14 ADC 采样相位与 PWM 波形对齐关系（按 A 线 §5.2 重绘）"""
    W, H = 1240, 640
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 18), "图 2-14  ADC 采样相位与 PWM 波形对齐关系（一个 PWM 周期 = 5000 ns）",
           font=_f(26, True), fill="#12222e")

    x0, x1, per = 150, 1150, 5000.0
    sx = (x1 - x0) / per

    def X(t):
        return x0 + t * sx

    def wave(y, a, b, label, color):
        d.line([(x0, y + 40), (X(a), y + 40)], fill=color, width=3)
        d.line([(X(a), y + 40), (X(a), y)], fill=color, width=3)
        d.line([(X(a), y), (X(b), y)], fill=color, width=4)
        d.line([(X(b), y), (X(b), y + 40)], fill=color, width=3)
        d.line([(X(b), y + 40), (x1, y + 40)], fill=color, width=3)
        d.text((40, y + 6), label, font=_f(17, True), fill=color)

    wave(100, 0, 980, "PWM_H", "#2f6f9f")
    wave(190, 1000, 4980, "PWM_L", "#2f6f9f")

    for (a, b) in ((980, 1000), (4980, 5000)):
        d.line([(X(a), 84), (X(b), 84)], fill="#c0392b", width=8)
    _text_at(d, X(978) - 30, 44, "死区 200 ns", 15, "#c0392b")
    _text_at(d, X(4962) - 96, 44, "死区 200 ns", 15, "#c0392b")

    d.rectangle([X(1000), 262, X(4980), 330], fill="#e6f0e2", outline="#2e8b57", width=2)
    _text_at(d, X(1010), 284, "低边管（Q2）导通窗口 1000–4980 ns  ← ISENSE 仅在此区间有效",
             16, "#1f6b45")

    d.line([(X(3000), 240), (X(3000), 560)], fill="#c0392b", width=4)
    d.polygon([(X(3000), 562), (X(3000) - 12, 544), (X(3000) + 12, 544)], fill="#c0392b")
    _text_at(d, X(3000) - 150, 578, "有效采样点 = 3000 ns（对应 ADC 周期 6）", 17, "#c0392b")

    for i in range(11):
        t = i * 500
        d.line([(X(t), 350), (X(t), 372)], fill="#7a8b99", width=2)
    d.text((40, 348), "ADC_CLK\n(2 MHz)", font=_f(15, True), fill="#5a6b78")
    for i in range(11):
        _text_at(d, X(i * 500) - 8, 380, str(i), 13, "#5a6b78", False)
    _text_at(d, X(4300), 404, "ADC 周期序号", 14, "#5a6b78", False)

    _text_at(d, 60, 500, "判定：3000 ns 落在 1000–4980 ns 的低边导通窗口内，"
                         "且距最近的开关沿 ≥ 1.9 µs（已避开开关振铃）→ 与功率级约束一致 √",
             17, "#1f6b45")

    im.save(os.path.join(FIGDIR, "图2-15-ADC采样相位.png"))
    return "图2-15-ADC采样相位.png"


def fig_design_flow():
    """图 1-1 设计流程"""
    W, H = 1180, 300
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    steps = [
        "需求与\n指标定义", "九区\n原理图设计", "网表逐脚核对\n（网络/单脚网体检）",
        "封装 + BOM\n三层核对", "PCB 布局布线\n（环路/地分域）", "打样\n与焊接",
        "分层上电\n开环验证", "闭环调试\n（2P2Z）",
    ]
    bw, bh, gap = 118, 92, 22
    x = 24
    y = 100
    colors = ["#dfe9f3", "#dfe9f3", "#e6f0e2", "#e6f0e2", "#fdeadf", "#fdeadf", "#f3e8f7", "#f3e8f7"]
    for i, s in enumerate(steps):
        _box(d, x, y, bw, bh, s, colors[i], fs=17)
        if i < len(steps) - 1:
            _arrow(d, (x + bw, y + bh / 2), (x + bw + gap - 4, y + bh / 2))
        x += bw + gap
    f = _f(30, True)
    d.text((24, 36), "图 1-1  设计流程", font=f, fill="#12222e")
    im.save(os.path.join(FIGDIR, "图1-1-设计流程.png"))
    return "图1-1-设计流程.png"


def _text_at(d, x, y, txt, fs=15, color="#12222e", bold=True):
    d.text((x, y), txt, font=_f(fs, bold), fill=color)


def fig_system():
    """图 2-1 系统整体框图（左：功率板九区；右：负载 / FPGA / ADC 模块）"""
    W, H = 1440, 700
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 18), "图 2-1  系统整体框图", font=_f(30, True), fill="#12222e")

    # ---------- 功率板面板 ----------
    d.rounded_rectangle([40, 80, 810, 620], radius=14, outline="#20323f", width=3, fill="#fbfdff")
    d.text((62, 92), "功率板（120.19 mm × 86.28 mm，2 层 1 oz）", font=_f(21, True), fill="#20323f")

    cw, ch = 210, 108
    xs = [70, 325, 580]
    ys = [140, 275, 410]
    zones = [
        ("A 区  电源输入\n24 V 滤波 / 防反接", "#dfe9f3"),
        ("C 区  功率级\n同步 Buck·Q1/Q2/L3", "#fdeadf"),
        ("G 区  输出与测试\nJ2 · TP2 · LED4", "#dfe9f3"),
        ("B 区  辅助电源\n12 V·5 V（LM2596）", "#e6f0e2"),
        ("D 区  栅极驱动\nIR2110 · 74HCT245", "#f3e8f7"),
        ("E 区  电压采样\n分压 → VSENSE", "#fff6da"),
        ("H 区  FPGA 接口\nJ3（26P 排针）", "#e8e8ef"),
        ("F 区  采样 + 保护\nINA180A2 · LM393", "#fff6da"),
        ("I 区  ADC 接口\nJ4（26P）· J5 · J6", "#e8e8ef"),
    ]
    for i, (txt, col) in enumerate(zones):
        r, c = divmod(i, 3)
        _box(d, xs[c], ys[r], cw, ch, txt, col, fs=17, radius=10)

    # ---------- 右侧三个实体 ----------
    RX = 1010
    _box(d, RX, 140, 400, 108, "负载 / 电子负载\n5 V · 0–3 A", "#fdeadf", fs=18)
    _box(d, RX, 275, 400, 150,
         "FPGA  XC7Z020（Zynq-7020）\n\nDPWM 200 kHz · 5 ns 分辨率\n数字死区 200 ns · 互补输出\n"
         "逐周期封波 + 闩锁 + 复位", "#dbe9f7", fs=17)
    _box(d, RX, 455, 400, 120,
         "AD9226  12 bit / 65 MSPS\n以 2 MHz 与 PWM 周期同步\n在“安静窗”内采样", "#e6f0e2", fs=17)

    # ---------- 板 ↔ 右侧：4 条接口箭头（标注放在 810~1010 的空档里）----------
    GAP = 820
    _arrow(d, (795, 194), (RX - 6, 194), color="#c0392b", width=4)
    _text_at(d, GAP, 166, "5 V / 3 A", 15, "#c0392b")

    _arrow(d, (RX - 6, 312), (795, 312), color="#2f6f9f", width=4)
    _text_at(d, GAP, 286, "PWM_H/L、SD", 15, "#2f6f9f")

    _arrow(d, (795, 392), (RX - 6, 392), color="#c0392b", width=4)
    _text_at(d, GAP, 366, "FAULT_N", 15, "#c0392b")

    _arrow(d, (795, 512), (RX - 6, 512), color="#2f6f9f", width=4)
    _text_at(d, GAP, 486, "ADC_CLK /", 14, "#2f6f9f")
    _text_at(d, GAP, 530, "ADC_D[11:0] /", 14, "#2f6f9f")
    _text_at(d, GAP, 552, "OTR", 14, "#2f6f9f")

    # ---------- 板内连接 ----------
    _arrow(d, (280, 194), (321, 194), color="#c0392b", width=3)   # A→C
    _arrow(d, (535, 194), (576, 194), color="#c0392b", width=3)   # C→G
    _arrow(d, (175, 248), (175, 271), color="#2f6f9f", width=3)   # A→B
    _text_at(d, (140), 250, "24 V", 14, "#2f6f9f")
    _arrow(d, (280, 329), (321, 329), color="#2f6f9f", width=3)   # B→D
    _text_at(d, 286, 307, "12 V", 14, "#2f6f9f")
    _arrow(d, (430, 271), (430, 248), color="#f39c12", width=3)   # D→C
    _text_at(d, 438, 252, "HO/LO", 14, "#f39c12")
    _arrow(d, (685, 248), (685, 271), color="#2e8b57", width=3)   # G→E
    _text_at(d, 692, 252, "VOUT", 14, "#2e8b57")
    _arrow(d, (685, 383), (685, 406), color="#2e8b57", width=3)   # E→I
    _text_at(d, 692, 386, "VSENSE", 14, "#2e8b57")
    _arrow(d, (535, 464), (576, 464), color="#2e8b57", width=3)   # F→I
    _text_at(d, 330, 524, "ISENSE → J6", 14, "#2e8b57")
    _arrow(d, (321, 464), (284, 464), color="#c0392b", width=3)   # F→H (FAULT_N)
    _text_at(d, 430, 524, "FAULT_N → J3", 14, "#c0392b")

    _text_at(d, 62, 596,
             "红色：功率与故障；蓝色：PWM 与数字总线；绿色：采样链路（→ J5/J6 → ADC 模块）", 16, "#4a5b68", False)
    im.save(os.path.join(FIGDIR, "图2-1-系统整体框图.png"))
    return "图2-1-系统整体框图.png"


def fig_zones():
    """图 2-2 功率板布局分区示意（俯视，按实际相对位置）"""
    S = 8.3          # px per mm
    OX, OY = 120, 96  # 板左上角像素
    BW, BH = 120.19, 86.28
    W = int(OX * 2 + BW * S)
    H = int(OY + BH * S + 96)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 18), "图 2-2  功率板布局分区示意（俯视图）", font=_f(30, True), fill="#12222e")

    def px(xmm, ymm):
        return (OX + xmm * S, OY + ymm * S)

    # 板框
    d.rounded_rectangle([OX, OY, OX + BW * S, OY + BH * S], radius=26,
                        outline="#20323f", width=4, fill="#fcfdfe")
    # 安装孔（距板边约 6.9 / 5.0 mm）
    for (hx, hy) in [(6.86, 5.9), (BW - 6.86, 5.9), (6.86, BH - 4.1), (BW - 6.86, BH - 4.1)]:
        cx, cy = px(hx, hy)
        d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], outline="#8496a4", width=3)

    def zbox(x, y, w, h, txt, col, fs=15):
        X, Y = px(x, y)
        _box(d, X, Y, w * S, h * S, txt, col, fs=fs, radius=8)

    # ---- 上边接口带 ----
    zbox(20, 4, 34, 11, "H 区  J3（26P）\n→ FPGA", "#e8e8ef", 15)
    zbox(63, 4, 34, 11, "I 区  J4（26P）\n→ ADC 模块", "#e8e8ef", 15)
    zbox(103, 19, 13, 13, "J5/J6\n模拟", "#e8e8ef", 14)

    # ---- 左：输入 ｜ 中：功率 ｜ 右：输出 ----
    zbox(1.5, 33, 10, 20, "J1\n24 V", "#dfe9f3", 16)
    zbox(14, 30, 26, 24, "A 区\n电源输入\n滤波 / 防反接", "#dfe9f3", 15)
    zbox(45, 27, 35, 27, "C 区  功率级\n同步 Buck\nQ1 / Q2 / L3\nR_shunt", "#fdeadf", 15)
    zbox(83, 30, 19, 24, "G 区\n输出与\n测试", "#dfe9f3", 15)
    zbox(108.5, 33, 10, 20, "J2\n5 V", "#dfe9f3", 15)

    # ---- 下排 ----
    zbox(14, 58, 26, 22, "B 区  辅助电源\n12 V / 5 V\n（LM2596×2）", "#e6f0e2", 14)
    zbox(45, 58, 26, 22, "D 区\n栅极驱动\nIR2110", "#f3e8f7", 15)
    zbox(75, 58, 22, 22, "F 区\n电流采样+保护\nINA180/LM393", "#fff6da", 13)
    zbox(100, 58, 18, 22, "E 区\n电压采样", "#fff6da", 15)

    # ---- 流向箭头 ----
    def ar(a, b, c, w=4):
        _arrow(d, px(*a), px(*b), color=c, width=w)

    ar((11.8, 43), (13.6, 43), "#c0392b")                 # J1→A
    ar((40.3, 40), (44.6, 38), "#c0392b")                 # A→C
    ar((80.3, 38), (82.6, 40), "#c0392b")                 # C→G
    ar((102.3, 43), (108.1, 43), "#c0392b")               # G→J2
    ar((27, 54.3), (27, 57.6), "#2f6f9f", 3)              # A→B 24V
    ar((40.3, 66), (44.6, 66), "#2f6f9f", 3)              # B→D 12V
    ar((58, 57.6), (58, 54.3), "#f39c12", 3)              # D→C 驱动
    ar((68, 54.3), (80, 62), "#2e8b57", 3)                # C→F 采样
    ar((80.3, 45), (100, 60), "#2e8b57", 3)               # C→E 电压采样
    ar((95, 57.6), (99, 33), "#2e8b57", 3)                # F/E→J5/J6

    # ---- 文字标注 ----
    _text_at(d, 24, 60, "24 V 输入 →", 17, "#c0392b")
    _text_at(d, W - 190, 60, "→ 5 V / 3 A 输出", 17, "#c0392b")
    _text_at(d, 132, OY + BH * S + 34,
             "红：功率流（左进右出）　蓝：辅助电源/驱动　绿：采样链路　灰：数字接口（→ J3 / J4）",
             16, "#4a5b68", False)
    _text_at(d, OX + 8, OY + BH * S + 8, "120.19 mm × 86.28 mm　/　2 层 1 oz　/　4×M3",
             14, "#5a6b78", False)

    im.save(os.path.join(FIGDIR, "图2-2-九区划分与信号流.png"))
    return "图2-2-九区划分与信号流.png"


# ============================================================
# 二、Word 文档
# ============================================================
EA = "宋体"
LAT = "Times New Roman"


def _set_run(run, size=12, bold=False, ea=EA, lat=LAT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = lat
    run._element.rPr.rFonts.set(qn('w:eastAsia'), ea)


def add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    _set_run(r, 18, True, ea="黑体")
    return p


def add_part(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    _set_run(r, 14, True, ea="黑体")
    return p


def add_h(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    _set_run(r, 12, True, ea="黑体")
    return p


def add_body(doc, text, indent=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.35
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    r = p.add_run(text)
    _set_run(r, 12)
    return p


def add_list(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.left_indent = Pt(24)
    r = p.add_run(text)
    _set_run(r, 12)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    _set_run(r, 10.5)
    r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    return p


def add_pic(doc, name, width_in=5.6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(FIGDIR, name), width=Emu(int(width_in * 914400)))


def add_ph(doc, text):
    """待插入素材的占位段"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.left_indent = Pt(24)
    r = p.add_run(text)
    _set_run(r, 11)
    r.font.color.rgb = RGBColor(0xB0, 0x30, 0x30)
    return p


# ============================================================
# 插图清单（清单驱动：有图就插、没图自动留红字占位）
#   下次补图：把文件按「候选文件名」放进 图/ 目录 → 重跑本脚本即可
# ============================================================
FIGS = [
    # no,    图题,                          候选文件名（任一命中即用）,                        是否由本脚本生成
    ("1-1",  "设计流程",                      ["图1-1-设计流程.png"],                            True),
    ("2-1",  "系统整体框图",                   ["图2-1-系统整体框图.png"],                        True),
    ("2-2",  "功率板布局分区示意（俯视图）",      ["图2-2-九区划分与信号流.png"],                     True),
    ("2-3",  "功率板 PCB 版图（顶层铜 + 丝印）",  ["功率板 PCB 版图（顶层铜 + 丝印）截图.png",
                                              "功率板PCB版图.png", "PCB版图.png"],               False),
    ("2-4",  "A 区原理图",                     ["A 区原理图.png", "A区原理图.png"],                False),
    ("2-5",  "B 区原理图",                     ["B 区原理图.png", "B区原理图.png"],                False),
    ("2-6",  "C 区原理图",                     ["C 区原理图.png", "C区原理图.png"],                False),
    ("2-7",  "D 区原理图",                     ["D 区原理图.png", "D区原理图.png"],                False),
    ("2-8",  "E 区原理图",                     ["E 区原理图.png", "E区原理图.png"],                False),
    ("2-9", "F 区原理图",                     ["F 区原理图.png", "F区原理图.png"],                False),
    ("2-10", "G 区原理图",                     ["G 区原理图.png", "G区原理图.png"],                False),
    ("2-11", "H 区原理图（J3 排针定义）",         ["H 区原理图.png", "H区原理图.png"],                False),
    ("2-12", "I 区原理图（J4/J5/J6 与模块接线）",  ["I 区原理图.png", "I区原理图.png"],                False),
    ("2-13", "FPGA 侧系统框图与数据通路",         ["图2-14-FPGA侧系统框图.png", "RTL顶层框图.png",
                                              "RTL 顶层框图.png", "RTL框图.png"],                 True),
    ("2-14", "ADC 采样相位与 PWM 波形对齐",       ["图2-15-ADC采样相位.png"],                        True),
    ("2-15", "环路开环波特图（解析模型：fc = 6.99 kHz、PM = 83.5°）",
                                              ["图2-16-环路Bode图.png", "环路Bode图.png"],         False),
    ("3-1",  "系统实物正面照片",                 ["实物正面.png", "实物正面照片.png"],                False),
    ("3-2",  "系统实物 45° 全局照片",            ["实物45度.png", "实物 45°全局.png",
                                              "实物45°全局.png"],                                 False),
    ("3-3",  "PCB 3D 预览（EDA 3D 视图）",        ["PCB3D预览.png", "PCB 3D预览.png"],               False),
    ("3-4",  "整机原理图总览",                   ["整机原理图总览1.png", "整机原理图总览2.png",
                                              "整机原理图总览.png"],                              False),
    ("3-5",  "PCB 布线与地平面分域",             ["PCB 布线与地平面.png"],                          False),
    ("3-6",  "DPWM 互补波形与死区",              ["DPWM波形.png", "DPWM 波形.png", "死区波形.png"],   False),
    ("3-7",  "保护误锁存修复前后对比",            ["保护误锁存修复前后对比.png", "保护响应.png",
                                              "保护响应波形.png"],                                False),
    ("3-8",  "ILA 闭环稳态：ADC 码值 = REF_CODE", ["ILA闭环稳态.png", "ILA截图.png", "ILA 截图.png"],
                                              False),
    ("3-9",  "启动响应实测（KEY1 复位，2 Ω 负载；峰值 6.56 V）",
                                              ["启动波形实测.png", "启动响应实测.png"],            False),
]
FIG_MAP = {f[0]: f for f in FIGS}
_inserted = []      # 已插入的图号
_pending = []       # 待补的图号 + 期望文件名


def _norm(s):
    """规范化文件名：去扩展名、去空格/全角空格、统一小写（.png/.jpg/.jpeg 都认）"""
    base = os.path.splitext(s)[0]
    return base.replace(" ", "").replace("\u3000", "").lower()


def find_figs(cands):
    """在 图/ 目录里按候选名匹配（宽松：忽略空格、大小写）；同一文件只取一次"""
    if not os.path.isdir(FIGDIR):
        return []
    files = os.listdir(FIGDIR)
    idx = {_norm(f): f for f in files}
    out = []
    for c in cands:
        hit = idx.get(_norm(c))
        if hit and hit not in out:      # ← 去重：多个候选名可能指向同一文件
            out.append(hit)
    return out


CACHE = os.path.join(BASE, "_fig_cache")


def _embed_path(fn):
    """大图缩到长边 ≤2400 px 再嵌入（控制 docx 体积，5.6 英寸下仍 ≈428 dpi）"""
    src = os.path.join(FIGDIR, fn)
    try:
        from PIL import Image, ImageOps
        im = Image.open(src)
        im = ImageOps.exif_transpose(im)          # 按 EXIF 方向摆正（手机竖拍）
        w, h = im.size
        if max(w, h) <= 2400:
            return src
        os.makedirs(CACHE, exist_ok=True)
        k = 2400.0 / max(w, h)
        out = os.path.join(CACHE, os.path.splitext(fn)[0] + "_s2400.jpg")
        im.convert("RGB").resize((int(w * k), int(h * k)), Image.LANCZOS).save(
            out, "JPEG", quality=88, optimize=True)   # 照片存 JPEG，体积小一个数量级
        print("  [缩小] %s  %dx%d -> %dx%d  (%.1f KB)"
              % (fn, w, h, int(w * k), int(h * k), os.path.getsize(out) / 1024.0))
        return out
    except Exception as e:
        print("  [警告] 缩图失败，用原图:", fn, e)
        return src


def add_fig(doc, no, width_in=5.6):
    """按图号插入插图；缺图则留红字占位并记录到待补清单"""
    no, caption, cands, generated = FIG_MAP[no]
    # 生成型插图（1-1/2-1/2-2）在 build() 之前已由脚本写入 图/ 目录，这里同样按文件名查找
    found = find_figs(cands)
    if not found:
        _pending.append((no, caption, cands))
        add_ph(doc, "【待插入】图 %s　%s（把文件放进 图/ 目录后重跑 生成脚本.py 即自动插入；"
                    "期望文件名：%s）" % (no, caption, " 或 ".join(cands)))
        return
    for i, fn in enumerate(found):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(_embed_path(fn), width=Emu(int(width_in * 914400)))
        tag = "图 %s　%s" % (no, caption)
        if len(found) > 1:
            tag = "图 %s（%s）　%s" % (no, "ab"[i] if i < 2 else str(i + 1), caption)
        add_caption(doc, tag)
    _inserted.append(no)
    return


def write_checklist():
    """把插图状态写回 图/待插入图清单.md（每次重跑自动更新）"""
    lines = ["# 【待插入】图片清单（自动生成，请勿手工改 —— 由 生成脚本.py 重写）", "",
             "> 用法：**把图片按「期望文件名」放进 `图/` 目录 → 重跑 `生成脚本.py`** →"
             " 有图的自动插入，没图的仍留红字占位。", "",
             "## 一、当前状态", "",
             "| 图号 | 图题 | 状态 | 期望文件名 |", "|---|---|---|---|"]
    for no, caption, cands, generated in FIGS:
        if no in _inserted:
            st = "✅ 已插入" if not generated else "✅ 脚本生成"
        else:
            st = "⏳ 待补"
        lines.append("| %s | %s | %s | `%s` |" % (no, caption, st, "` `".join(cands)))
    n_in = len(_inserted)
    n_pd = len(_pending)
    lines += ["", "**进度：已插入 %d 张 / 待补 %d 张**" % (n_in, n_pd), "",
              "## 二、补图小技巧", "",
              "1. **文件名不用一字不差** —— 脚本会忽略空格、不区分大小写；也可以用上表列出的任一候选名 ✅",
              "2. **插入宽度 5.6 英寸**（版心 5.768″ 以内，不会溢出）✅",
              "3. **示波器截图要带读数**（频率/幅值/时间刻度），报告里最有力 ✅",
              "4. **照片要求**：光线足、背景干净、能看清丝印与接线；正面 + 45° 各一张 ✅",
              "5. **同一图号多张**（如整机原理图总览 1/2）会自动编成（a）（b）✅", "",
              "## 三、⭐ 与正文表述的对应（避免图文不符）", "",
              "| 正文数字 | 必须由图证明 |", "|---|---|",
              "| 200.00 kHz、980 ns / 3980 ns（开环 20 %）、死区 200.0 ns | 图 3-6 |",
              "| 闭环带载 PWM_H 23.0 % / PWM_L 70.0 %（空载 16.8 %）| 图 3-6 |",
              "| 保护误锁存修复（0.6 V → 4.8 V）| 图 3-7 |",
              "| ADC 稳态码值 2453 = REF_CODE（误差 0 码）| 图 3-8 |",
              "| 分区与地平面分域、星点 | 图 3-5 |",
              "| 九区电路结构 | 图 2-4 ~ 图 2-12 |", "",
              "> ⚠️ **补不上的指标，就保持正文里的“待测”** —— 宁可少写，不要图文不符 ✅", ""]
    with open(os.path.join(FIGDIR, "待插入图清单.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("checklist updated: 已插入 %d / 待补 %d" % (n_in, n_pd))
    if _pending:
        print("  待补：", ", ".join("图" + n for n, _, _ in _pending))


def _set_table_borders(t, color="7F7F7F", sz="6"):
    """模板 styles.xml 里没有 Table Grid 样式，直接写 tblBorders 保证有框线"""
    from docx.oxml import OxmlElement
    tblPr = t._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement('w:' + edge)
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), sz)
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)
        borders.append(el)
    tblPr.append(borders)


def add_table(doc, headers, rows, widths=None, fs=10.5):
    t = doc.add_table(rows=1, cols=len(headers))
    try:
        t.style = "Table Grid"
    except KeyError:
        _set_table_borders(t)
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        _set_run(r, fs, True, ea="黑体")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(v))
            _set_run(r, fs)
    if widths:
        for r_ in t.rows:
            for i, w in enumerate(widths):
                r_.cells[i].width = Emu(int(w * 914400))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def build():
    # ⭐ 以竞赛模板为底稿：页眉图片（“芯辰大海 点亮未来”）、页脚页码域、
    #    全部样式与页面设置（A4 / 左右 1.25" / 上下 1"）原样保留。
    #    模板放在本文件夹或上一级都能找到 ✅
    tpl = None
    for cand in (os.path.join(BASE, "技术文档模板.docx"),
                 os.path.join(BASE, "..", "技术文档模板.docx")):
        if os.path.exists(cand):
            tpl = cand
            break
    if tpl:
        doc = Document(tpl)
        body = doc.element.body
        # 只清空正文内容（段落 + 表格），保留末尾的 w:sectPr（页眉/页脚引用就在里面）
        for child in list(body.iterchildren()):
            if child.tag in (qn('w:p'), qn('w:tbl')):
                body.remove(child)
        print("base: %s（保留页眉/页脚/样式）" % os.path.basename(tpl))
    else:
        doc = Document()
        print("base: 新建空文档（未找到模板！页眉/页脚将缺失）")

    # 页面设置（与模板一致；模板缺失时兜底）
    s = doc.sections[0]
    s.page_width = Emu(7560310)
    s.page_height = Emu(10692130)
    s.left_margin = Emu(1143000)
    s.right_margin = Emu(1143000)
    s.top_margin = Emu(914400)
    s.bottom_margin = Emu(914400)
    # 默认样式
    st = doc.styles["Normal"]
    st.font.name = LAT
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), EA)

    # ---------------- 封面标题 ----------------
    add_title(doc, "基于 FPGA 的全数字控制同步 Buck 降压电源设计")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("—— 5 ns 分辨率数字 PWM、周期同步采样与逐周期保护")
    _set_run(r, 12, False)
    r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)

    # ---------------- 摘要 ----------------
    add_part(doc, "摘要")
    add_body(doc,
             "本作品面向精密仪器的低压供电轨（如半导体制造与精密测量装备中传感器、模拟前端的数字预稳压级），"
             "以 AMD Zynq-7020（XC7Z020）为核心，设计并实现了一套 24 V 输入、5 V/0–3 A 输出的"
             "全数字控制同步 Buck 降压电源。系统将开关频率设为 200 kHz，由 FPGA 在 200 MHz 时钟域内产生"
             "互补 PWM 波形；DPWM 在 200 MHz 时钟域内以 5 ns 时间分辨率（占空比 0.1%）调节脉宽，"
             "并插入 200 ns 数字死区，取代传统模拟 PWM"
             "控制器；输出电压与电感电流经采样调理后，由 12 bit／65 MSPS 的 AD9226 以 2 MHz 速率、"
             "并与 PWM 周期严格同步地在“安静窗”（开关瞬态结束之后）内采样，送入 FPGA 内的 2P2Z 数字补偿器"
             "构成闭环，实现数字化的环路补偿与实时监控。")
    add_body(doc,
             "在保护方面，本作品构建了三层保护架构：10 mΩ 分流电阻配合 INA180A2（50 V/V）得到 0.5 V/A 的"
             "电流采样灵敏度，经 LM393 双通道比较器分别实现可调过流保护（OCP，默认 3.5 A）与过压保护"
             "（OVP，设计目标 5.76 V）；比较器输出线与形成 FAULT_N 故障信号，FPGA 在 2 个 200 MHz 时钟"
             "内完成逐周期封波并进入闩锁状态、直至人工复位，从而在功率器件受损之前切断驱动。"
             "该数字链路的固有延迟实测 58 ns（FAULT_N 引脚到 PWM 引脚，无滤波状态）；为抑制比较器毛刺另有"
             "1 µs 数字滤波，计入滤波后端到端约 1.0 µs——仍比中断式软件保护快 2~3 个数量级。")
    add_body(doc,
             "硬件方面，原理图按功能划分为 A–I 九个功能区（电源输入、辅助电源、功率级、栅极驱动、电压采样、"
             "电流采样与保护、输出测试、FPGA 接口、ADC 模块接口），板卡尺寸 120.19 mm × 86.28 mm、"
             "2 层 1 oz 铜厚，采用功率地与信号地分域、单点星形汇接、开关环路面积最小化、开尔文电流采样与"
             "按载流分级的铜宽设计。全部网络经网表逐引脚核对，并完成封装与 BOM 三层核查。")
    add_body(doc,
             "目前已完成：原理图九区设计与核对、PCB 设计并投板、功率板焊接与整机联调，数字闭环已在上板"
             "稳定运行——闭环输出 5.00–5.01 V，ADC 稳态码值恒等于参考码（2453），即**稳态误差 0 码**，"
             "闭环带载（2 Ω）占空比 22.6~23.0 %、闭环空载 16.8 %（ILA 与示波器实测，命令字随工况变化），"
             "空载输入电流 46 mA；"
             "独立时序实测得开关频率 200.00 kHz、高侧脉宽 980 ns、"
             "低侧脉宽 3980 ns、死区 200 ns，"
             "保护响应：数字链路固有延迟 58 ns（无滤波），含 1 µs 数字滤波后故障到封波约 1.0 µs；"
             "ADC 采集接口的 RTL 仿真自检 7/7 通过。")
    add_body(doc,
             "采样通道的关键参数最终由实测标定：12 位 ADC 链路实测灵敏度 416 码/V"
             "（手册标称 409.6 码/V，偏差 1.5 %）、零点恰为中点 2048 码（无偏置），据此在 FPGA 内以实测"
             "增益系数校正。另有一项只有上板才会暴露的硬件前提：AD9226 模块的模拟输入端为 50 Ω 端接，"
             "而板上分压器的戴维南阻抗约 10.6 kΩ，直接相连会把反馈信号衰减到 4 %（实测 1.70 V 跌至 "
             "0.047 V），本版联调改用板外 220 Ω／2.2 kΩ 低阻分压（实测分压比 0.2017、参考码 2453），"
             "下一版将在功率板上增设运放跟随器从根本上解决。")
    add_body(doc, "关键词：数字电源；FPGA；同步 Buck；DPWM；2P2Z 数字补偿；逐周期保护")

    # ---------------- 第一部分 ----------------
    add_part(doc, "第一部分　作品概述")
    add_h(doc, "1.1　功能与特性")
    add_body(doc,
             "本作品是一台由 FPGA 全数字控制、可闭环调节并具备完整保护功能的降压型直流变换器。输入 24 V，"
             "输出 5 V，额定电流 3 A（0–3 A 连续可调负载），开关频率固定 200 kHz。FPGA 产生互补的高侧／低侧"
             "PWM 驱动信号并通过 IR2110 浮动驱动双 N 沟道 MOSFET（IRLZ44N）构成的同步 Buck 功率级；"
             "输出 LC 滤波后经端子输出，板载 LED 分别指示 24 V、12 V、5 V 与 VOUT 状态，并提供 TP1（VSENSE）、"
             "TP2（VOUT/GND）、TP3（PWM 同步脉冲）三个测试点便于示波器观察。")
    add_body(doc,
             "控制与保护特性：① 输出端经 30 kΩ 与 10 kΩ（含 10 kΩ 精密电位器）分压，分压比 0.25–0.40 可调，"
             "5 V 输出对应约 1.25–2.00 V 的 VSENSE 信号；② 10 mΩ 分流电阻串于低侧 MOS 源极与地之间，"
             "经 INA180A2 放大 50 倍后得到 0.5 V/A 的 ISENSE 信号；③ 二者经 LM393 双通道比较器实现"
             "OCP（阈值可调，默认 3.5 A）与 OVP（设计目标 5.76 V），故障时拉低 FAULT_N；④ FPGA 在 2 个 200 MHz "
             "内（数字链路 58 ns；含 1 µs 滤波后约 1.0 µs）"
             "逐周期封锁两路 PWM，并闩锁故障状态；⑤ 全部模拟信号引出至 J5/J6，数字与电源接口引出至"
             "J3/J4 排针，便于示波器与逻辑分析仪测量。")
    add_h(doc, "1.2　应用领域")
    add_body(doc,
             "（1）应用定位：面向\u201c对供电稳定性要求高、单路功率在数十瓦以内\u201d的精密低压负载，作为其数字预稳压级。"
             "这类负载的通行供电架构是\u201c开关前级＋线性后级\u201d两级串联——开关变换器把 24 V 母线高效降到 5 V "
             "并承担瞬态响应与故障保护，后级再以 π 型无源滤波、低压差线性稳压器（LDO）与电压基准把纹波压到毫伏以下。"
             "本作品正是针对这一前级位置设计：数字控制的价值不在于替代线性稳压器的精度，而在于 5 ns 级的调制分辨率、"
             "百纳秒级的保护速度与完全可重构的环路参数。")
    add_body(doc,
             "（2）典型场景：半导体制造与精密测量装备中传感器与模拟前端的低压供电轨。以光刻设备的对准与测量子系统为例——"
             "对准传感器的图像与信号处理电路、激光干涉仪的接收前端、位置编码器的信号调理，以及温控回路（TEC）的驱动供电，"
             "都是 5 V 量级的低压负载；其供电纹波与瞬态扰动会直接耦合进位移解算误差，因此对稳态纹波、负载瞬态恢复与上电行为"
             "要求严格。这类子系统通常在设备内由 24 V 直流母线统一配电，正是本作品 24 V→5 V／0–3 A 的输入输出形态。")
    add_body(doc,
             "（3）指标映射与差距：此类模拟供电轨的典型稳态目标在 0.1 % 量级（5 V 下约 5 mV）。本作品直接输出的实测纹波为 "
             "60 mV（1.2 %），尚不足以直接作为精密模拟轨使用；但在两级架构下可以满足要求——200 kHz 的 60 mV 纹波经 "
             "π 型磁珠／LC 滤波（约 −30 dB）降至约 2 mV，再经直流电源抑制比 60 dB、200 kHz 处约 20 dB 的 LDO 抑制后"
             "低于 1 mV（0.02 %）。前级在此架构中承担的三项职能都由数字控制实现：① 5 ns（0.1 %）的占空比分辨率使稳态误差"
             "可以细粒度修正；② 58 ns 的数字保护链路与 1 µs 数字滤波兼顾快速封波与抗误触发；③ 环路系数、软启动斜率与"
             "限幅值均由 RTL 常量给出，可逐台标定并借片内 ILA 在线观测中间变量。本版的不足同样明确：穿越频率 6.99 kHz、"
             "仿真负载阶跃恢复约 4 ms、启动过冲约 +24 %，与这类应用对瞬态恢复的要求仍有差距，改进方向见 §3.6。")
    add_body(doc,
             "（4）其它适用场景：精密仪器中 12～16 位 ADC／DAC 与电压基准的前级预稳压；光电探测器、激光二极管的恒压偏置"
             "前级（后级实现恒流）；工业控制、通信设备与嵌入式计算平台中常见的 24 V→5 V 配电形态；以及作为数字控制算法的"
             "教学与科研验证平台——补偿器完全以 RTL 实现，可快速替换或并行比较 2P2Z、PID、滑模与预测控制等算法。")
    add_h(doc, "1.3　主要技术特点")
    add_body(doc,
             "① 全数字控制：开关频率、占空比、死区与环路补偿全部由 FPGA 数字逻辑产生，无模拟 PWM 控制器，"
             "参数可通过修改 RTL 在线调整，并具备重复性一致、不受温漂影响的优点。")
    add_body(doc,
             "② 全数字高分辨率调制：DPWM 在 200 MHz 时钟域内以 5 ns 时间分辨率（占空比 0.1%）调节脉宽，"
             "死区由计数器统一产生、不随占空比与温度变化，调制端与控制器完全同源同步。")
    add_body(doc,
             "③ 周期同步“安静窗”采样：ADC 采样时刻与 PWM 周期严格对齐，并安排在开关瞬态结束、"
             "振铃衰减之后的窗口内，避免把开关噪声采进环路。")
    add_body(doc,
             "④ 三层保护：硬件比较器（LM393）快速检测 + FPGA 逐周期封波（数字链路 58 ns；"
             "含 1 µs 滤波后约 1.0 µs）+ 故障闩锁与"
             "人工复位，兼顾速度与安全。")
    add_body(doc,
             "⑤ 面向开关电源的板级设计纪律：开关环路面积最小化、功率地与信号地分域单点汇接、"
             "电流采样开尔文连接、按载流分级的铜宽、MOSFET 立式散热布局。")
    add_h(doc, "1.4　主要性能指标")
    add_table(doc,
              ["项目", "指标", "项目", "指标"],
              [
                  ["输入电压", "24 V DC", "开关频率", "200 kHz（周期 5000 ns）"],
                  ["输出电压", "5 V（额定）", "占空比", "闭环带载（2 Ω）22.6~23.0 %；闭环空载 16.8 %"],
                  ["输出电流", "0–3 A", "死区时间", "200 ns（FPGA 数字死区，按驱动延迟失配留余量）"],
                  ["DPWM 分辨率", "5 ns（200 MHz 计数，占空比步进 0.1%）", "保护响应", "数字链路 58 ns；含 1 µs 滤波约 1.0 µs"],
                  ["电压采样", "板上电位器分压比 0.25–0.40 可调（工作点 0.39）；联调实测改用板外 220 Ω／2.2 kΩ 低阻分压（0.2017）", "OCP 阈值", "3.5 A（1.5–4.5 A 可调）"],
                  ["电流采样", "10 mΩ + INA180A2（50 V/V）= 0.5 V/A", "OVP 阈值", "≈5.8 V（2.245 V ÷ 0.39，随分压比联动）"],
                  ["ADC", "AD9226，12 bit / 65 MSPS；2 MHz 同步采样；**实测灵敏度 416 码/V、零点 2048（无偏置）**", "控制算法", "2P2Z 数字补偿器（FPGA 内实现）"],
                  ["板卡尺寸", "120.19 mm × 86.28 mm，2 层 1 oz", "辅助电源", "LM2596×2 → 12 V / 5 V"],
              ], widths=[0.95, 1.85, 0.95, 1.95], fs=10)
    add_caption(doc, "表 1-1　主要性能指标")
    add_h(doc, "1.5　主要创新点")
    add_list(doc, "① 全数字 DPWM：调制、死区与保护全部在 200 MHz 时钟域内以数字逻辑实现（时间分辨率 5 ns），调制精度不受模拟比较器与斜坡发生器漂移影响。")
    add_list(doc, "② 周期同步“安静窗”采样：采样时刻与 PWM 周期锁定并避开开关瞬态，从源头降低采样噪声对环路的影响。")
    add_list(doc, "③ 三层保护架构：硬件比较器快速检测、FPGA 逐周期封波（数字链路固有 58 ns，含 1 µs "
                  "数字滤波后端到端约 1.0 µs）、故障闩锁＋人工复位，速度与安全兼顾。")
    add_list(doc, "④ 开尔文电流采样：分流电阻两端单独引出采样线至放大器，消除走线压降引入的测量误差。")
    add_list(doc, "⑤ 功率地与信号地分域、单点星形汇接：把 3 A 级开关电流约束在功率岛内，避免污染采样与比较器参考。")
    add_h(doc, "1.6　设计流程")
    add_fig(doc, "1-1")
    add_body(doc,
             "整机设计流程如图 1-1 所示：从需求与指标定义开始，先完成 A–I 九区原理图设计，再以网表逐网络、逐引脚核对，"
             "并做“单脚网”与“悬空元件”体检；随后完成封装与 BOM 三层核查，进入 PCB 布局布线"
             "（开关环路最小化、地分域、铜宽分级）；打样后按分层顺序焊接与上电，先开环验证驱动、"
             "死区与自举，再接入数字补偿闭环调试。")

    # ---------------- 第二部分 ----------------
    add_part(doc, "第二部分　系统组成及功能说明")
    add_h(doc, "2.1　整体介绍")
    add_body(doc,
             "系统由三块电路实体构成：功率板（本作品主体）、FPGA 控制板（Zynq-7020 开发板）与"
             "AD9226 高速 ADC 模块，二者通过 J3/J4 排针以杜邦线互连。功率板负责功率变换、辅助供电、"
             "栅极驱动、信号调理与保护；FPGA 负责数字 PWM 生成、采样时序控制、闭环补偿与故障处理；"
             "ADC 模块负责把调理后的模拟量转换为 12 bit 数字量。")
    add_fig(doc, "2-1")
    add_body(doc,
             "信号与能量流向如下：24 V 输入经 A 区滤波后，一路送入 C 区同步 Buck 功率级，另一路送入"
             "B 区辅助电源产生 12 V 与 5 V；FPGA 输出的 PWM_H／PWM_L 经 D 区（74HCT245 电平缓冲 + "
             "IR2110 浮动驱动）驱动 Q1／Q2；功率级输出经 L3 与输出电容滤波后，由 G 区端子输出至负载。"
             "E 区分压得到 VSENSE、F 区经分流电阻与 INA180A2 得到 ISENSE，两者送入 AD9226 模块，"
             "转换结果以 12 位并行数据回送 FPGA；同时 F 区的 LM393 依据 ISENSE／VSENSE 产生 FAULT_N，"
             "经 H 区送入 FPGA 触发逐周期封波。由此形成“PWM 输出 → 功率变换 → 采样 → 数字补偿 → PWM 输出”"
             "的完整数字闭环。系统整体框图见图 2-1。")

    add_h(doc, "2.2　硬件系统介绍")
    add_h(doc, "2.2.1　硬件整体介绍")
    add_body(doc,
             "功率板为 2 层板，尺寸 120.19 mm × 86.28 mm，四角圆角 R7.62 mm，板厚 1.6 mm，铜厚 1 oz，"
             "四角设 4 个 Ø3.2 mm 安装孔（孔心距 110.5 mm × 76.2 mm）。板面按功能划分为九个区（图 2-2）：")
    add_fig(doc, "2-2")
    add_table(doc,
              ["区", "名称", "主要器件与作用"],
              [
                  ["A", "电源输入", "接线端子、船型开关、防反接二极管 D1、输入电解电容与陶瓷电容，完成 24 V 输入滤波与上电控制"],
                  ["B", "辅助电源", "LM2596×2 分别产生 12 V（IR2110 驱动供电）与 5 V（逻辑与 ADC 供电），含续流二极管与输出滤波"],
                  ["C", "功率级", "IRLZ44N 上／下管（立式散热）、10 µH 一体成型电感 L3、输出电容组、10 mΩ 分流电阻"],
                  ["D", "栅极驱动", "74HCT245 电平缓冲、IR2110 浮动驱动、自举二极管与电容、栅极／栅源电阻"],
                  ["E", "电压采样", "30 kΩ 上臂与 10 kΩ+10 kΩ 电位器下臂分压，输出 VSENSE（含 RC 滤波与钳位保护）"],
                  ["F", "电流采样与保护", "INA180A2 电流检测放大器、LM393 双通道比较器分别实现 OCP 与 OVP，线与输出 FAULT_N"],
                  ["G", "输出与测试", "5 V 输出端子、测试排针 TP2、输出指示灯 LED4 与泄放电阻"],
                  ["H", "FPGA 接口", "26P 排针 J3，引出自有功能序的 PWM、SD、FAULT_N、ADC 总线、时钟与电源/地"],
                  ["I", "ADC 接口", "26P 排针 J4 接 AD9226 模块，J5／J6 引出 VSENSE／ISENSE 模拟量，含模块去耦电容"],
              ], widths=[0.4, 1.05, 4.25], fs=10)
    add_caption(doc, "表 2-1　九个功能区及其作用")

    add_h(doc, "2.2.2　机械设计介绍")
    add_body(doc,
             "机械设计围绕“散热、接线与固定”三件事展开：① 两只功率 MOSFET（TO-220）采用立式安装并"
             "预留小散热片空间，散热片垂直板面向上，上方预留 ≥25 mm 净空，避免遮挡接口与相邻电容；"
             "② 输入／输出端子分置板卡对边（J1 朝左、J2 朝右），使 3 A 级电流走成一条直线，"
             "缩短功率回路并避免输入输出交叉；③ 数字与模块接口（J3／J4）置于板卡上边并朝板外，"
             "便于杜邦线引出至 FPGA 板与 ADC 模块；④ 四角 M3 安装孔按 (6.858, 5.842) 等位置对称布置，"
             "可配铜柱固定或架高散热。板卡版图与丝印见图 2-3。")
    add_fig(doc, "2-3")
    add_body(doc,
             "整机装配后的实际形态见图 3-1 至图 3-3 的实物照片；由于本机总损耗不足 9 W、功率管与"
             "电感表面积充裕，初版不装散热片，仅在 3 A 满载长时运行时依温升实测决定是否加装。",
             indent=True)

    add_h(doc, "2.2.3　电路各模块介绍")
    add_body(doc, "以下按功能区逐块说明电路设计与关键信号，各功能区原理图依次见图 2-4 至图 2-12。", indent=True)

    add_h(doc, "（1）A 区　电源输入")
    add_body(doc,
             "24 V 输入经接线端子 J1 进入，经船型开关 SW1 后由串联肖特基二极管 D1（SS54）实现防反接保护，"
             "随后进入 24 V 母线。母线并联 100 µF 电解电容（C1、C2）与 1210 封装 10 µF 陶瓷电容（C3、C4）、"
             "1206 封装 10 µF／50 V 陶瓷电容（C11）以及 220 µF／50 V 电解电容（C23）；其中高频陶瓷电容在"
             "PCB 上紧贴功率管漏极布置，为开关电流提供就近的低阻抗回路。LED1 与限流电阻构成 24 V 上电指示。"
             "关键信号：24 V（输入）、GND。")
    add_fig(doc, "2-4")

    add_h(doc, "（2）B 区　辅助电源")
    add_body(doc,
             "采用两片 LM2596 降压型开关稳压器构成两级辅助电源：U1 由 24 V 产生 12 V，用于 IR2110 的"
             "VCC 与自举充电；U2 由 12 V 产生 5 V，供逻辑器件（74HCT245、IR2110 的 VDD）、比较器、"
             "电流检测放大器与 ADC 模块使用。每级包含续流二极管（D2、D3）、功率电感（L1 68 µH、L2 68 µH）"
             "与输出滤波电容，并各配 100 nF 高频去耦电容。关键信号：24 V、12 V、5 V、GND。")
    add_fig(doc, "2-5")

    add_h(doc, "（3）C 区　同步 Buck 功率级")
    add_body(doc,
             "功率级为同步 Buck 拓扑：上管 Q1 漏极接 24 V 母线，源极与下管 Q2 漏极相连形成开关节点 SW，"
             "SW 经 10 µH 一体成型电感 L3（额定电流 7.8 A、饱和电流 8.5 A）接至输出 VOUT；"
             "下管 Q2 源极经 10 mΩ 分流电阻接地。按 24 V→5 V、200 kHz、10 µH 计算，电感纹波电流约 1.98 A"
             "（峰峰值），额定 3 A 输出时电感峰值电流约 4.0 A，相对 8.5 A 的饱和电流留有 2 倍以上余量。"
             "输出侧并联 2×10 µF（0805）与 4×22 µF（1206）陶瓷电容构成全陶瓷输出电容组（标称 108 µF，"
             "考虑直流偏压降容后有效容量约 55 µF），并以 10 kΩ 电阻做泄放与预负载。关键信号：24 V、SW、"
             "VOUT、ISENSE_P、GND。")
    add_fig(doc, "2-6")

    add_h(doc, "（4）D 区　栅极驱动")
    add_body(doc,
             "FPGA 输出的 PWM 信号经 74HCT245 缓冲后送入 IR2110 高压浮动驱动器：HIN／LIN 分别控制"
             "高侧与低侧输出，SD 为关断输入（高电平有效），VCC 由 12 V 供电，VDD 由 5 V 供电。"
             "高侧驱动采用自举方式：自举二极管 D4（UF4007）阳极接 12 V、阴极接 VB，自举电容由 10 µF 与"
             "100 nF 并联构成，跨接于 VB 与 VS（即 SW 节点）之间；IR2110 的 COM 接在下管源极侧，"
             "保证驱动回流不流入控制地。栅极串接 10 Ω 电阻抑制振铃，栅源间并接 10 kΩ 电阻保证驱动掉电时"
             "功率管可靠关断。关键信号：PWM_H、PWM_L、SD、HO、LO、VB、SW。")
    add_fig(doc, "2-7")

    add_h(doc, "（5）E 区　电压采样")
    add_body(doc,
             "输出电压经 30 kΩ 上臂电阻与“10 kΩ 电位器 + 10 kΩ 固定电阻”下臂构成的分压网络取样，"
             "分压比可在 0.25–0.40 之间调节，工作点定为 **0.39**（5 V 输出对应 VSENSE = 1.95 V），"
             "该取值经实测确认可用：12 位 ADC 链路的实测灵敏度 **416 码/V**（手册标称 409.6 码/V，偏差 1.5 %），"
             "其零点恰为 12 位中点 **2048 码**（0 V 输入对应 2048）—— 据此推算反馈饱和点约 **12.6 V**，"
             "5 V 工作点余量约 55%，即使输出出现过冲到 6 V 亦不会饱和；折算到输出的分辨率约 **4.1 mV/码**（0.08%），"
             "配合补偿器中的积分环节可实现无静差稳压。二者的偏移与增益均在 FPGA 内以实测标定值校正。"
             "**分压器之后必须加一级单位增益运放缓冲**：AD9226 模块的模拟输入为 50 Ω 端接，而本区分压器的"
             "戴维南输出阻抗高达 12 kΩ，直接相连会把 VSENSE 衰减到不足 0.5%（仅约 3 个 ADC 码），反馈完全失效；"
             "缓冲器要求单电源 5 V、轨到轨、失调 ≤ 数百 µV，并具备 ≥50 mA 输出能力以驱动 50 Ω 端接。"
             "VSENSE 经 1 kΩ 限流电阻与 10 nF 电容组成一阶低通滤波器，"
             "并设置 BAT54S 双二极管钳位（分别针对 3.3 V 与地）与测试点 TP1，保证异常情况下不会把"
             "超范围电压送入 ADC。关键信号：VOUT、VSENSE、3V3、GND。")
    add_fig(doc, "2-8")

    add_h(doc, "（6）F 区　电流采样与保护")
    add_body(doc,
             "电流采样采用低侧方案：10 mΩ／2512 分流电阻位于下管源极与地之间，两端以开尔文方式分别"
             "引出至 INA180A2 的 IN+／IN−，放大 50 倍后得到 0.5 V/A 的 ISENSE 信号，4 A 对应 2.0 V，"
             "与 ADC 量程匹配。ISENSE 分两路使用：一路直接送往 ADC 模块（由 FPGA 在开关瞬态结束后的"
             "窗口内采样，无需额外滤波）；另一路经 1 kΩ+10 nF（τ=10 µs）滤波后送入 LM393。")
    add_body(doc,
             "保护由 LM393 双通道比较器实现：通道 1 以 3.3 V 经 4.7 kΩ 与 10 kΩ 电位器分压产生 0–2.245 V "
             "可调阈值（默认对应约 3.5 A）作为基准，与滤波后的电流信号比较，实现过流保护（OCP）；"
             "通道 2 以 3.3 V 经 R15(4.7 kΩ) 与 R16(10 kΩ) 分压得到 2.245 V 固定基准，与 VSENSE 比较"
             "实现过压保护（OVP），动作点 = 基准 ÷ 分压比 = 2.245 ÷ 0.39 ≈ 5.76 V（+15% 余量）。"
             "仿真显示满载跳变时输出过冲可达 +20 %（约 6.0 V），会越过该阈值，因此该电阻按硬件"
             "预留可调空间：若联调中确认过冲会触发误保护，把 R16 由 10 kΩ 调至 15 kΩ 即可把动作点抬到 6.4 V。"
             "设计上特别记录了二者的联动关系：若日后调整分压比，过压动作点会随之反向漂移"
             "（例如分压比取 0.25 时会漂到 9.0 V、保护形同虚设），必须同步调整 R16。过流保护"
             "（OCP）阈值取自 ISENSE 支路，与分压比无关。两路比较器输出为开集结构，"
             "直接线与形成 FAULT_N 信号并由 10 kΩ 电阻"
             "上拉至 3.3 V，任一保护动作都会拉低 FAULT_N。关键信号：ISENSE、ISENSE_P／ISENSE_N、VSENSE、"
             "FAULT_N、3V3、GND。")
    add_fig(doc, "2-9")

    add_h(doc, "（7）G 区　输出与测试")
    add_body(doc,
             "输出经 5.08 mm 间距接线端子 J2 引出，配 2P 测试排针 TP2 便于示波器探头与电子负载接线；"
             "LED4 与 1 kΩ 限流电阻构成输出指示，10 kΩ 电阻提供输出泄放与最小预负载，避免空载时"
             "输出电压因电容储能而长时间保持。关键信号：VOUT、GND。")
    add_fig(doc, "2-10")

    add_h(doc, "（8）H 区　FPGA 接口")
    add_body(doc,
             "J3 为 2×13（26P）排针，按“自有功能序”排列，通过单根母-母杜邦线接入 FPGA 板 J10 接口。"
             "引出的信号包括：PWM_H、PWM_L、SD、FAULT_N、ADC_CLK、PWM 同步脉冲（TICK）以及 12 位 ADC "
             "数据总线 ADC_D[11:0]、OTR，另含 3V3 与多处 GND。由于 FPGA 板 J10 的第 2 脚为 5 V 输出，"
             "本板不使用该脚，仅共地不共 5 V，以避免数字板电源与本板辅助电源互相串扰。"
             "关键信号：PWM_H／PWM_L／SD／FAULT_N／ADC_CLK／ADC_D[11:0]／OTR／3V3／GND。")
    add_fig(doc, "2-11")

    add_h(doc, "（9）I 区　ADC 模块接口")
    add_body(doc,
             "J4 为与 J3 同规格的 2×13 排针，用于连接 AD9226 高速 ADC 模块：1–12 脚为 ADC_D0–ADC_D11，"
             "13 脚为 OTR（超量程指示），14 脚为 ADC_CLK，并引出 5 V、3V3 与多个 GND，"
             "模块电源输入端配置 10 µF 与 100 nF 去耦电容。模拟量通过独立的 J5（VSENSE+GND）与"
             "J6（ISENSE+GND）引出，与数字接口在板面布置上保持距离，走线不穿越数字区域。"
             "需要特别说明的是，所选用的 AD9226 模块其数字输出电平由模块自身的 DRVDD 决定，"
             "必须确保其数字侧工作于 3 V／3.3 V，否则 5 V 电平将超出 FPGA IO 的绝对最大输入范围，"
             "这一约束已作为模块选型与验收的首要条件。关键信号：ADC_D[11:0]、OTR、ADC_CLK、VSENSE、"
             "ISENSE、5V、3V3、GND。")
    add_fig(doc, "2-12")

    add_h(doc, "2.3　软件系统介绍")
    add_h(doc, "2.3.1　软件整体介绍")
    add_body(doc,
             "软件部分为运行于 Zynq-7020 可编程逻辑（PL）侧的全数字控制器，采用 Verilog HDL 编写，"
             "在 Vivado 中完成综合、实现与时序约束。顶层模块聚合以下子模块：① 时钟与复位管理；"
             "② 数字 PWM 调制器（DPWM）；③ ADC 采集接口（adc_if）；④ 保护与故障处理状态机；"
             "⑤ 2P2Z 数字补偿器；⑥ 在线逻辑分析（ILA）观测探针。控制数据通路为：ADC 采样值经"
             "定标后进入 2P2Z 补偿器，输出占空比命令送入 DPWM 比较器，与载波比较后生成互补 PWM；"
             "保护状态机可随时强制封波。软件总体框图与数据通路见图 2-13。")
    add_fig(doc, "2-13")

    add_h(doc, "2.3.2　软件各模块介绍")
    add_body(doc, "（1）数字 PWM 调制器（DPWM）", indent=True)
    add_body(doc,
             "以板载 50 MHz 时钟经 PLL 倍频至 200 MHz 作为计数时钟，周期寄存器设定为 5000 ns"
             "（对应 200 kHz）。占空比命令与递增载波比较产生高侧 PWM，取反并插入 200 ns 数字死区后"
             "形成低侧 PWM，两路信号严格互补且死区固定。在 200 MHz 时钟域内，脉宽调节步进可达"
             "时间分辨率 5 ns（占空比步进 0.1%）。输出为标准 3.3 V LVCMOS33 电平。关键输入：占空比命令、使能；"
             "关键输出：PWM_H、PWM_L、PWM 周期同步脉冲。死区取 200 ns（40 个计数）而非最初的 20 ns，"
             "依据是 IR2110 两路传输延迟本身滞后约 120 ns／95 ns、且两路失配可达 10~25 ns，20 ns 的数字死区"
             "传到栅极后可能变为负值而形成直通；上板实测印证了这一点（见 3.4 节）。ILA 实测：pwm_h 高电平 "
             "15.6 %、pwm_l 76.6 %、死区 40 个 5 ns 点，两路在全部采样点无重叠。")
    add_body(doc, "（2）ADC 采集接口（adc_if）", indent=True)
    add_body(doc,
             "负责产生 2 MHz ADC_CLK（200 MHz ÷ 100），与 PWM 同源，采样相位固定。在每个 PWM 周期的"
             "安静窗内采三次（第 220／250／280 拍，间隔 150 ns），第 281 拍做“三点取二”多数表决，"
             "使单点毛刺不进入环路。模块还包含位序映射、OTR 超量程状态采集、采样有效性标志、"
             "上电预热计数与采样相位确定性控制；RTL 仿真自检 7/7 通过。")
    add_body(doc,
             "位序口径以模块手册（第 4~5 页）为准：模块 `D0` 为最低位（LSB）、`D11` 为最高位（MSB），"
             "与 FPGA 的接线满足“J10 针号 = 9 + D 编号”（D11→J10:20 … D0→J10:9）；RTL 侧的取反开关"
             "（`adc_inv_off`）使最终码值随输入电压单调递增——这一点由下表的三点直流标定直接验证。")
    add_table(doc,
              ["输入（DC，50 Ω 源）", "实测码值", "理论值（2048 + 409.6×V）"],
              [["0.0 V", "2053", "2048"],
               ["+1.0 V", "2464", "2457"],
               ["+2.0 V", "2880", "2867"]],
              widths=[1.9, 1.5, 1.9], fs=10.5)
    add_caption(doc, "表 2-2　AD9226 链路三点直流标定（实测）")
    add_body(doc,
             "最小二乘拟合得 **code = 2048 + 416×Vin**，灵敏度 416 码/V（手册 409.6 码/V，偏差 1.5 %），"
             "零点恰为中点 2048 码（无偏置），重复采样抖动仅 ±1 LSB。据此在 FPGA 内以实测灵敏度完成码值—"
             "电压换算，并把参考码定为 2453（对应 5 V 经 0.2017 分压后的名义值）。采样相位与 PWM 波形的对齐关系见图 2-14。")
    add_fig(doc, "2-14")
    add_body(doc, "（3）模拟接口阻抗匹配（上板发现并解决）", indent=True)
    add_body(doc,
             "这一节记录的问题只有上板才会暴露：功率板的 VSENSE 是一个高阻节点（分压器戴维南阻抗实测约 "
             "10.6 kΩ），而 AD9226 模块的模拟输入端内部为 50 Ω 端接。两者直连时，50 Ω 负载把分压点"
             "“吊”了下来——实测 VSENSE 由 1.70 V 跌到 **0.047 V**（衰减到约 1/36），折算到输出只剩十余个 "
             "ADC 码，反馈通道实际上已经完全失效。")
    add_body(doc,
             "解决方式分两层：① **本版（不改板）**：在板外用 220 Ω／2.2 kΩ 构成低阻分压（戴维南阻抗仅约 "
             "200 Ω，远小于 50 Ω 输入对它的影响可以忽略），实测分压比 **0.2017**，参考码定为 2453；"
             "② **下一版（改板）**：在功率板上增设一级单位增益运放跟随器（单电源 5 V、轨到轨、低失调、"
             "输出能力 ≥50 mA 以驱动 50 Ω 负载），从根本上消除负载效应。")
    add_body(doc,
             "这一问题的价值在于它纠正了一个容易想当然的假设：分压电阻的比值只决定“算出来的电压”，"
             "而**谁能驱动负载才决定“量到的电压”**——高阻分压后必须紧跟缓冲级，这是模拟接口的常识性纪律，"
             "也是本作品从“仿真通过”走向“上板可用”之间必须跨过的一道坎。")
    add_body(doc, "（4）保护与故障处理", indent=True)
    add_body(doc,
             "以 FAULT_N 为触发源，采用两级保护：第一级是**逐周期封锁**，核心封波逻辑只用 2 个 "
             "200 MHz 时钟周期（10 ns），故障消失后自动恢复，用于抑制瞬时过流；第二级是**闩锁关断**，"
             "置位故障标志并保持关断，直至人工复位（PL 按键）。**数字链路本身的固有延迟是 58 ns**"
             "（FAULT_N 引脚→PWM 引脚，含 2FF 同步器与输出寄存器，在未加滤波时实测）；"
             "此后为抑制比较器毛刺又串入 1 µs 数字滤波，因此当前配置下故障到封波的端到端延迟约 1.0 µs。"
             "功率管真正关断还需再叠加 IR2110 约 95~120 ns 的传输延迟。同时可通过 SD 信号直接关闭 IR2110 "
             "输出，形成“硬件比较器 + 数字封波 + 闩锁”的多重保护。已通过封波、SD 关断、逐周期自恢复、闩锁不自动恢复、复位解除与响应时间六项证据验证。")
    add_body(doc,
             "上板后暴露的一个问题促成了保护逻辑的关键加固：FAULT_N 最初没有数字滤波，比较器输出上一个"
             "纳秒级毛刺被同步链采到后即触发闩锁，表现为“复位后驱动立刻关断、输出仅 0.6 V”，"
             "极易被误判为功率级损坏。改进为**1 µs 数字滤波 + 2.62 ms 上电消隐**后，误锁存消失，"
             "而真实短路过流仍在 1 µs 内被可靠封锁（详见 3.4 节第 3 条）。")
    add_body(doc, "（5）2P2Z 数字补偿器与端到端闭环仿真", indent=True)
    add_body(doc,
             "依据功率级参数（L=10 µH、C≈55 µF 有效值、开关频率 200 kHz、负载 0–3 A）设计两极点两零点"
             "补偿器。由于输出电容为全陶瓷方案、ESR 仅约 1–2 mΩ，其 ESR 零点位于约 1.4 MHz，"
             "远高于目标穿越频率，因此补偿器必须自行提供足够的相位超前；输出 LC 双极点的品质因数"
             "Q = R·√(C/L) ≈ 3.9、谐振频率约 6.8 kHz，穿越频率只能取在谐振点附近（约 7 kHz），"
             "相位裕度约 82°。曾尝试把穿越频率提高到 10 kHz，相位裕度骤降至 14°，予以否决。"
             "最终定稿：穿越频率 6.98 kHz；相位裕度的设计目标为 82.6°，含采样与环延时模型的闭环仿真结果为 83.9°。"
             "另用解析模型（2P2Z × Buck 二阶振荡环节 × e^(−sTd)，Td = 7.5 µs）独立复核，得 fc = 6.99 kHz、"
             "PM = 83.5°——两种建模方式相差不到 2 %，互为印证，说明该环路的稳定性结论对建模假设不敏感。"
             "实现上采用 Q14 定点系数、48 位累加器与内部状态限幅（抗积分饱和），"
             "并与 Python 参考实现逐点对拍 1100 点，失配 0 点。")
    add_body(doc,
             "为在设计阶段暴露问题，我们搭建了端到端 RTL 闭环仿真链：被控对象（LC 功率级）平均模型 → "
             "AD9226 采样模型 → adc_if 采集接口 → 2P2Z 补偿器 → DPWM 调制器，整条链路在 RTL 层闭合，"
             "稳态收敛到 4.99 V（设定 5.0 V）、占空比 208（理论 208），"
             "且振荡幅度单调衰减，证明环路稳定。仿真同时给出了环路延迟："
             "AD9226 流水线 7 拍（3.5 µs）+ 数据锁存相位（≈3.45 µs）+ 补偿器计算（50 ns）≈ 7.0 µs"
             "（1.4 个开关周期）。闭环仿真的稳态结果为：Vout = 4.9946 V、输出纹波 14.9 mV。"
             "负载跳变目前只有仿真结果：0.7→3 A 时跌落 15.3 %、3→0.3 A 时过冲 20.2 %、恢复时间约 4.0 ms（回程过冲恢复 2.5 ms），实测负载阶跃待补。"
             "按解析模型绘制的环路开环波特图见图 2-15。")
    add_fig(doc, "2-15")
    add_body(doc,
             "仿真与器件手册的交叉核对纠正了一处关键假设，是本作品“仿真驱动设计”的直接体现："
             "仿真最初按“ADC 输入 0–2 V、2048 码/V”建模，据此判断分压比 0.39 时反馈余量仅 2.5%、"
             "并建议下调分压比；进一步核对 AD9226 模块的实际传输特性（模拟输入 ±5 V 对应全量程，"
             "即 409.6 码/V、0 V 对应码值中点 2048）后确认——原分压比下的反馈饱和点为 12.8 V，"
             "余量充足，分压比应维持 0.39 不变。这一过程说明：**采样通道的“量程与灵敏度”"
             "必须以器件手册为准，不能凭直觉假设**；同时也暴露出仿真模型的输入条件本身需要被验证。")
    add_body(doc,
             "核对中还发现一个必须由硬件解决的前提：模块的模拟输入为 50 Ω 端接，"
             "而反馈分压器的戴维南阻抗约 2.5 kΩ，直接相连时 VSENSE 会被分压到不足 2%"
             "（折算到输出仅十余个 ADC 码），反馈将完全失效。因此在功率板上增设一级"
             "单位增益运放缓冲（单电源 5 V、轨到轨、低失调、具备数十 mA 输出能力），"
             "使分压器不被吊载、并能驱动模块的 50 Ω 输入。")
    add_body(doc, "（6）引脚与时序约束", indent=True)
    add_body(doc,
             "通过 XDC 文件对 13 根 ADC 引脚及其余控制信号进行管脚绑定与电平标准约束（LVCMOS33），"
             "已完成综合实现并满足时序（最差负裕量 WNS 为正）。")

    # ---------------- 第三部分 ----------------
    add_part(doc, "第三部分　完成情况及性能参数")
    add_h(doc, "3.1　整体介绍")
    add_body(doc,
             "截至文档编写时，系统已完成原理图设计、板级核查、PCB 设计与投板、功率板焊接与整机联调："
             "数字 PWM、ADC 采集、2P2Z 补偿与三层保护均已在实际硬件上闭环运行，**闭环稳压输出 5.00–5.01 V、"
             "ADC 稳态误差 0 码**，综合时序余量 +0.581 ns。功率板功率级上电调试历时 6 天，"
             "期间发现并修正的三个硬件问题已整理为 3.4 节。")
    add_fig(doc, "3-1")
    add_fig(doc, "3-2")

    add_h(doc, "3.2　工程成果")
    add_h(doc, "3.2.1　机械成果")
    add_body(doc,
             "完成功率板机械设计：120.19 mm × 86.28 mm 圆角板形、四角 M3 安装孔、端子分置对边、"
             "功率管立式散热布局与接口朝上布置。Gerber 输出经投板前检查，层叠、钻孔、板框与安装孔"
             "参数均符合设计预期。")
    add_fig(doc, "3-3")

    add_h(doc, "3.2.2　电路成果")
    add_body(doc,
             "完成 A–I 九个功能区的原理图设计与全网络核对：整板共 51 个网络、86 个元件，"
             "经网表逐引脚比对，实现零单脚网络、零悬空元件；完成封装与 BOM 三层核查（封装比对、"
             "元件参数与编号核对），并据此完成打样投板。整机原理图总览、布线与地平面分域分别见图 3-4、图 3-5。")
    add_fig(doc, "3-4")
    add_fig(doc, "3-5")

    add_h(doc, "3.2.3　软件成果")
    add_body(doc,
             "完成 DPWM、保护链路与 ADC 采集接口的 RTL 设计与验证：DPWM 已在开发板上实测输出"
             "200.00 kHz 的互补波形，开环 20 % 工况下高低侧脉宽分别为 980 ns 与 3980 ns，闭环带载（2 Ω）高侧占空比 22.6~23.0 %，死区实测 200 ns（ILA 40 拍），"
             "输出电平为 3.3 V LVCMOS33；保护链路六项证据齐备；ADC 接口自检 7/7 通过。")
    add_body(doc,
             "完成端到端 RTL 闭环仿真链（被控对象模型 → AD9226 模型 → adc_if → 2P2Z → DPWM），"
             "稳态收敛到 4.99 V、相位裕度 83.9°、环路总延时 7.0 µs（1.4 个开关周期），"
             "并据此定稿数字软启动时间（约 5 ms）；实测标定了 ADC 链路的灵敏度（416 码/V）与零点"
             "（2048 码中点），确认板上分压比 0.39 的反馈饱和点约 12.6 V、OVP 动作点 5.76 V 不变。"
             "上板联调时进一步发现模块 50 Ω 输入阻抗会把 10.6 kΩ 的 VSENSE 分压器“吊载”到不足 4 %，"
             "改用板外 220 Ω／2.2 kΩ 低阻分压（0.2017、参考码 2453）后反馈链路恢复正常并完成闭环；"
             "下一版将在板上增设运放跟随器。详见 2.3.2 节。DPWM 互补波形与死区、保护误锁存修复前后对比、"
             "ILA 实测闭环稳态分别见图 3-6、图 3-7、图 3-8。")
    add_fig(doc, "3-6")
    add_fig(doc, "3-7")
    add_fig(doc, "3-8")
    add_h(doc, "3.3　特性成果")
    add_body(doc, "已完成的量化指标如下表。效率与温升受现有测试负载与线材条件限制尚未测全，如实留待后续补齐。")
    add_table(doc,
              ["序号", "量化指标", "设计值／预期", "实测结果", "状态"],
              [
                  ["1", "开关频率", "200 kHz（周期 5000 ns）", "200.00 kHz", "已实测"],
                  ["2", "占空比（闭环，带载 2 Ω / 空载）", "≈23 %", "22.6~23.0 %（带载）／16.8 %（空载）", "已实测"],
                  ["3", "高低侧脉宽（开环 20 % 工况）", "≈1000 / 3800 ns", "980 ns / 3980 ns", "已实测"],
                  ["4", "死区时间", "200 ns（40 个 5 ns 计数值）", "200 ns（ILA 40 拍）", "已实测"],
                  ["5", "PWM 输出电平", "3.3 V LVCMOS33", "3.3 V", "已实测"],
                  ["6", "保护响应时间", "≤ 100 ns（数字链路）", "数字链路 58 ns；含 1 µs 滤波约 1.0 µs；驱动再加 95~120 ns", "已实测"],
                  ["7", "ADC 接口自检", "全部通过", "7/7 通过；灵敏度 416 码/V", "已实测"],
                  ["8", "输出电压（闭环）", "5.00 V", "5.00–5.01 V；稳态误差 0 码", "已实测"],
                  ["9", "输出纹波", "≤ 50 mV", "60 mV（AC 耦合 + 短地弹簧）", "已实测"],
                  ["10", "负载阶跃响应（仿真）", "过冲／跌落 ≤ 20 %、恢复 ≤ 5 ms", "仿真：−15.3 %／+20.2 %、4.0/2.5 ms", "仅仿真，实测待补"],
                  ["11", "效率", "—", "待测", "待测"],
                  ["12", "过流保护点", "3.5 A", "6 项保护联调通过", "已实测"],
                  ["13", "综合时序余量", "WNS ≥ 0", "+0.581 ns", "已实测"],
                   ["14", "启动过冲（KEY1 复位，2 Ω 负载）", "≤ 5 %（软启动 5 ms）", "峰值 6.56 V（+24 %），尖峰短于 1 µs 滤波未触发保护", "已实测，下一版改进"],
              ], widths=[0.45, 1.45, 1.6, 1.2, 1.0], fs=10)
    add_caption(doc, "表 3-1　量化指标完成情况")
    add_h(doc, "3.4　上板调试中的三个典型问题")
    add_body(doc, "功率板首次上电到闭环跑通的 6 天里，出现了三个具有代表性的问题。"
                  "它们都不是算法错误，而是\u201c设计假设与真实硬件不符\u201d，且都在损坏器件之前被定位：")
    add_table(doc,
              ["问题", "现象", "根因", "修复"],
              [
                  ["**电解电容极性丝印反了**",
                   "上电即 3.6 W 过载，输入被拉到 12 V/300 mA，C14/C23 发烫",
                   "PCB 封装正负极与原理图相反，按丝印装即全部反接",
                   "按原理图方向重焊 → 空载 13 mA"],
                  ["**死区 20 ns 太短**",
                   "PWM 一启动输入电流冲满 300 mA 限流，14.8 V 跌落，Q1/Q2 发烫",
                   "IR2110 两路传输延迟约 120/95 ns、失配 10~25 ns，20 ns 死区到栅极可能变负（直通）",
                   "死区改 **200 ns** → 电流降至 46 mA"],
                  ["**FAULT_N 无数字滤波**",
                   "复位后 SD 立即回高、功率级\u201c假死\u201d，VOUT 仅 0.6 V",
                   "比较器输出毛刺被同步器采到即闩锁，系统进入永久故障态",
                   "加 **1 µs 数字滤波 + 2.62 ms 上电消隐**"],
              ], widths=[1.15, 1.70, 1.75, 1.10], fs=9)
    add_caption(doc, "表 3-2　上板调试中的三个典型问题")
    add_body(doc, "第三个问题的定位方法尤其值得记录：先用\u201c旁路保护\u201d实验证明功率级本身完全正常"
                  "（开环占空比能正常建立输出），才把怀疑范围收窄到保护逻辑自身，"
                  "避免了对功率器件的无谓拆换。")
    add_h(doc, "3.5　测量方法与常见陷阱")
    add_body(doc, "上板调试中，多次\u201c测量结论\u201d本身是错的，最终都回到\u201c先证明工具可信\u201d这一原则：")
    add_list(doc, "① 万用表量高速数字线（2 MHz 方波）读到的是平均值（0.7~1.2 V），"
                  "曾被误判为\u201cAD9226 损坏\u201d；改用示波器后确认波形完整。")
    add_list(doc, "② 示波器用长地线夹量纹波，探头环路拾取开关辐射，看到约 1 V 的假纹波；"
                  "换短地弹簧后真实纹波仅 60 mV。")
    add_list(doc, "③ 在线逻辑分析仪窗口只有 10 µs，无法覆盖毫秒级故障；"
                  "曾据此得出\u201c硬件没坏\u201d的错误结论，后改用长窗口与分段触发。")
    add_list(doc, "④ 判断 MOS 是否导通用在线测 Rds(on)，需先扣除探头与走线电阻。")
    add_list(doc, "⑤ 任何\u201c执行器不动\u201d的现象，先证明执行器本身能动（开环直驱），再查控制链路。")
    add_h(doc, "3.6　实测暴露的不足与下一版改进")
    add_body(doc,
             "把实测中暴露的问题如实记录下来，既是对作品的自我审查，也是下一版设计的输入。"
             "最突出的一项是启动过冲：按 KEY1 复位、带 2 Ω 负载重新启动时，输出实测峰值 6.56 V（约 +24 %），"
             "已超过 OVP 参考电压 5.76 V；由于过冲尖峰持续时间短于 1 µs 数字滤波窗口，保护未动作，"
             "输出在 2 ms 内恢复至 5 V（图 3-9）。根因是本版软启动仅以参考码线性斜坡实现，"
             "未做成带占空比斜率限制的启动状态机，输出建立瞬间环路饱和。下一版将把软启动改为带"
             "占空比斜率限制（duty slew limit）的状态机并减小参考斜坡步长，同时复核 OVP 阈值、"
             "比较器基准与 1 µs 滤波窗口三者的配合关系。")
    add_fig(doc, "3-9")
    add_body(doc,
             "反馈与功率通路还有三处需在下一版修正：① AD9226 模块的输入端为 50 Ω 端接，"
             "无法由板上 10.6 kΩ 的反馈分压器驱动（实测直连时 1.70 V 跌至 0.047 V），本版以板外"
             "220 Ω／2.2 kΩ 低阻分压绕过，下一版应在板上增设一级轨到轨（RRIO）运放跟随器、"
             "把电压采样口改为 SMA 座，使源阻抗降到 1 Ω 以下，可直接驱动 50 Ω 负载；"
             "② 反馈取样点位于输出端子之前，实测 J2 端子 5.33 V 时负载端仅 5.00 V，线损不可忽略，"
             "下一版应把取样点移到负载侧（或改用四线取样）；③ 输出端子与功率铜箔的等效回路电阻约 0.19 Ω，"
             "大电流下压降与损耗显著，不满足 3 A 额定输出的要求，下一版需把输出口改为插拔式大电流接线端子"
             "（额定 ≥10 A、焊盘加宽并辅以多个过孔、阻焊开窗加锡），功率铜箔加宽至 2 mm 以上并采用 2 oz 铜。")
    add_body(doc,
             "保护阈值也需在下一版重新标定：OVP 的设计目标是 5.76 V（按板内分压比换算），但实际动作点本版未做实测标定——"
             "该阈值由比较器基准与分压比反推，而基准实际取值与分压电阻容差尚未逐台核实，不能当作已实测指标引用；"
              "下一版将以可编程基准逐点测出实际动作点，再据此重选分压电阻（而非简单抬高阈值），"
             "并同步复核 ADC 满量程与 OTR 引脚的状态。此外 FAULT_N 缺少 RC 与迟滞、"
             "板级缺少关键测试点、12 V 输入需标注 VIN ≥ 16 V 等细节，均已列入下一版改板清单。")
    add_body(doc,
             "受现有电子负载与线材条件限制，效率与温升尚未完成全工况测量，本报告如实留待后续补齐。"
             "已有的实测线索表明功率通路损耗是效率的主要瓶颈，这一点与上述端子、铜箔问题相互印证，"
             "也说明下一版的改进重点应放在功率通路而不是控制算法。")

    # ---------------- 第四部分 ----------------
    add_part(doc, "第四部分　总结")
    add_h(doc, "4.1　可扩展之处")
    add_body(doc,
             "① 控制算法扩展：在现有 2P2Z 基础上可并行实现 PID、滑模、无差拍或模型预测控制，"
             "并借助 FPGA 的并行特性做多算法在线对比；② 系统级扩展：可扩展为多相并联 Buck 或加入"
             "同步整流优化、软启动与均流控制，提高功率等级与效率；③ 器件升级：将硅基 MOSFET 替换为"
             "GaN／SiC 器件并把开关频率提高一个数量级，验证高带宽数字控制的价值；④ 通信与监控（本版未实现，仅作扩展方向）："
             "可后续在 Zynq 的 PS 侧运行嵌入式程序，通过 USB／以太网／CAN 上传运行数据并实现上位机监控与"
             "参数在线整定；⑤ 能量双向：改造为双向 Buck/Boost，用于电池充放电与储能变换场景。")
    add_h(doc, "4.2　心得体会")
    add_body(doc,
             "这次设计的最大收获，是认识到数字电源的难点并不只在算法，而在“数字与模拟的接口处”。"
             "FPGA 可以把时序做到纳秒级、把补偿器写成几十行 RTL，但要让环路真正稳定工作，"
             "必须先解决采样点落在哪里、开关噪声如何不进入采样通道、功率回路的地电流如何不污染"
             "比较器基准这些看似“不算法”的问题。为此我们在原理图阶段就把采样链路与保护链路分开设计，"
             "在 PCB 阶段坚持开关环路面积最小化、功率地与信号地分域单点汇接、电流采样开尔文连接，"
             "并按载流把铜宽分级。回头看，这些约束比任何一行 RTL 都更能决定成败。")
    add_body(doc,
             "第二点体会是“核对”的价值。我们在原理图完成后坚持用 EDA 导出的网表逐网络、逐引脚比对，"
             "并用“单脚网络”和“悬空元件”两个指标做体检，先后发现并修正了电源网络被误合并、"
             "自举电源误接到开关节点、缓冲器输入错挂、无源支路漏接、电感参数单位写错等问题；"
             "在二极管极性核对中，还发现换料会导致元件引脚号变化，必须逐一对照符号与网络确认方向。"
             "这些错误如果留到板子回来才发现，代价将是飞线甚至炸管。我们由此养成了“每改一次就重新导出、"
             "重新比对”的习惯，也体会到工程上“可验证”比“看起来对”重要得多。")
    add_body(doc,
             "第三点体会来自分工与协作。一人主攻 PL 侧逻辑与时序，一人主攻功率级、器件选型与板级实现，"
             "通过接口表把跨专业边界“冻结”下来，并约定只以文档与仓库为准，避免口头传递造成偏差。"
             "当发现接口表里针号定义与实物不符时，我们没有回避，而是用示波器与信号源逐脚实测频率，"
             "把针号定义重新确认到物理事实，再回写文档——这件事让我们明白，接口是两个人的契约，"
             "必须以可复现的证据来维护。")
    add_body(doc,
             "首次上电暴露的一个问题很值得记录：24 V 输入一上电即进入恒流限流（150 mA），电压由 24 V 跌到 12 V"
             "并继续下塌。断电检查显示全部静态电阻正常（24 V–GND 开路、开关节点对地 7.84 kΩ），说明不是死短路；"
             "而“电压越低、输入电流反而越大”是典型的恒功率负载特征，据此把怀疑范围收窄到后级变换器所带的负载。"
             "最终定位到 24 V 母线电解电容：原理图使用的是无极性电容符号（无 `+` 标记），而 PCB 采用带 `+` 丝印的"
             "电解封装，封装把 `+` 固定在 1 脚；该实例因符号镜像使 1 脚接到 GND，于是板级丝印与电气极性相反，"
             "按丝印装配即造成反接，电容发热鼓包并产生大漏电流。按实测焊盘电压重新装配后，板卡恢复正常（空载 CV 正常）。")
    add_body(doc,
             "这一教训指向两类可复用的做法：其一，**符号与封装的信息必须一致** —— 有极性器件必须使用带极性的符号，"
             "否则旋转/镜像时没有任何视觉提示；其二，**DRC 只检查线宽、间距与短路，不检查极性**，"
             "所以必须把“极性端 → 所接网络是否符合电气直觉”列为独立的打板前检查项，并在首板上电时"
             "以**实测焊盘电压**（而非丝印）确认极性。")
    add_body(doc,
             "最后是时间与风险的管理。我们把工作拆成若干可验证的阶段性目标（DPWM 上板、采样通路打通、"
             "保护链路验证、闭环稳定），每个目标都有明确的判据与截止时间，宁可提前完成也不留到最后。"
             "正是这种“小步可验证”的推进方式，让我们在打板等待期内仍能推进数字侧验证，"
             "把不确定性尽量前移、尽早暴露。这些方法上的收获，比这块板子本身更值得带走。")

    # ---------------- 第五部分 ----------------
    add_part(doc, "第五部分　参考文献")
    refs = [
        "[1] Analog Devices. AD9226: 12-Bit, 65 MSPS, 1.8 V/3 V/5 V Analog-to-Digital Converter Data Sheet[Z]. Analog Devices, Inc.",
        "[2] Infineon Technologies. IR2110 / IR2113 High and Low Side Driver Data Sheet[Z]. Infineon Technologies AG.",
        "[3] Texas Instruments. INA180 Low- and High-Side Voltage Output, Current-Sense Amplifiers Data Sheet[Z]. Texas Instruments.",
        "[4] Texas Instruments. LM2596 SIMPLE SWITCHER 3-A Step-Down Voltage Regulator Data Sheet[Z]. Texas Instruments.",
        "[5] Texas Instruments. LM393 Low-Power, Low-Offset Voltage, Dual Comparators Data Sheet[Z]. Texas Instruments.",
        "[6] Infineon Technologies. IRLZ44N HEXFET Power MOSFET Data Sheet[Z]. Infineon Technologies AG.",
        "[7] Vishay Semiconductors. BAT54S Small Signal Schottky Diodes Data Sheet[Z]. Vishay Intertechnology.",
        "[8] AMD (Xilinx). 7 Series FPGAs SelectIO Resources User Guide (UG471)[Z]. AMD.",
        "[9] AMD (Xilinx). Vivado Design Suite User Guide: Using Constraints (UG903)[Z]. AMD.",
        "[10] IPC. IPC-2221B: Generic Standard on Printed Board Design[S]. IPC — Association Connecting Electronics Industries.",
        "[11] 王兆安, 刘进军. 电力电子技术[M]. 北京: 机械工业出版社.",
        "[12] 张卫平. 开关变换器的建模与控制[M]. 北京: 中国电力出版社.",
    ]
    for r in refs:
        add_list(doc, r)

    out = os.path.join(BASE, "技术文档-FPGA数字电源-20261012.docx")
    doc.save(out)
    print("saved:", out)
    write_checklist()


if __name__ == "__main__":
    fig_design_flow()
    fig_system()
    fig_zones()
    fig_fpga_arch()
    fig_sample_phase()
    build()
