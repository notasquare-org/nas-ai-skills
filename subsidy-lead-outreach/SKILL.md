---
name: subsidy-lead-outreach
description: Enriches a spreadsheet of companies sourced from government subsidy/certification programs (IT implementation subsidies, DX certification lists, reskilling grant recipients, etc.) into a cold-email-ready outreach list — finds each company's official website via web search, extracts a contact email or inquiry form, assigns a sales persona based on which subsidy program the company came from, and fills in persona-matched email subject/body text directly into the sheet. Use this whenever the user wants to turn a company-name list (any 補助金/認定/助成金 recipient list, DX認定事業者リスト, 商工会議所 or 自治体 case-study list) into a 営業リスト, メルアポリスト, or cold outreach list, or asks to enrich company names with 公式サイト/連絡先/メールアドレス, or wants to classify leads by ペルソナ for sales messaging. Also trigger when the user adds a new subsidy/certification source and wants it mapped into the existing persona system.
---

# Subsidy Lead Outreach

## What this skill is for

Government subsidy, grant, and certification programs in Japan routinely publish the names of recipient companies (成果事例集, DX認定事業者リスト, 補助金交付決定事業者一覧, etc.), but never their contact details — publishing an email address or phone number for every recipient would violate the privacy and purpose-limitation norms those programs operate under. This skill closes that gap through public web search rather than scraping restricted data sources, and turns the result into something a human can actually mail-merge from.

The deeper point of this skill is not just "find a website" — it is to turn a name-only government list into a list segmented by **why this company is worth contacting**, because the pitch differs by persona. A company that received hands-on implementation support needs a different message than one that only declared a DX strategy on paper. Getting the persona right matters more than getting every single URL.

## Before you start: read the persona mapping

Read [references/persona-mapping.md](references/persona-mapping.md) in full before processing any companies. It defines which subsidy/certification sources map to which persona, and it is meant to grow — when the user mentions a new subsidy source that isn't listed there yet, add it (see "Adding a new source" below) rather than guessing a persona inline.

## Intake — ask before running

Do not start enriching companies until you know:

1. **Which spreadsheet, which tab, which rows.** Get the sheet URL/ID and the range of companies to process this round. If the user only points at a sheet without specifying rows, ask which rows (or offer to start from the first row that has no 判定 value yet, i.e. resume where the last run left off).
2. **How many companies this run.** A single company takes one web search plus a site visit to confirm and extract contact info — in testing, 30 straightforward companies took about 3 minutes of agent time end-to-end. That estimate assumes the official site is reachable over normal HTTPS; a batch with several older SME sites (expired certificates, HTTP-only hosting, a sister-brand domain that needs tracking down) runs slower per company, sometimes several times slower for the affected ones. Recommend a batch of **30–50 companies**, mention that the estimate is for the easy case, and ask the user to confirm or adjust; don't default to processing an entire list of hundreds in one call, since a smaller batch lets the user spot-check quality before committing to the rest.
3. **Which column holds the source/出典**, so persona assignment can be looked up automatically. If the sheet doesn't have one, ask the user what persona to assume for the whole batch, or whether to add one by asking per company.

Never invent a spreadsheet ID, a company list, or contact details. If the user hasn't given you the sheet, ask for it before doing any work — this skill reads live company names, not customer data bundled with the skill (see "What never goes in this skill" below).

## Workflow

For each company in the batch:

### 1. Look up the persona

Match the company's 出典/source value against [references/persona-mapping.md](references/persona-mapping.md). If no source column exists, use whatever persona the user specified for the batch.

### 2. Find the official website

Search with a query that includes the company name, an industry keyword, and a location keyword — e.g. `会社名 業種 所在地`. A bare company name search is how the gBizINFO-based approach failed in practice (see "Why not gBizINFO" below) — the industry and location terms are what let you tell a real match from a same-named company in a different prefecture.

**Before accepting a result as the official site, check that at least two of these three line up with what you already know about the company:**
- the company name in the result matches (allowing for legal-entity-type differences like 株式会社 vs the bare name)
- the industry mentioned matches or plausibly relates to the known 業種
- the address/area mentioned matches the known 都道府県/市

Classify the result as one of three states — this three-way split exists because silently guessing wrong here means a sales email goes to a stranger's inbox, which is worse than finding nothing:

- **確定** — at least two of the three signals line up and nothing contradicts them. Record the URL.
- **不確実** — a company by that name exists but something doesn't fit (wrong prefecture, mismatched industry, or multiple plausible same-named companies with no way to tell them apart). Record the best-candidate URL anyway in 備考, but mark it 不確実 and state in one phrase what didn't line up — e.g. `所在地が東京都で一致せず` or `同名3社あり業種で絞れず`. Say exactly which signal failed, not just that something did; do not write the URL into the confirmed-URL column. A human should decide whether to use it.
- **未発見** — no plausible match at all, including when only a same-named company in a clearly different location turns up. Say so plainly (e.g. `同名企業は他県にのみ存在`) rather than forcing a weak match.

Never treat a business-directory site (Baseconnect, 日本の人事部, マピオン, 求人ボックス, houjin.jp, biz.ne.jp, etc.) as the official site itself — if one of those pages links to the real official site, follow that link and verify it the same way; otherwise the company counts as 未発見. These directory sites tend to crowd the top of search results for smaller companies, so if the first page of results is mostly directories, add a domain hint to the query (e.g. append `co.jp` or `会社概要`) rather than giving up after the first search.

**When the official site itself can't be reached** (expired TLS certificate, misconfigured SNI, plain-HTTP-only legacy hosting — not rare for older SME sites), don't treat that as 未発見 by default. Try fetching over plain HTTP if HTTPS fails. If you can read the page that way and it corroborates the company (matching address, phone number, or a linked sister-brand site run by the same company), that's still 確定 — note the access workaround in 備考 so a human knows the page may need the same workaround later. Only fall back to 不確実 if the content can't be read through any method and you're relying on an indirect source (a directory listing, a press mention) to vouch for the URL instead of reading it yourself.

### 3. Extract a contact point (確定 companies only)

Visit the confirmed official site's "お問い合わせ" / "会社概要" / "Contact" page.

- If a plain email address is printed on the page, record it and set 連絡先種別 to `メール`.
- If only a contact form exists (far more common for Japanese SMEs than a published email address), record the form's URL and set 連絡先種別 to `フォーム`.
- Never fabricate an address by guessing a pattern like `info@` + the domain. An address that looks plausible but was never actually seen on the page is worse than no address, because it will bounce or reach the wrong inbox.
- If neither exists, set 連絡先種別 to `不明` and leave 連絡先 blank.

### 4. Fill in the persona's email text

Read [assets/email_templates.md](assets/email_templates.md) and take the subject/body for the company's persona. Two placeholders get merged in, both from data you already have — nothing requires new research:
- `{{会社名}}` — the company name, into the greeting line.
- `{{出典プログラム名}}` — the sheet's 出典 column value for that row, verbatim. If the sheet has no 出典 column or the cell is blank, ask the user once per batch what to put there (or whether to drop that clause from the subject/body) rather than guessing a program name.

The rest of the body is identical across companies in the same persona on purpose (see "Why the templates stay generic" in that file). Do not write company-specific personalization into the body even if you found an interesting detail about the company; that was a deliberate design choice made after weighing it against the time cost of researching every company individually.

### 5. Write the results back to the sheet

Add or fill these columns for each processed row (create them if the sheet doesn't have them yet, matching the sheet's existing header style):

| Column | Content |
|---|---|
| 判定 | 確定 / 不確実 / 未発見 |
| 公式URL | the confirmed URL (blank if 不確実 or 未発見) |
| 連絡先種別 | メール / フォーム / 不明 |
| 連絡先 | the email address or form URL |
| ペルソナ | the persona code from persona-mapping.md |
| メール件名 | from the matched template |
| メール本文 | from the matched template, with company name merged in |
| 備考 | judgment reasoning for 不確実/未発見, or anything else worth a human's attention |

Follow the Google Sheets skill's rules for writing values accurately — large batches of hand-typed Japanese text are where mistakes creep in, so after writing, read back what you wrote and diff it against what you intended to write before reporting the batch as done. This caught real corruption (wrong kanji substitutions) during this skill's development; do not skip it to save time.

### 6. Report a summary

Give the user counts (確定 / 不確実 / 未発見), not a row-by-row recap. Point out anything that needs a human decision: 不確実 cases, companies with no contact method found, and the running total of companies left unprocessed in the sheet.

## Why not gBizINFO

It is tempting to reach for gBizINFO (METI's free, commercially-usable company database API) to get official URLs in bulk, since it is fast and has no rate-limit friction. In practice it does not work for this: in a 30-company test, only about 4% of small/medium companies had their `company_url` field populated at all, and worse, name-based search matched several companies to same-named but unrelated companies in other prefectures (a Kyoto construction company matched to an unrelated Tokyo company, for instance). A follow-up web-search-based pass on the identical 30 companies confirmed 67% with correctly verified URLs. Use gBizINFO only as a secondary cross-check if you already have strong signal from elsewhere (e.g., to look up a 法人番号 once you already know the company for certain) — never as the primary way to find a URL or confirm an identity.

## Adding a new subsidy/certification source

When the user mentions a company list from a program not yet in [references/persona-mapping.md](references/persona-mapping.md), add a row there rather than hard-coding a one-off persona in this file: the source name/keyword, the persona it implies, and a one-line reason (what receiving this particular subsidy/certification tells you about where the company is stuck). This is what keeps the skill generic as new government programs show up instead of needing a rewrite each time.

## What never goes in this skill

Per this repository's rules, never commit API keys, OAuth tokens, real company lists, or spreadsheet IDs into this skill folder. [references/persona-mapping.md](references/persona-mapping.md) and [assets/email_templates.md](assets/email_templates.md) describe the *pattern* (which kinds of sources map to which persona, what the template structure looks like) in generic terms — actual customer data lives only in the user's own spreadsheet, supplied fresh at intake time each run.
