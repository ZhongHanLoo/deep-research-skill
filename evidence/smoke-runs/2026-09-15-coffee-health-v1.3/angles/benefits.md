# Angle
**benefits — mortality and cardiometabolic outcomes**

## Hypothesis / Would disconfirm
Hypothesis: moderate intake is associated with lower all-cause mortality and lower type 2 diabetes risk in observational cohorts, with no causal proof.
Would disconfirm: large cohorts or Mendelian randomisation showing null or harmful associations at 2-4 cups/day.

## Queries issued
1. `coffee consumption all-cause mortality meta-analysis cohort`
2. `coffee type 2 diabetes risk umbrella review`
3. `Mendelian randomization coffee consumption mortality cardiovascular`
4. `Poole coffee consumption health umbrella review BMJ 2017` (follow-up to locate the primary umbrella-review article after the first search surfaced only a correction notice)
5. `"j5024" BMJ Poole coffee consumption health umbrella review PMC full text` (follow-up to find the original full-text article, PMC5765813 being an erratum)

## Pointers (not evidence)
- PubMed abstract "Association of coffee drinking with all-cause mortality: a systematic review and meta-analysis" (pubmed.ncbi.nlm.nih.gov/25089347) — older (2014) meta-analysis, superseded by the larger Poole et al. umbrella review; not fetched.
- ResearchGate PDF request page for a mortality meta-analysis — not a primary host, not fetched.
- PMC9673438, PMC12168468, PMC10499477, ScienceDirect US-cohort mortality study — additional cohort/meta-analysis pointers on all-cause mortality; not fetched once the umbrella review (which subsumes many of these) and the MR paper were secured, per the 3-source stop rule.
- Annual Reviews "Coffee, Caffeine, and Health Outcomes: An Umbrella Review" — likely paywalled; not fetched (Poole et al. BMJ umbrella review used instead, open access).
- Diabetes Care dose-response meta-analysis on caffeinated/decaffeinated coffee and T2D (diabetesjournals.org) — good candidate, not fetched; the Poole umbrella review already reanalyses this outcome and cites it. Left as a gap/next-round pointer.
- PMC12121416 (umbrella review of food groups and T2D/metabolic syndrome, broader than coffee) — not fetched, off-target (not coffee-specific).
- PMC11668367 / journals.lww.com umbrella review of coffee and stroke/CVD/dementia — not fetched, overlaps with sources already secured.

## Sources fetched
- **[2]** "Coffee consumption and health: umbrella review..." (PMC5765813, pmc.ncbi.nlm.nih.gov) — status ok, fetched via raw-http, but this PMCID is the **January 2018 correction/erratum notice** for the Poole et al. BMJ article, not the full text (only ~4,400 chars, no results sections). Not graded and no claims registered from it — the same work was re-fetched successfully as [4]. Noted here per the "one registration per work" rule; does not count toward the 3-source target.
- **[4]** Poole R, et al. "Coffee consumption and health: umbrella review of meta-analyses of multiple health outcomes." *BMJ* 2017;359:j5024 (bmj.com, full text). Status ok, raw-http, ~98,700 chars. **Grade: primary**, published 2017-11-22, publisher BMJ.
- **[3]** Nordestgaard AT, Nordestgaard BG. "Coffee intake, cardiovascular disease and all-cause mortality: observational and Mendelian randomization analyses in 95 000-223 000 individuals." *Int J Epidemiol* 2016;45(6):1938-52 (academic.oup.com, fetched via wayback archive, full text, ~71,500 chars). **Grade: primary**, published 2016-12-29, publisher International Journal of Epidemiology (Oxford Academic).
- **[7]** Nordestgaard AT, Thomsen M, Nordestgaard BG. "Coffee intake and risk of obesity, metabolic syndrome and type 2 diabetes: a Mendelian randomization study." *Int J Epidemiol* 2015;44(2):551-65 (pubmed.ncbi.nlm.nih.gov, abstract page only via jina-reader — full text was not accessible). **Grade: primary**, published 2015-05-22 (Epub date), publisher International Journal of Epidemiology (via PubMed abstract).

## Claims extracted
Source [4] (BMJ umbrella review):
- c015 (central): largest all-cause mortality risk reduction (RR 0.83, 0.83-0.88) at 3-4 cups/day vs none.
- c016 (central): high vs low coffee associated with 30% lower T2D risk (RR 0.70, 0.65-0.75).
- c017 (supporting): authors say RCTs are still needed to establish causality.
- c018 (supporting): 75% of outcomes rated "very low" quality evidence (GRADE).
- c019 (supporting): authors note MR studies found no genetic evidence of causality for T2D/mortality, suggesting confounding.
- c020 (supporting): benefit plateaus (not reverses) above 3-4 cups/day.

Source [3] (Nordestgaard 2016, CVD/mortality MR):
- c021 (central): observational U-shaped mortality/CVD benefit not replicated by genetic (caffeine-allele) analysis.
- c022 (supporting): lowest observational risk at medium coffee intake (U-shape detail).
- c023 (supporting): genetic allele hazard ratios near-null (1.01-1.02) across five endpoints.
- c024 (supporting): study's genetic instrument had 80% power to detect only a small causal effect.
- c025 (supporting): authors interpret null genetic result as evidence of confounding, not causation.

Source [7] (Nordestgaard 2015, T2D/obesity/metabolic-syndrome MR):
- c026 (central): observational T2D/obesity/metabolic-syndrome benefit found no genetic evidence of causality.
- c027 (supporting): genetic risk score (9-10 vs 0-3 alleles) = 29% higher actual coffee intake.
- c028 (supporting): per-allele T2D odds ratios cluster near 1.0 (null) across genetic variants.
- c029 (supporting): observationally, high coffee intake also linked to higher BMI/BP/triglycerides/cholesterol, not lower glucose.
- c030 (tangential): study population 93,179 individuals, two general-population cohorts.

## Verdict on hypothesis
**Mixed.** The observational half of the hypothesis is strongly supported: a large umbrella review of 201 meta-analyses finds the largest all-cause mortality reduction (RR 0.83) at 3-4 cups/day and a 30% lower type 2 diabetes risk for high versus low consumption, with no increased harm at higher intake. But the "would disconfirm" criterion is partly met: two independent Mendelian randomisation studies (95,000-223,000 and 93,179 participants) found genetically predicted coffee/caffeine intake had **no** association with all-cause mortality, cardiovascular disease, or type 2 diabetes, contradicting a causal reading of the cohort data and supporting the authors' own conclusion that residual confounding, not causation, likely explains the observational benefit — which is consistent with the hypothesis's explicit "no causal proof" clause rather than a reversal of it.

## Gaps / suggested sub-questions
- Decaf vs caffeinated persistence of benefit was only lightly touched (umbrella review notes decaf shows similar mortality/T2D associations of comparable magnitude) — a next round could fetch the Diabetes Care dose-response meta-analysis (diabetesjournals.org, Ding et al. 2014) specifically for the caffeinated-vs-decaffeinated T2D comparison.
- Dose-response shape: the umbrella review documents a plateau (not reversal) above 3-4 cups/day for mortality/CVD, but the Nordestgaard 2016 paper describes a U-shape with higher risk at both very low and very high intake — these two characterizations are not fully reconciled and a next round should look for a more recent (2020s) large cohort or dose-response meta-analysis to adjudicate.
- No 2020s-era large cohort (e.g., UK Biobank, ~500,000 participants) was fetched for this angle despite being surfaced by search (ScienceDirect US-cohort study, PMC9673438); the brief's 2015-2026 window is currently anchored on 2015-2017 sources only for this angle. A next round should fetch one recent (post-2020) large cohort to check whether newer data change the magnitude or shape of the association.
- This angle did not investigate mechanism papers (chlorogenic acid, caffeine metabolism/CYP1A2 genotype) in depth beyond what the umbrella review mentions in passing.

Sources fetched: 3 content-bearing (plus 1 duplicate/erratum not counted). Claims registered: 16 (4 central, 11 supporting, 1 tangential).
