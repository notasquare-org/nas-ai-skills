# Persona mapping

This table is the whole reason the skill can stay generic across however many subsidy or certification lists show up over time. The persona isn't guessed from the company itself — it's inferred from *which program put the company on the list in the first place*, because that program's requirements tell you something real about where the company is stuck.

Match a company's 出典/source value against the **source pattern** column (substring match is fine — e.g. a source string containing "デジタル化推進事業" matches pattern A). If a source doesn't match anything here, don't guess: ask the user what persona it implies, then add a row so the next run doesn't have to ask again.

A word of caution on "成果事例集" (results/case-study collection) specifically: it's deliberately *not* one of the match keywords below, even though most of the sources this skill has seen so far are named that way. The phrase on its own just means "a collection of success stories" — it says nothing about whether the program behind it funded implementation or just gave out an award for already-existing success. Match on what the program *required*, not on the word "事例集" appearing in its name; if a 出典 string only says something like "〇〇成果事例集" with no other hint, treat it as a new source (see below) rather than assuming pattern A.

| Code | Source pattern (出典 contains…) | What the source implies | Persona / pitch angle |
|---|---|---|---|
| A | 専門家派遣, 導入補助, デジタル化推進事業, 中小企業団体中央会, DX推進支援補助, 京都市DX推進事業, 近畿経済産業局IT導入事例, 関西DXポータル(kiis)事例, 堺市産業振興センター, 堺市サービス業デジタルツール導入事例集 | The company received hands-on implementation help (a dispatched IT expert, equipment/system subsidy, a municipal case-study program that profiles companies after they actually built something) and presumably has *something built*. These programs fund or showcase the build, not the rollout. | **実装済み・定着課題**: the company likely has a system in place but adoption on the floor is the open question. Pitch: use reskilling-subsidy money to get staff actually using what was built. |
| B | DX認定, DX認定事業者 | DX認定 only requires a declared strategy/vision document from leadership — it does not require proof that anything was executed. Companies here cleared the "understands the value" bar but the program itself never tested execution. | **理解はしている・現場未着手**: leadership gets it, but there's no evidence of execution yet. Pitch: translate the stated DX vision into something the floor can actually run through AI/automation. |
| C | *(reserved for the next source — fill in once a new program shows up)* | | |

These five 出典 values were added after classifying the 341-company production list in `関西DX事例企業リスト` (sheet tab, code A, 181 companies) and `DX認定事業者(近畿・中小企業)` (sheet tab, code B, 160 companies) — all rows in each tab share one persona, so ペルソナ was filled in directly from the tab rather than re-derived per company. Treat each tab as a batch unit: a new tab built from a new source gets its own persona lookup added here before the Skill runs on it.

## How to judge a brand-new source if the user doesn't tell you

Ask: what does a company have to show the program to qualify? If the program paid for or required *doing something concrete* (equipment, a dispatched expert, a training grant actually completed), it's closer to pattern A. If the program only required leadership to *declare* an intention, plan, or strategy, with no execution check, it's closer to pattern B. Programs that don't fit either — e.g. an award for a company that's already succeeding, or a directory with no qualification bar at all — probably don't belong in this pipeline at all; flag that to the user rather than forcing a fit.
