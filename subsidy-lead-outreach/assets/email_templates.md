# Email templates by persona

## Why the templates stay generic

Early in designing this skill, the alternative — researching something specific about each company and writing a personalized line for it — was considered and deliberately dropped. Researching 30–50 companies deeply enough to say something genuinely specific about each one costs roughly as much agent time as the enrichment step itself, for a payoff that's unproven at this stage (no reply-rate data yet to say personalization is worth it here). The same text within a persona also makes it trivial to A/B the persona split itself later: if persona A gets meaningfully more replies than B, that's a clean signal with generic copy and a confounded one with personalized copy. Only the company name is merged in, into the greeting line.

## Before first use

These are drafts, not approved copy. Read them, edit them to sound like you, and only then let the skill fill them into a sheet for real. Nothing in this skill sends email on its own — it only prepares the 件名/本文 columns for a human (or a separate, explicitly-approved sending step) to act on.

---

## Persona A — 実装済み・定着課題

For companies whose source program funded hands-on implementation (a dispatched expert, an equipment/system subsidy). The working hypothesis is: something got built, but it may not have taken root on the floor.

**件名:**
```
【{{出典プログラム名}}採択企業様へ】導入したシステムの"定着"は進んでいますか
```

**本文:**
```
{{会社名}} ご担当者様

突然のご連絡、失礼いたします。
Not a Square（ノットアスクエア）の酒井と申します。

貴社が{{出典プログラム名}}にてデジタル化の取り組みに採択されたことを拝見し、ご連絡いたしました。

多くの企業様とお話しする中で、
「システムは導入したものの、一部の社員しか使いこなせていない」
「せっかく投資したのに、現場に根づかないまま時間が経ってしまっている」
というお悩みをよく伺います。

Not a Squareでは、リスキリング系の補助金を活用しながら、既に導入されているシステムやAIツールを現場で使いこなせる状態まで伴走する、実践的な人材育成支援を行っています。

もし近いお悩みをお持ちでしたら、30分ほどお時間をいただき、現状を整理させていただくことも可能です。
ご興味があれば、本メールにご返信ください。

--
Not a Square
酒井涼雅
```

---

## Persona B — 理解はしている・現場未着手

For companies whose source program only required a declared strategy (DX認定 and similar). The working hypothesis is: leadership already sees the case for DX/AI, but there's no evidence execution has started yet.

**件名:**
```
【DX認定取得企業様へ】戦略を"現場で動くAI"に変える方法
```

**本文:**
```
{{会社名}} ご担当者様

突然のご連絡、失礼いたします。
Not a Square（ノットアスクエア）の酒井と申します。

貴社がDX認定を取得されていることを拝見し、ご連絡いたしました。

経営層でDXの方向性を明確に示されている企業様ほど、
「戦略は掲げたが、どこから現場に落とし込めばいいか分からない」
というお悩みを抱えていらっしゃることが多いと感じています。

Not a Squareでは、掲げられたDX戦略を、実際に現場で使えるAIツールや業務フローに落とし込むところまで伴走する支援を行っています。

もしご興味があれば、30分ほどお時間をいただき、現状を整理させていただくことも可能です。
ご返信をお待ちしております。

--
Not a Square
酒井涼雅
```
