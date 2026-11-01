#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
两版技能共用同一套脚本，这个工具负责守住"逐字相同"。

用法（在 skills/ 的上一级跑）:
    python3 tools/sync_scripts.py            # 以女版为准，覆盖男版
    python3 tools/sync_scripts.py --check    # 只检查，不一致就 exit 1
    python3 tools/sync_scripts.py --from men # 反方向同步

为什么需要它: check_draft.py 修了一个 bug，只在一边修，另一边的质检就悄悄失效了。
"""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path

SCRIPTS = ["check_draft.py", "check_variation.py", "new_article.py"]
ROOT = Path(__file__).resolve().parent.parent / "skills"
DIRS = {"f": ROOT / "midlife-women-first-time" / "scripts",
        "m": ROOT / "midlife-men-first-time" / "scripts"}


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser(description="校验/同步两版共用的脚本")
    ap.add_argument("--check", action="store_true", help="只检查，不改文件")
    ap.add_argument("--from", dest="src", choices=["f", "m"], default="f",
                    help="以哪一版为准（默认女版 f）")
    a = ap.parse_args()

    src = DIRS[a.src]
    dst = DIRS["m" if a.src == "f" else "f"]
    bad = 0

    for name in SCRIPTS:
        s, d = src / name, dst / name
        if not s.exists():
            print(f"❌ 源文件缺失：{s}")
            bad += 1
            continue
        if not d.exists():
            print(f"⚠️  对面缺失：{d}")
            bad += 1
        elif digest(s) == digest(d):
            print(f"✅ {name}  一致 ({digest(s)})")
            continue
        else:
            print(f"❌ {name}  不一致  源 {digest(s)} / 对面 {digest(d)}")
            bad += 1
        if not a.check:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            print(f"   → 已同步到 {d}")

    if a.check and bad:
        print(f"\n🚫 {bad} 个文件不一致。跑 `python3 tools/sync_scripts.py` 修。")
        return 1
    print("\n✅ 完成。" if not bad else f"\n已同步 {bad} 个文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
