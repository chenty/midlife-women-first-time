#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中年女人的第一次 · 反同质化检测

比对最近若干篇草稿/成稿，找出"骨架重合"的位置，防止批量产出后读者觉得篇篇一样。

用法:
    python3 scripts/check_variation.py 第1篇.md 第2篇.md 第3篇.md
    python3 scripts/check_variation.py 稿子/*.md --json

退出码: 0 = 无明显重合, 1 = 有高度重合项
"""

import argparse
import json
import re
import sys
from pathlib import Path

GOLDEN = {
    "账本式": r"都叫[^。！？\n]{0,25}才叫",
    "归属式": r"是她的[^。！？\n]{0,25}永远",
    "时间对比式": r"[^。！？\n]{0,12}头一[回次][^。！？\n]{0,12}知道",
    "反面定义式": r"不是要[^。！？\n]{0,25}要的是",
    "微小定量式": r"那么[零一二三四五六七八九十两0-9][^。！？\n]{0,6}",
    "动作收束式": r"在她手里",
}
ACTION_VERBS = "调拿坐走推拧握翻插停站蹲拎提换擦写完"
# 「作者收回判断」的位置——最容易固化成套路的一个动作
INSIGHT = ["我没夸", "现在不这么想", "我当时以为", "我当下以为", "我原以为",
           "后来才知道", "现在想想", "我原来", "后来我才",
           "我才想明白", "我才知道", "我才意识到", "我才发现"]


def paragraphs(path: Path):
    raw = path.read_text(encoding="utf-8").splitlines()
    ps = [l.strip() for l in raw if l.strip() and not l.strip().startswith("<!--")]
    if ps and ps[0].startswith("#"):
        ps = ps[1:]
    return ps


def fingerprint(path: Path) -> dict:
    ps = paragraphs(path)
    body = "\n".join(ps)
    tail = "\n".join(ps[-6:])
    head = body[: max(1, int(len(body) * 0.4))]

    # 入口类型
    p0 = ps[0] if ps else ""
    if re.search(r"[0-9零一二三四五六七八九十百]+(条|个|次|人|岁|年|回)", p0[:25]):
        entry = "数字先行"
    elif p0[:1] in "\"\u201c\u300c'":
        entry = "原话先行"
    elif any(v in p0[:25] for v in ACTION_VERBS) and len(p0) <= 60:
        entry = "动作开场"
    else:
        entry = "陈述开场"

    # 连问三句
    triple_ask = head.count("？") >= 2 and ("摇头" in head)

    # 金句句式
    g = {k: len(re.findall(v, body)) for k, v in GOLDEN.items()}
    g = {k: v for k, v in g.items() if v}

    # 结局形态
    if re.search(r"不考了|放弃|退费|退钱|算了", tail):
        ending = "C·放弃"
    elif re.search(r"还没|没有|不知道|不开|用不上", tail):
        ending = "A·未完成"
    elif re.search(r"拿到了|买了|开上|到手", tail):
        ending = "B·完成有代价"
    else:
        ending = "其他"

    # 结尾提问类型
    last = next((p for p in reversed(ps) if re.search(r"[\u4e00-\u9fff]", p)), "")
    if re.search(r"什么时候|上一次|哪一年", last):
        q = "时间式"
    elif re.search(r"钱|花|买", last):
        q = "钱式"
    elif re.search(r"有没有|是不是", last):
        q = "未完成/存货式"
    else:
        q = "其他"

    pos = sorted(round(body.find(kw) / max(len(body), 1) * 100)
                 for kw in INSIGHT if body.find(kw) >= 0)
    insight = pos[-1] if pos else None          # 取最后一次＝真正的"收回判断"
    late = [x for x in pos if 70 <= x <= 100]

    return {
        "file": path.name,
        "顿悟位置": insight if insight is not None else "无",
        "_late": late,
        "字数": len(re.sub(r"\s", "", body)),
        "入口": entry,
        "连问三句": triple_ask,
        "金句": tuple(sorted(g.keys())),
        "结局": ending,
        "结尾提问": q,
        "粗体": body.count("**") // 2,
    }


DIMENSIONS = ["入口", "连问三句", "金句", "结局", "结尾提问"]


def main():
    ap = argparse.ArgumentParser(description="反同质化检测：找出篇与篇之间重叠的骨架特征")
    ap.add_argument("files", nargs="+", help="2 篇及以上的草稿/成稿")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    paths = [Path(f) for f in a.files]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        print("找不到文件：" + "、".join(missing), file=sys.stderr)
        return 2
    if len(paths) < 2:
        print("至少给 2 篇才能比对。", file=sys.stderr)
        return 2

    fps = [fingerprint(p) for p in paths]
    flags = []
    for dim in DIMENSIONS:
        vals = [str(f[dim]) for f in fps]
        if len(set(vals)) == 1 and len(vals) >= 2:
            flags.append((dim, vals[0], "全部相同"))
        elif len(vals) >= 3 and vals.count(vals[0]) >= 2 and len(set(vals)) == 1:
            flags.append((dim, vals[0], "重复"))

    lates = [f["_late"][0] for f in fps if f["_late"]]
    if len(lates) >= 2 and max(lates) - min(lates) <= 12:
        flags.append(("顿悟位置", f"{min(lates)}%–{max(lates)}%",
                      "都在同一位置出现「作者收回判断」"))

    for f in fps:
        f.pop("_late", None)

    if a.json:
        print(json.dumps({"fingerprints": fps,
                          "collisions": [{"维度": d, "值": v, "说明": m} for d, v, m in flags]},
                         ensure_ascii=False, indent=2))
        return 1 if flags else 0

    print("🔍 反同质化检测")
    print("─" * 52)
    cols = ["file", "字数", "入口", "顿悟位置", "结局", "结尾提问", "粗体"]
    print(" | ".join(c.rjust(6) if c != "file" else "文件" for c in cols))
    for f in fps:
        print(" | ".join(
            (f[c] if c == "file" else str(f[c]).rjust(6)) for c in cols))
    print("─" * 52)
    print("金句句式：")
    for f in fps:
        print(f"  {f['file']}: {'、'.join(f['金句']) or '（无）'}")

    print("─" * 52)
    if flags:
        print("⚠️  骨架重合：")
        for d, v, m in flags:
            print(f"  · {d}：{m} → 「{v}」")
        print("\n建议：")
        for d, v, m in flags:
            if d == "入口":
                print("  → 换入口：见 references/variation.md 第三节（6 种入口）")
            elif d == "连问三句":
                print("  → 保留一篇即可；其余的换成「没人反对，也没人支持」或「阻力是她自己」")
            elif d == "金句":
                print("  → 三篇内最多一次账本式；考虑写一篇「零金句篇」")
            elif d == "结局":
                print("  → 三篇内必须有 B（完成但有代价）或 C（她放弃了）")
            elif d == "顿悟位置":
                print("  → 换作者的姿势：不给顿悟 / 一开始就明白但什么也做不了 / 我就在里面 / 到最后才发现错的是另一件事")
            elif d == "结尾提问":
                print("  → 换提问模板：见 references/language.md 第三节")
        return 1

    print("🟢 骨架有明显差异，可以发。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
