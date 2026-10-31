# -*- coding: utf-8 -*-
"""校验生成的技术文档：页眉图片、页脚页码、版心、表格/插图宽度、结构。"""
import os
import sys
import zipfile
from docx import Document

# 本脚本位于 <项目>/04-技术文档/工具/，故 BASE 取上一级
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCX = os.path.join(BASE, "技术文档-FPGA数字电源-20261012.docx")

z = zipfile.ZipFile(DOCX)
names = z.namelist()
print("媒体:", [n for n in names if n.startswith("word/media")])
print("页眉:", [n for n in names if "header" in n])
print("页脚:", [n for n in names if "footer" in n])

h = z.read("word/header1.xml").decode("utf-8")
print("header1 含图片:", "<w:drawing>" in h)
if "wp:extent" in h:
    cx = h.split('wp:extent cx="')[1].split('"')[0]
    cy = h.split('cy="')[1].split('"')[0]
    print("  图片尺寸: %.3f x %.3f in (EMU %s x %s)" % (int(cx) / 914400, int(cy) / 914400, cx, cy))
rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
print("document 引用 header1:", "header1.xml" in rels)

f = z.read("word/footer1.xml").decode("utf-8")
print("footer1 含 PAGE 域:", "PAGE" in f)

d = Document(DOCX)
s = d.sections[0]
tw = (s.page_width - s.left_margin - s.right_margin) / 914400
print("页面: %.3f x %.3f in  版心宽 %.3f in  边距 L/R %.3f / T/B %.3f" % (
    s.page_width / 914400, s.page_height / 914400, tw,
    s.left_margin / 914400, s.top_margin / 914400))
print("页眉是否继承模板:", d.sections[0].header is not None)
hp = [p.text for p in d.sections[0].header.paragraphs]
print("页眉段落数:", len(hp), "文本:", hp)
print("段落数:", len(d.paragraphs), " 表格数:", len(d.tables))
for i, t in enumerate(d.tables):
    w = sum((c.width or 0) for c in t.rows[0].cells) / 914400
    flag = "OK" if w <= tw else "★溢出"
    print("  表%d: %d行 x %d列  宽 %.3f in  %s" % (i + 1, len(t.rows), len(t.columns), w, flag))
for i, sh in enumerate(d.inline_shapes):
    w = sh.width / 914400
    flag = "OK" if w <= tw else "★溢出"
    print("  图%d: 宽 %.3f in (%.2f x %.2f in)  %s" % (
        i + 1, w, w, sh.height / 914400, flag))

must = ["摘要", "第一部分", "第二部分", "第三部分", "第四部分", "第五部分", "参考文献"]
allt = "\n".join(p.text for p in d.paragraphs)
print("章节齐备:", all(m in allt for m in must), [m for m in must if m not in allt])
