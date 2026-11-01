#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中年女人的第一次 · 骨架生成器

用法:
    python3 scripts/new_article.py "四十岁去考驾照，教练问她是不是家里要买车" --object 座椅 -o draft.md
    python3 scripts/new_article.py --template-only -o draft.md

生成后填空 → 再用 check_draft.py 质检。
提示: 填不出来的空，就是你还没采到的素材。回去问，别编。
"""

import argparse
from datetime import date
from pathlib import Path

TEMPLATE = """# {title}

<!-- 锚点物件：{obj} · 目标 1200–1800 字 · 段落 ≤3 行 · 粗体 ≤5 处 -->

{obj_first}

【某人】在旁边看了半天，问她："【合理的误解 1】？"

她摇头。

"【合理的误解 2】？"

她还是摇头。

这是我在【场景】的第【N】周／次，跟我同车／共事的人，是个【年龄 + 一句性格特征】。我在【我的身份】，见的人多，她给我的印象最深刻。

【旁人的统计式判断】：在【这个地方】，这把年纪【做这件事】的，十个有九个是【大多数人的动机】，但她不是。

【她为什么想要：一件具体往事，含数字】。

**"【她的原话】"**

【反对者的原话 1】；【反对者的原话 2】。

【某人】没硬拦，就是【一句克制的描述】。

这话不算坏，周围不少人都这么想。【把反对方的立场说圆，读者的防备才放下】

我手机上总刷到【别人的宏大故事】，看着都挺远。她没那些，她就是【她做的小事，带量化】。

头一回【做这件事】，她【身体反应】，【失败的画面，带数字】，她自己先笑了。

【关卡】她【失败了几次】。前【N】次都是【具体的失败原因】，第【N+1】次才过。【谁】急了，说她【被嫌弃的话】；【谁】也笑。她不恼，【一个小动作】。

她跟我说，【朴素的自我开解，带"不跟谁比"的意思】。

她算的是另一笔：【把她的账算清楚】
**"【A】都叫【好词】，轮到【B】，才叫【坏词】。"**

这条路也不轻松。【把难堪复述一遍，不加修饰】。到现在【她卡在哪一步】，【结果还没落地】，【学出来到底用不用得上，她自己也不知道】。

我没夸她励志，她也不励志。【具体说明：她并没有因此达成什么了不起的事】。

我只看见她每次【那个动作】，都把{obj}【量化动作】，调到自己的位置，【收束动作】。

【一个画面：她在那里的样子，不慌也不躲】

**{obj}在她手里，【后半句】，她【动词】。**

你心里是不是也有一件【想学、又怕没用】的事？
"""

OBJ_HINT = {
    "座椅": "上车第一件事，她把驾驶座往前调，调一下，坐一坐，再调一下。",
    "方向盘": "上车第一件事，她把手放到方向盘上，握一下，松一下，再握紧。",
    "钥匙": "出门前，她把钥匙在手里翻了两下，才插进去。",
}


def main():
    ap = argparse.ArgumentParser(description="生成《中年女人的第一次》骨架草稿")
    ap.add_argument("title", nargs="?", default="【标题：年龄+身份 + 小事 + 一句外部误解】")
    ap.add_argument("--object", "-o", dest="obj", default="【锚点物件】",
                    help="锚点物件，如 座椅 / 方向盘 / 钥匙 / 一双鞋")
    ap.add_argument("--out", "-f", default="draft.md", help="输出文件")
    a = ap.parse_args()

    obj = a.obj
    first = OBJ_HINT.get(obj, f"上车第一件事，她把{obj}【动作三拍：动一下，停一下，再动一下】。")

    text = TEMPLATE.format(title=a.title, obj=obj, obj_first=first)
    out = Path(a.out)
    if out.exists():
        print(f"⚠️  目标文件已存在，未覆盖：{out}\n   换个 --out 或先备份。")
        return 1
    out.write_text(text, encoding="utf-8")

    print(f"✅ 骨架已生成：{out}")
    print(f"   标题：{a.title}")
    print(f"   物件：{obj}")
    print(f"   今天：{date.today().isoformat()}")
    print("\n下一步：")
    print("  1. 把【】填掉。填不出来的空 = 还没采到的素材，回去问，别编。")
    print(f"  2. 填完跑：python3 scripts/check_draft.py {out} --object {obj}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
