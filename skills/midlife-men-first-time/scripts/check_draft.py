#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中年女人的第一次 · 发布前质检

用法:
    python3 scripts/check_draft.py draft.md --object 座椅
    python3 scripts/check_draft.py draft.md --object 座椅 --json

退出码: 0 = 无失败项, 1 = 有失败项(不允许发布)

检查项:
    禁用词 / 说教词 / 心理描写 / 引导语 / 可量化细节 / 锚点物件闭环 /
    结局是否圆满 / 结尾提问 / 粗体数量 / 金句密度 / 段落长度 / 篇幅 / 开场
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 规则常量

# 命中即失败：结论型大词与说教词
FAIL_WORDS = [
    "觉醒", "独立女性", "逆袭", "破防", "泪目", "全网",
    "重生", "中年女人都该", "所有女人", "我决定", "我终于",
    "你应该", "你们应该", "请记住", "我们女人", "女人都该",
]
# 命中即失败：引导语（这套文体要求结尾零引导）
LEAD_WORDS = ["点赞", "点个赞", "在看", "关注我", "转发", "收藏", "三连", "分享给朋友"]
# 警告：借来的抒情
PSYCH_WORDS = ["感到", "觉得", "心里", "内心深处", "不禁", "忍不住"]
# 警告：上价值结尾
PREACH_END = ["你应该", "我们要", "愿你", "希望每个", "请记住", "这才是真正"]
# 活人感：文章腔标记（命中即 WARN，报告用）
ALIVE_META = ["像一台", "像一具", "似的", "仿佛", "宛如", "犹如", "如同"]
ALIVE_GENERIC = ["我们", "大家", "人们", "所有人", "很多人", "一类人"]
ALIVE_SUMMARY = ["这就是", "这才是", "说到底", "归根结底", "无非", "本质上",
                 "说来", "一句话说", "其实都"]
ALIVE_PATHOS = ["让人心酸", "令人心酸", "令人唏嘘", "不免", "何尝不是", "不忍",
                "不由", "令人感动", "让人动容"]

# 爽文判定
COOL_WORDS = ["拿到了驾照", "拿到驾照", "买了车", "自驾", "成功", "终于",
              "圆满", "梦想成真", "逆袭", "从此", "自由自在"]
NEGATION = ["没", "不", "无", "别", "未"]

CN = r"[0-9零一二三四五六七八九十百千万两半几]+"
QTY = (r"(回|次|遍|个|年|岁|米|块|元|步|格|天|小时|分钟|号|趟|件|台|斤|"
       r"公里|人|句|周|月|点|条|口|张|双|只|杯|碗)")
DETAIL_RE = re.compile(CN + QTY)
DETAIL_STOP = {"几点", "一下", "一点"}

GOLDEN_PATTERNS = {
    "账本式": r"都叫[^。！？\n]{0,25}才叫",
    "归属式": r"是[她他][^。！？\n]{0,25}永远",
    "时间对比式": r"[^。！？\n]{0,12}头一[回次][^。！？\n]{0,12}知道",
    "反面定义式": r"不是要[^。！？\n]{0,25}要的是",
    "微小定量式": r"那么[零一二三四五六七八九十两0-9][^。！？\n]{0,6}",
    "动作收束式": r"在[她他]手[里上]",
}

TITLE_BAN = ["觉醒", "独立", "重生", "逆袭", "我决定", "我终于", "破防", "泪目", "全网"]


# ---------------------------------------------------------------- 工具函数

def cjk_len(s: str) -> int:
    """字数口径：非空白字符数（与公众号后台一致，含标点）"""
    return len(re.sub(r"\s", "", s))


def load_paragraphs(path: Path):
    raw = path.read_text(encoding="utf-8").splitlines()
    paras = [l.strip() for l in raw if l.strip()]
    title = None
    if paras and paras[0].lstrip("#").strip() and raw[0].lstrip().startswith("#"):
        title = paras[0].lstrip("#").strip()
        paras = paras[1:]
    elif paras and len(paras[0]) <= 40:
        title = paras[0]
        paras = paras[1:]
    return raw, title, paras


def find_ctx(text: str, word: str, width: int = 12, limit: int = 3):
    out = []
    for m in re.finditer(re.escape(word), text):
        i = m.start()
        out.append(text[max(0, i - width): i + len(word) + width].replace("\n", " "))
        if len(out) >= limit:
            break
    return out


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, name, msg, detail=None):
        self.items.append({"level": level, "name": name, "msg": msg, "detail": detail or []})

    @property
    def fails(self):
        return [i for i in self.items if i["level"] == "FAIL"]

    @property
    def warns(self):
        return [i for i in self.items if i["level"] == "WARN"]

    @property
    def passes(self):
        return [i for i in self.items if i["level"] == "PASS"]


# ---------------------------------------------------------------- 主逻辑

def check(path: Path, obj=None, expect_title=None, short=False):
    raw, title, paras = load_paragraphs(path)
    body = re.sub(r"<!--.*?-->", "", "\n".join(paras), flags=re.S).strip()
    r = Report()

    # --- 0 篇幅
    n = cjk_len(body)
    lo, hi = (400, 900) if short else (1000, 2200)
    r.add("PASS" if lo <= n <= hi else "WARN",
          "篇幅", f"{n} 个汉字" + ("" if lo <= n <= hi
                                   else (f"（速写理想 {lo}–{hi}）" if short else "（理想 1200–1800）")))

    # --- 0.5 未填占位符（防编造的机械护栏）
    holes = re.findall(r"【[^】]{0,40}】", body)
    if holes:
        r.add("FAIL", "未填占位符", f"还有 {len(holes)} 处没填",
              ["这些空就是还没采到的素材——回去问，别编："] + holes[:8])
    else:
        r.add("PASS", "未填占位符", "无")

    # --- 1 禁用词 / 说教词
    hits = [(w, find_ctx(body, w)) for w in FAIL_WORDS if w in body]
    if hits:
        r.add("FAIL", "禁用词/说教词", f"命中 {len(hits)} 个", [f"{w} → {c}" for w, c in hits])
    else:
        r.add("PASS", "禁用词/说教词", "无")

    # --- 2 引导语（引号内是当事人原话，不算结尾引导）
    narr_body = body
    for pat in (r'"[^"\n]{0,400}"', r"'[^'\n]{0,400}'",
                r'\u201c[^\u201d\n]{0,400}\u201d', r'\u300c[^\u300d\n]{0,400}\u300d',
                r'\u300e[^\u300f\n]{0,400}\u300f'):
        narr_body = re.sub(pat, "", narr_body)
    hits = [(w, find_ctx(narr_body, w)) for w in LEAD_WORDS if w in narr_body]
    if hits:
        r.add("FAIL", "结尾引导语", "出现了，本文体要求零引导",
              [f"{w} → {c}" for w, c in hits])
    else:
        r.add("PASS", "结尾引导语", "无")

    # --- 3 心理描写（只查作者的叙述；引号内是当事人的原话，不算抒情）
    narr = body
    for pat in (r'"[^"\n]{0,400}"', r"'[^'\n]{0,400}'",
                r'\u201c[^\u201d\n]{0,400}\u201d', r'\u300c[^\u300d\n]{0,400}\u300d',
                r'\u300e[^\u300f\n]{0,400}\u300f'):
        narr = re.sub(pat, "", narr)
    psych = narr.replace("你心里", "")
    hits = {w: psych.count(w) for w in PSYCH_WORDS if w in psych}
    total = sum(hits.values())
    if total == 0:
        r.add("PASS", "心理描写", "无（行动不写心 ✓）")
    else:
        r.add("WARN" if total <= 2 else "FAIL", "心理描写",
              f"{total} 处 —— 建议改成动作",
              [f"{w} ×{c}：{find_ctx(psych, w, 8, 1)[0] if find_ctx(psych, w, 8, 1) else ''}"
               for w, c in hits.items()])

    # --- 4 可量化细节
    matches = [m.group(0) for m in DETAIL_RE.finditer(body)]
    strong = [m for m in matches if m[0] not in "一每这那" and m not in DETAIL_STOP]
    uniq = sorted(set(strong), key=len, reverse=True)
    if len(uniq) >= 3:
        r.add("PASS", "可量化细节", f"{len(uniq)} 个：{'、'.join(uniq[:8])}")
    else:
        r.add("FAIL", "可量化细节",
              f"只有 {len(uniq)} 个（需 ≥3 个带数字的动作/失败/细节）",
              ["回来问他/她：第几次？花多少？等多久？排到第几个？"])

    # --- 5 锚点物件闭环
    if obj:
        idx = [m.start() for m in re.finditer(re.escape(obj), body)]
        L = max(len(body), 1)
        if len(idx) < 2:
            r.add("PASS" if short else "FAIL", "锚点物件闭环",
                  "速写不强制锚点物件" if short else
                  f"「{obj}」只出现 {len(idx)} 次，必须在①段和⑦段各出现一次")
        else:
            first, last = idx[0] / L, idx[-1] / L
            ok = first <= 0.35 and last >= 0.7
            sents = [x.strip() for x in re.split(r"(?<=[。！？\n])", body) if obj in x]
            extra = []
            if len(sents) >= 2:
                extra = [f"首现：{sents[0][:44]}",
                         f"末现：{sents[-1][:44]}",
                         "A→A′ 测试：只读这两句，看得出她变了吗？看不出 → 不是闭环，是重复"]
            if short and not ok:
                r.add("PASS", "锚点物件闭环",
                      f"「{obj}」出现 {len(idx)} 次（速写不强制首尾闭环）", extra)
            else:
                r.add("PASS" if ok else "WARN", "锚点物件闭环",
                      f"「{obj}」出现 {len(idx)} 次（首 {first:.0%} / 末 {last:.0%}）"
                      + ("" if ok else " —— 首尾位置不够，检查是否只在中间出现"),
                      extra)
    else:
        r.add("WARN", "锚点物件闭环", "未指定 --object，跳过")

    # --- 6 结局是否圆满（本技能最致命的一项）
    tail = "\n".join([x for x in paras if re.search(r"[\u4e00-\u9fff]", x)][-4:]) or body[-400:]
    bad = []
    for w in COOL_WORDS:
        for m in re.finditer(re.escape(w), tail):
            pre = tail[max(0, m.start() - 6): m.start()]
            if not any(ng in pre for ng in NEGATION):
                bad.append(w)
                break
    if bad:
        r.add("FAIL", "结局是否圆满", f"结尾出现成功向表达：{'、'.join(bad)}",
              ["改成：她还没成 / 还在练 / 学出来到底用不用得上她自己也不知道"])
    else:
        r.add("PASS", "结局是否圆满", "未发现成功向表达（留白 ✓）")

    # --- 7 结尾提问
    last = ""
    for p in reversed(paras):
        if re.search(r"[\u4e00-\u9fff]", p):
            last = p
            break
    problems = []
    if not last.endswith(("？", "?")):
        problems.append("结尾不是问句")
    if "你" not in last and "有没有" not in last:
        problems.append("没有把话筒递给读者（缺「你」）")
    if re.search(r"你怎么看|如何看待|你怎么想|有什么感想", last):
        problems.append("问观点了，应改成问经历（「你有没有……」）")
    if problems:
        r.add("PASS" if short else "FAIL", "结尾提问",
              "速写不强制提问，结尾是动作即可" if short else "；".join(problems),
              [] if short else [f"当前结尾：{last[:40]}"])
    else:
        r.add("PASS", "结尾提问", f"「{last[:30]}…」")

    # --- 8 上价值结尾
    tail_end = body[-400:]
    hits = [w for w in PREACH_END if w in tail_end]
    if hits:
        r.add("WARN", "上价值结尾", f"结尾 400 字出现：{'、'.join(hits)}",
              ["结尾要落回动作，不要落到道理"])
    else:
        r.add("PASS", "上价值结尾", "无")

    # --- 9 粗体数量
    bold = body.count("**") // 2
    r.add("PASS" if bold <= 5 else "WARN", "粗体引用",
          f"{bold} 处" + ("" if bold <= 5 else "（超过 5 处，满篇加粗等于都不加）"))

    # --- 10 金句密度
    found = {}
    for name, pat in GOLDEN_PATTERNS.items():
        ms = re.findall(pat, body)
        if ms:
            found[name] = len(ms)
    total_g = sum(found.values())
    detail = [f"{k} ×{v}" for k, v in found.items()]
    if short and total_g >= 2:
        r.add("PASS", "金句密度", f"共 {total_g} 句（速写不强制账本式）", detail)
    elif "账本式" not in found:
        r.add("WARN", "金句密度", f"共 {total_g} 句，但缺「账本式」（最强的一句）", detail)
    elif total_g >= 4:
        r.add("PASS", "金句密度", f"共 {total_g} 句，含账本式", detail)
    else:
        r.add("WARN", "金句密度", f"只有 {total_g} 句（建议 ≥4）", detail)

    # --- 10.5 语言节奏（短句比 / 平均句长）
    sents = [x for x in re.split(r"(?<=[。！？；])", body) if re.search(r"[\u4e00-\u9fff]", x)]
    L = [len(re.sub(r"\s", "", x)) for x in sents] or [0]
    avg = sum(L) / len(L)
    short = sum(1 for x in L if x <= 12) / len(L)
    very_short = sum(1 for x in L if x <= 8) / len(L)
    body_ps = [x for x in paras if re.search(r"[\u4e00-\u9fff]", x)]
    PL = [cjk_len(x) for x in body_ps] or [0]
    avg_p = sum(PL) / len(PL)
    one_sent = sum(1 for x in PL if x <= 15) / len(PL)
    msg = (f"平均句 {avg:.1f} 字 · ≤12字 {short:.0%} ｜ "
           f"平均段 {avg_p:.0f} 字 · 一句成段 {one_sent:.0%}")
    if very_short > 0.22 or short > 0.45 or one_sent > 0.28:
        r.add("WARN", "语言节奏", msg + " —— 切得太碎，读起来像敲桌子",
              ["先并段落（一句一段最伤节奏），把单句段并成 2–3 句的连续段落",
               "只有开场钩子、念白、金句、转折支点、提问前，才允许一句成段"])
    elif short < 0.10:
        r.add("WARN", "语言节奏", msg + " —— 长句过多，缺顿挫", ["在转折处断开一两句"])
    else:
        r.add("PASS", "语言节奏", msg)

    # --- 11 段落长度
    long_paras = [(i + 1, cjk_len(p)) for i, p in enumerate(paras) if cjk_len(p) > 150]
    if long_paras:
        r.add("WARN", "段落长度",
              f"{len(long_paras)} 段超过 150 字",
              [f"第 {i} 段 {c} 字" for i, c in long_paras[:5]])
    else:
        r.add("PASS", "段落长度", "全部 ≤150 字")

    # --- 12 开场
    if not paras:
        r.add("FAIL", "开场", "没有正文")
    else:
        p0 = paras[0]
        ok = cjk_len(p0) <= 100 and not p0.startswith(("我", "她说", "有一个人"))
        r.add("PASS" if ok else "WARN", "开场",
              ("从动作/画面起 ✓" if ok else f"第一段 {cjk_len(p0)} 字或以「我」起，检查是不是从动作开始的"))

    # --- 13 外部误解
    head = body[: max(1, int(len(body) * 0.3))]
    ok = ("问" in head) or ("？" in head) or ("?" in head)
    r.add("PASS" if ok else "WARN", "外部误解",
          "前 30% 有第三方的问句 ✓" if ok else "前 30% 没出现第三方的提问（「某人问……？」），②段可能缺失")

    # --- 14 标题
    if title:
        ban = [w for w in TITLE_BAN if w in title]
        r.add("FAIL" if ban else "PASS", "标题",
              (f"命中禁用词：{'、'.join(ban)}" if ban else f"「{title}」"))
    elif expect_title:
        r.add("PASS", "标题", f"「{expect_title}」")
    else:
        r.add("WARN", "标题", "未检测到标题行")

    # --- 15 活人感
    hits = []
    for label, words in [("比喻", ALIVE_META), ("泛化主语", ALIVE_GENERIC),
                         ("总结句", ALIVE_SUMMARY), ("替读者感动", ALIVE_PATHOS)]:
        f = [w for w in words if w in body]
        if f:
            hits.append(f"{label}：{'、'.join(f)}")
    if hits:
        r.add("WARN", "活人感", "；".join(hits),
              ["比喻一律删；泛化主语换成具体的人；总结句是文章腔核心；"
               "替读者感动 = 命令读者哭", "改法见 references/alive.md 第三节"])
    else:
        r.add("PASS", "活人感", "无文章腔标记")
    # 多余的一笔 / 原话
    if any(q in body for q in ("“", "\"", "「")):
        r.add("PASS", "原话", "正文含引号对话 ✓")
    else:
        r.add("WARN", "原话", "全篇没有一句原话",
              ["活人感七成来自原话，见 references/alive.md 第二节"])

    return r, n, len(paras), bold


def render(r, path, n, np_, bold):
    icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}
    out = []
    out.append("📋 发布前质检报告")
    out.append(f"文件：{path}")
    out.append("─" * 46)
    out.append(f"字数 {n} · 段落 {np_} · 粗体 {bold} 处")
    out.append(f"结果：❌ {len(r.fails)} 失败 · ⚠️  {len(r.warns)} 警告 · ✅ {len(r.passes)} 通过")
    out.append("─" * 46)
    for it in r.items:
        out.append(f"{icon[it['level']]} {it['name']}：{it['msg']}")
        for d in it["detail"]:
            out.append(f"     · {d}")
    out.append("─" * 46)
    out.append("")
    out.append("🧠 脚本查不出的四问（发之前自己答一遍，答不上就别发）")
    out.append("   1. 发现是什么？——一个你事先不知道、查完才敢写的事实。没有 → 这篇是空转。")
    out.append("   2. 材料之间如何连接？——我凭什么把这两段放在一起？")
    out.append("   3. 意义如何逐渐变化？——那个物件到结尾和开头还一样吗？")
    out.append("   4. 读者为什么会重新理解开头？——结尾两句，能反过来照亮开头吗？")
    out.append("─" * 46)
    if r.fails:
        out.append("🚫 有失败项，不允许发布。改完重跑。")
    elif r.warns:
        out.append("🟡 无失败项，可以发。警告项请自行取舍。")
    else:
        out.append("🟢 全部通过，可以发布。")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="中年女人的第一次 · 发布前质检")
    ap.add_argument("draft", help="草稿文件路径（.md / .txt）")
    ap.add_argument("--object", "-o", default=None, help="锚点物件，如 座椅 / 方向盘 / 钥匙")
    ap.add_argument("--title", "-t", default=None, help="标题（文件中没有标题行时使用）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--short", action="store_true",
                    help="速写模式（日更用）：篇幅 400–900，金句不强制，结尾问句与锚点闭环可选")
    a = ap.parse_args()

    p = Path(a.draft)
    if not p.exists():
        print(f"找不到文件：{p}", file=sys.stderr)
        return 2

    r, n, np_, bold = check(p, a.object, a.title, short=a.short)

    if a.json:
        print(json.dumps({
            "file": str(p),
            "chars": n, "paragraphs": np_, "bold": bold,
            "fails": len(r.fails), "warns": len(r.warns), "passes": len(r.passes),
            "items": r.items,
        }, ensure_ascii=False, indent=2))
    else:
        print(render(r, p, n, np_, bold))

    return 1 if r.fails else 0


if __name__ == "__main__":
    sys.exit(main())
