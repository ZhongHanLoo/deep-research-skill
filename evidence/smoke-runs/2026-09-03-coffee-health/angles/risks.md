# Angle

**risks** — caffeine limits, subgroups and adverse effects

## Hypothesis / Would disconfirm

Hypothesis: regulators put a safe ceiling near 400 mg caffeine/day for adults and 200 mg in pregnancy; risks concentrate in pregnancy, sleep, anxiety and unfiltered coffee (LDL cholesterol).

Would disconfirm: regulator guidance or trials showing harm at moderate intake in the general adult population.

## Queries issued

1. FDA caffeine 400 mg safe limit adults
2. caffeine pregnancy 200 mg guidance miscarriage
3. EFSA caffeine safety adults 400 mg opinion
4. unfiltered coffee cafestol LDL cholesterol
5. FDA "Spilling the Beans" caffeine consumer update
6. caffeine anxiety sleep systematic review moderate intake
7. efsa.europa.eu scientific opinion safety caffeine 2015
8. caffeine cardiovascular arrhythmia moderate consumption risk adults
9. boiled coffee cholesterol randomized trial meta-analysis cafestol serum lipids

## Pointers (not evidence)

- x.com (OHdeptofhealth tweet) — skipped, social-media restatement of FDA guidance, not primary.
- Mayo Clinic, MD Anderson, Cleveland Clinic, various consumer-health blogs — skipped as secondary paraphrases of the same FDA/EFSA figures already available from primary sources.
- caffeineinformer.com, various SEO health blogs on arrhythmia — skipped, not authoritative.
- ScienceDirect/CHEST/AJMC articles on caffeine and arrhythmia — noted as a promising disconfirming/confirming angle but not fetched (target already met with novel claims from other sources; search snippets indicate moderate coffee is *not* associated with increased arrhythmia risk and may even be modestly protective, which is relevant context but unverified by direct read).
- NIEHS/NTP cafestol-kahweol background document — not fetched, redundant with the Jee et al. meta-analysis already fetched.

## Sources fetched

- [6] "Spilling the Beans: How Much Caffeine is Too Much?" — FDA consumer update. status: ok. method: raw-http. grade: primary (FDA, published 2024-08-28).
- [8] "Moderate Caffeine Consumption During Pregnancy" — ACOG Committee Opinion No. 462. status: ok. method: raw-http. grade: primary (ACOG, August 2010, reaffirmed 2026).
- [9] "Caffeine intake and anxiety: a meta-analysis" — PMC10867825. status: ok. method: jina-reader. grade: primary (peer-reviewed meta-analysis).
- [10] "Coffee consumption and serum lipids: a meta-analysis of randomized controlled clinical trials" (Jee et al., Am J Epidemiol 2001) — PubMed abstract page. status: ok. method: jina-reader. grade: primary (peer-reviewed meta-analysis; only abstract text was available/quoted, full text not accessed).
- [12] EFSA Journal opinion (Wiley Online Library, doi:10.2903/j.efsa.2015.4102). status: ok per fetch script, but page returned only a Cloudflare "Performing security verification" bot-check screen (311 chars) — **not usable, no claims extracted from it**. grade: unreliable (unfetchable in practice). Reported here so it is not mistaken for a read source.
- [13] "EFSA opinion on the safety of caffeine" — EUFIC summary of the EFSA 2015 scientific opinion. status: ok. method: raw-http. grade: secondary (EUFIC summarizing EFSA; used as substitute since the primary EFSA document [12] was blocked).

## Claims extracted

- c016 [6]: FDA cites 400 mg/day as amount not generally associated with negative effects for most adults. (central)
- c017 [6]: FDA advises pregnant/trying-to-conceive/breastfeeding people to consult a provider about limiting caffeine. (central)
- c018 [6]: FDA estimates toxic effects (e.g., seizures) near 1,200 mg rapid consumption. (supporting)
- c019 [6]: A 2017 IAFNS systematic review confirmed safety of the 400 mg/day level. (supporting)
- c020 [8]: ACOG: moderate caffeine (<200 mg/day) not a major contributor to miscarriage/preterm birth. (central)
- c021 [8]: Weng et al. found adjusted HR 2.23 for miscarriage at ≥200 mg/day intake. (central)
- c022 [8]: Savitz et al. found no association between caffeine intake (any level) and miscarriage — contradicts Weng et al. (central)
- c023 [8]: IUGR odds ratios rose with caffeine intake, peaking at 200–299 mg/day (OR 1.5). (supporting)
- c024 [9]: Meta-analysis: caffeine intake overall increased anxiety risk (SMD 0.94) in healthy adults. (central)
- c025 [9]: High-dose (≥400 mg) caffeine showed much larger anxiety increase (SMD 2.86) than low-dose (<400 mg, SMD 0.61). (central)
- c026 [9]: Even low-dose (<400 mg) caffeine was linked to a statistically significant, moderate anxiety increase. (central)
- c027 [9]: Authors recommend caffeine intake not exceed 400 mg/day in healthy populations. (supporting)
- c028 [10]: Unfiltered (not filtered) coffee increases serum total and LDL cholesterol (meta-analysis of RCTs). (central)
- c029 [10]: Filtered-coffee trials showed very little cholesterol increase. (supporting)
- c030 [10]: Cholesterol increases were greater in patients with hyperlipidemia and in boiled/caffeinated coffee trials. (supporting)
- c031 [13]: EFSA: single doses up to 200 mg and daily intake up to 400 mg do not raise safety concerns for healthy adults. (central)
- c032 [13]: EFSA: regular caffeine intake up to 200 mg/day is safe in pregnancy/breastfeeding — matches ACOG threshold. (central)
- c033 [13]: EFSA notes caffeine can affect sleep at doses around 100 mg in certain individuals, especially near bedtime. (supporting)

## Verdict on hypothesis

**Mixed/supported with a caveat.** The 400 mg/day (adult) and 200 mg/day (pregnancy) ceilings are confirmed by two independent regulators (FDA and EFSA) and by ACOG, and unfiltered coffee's LDL-raising effect via cafestol is confirmed by a peer-reviewed RCT meta-analysis — all consistent with the hypothesis. However, the anxiety meta-analysis complicates the "risk concentrates only above the ceiling" framing: it found a statistically significant, moderate anxiety increase even in the *low-dose (<400 mg)* subgroup, and the two large pregnancy-miscarriage cohort studies ACOG reviewed directly contradict each other (one shows an HR of 2.23 at ≥200 mg, the other shows no association at any dose) — so "the 200 mg pregnancy line is evidence-backed" is weaker than regulator language implies; it is better described as a precautionary consensus amid conflicting primary data.

## Gaps / suggested sub-questions

- Full text of the Jee et al. (2001) meta-analysis and more recent coffee-cholesterol meta-analyses (e.g., Cai et al. 2012) were not read — only the abstract; a next round should fetch full text for effect-size confidence intervals.
- The primary EFSA opinion document (Wiley, source [12]) could not be fetched (Cloudflare bot-check); a next round should try the EFSA's own efsa.europa.eu domain or an open-access mirror/PDF instead of the Wiley-hosted version.
- Caffeine and cardiovascular/arrhythmia risk was searched but not fetched; snippets suggested moderate coffee is not associated with increased arrhythmia risk and may be mildly protective — this would be a second disconfirming-of-harm data point worth verifying directly in a future round.
- No source specific to caffeine and sleep-onset latency at moderate (not high) doses in the general population was fetched in depth (EFSA's mention of ~100 mg affecting some individuals was only a passing note); a dedicated sleep-focused fetch (e.g., the SLEEP journal dose-timing RCT found in search) would strengthen this sub-claim.
- Genetic/individual variability in caffeine sensitivity (e.g., CYP1A2 metabolizer status) was not explored, despite FDA and EFSA both flagging "individual sensitivity" as a factor.
