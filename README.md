# 中年中年 · 两个写作技能包

同一套技法，两个不同的伤口。

| | 写谁 | 张力从哪来 | 最怕写成 |
|---|---|---|---|
| [中年女人的第一次](skills/midlife-women-first-time/) | 40+ 女人做一件没人支持的小事 | **被拦住**：「你凭什么」 | 励志文 |
| [中年男人的第一次](skills/midlife-men-first-time/) | 40+ 男人做一件没人当真、也没人反对的小事 | **被放过**：「挺好的」 | 自怜文 |

> 女人到了四十岁，是被拦住的。男人到了四十岁，是被放过的。
> 被拦住的人有话说，被放过的人说不出话——因为他找不到一个可以怪的人。

两个包**互不依赖**，可以只装一个。`scripts/` 里三个脚本两边完全相同，逐字一致。

---

## 装

两个一起装：

```bash
git clone --depth 1 https://github.com/chenty/midlife-women-first-time.git /tmp/ms
mkdir -p ~/.claude/skills
cp -r /tmp/ms/skills/* ~/.claude/skills/
```

只装一个：

```bash
cp -r /tmp/ms/skills/midlife-men-first-time ~/.claude/skills/     # 男版
cp -r /tmp/ms/skills/midlife-women-first-time ~/.claude/skills/   # 女版
```

也可以直接在 Claude 里 Settings → Capabilities → Skills → Upload skill，传对应目录的 zip。

更新：

```bash
cd /tmp/ms && git pull && cp -r skills/* ~/.claude/skills/
```

---

## 自检

```bash
python3 ~/.claude/skills/midlife-women-first-time/scripts/check_draft.py \
  ~/.claude/skills/midlife-women-first-time/assets/sample_pass.md --object 方向盘

python3 ~/.claude/skills/midlife-men-first-time/scripts/check_draft.py \
  ~/.claude/skills/midlife-men-first-time/assets/sample_pass.md --object 吉他
```

两个都应该输出 `❌ 0 失败 · ⚠️ 0 警告 · ✅ 17 通过`。

> `--object` 是这篇的**锚点物件**（贯穿首尾、结尾含义发生变化的那件东西）。
> 它不一定等于标题词：女版范本的标题里是"驾照"，锚点是**方向盘**。

---

## 目录

```
skills/
  midlife-women-first-time/     女版（自包含）
  midlife-men-first-time/       男版（自包含）
tools/
  sync_scripts.py               校验/同步两版共用的三个脚本
```

`--check` 会在不一致时报错：

```bash
# 在仓库根目录
python3 skills/../tools/sync_scripts.py --check
```

改脚本时只改一处，然后跑一次同步，两边都更新——**避免"修了一个 bug，另一边的质检还悄悄失效"。**

---

## 共同的那部分

两个包共享同样的形：

- **白描，不判断。** 只写看见的，不写判断的；删掉所有"感到 / 觉得 / 心里"。
- **不给圆满结局。** 未完成 / 完成但有代价 / 放弃了，三种合法形态，但不许"终于"。
- **零引导语。** 结尾不求赞、不上价值，只留一个问题。
- **一个锚点物件。** 开头出现、结尾回来，含义必须变。
- **17 项机械质检。** 过不了就不许发。

不同的那部分，每个包的 `SKILL.md` 开头就写清楚了。
