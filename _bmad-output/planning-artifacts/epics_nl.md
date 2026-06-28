---
stepsCompleted: ['step-01-validate-prerequisites']
inputDocuments:
  - 'docs/prd/PRD - v3.0D.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-l10n_cw_hr_payrol-2026-06-25/ARCHITECTURE-SPINE.md'
  - 'docs/tech_design_l10n_cw_hr_payroll_v3.0D.txt'
translationOf: 'epics.md'
language: 'nl'
---

::: {custom-style="Title"}
l10n_cw_hr_payroll — Epic-overzicht
:::
::: {custom-style="Subtitle"}
Curaçaose payroll-lokalisatie voor Odoo 19 Enterprise — versie 19.0.0.1.0
:::

# Epic-overzicht

## Overzicht

Dit document vertaalt de eisen uit de PRD en de Architecture Spine (met het v3.0D Technisch Ontwerp als implementatiereferentie) naar bouwbare epics en stories. Er is geen apart UX-ontwerpdocument: de module gebruikt de standaardschermen van Odoo, alleen uitgebreid waar Odoo-modellen worden uitgebreid, plus een klein in-module stylesheet-thema.

## Eisenoverzicht

### Functionele eisen

**Wettelijke berekeningsengine**

- FR001: Bereken de maandelijkse loonadministratie voor alle medewerkers in één run met één actie.
- FR002: Voer de wettelijke berekening uit als een geordende reeks Odoo Salarisregel-records (`hr.salary.rule`), geëvalueerd in strikt oplopende volgorde (Sequence 10–150) — de circa 21 regels die de 14 wettelijke Stappen uitvoeren. Interne hulpregels worden van de loonstrook verborgen door de "toon op loonstrook"-vlag uit te zetten (`appears_on_payslip = False`).
- FR003: Bereken het totale brutoloon — de brutoloonregel (`TOTAL_LOON`) = maandelijks contractloon + loon in natura (natura-loon).
- FR004: Bereken vier overurentypes (doordeweeks, zaterdag, zondag, feestdag) als afzonderlijke, benoemde loonstrookregels, op basis van ingevoerde uren en een tarief per medewerker, elk toegevoegd aan de toeslagencategorie (`ALW`).
- FR005: Bereken de BVZ-zorgpremie — werkgever vast 9,3% en werknemer vast 4,3% (volgens de officiële SVB-tabel 2026; er is geen inkomensafhankelijke werknemersschaal) — over de jaarlijks afgetopte BVZ-grondslag (XCG 150.000/jaar).
- FR006: Bereken de AOV/AWW-premie (ouderdom en nabestaanden) — werknemer 6,5% en werkgever 9,5% tot het plafond van XCG 100.000/jaar, **cumulatief** toegepast (AD-24) — plus een werknemerstoeslag van 1% over het jaar-tot-datum-inkomen boven het plafond.
- FR007: Bereken de AVBZ-premie (langdurige zorg) — werknemer vast 1,5%, werkgever vast 0,5% (volgens de officiële SVB-tabel 2026; er is geen inkomensafhankelijke werknemersschaal) — over de AOV-grondslag afgetopt op het AVBZ-plafond (XCG 606.247,08/jaar).
- FR008: Bereken de loonbelasting door het bruto maandtarief op te zoeken in de officiële Belastingdienst lb-maandtabel (`hr.loonbelasting.tabel`) voor de fiscale loongrondslag (`TAX_INC`) en de einddatum van de loonstrookperiode; tel het boven-plafondtarief van de tabel (46,5% voor 2026) op over eventueel bedrag boven het tabelplafond (MR 144 § Algemeen). Het ruwe tabelresultaat is het LOONBEL_RAW-bedrag (Seq 90). Trek daarna de toeslagen (basiskorting + medewerkersspecifieke kortingen) als geld van het ruwe belastingbedrag af — niet van het belastbaar inkomen — met een ondergrens van nul (Seq 100, LOONBEL). De lb-maandtabel 2026 is gepubliceerd **exclusief basiskorting** (belast vanaf de eerste gulden), dus de basiskorting wordt hier apart afgetrokken — die zit dus **niet** al in de tabel.

  Voorbeeld: TAX_INC = XCG 3.245,00/mnd → zoek op wage_from = 3.245 in de lb-maandtabel 2026 → loonbelasting = XCG 316,39 (ruw); basiskorting = XCG 2.915,00/12 = XCG 242,92; LOONBEL = −(316,39 − 242,92) = −XCG 73,47. Voorbeeld boven het plafond: loon = XCG 20.000,00/mnd → plafondbelasting XCG 4.862,91 (bij het plafond van 16.670) + 46,5% × (20.000 − 16.670 = 3.330) = XCG 1.548,45 → loonbelasting = XCG 6.411,36.
- FR009: Pas de basiskorting automatisch toe op elke medewerker; pas de alleenverdieners-, kinder- en ouderentoeslag toe vanuit velden op de medewerker.
- FR010: Bereken de extra belasting op bijzondere beloningen (vakantiegeld, bonus, gratificatie, incidentele overuren) met de marginale-tarieftabel ("exclusief basiskorting"): zoek het enkele schijftarief voor het jaarloon van de medewerker op (`lookup_marginal_rate`) en pas dat toe op alleen het bedrag van de bijzondere beloning. Het tarief wordt **eenmaal per belastingjaar** vastgesteld op basis van het jaarloon van het voorgaande jaar (herleid tot jaarloon bij gedeeltelijk jaar; het verwachte jaarloon van dit jaar voor nieuwe medewerkers), met een **handmatige correctie** door de salarisadministrateur naar het huidige jaarloon wanneer het voorgaande jaar geen goed beeld geeft; het wordt per (medewerker, jaar) bewaard als standaardwaarde en het **toegepaste tarief wordt op de loonstrookregel vastgelegd** (de audit-waarheid). Een bijzondere beloning is een `ALW`-looncomponent met een `is_bijzondere_beloning`-vlag: het blijft in NET en in de SVB-premiegrondslag (premies zijn **wel** van toepassing), maar de `TAX_INC`-regel sluit het uit van de maandtabel zodat het alleen via deze tabel wordt belast. Overwerk heeft **drie** routes — *regulier* (maandtabel), *incidenteel* (deze bijzondere tabel), of *Lei di Bion-vrijgesteld* (vrijgesteld — zie FR011b/AD-23) — handmatig gekozen door de salarisadministrateur; geen frequentiedrempel in de engine. Zie AD-21.
- FR011: Bereken de ZV-premie (ziekte, werkgever 1,9%) en de OV-premie (ongevallen, werkgever, variabel per gevarenklasse) over het gedeelde ZV/OV-**maandplafond** (XCG 7.146,10/maand), direct toegepast — niet geannualiseerd.
- FR011b: Ondersteun **Lei di Bion-vrijgesteld overwerk** (AD-23) — overwerk tot 10 uur per week, onder een goedgekeurde werkgeversbeschikking, wordt vrij van **zowel** loonbelasting als SVB-premies uitbetaald (0% / 0%): het krijgt een `is_lei_di_bion_exempt`-vlag, wordt uitgesloten van zowel `TAX_INC` als de premiegrondslagen, maar wordt wel netto uitbetaald. De beschikking moet **worden aangeleverd en goedgekeurd door de Payroll Manager** (`group_l10n_cw_payroll_manager`); zonder goedkeuring, of voor uren boven het plafond, valt het overwerk terug op een belaste route (regulier → maandtabel of incidenteel → bijzondere). Voorbeeld: 10 overuren = XCG 302,90 bruto → vrijgesteld: 302,90 netto; niet vrijgesteld (bijzondere 9,75%): 273,37 netto.
- FR012: Bereken het nettoloon — de nettoloonregel (`NET`) = categorieën basis + toeslagen + inhoudingen (`BASIC + ALW + DED`) — en onbelaste vergoedingen als afzonderlijke regel na netto via de onbelaste-regel (`NONTAXED`); uitbetaald bedrag = netto + onbelast.
- FR013: Bereken de totale werkgeverskosten als informatief totaal via de werkgeverskostenregel (`TOTAL_ER_COST`).
- FR014: Laat de salarisadministrateur afzonderlijke premies en belastingen per medewerker aan- of uitzetten via de aan/uit-vlag (`enabled`) op de loonregel van de medewerker; een uitgezette regel geeft 0,00 terug zonder de keten te breken, terwijl de gedeelde basisregels altijd draaien.

**Looncomponentmodel en configuratie**

- FR015: Lever het drielaags looncomponentmodel — Tier 1 globale regels (het Salarisregel-model, `hr.salary.rule`), Tier 2 bedrijfssjabloonsets (het Looncomponentset-model, `hr.wage.component.set`, met zijn regels) en Tier 3 loonregels per medewerker (het Medewerker-loonregel-model, `hr.employee.wage.line`).
- FR016: Pas een Tier 2-sjabloonset toe op één of meer medewerkers via de toepaswizard, waarbij onafhankelijke Tier 3-loonregels worden aangemaakt die niet meewijzigen als de set later wordt bewerkt.
- FR017: Sla elk wettelijk tarief, plafond en grens op als gedateerde data, zodat een tariefwijziging een data-aanpassing is zonder code-implementatie. Er zijn drie opslagplaatsen (AD-5): **SVB-premies + plafonds** in één record per jaar (`hr.svb.parameters`, één per jaar, conform de jaarlijkse SVB-tabel — zie AD-22); de **bijzondere-beloningstarieven en de Belastingdienst-scalairen** (basiskorting, verwervingskosten, toeslagen) als gedateerde `hr.tax.bracket`-records; en **loonbelasting** in de officiële lb-*tabel (`hr.loonbelasting.tabel` — zie FR031 en AD-20). Vervang een waarde door het oude record af te sluiten (`valid_to`) en een nieuw gedateerd record toe te voegen; alle records zijn append-only.
- FR018: Houd een lopend jaar-tot-datum-totaal bij per medewerker, per component, per jaar in het Jaar-tot-datum-model (`hr.wage.component.ytd`), bijgewerkt bij het afsluiten van een run en bewaard over jaren heen.
- FR019: Lever de toeslagvelden en de beschikkingsinvoer (beschikking) op de medewerker, en een gevarenklasse-percentage (OV%) op het contract.

**Runlevenscyclus en boekhouding**

- FR020: Stuur de run door zijn fasen (Concept → Te controleren → Afgesloten / CONCEPT → TE CONTROLEREN → AFGESLOTEN) en elke loonstrook door zijn fasen (Concept → Te controleren → Bevestigd / CONCEPT → TE CONTROLEREN → BEVESTIGD, met annuleren), waarbij herberekening vóór afsluiten is toegestaan.
- FR021: Bevestig en vergrendel bij afsluiten de loonstroken, herbereken de jaar-tot-datum-totalen, boek de journaalpost en stel de run-rapporten beschikbaar — dit afsluiten is het enige punt waarop resultaten worden vastgelegd.
- FR022: Genereer bij afsluiten een sluitende journaalpost (de boekingspost, `account.move`) waarbij totaal debet gelijk is aan totaal credit per constructie, met de configureerbare grootboekmapping en de werkelijk berekende bedragen (2 decimalen).

**Rapporten**

- FR023: Produceer de loonstrook-PDF (rapport A-01) in Curaçaose lay-out.
- FR024: Produceer de maandelijkse aangifte loonbelasting (rapport B-01) en de aangifte SVB-premies (rapport B-02) per run, met bedragen in hele XCG — decimalen worden weggelaten (afgekapt), niet afgerond.
- FR025: Produceer het sluitende loonjournaalpost-overzicht (rapport B-05) per run.

**Beveiliging en toegang**

- FR026: Lever vier beveiligingsrollen (Medewerker, Salarisgebruiker, Salarisbeheerder, Accountant) met minimale rechten.
- FR027: Beperk elke medewerker tot zijn eigen loonstroken met een recordregel die de ingelogde gebruiker matcht (`employee_id.user_id = user`).

**Run-lidmaatschap en contractperiode**

- FR028: Een loonrun laat een medewerker voor een periode **automatisch** weg wanneer (a) hij geen gewerkte uren in die periode heeft, of (b) hij niet langer in dienst is (contract beëindigd op of vóór de periode). Dit is automatisch — nooit een handmatige stap; weggelaten medewerkers krijgen geen loonstrook en komen niet voor in de runtotalen of de journaalpost.
- FR029: Elk arbeidscontract heeft een verplichte begindatum en een optionele einddatum; het invoeren van een einddatum bepaalt wanneer de medewerker uit dienst gaat. De run gebruikt deze datums om te bepalen of een medewerker in de periode in dienst is (zie FR028). Vaste contracten zonder einddatum zijn toegestaan.

**Loonstrookdistributie**

- FR030: Distribueer loonstroken naar medewerkers als een afzonderlijke, expliciete actie die beperkt is tot de meest senior bestaande rol, de Salarisbeheerder (`group_l10n_cw_payroll_manager`), alleen toegestaan na het afsluiten van de run en een expliciete bevestiging "geen restore nodig". Het afsluiten van een run distribueert niet. Het verzendkanaal (e-mail / Medewerkersportaal / app) is uitgesteld (OQ-01).
- FR031: Sta de Salarisbeheerder toe een Belastingdienst lb-maandtabel te uploaden door een CSV-bestand te importeren in `hr.loonbelasting.tabel` / `hr.loonbelasting.tabel.lijn` via de standaard Odoo-importactie. Dit dekt twee scenario's: (a) **Jaarlijkse upload** — vóór de eerste run van elk nieuw jaar de nieuwe tabel uploaden; is die nog niet beschikbaar, dan wordt de tabel van het vorige jaar (met open `valid_to`) automatisch gebruikt totdat de nieuwe tabel arriveert. (b) **Correctie gedurende het jaar** — publiceert de Belastingdienst een gecorrigeerde tabel voor het lopende jaar, dan wordt die als nieuw koptekstrecord voor hetzelfde jaar geüpload. Het systeem selecteert automatisch de juiste versie per loonstrook: de actieve tabel met `valid_from ≤ payslip.date_to`, gesorteerd op meest recente `valid_from` eerst en bij gelijke `valid_from` op de volgorde van upload (meest recentste upload wint). Herberekening van eerder afgesloten loonstroken pakt de gecorrigeerde tabel automatisch op. Vervangen tabelrecords worden bewaard voor audit.

### Niet-functionele eisen

- NFR001: **Wettelijke correctheid** — uitvoer komt overeen met de officiële publicaties van Belastingdienst/SVB 2026 binnen XCG 0,02 (alleen afronding), voor representatieve medewerkers (standaard, BVZ-vrijgesteld, boven het plafond, en met bijzondere beloning).
- NFR002: **Auditeerbaarheid** — elke stap is herleidbaar: hulpbedragen bestaan als eigen regels, tarieven zijn inspecteerbare gedateerde records, elk custom model heeft een wijzigingslog (de chatter-mixin, `mail.thread`), en tariefrecords zijn append-only.
- NFR003: **Operationele onafhankelijkheid** — de volledige maandelijkse loonadministratie draait binnen Odoo, zonder externe payroll-service of spreadsheet.
- NFR004: **Regelgevende wendbaarheid** — jaarlijkse of ad-hoc tariefwijzigingen vereisen geen code-implementatie; oude records blijven bewaard zodat eerdere perioden correct herberekenen.
- NFR005: **Boekhoudkundige integriteit** — elke afsluiting levert een sluitende journaalpost per constructie.
- NFR006: **Gegevensbescherming** — minimale rechten via groepstoegang, een audittrail, append-only wettelijke records, en geen verzending van loongegevens naar externe diensten (Landsverordening bescherming persoonsgegevens).
- NFR007: **Platform** — Odoo 19 Enterprise op Odoo.sh of self-hosted Enterprise; Odoo SaaS wordt niet ondersteund.
- NFR008: **Idempotente afsluiting** — een run opnieuw openen en afsluiten mag de jaar-tot-datum-totalen niet dubbel tellen of dubbele of niet-sluitende journaalposten boeken (Architecture AD-9).

### Aanvullende eisen

**Uit de Architecture Spine (invarianten AD-1…AD-20) — deze gelden voor elke berekenings-story:**

- AR001: **Geen starter-template.** Dit is een nieuwe (greenfield) Odoo-module; de eerste epic zet de module-steiger op volgens Technisch Ontwerp §13 (manifest, packagelay-out en de laaggrenzen, AD-11).
- AR002: **Tekenconventie (AD-1)** — werknemersinhoudingen en -premies zijn negatief; werkgeverskosten en basisbedragen zijn positief.
- AR003: **Categorieregels (AD-2)** — netto = basis + toeslagen + inhoudingen (`BASIC + ALW + DED`, met inhoudingen negatief); werkgeverskosten staan in de werkgeverscategorie (`ER`) en blijven buiten netto; overuren gaan in toeslagen (`ALW`); onbelaste vergoedingen (`NONTAXED`) zijn een afzonderlijke regel na netto.
- AR004: **Strikte volgorde en referentiediscipline (AD-3)** — vaste oplopende volgorde; een regel mag alleen eerdere resultaten lezen — eerdere regelbedragen (`rules.CODE.amount`) en categorietotalen (`categories.X`).
- AR005: **Premieplafonds (AD-4 / AD-24)** — SVB-premies met een **jaarplafond** (AOV/AWW, BVZ, AVBZ) worden **cumulatief** berekend (AD-24): premie over het premieloon tot-en-met-deze-periode afgetopt op het jaarplafond, minus reeds ingehouden premie — zodat een eenmalige uitkering alleen wordt belast over de resterende ruimte onder het jaarmaximum (de ×12-annualisatie wordt hiervoor **niet** gebruikt; die faalt bij het plafond). ZV/OV gebruiken een maandplafond, direct toegepast. Loonbelasting gebruikt de periodespecifieke lb-*tabel direct — geen annualisatie (zie AR024). Onder elk plafond is de cumulatieve uitkomst gelijk aan vast tarief × grondslag, dus gewone loonstroken veranderen niet.
- AR006: **Tarieven zijn data (AD-5)** — geen tarief, plafond of grens hardgecodeerd in rule-Python (dit overschrijft de hardgecodeerde v3.0D-listings). Wettelijke data staat in drie append-only gedateerde opslagplaatsen: **SVB-premies + plafonds** in één record per jaar (`hr.svb.parameters`, AD-22); **`bijzondere_beloning`-tarieven + de Belastingdienst-scalairen** (basiskorting, verwervingskosten, toeslagen) in `hr.tax.bracket` op `tax_type`; **loonbelasting** in `hr.loonbelasting.tabel` (AR024). SVB-premies staan **niet** in `hr.tax.bracket` — door ze naar één record per jaar te verplaatsen staat elk gedeeld plafond precies één keer opgeslagen (geen dubbele kopieën per betaler die uiteen kunnen lopen).
- AR007: **Aan/uit-gate en never-gate-set (AD-6)** — zet de gedeelde basisregels nooit uit: de BVZ-grondslag (`BVZ_PREM_INC`), de AOV-grondslag (`AOV_PREM_INC`), de belastinggrondslag (`TAX_INC`), de ruwe belasting (`LOONBEL_RAW`), netto (`NET`) en werkgeverskosten (`TOTAL_ER_COST`).
- AR008: **Zichtbaar versus meegeteld in de berekening (AD-7)** — een audit-vrijstelling houdt de regel zichtbaar maar buiten de berekening (zichtbaarheidsvlag aan, berekeningsvlag uit: `active=True, enabled=False`).
- AR009: **Drielaagse ontkoppeling (AD-8)** — een set toepassen is een eenmalige kopie; de gekoppelde regel op een Tier 3-loonregel (`salary_rule_id`) is alleen-lezen na aanmaak.
- AR010: **Eén vastlegpunt (AD-9)** — alleen de run-afsluitactie (`action_close()`) wijzigt de jaar-tot-datum-totalen en het journaal; de totalen worden herberekend (niet blind opgeteld) zodat opnieuw openen en afsluiten correct blijft, en opnieuw openen draait de journaalpost (`account.move`) terug. De gecontroleerde reopen is de enige in-app reopen; een volledige database-restore is alleen voor noodgevallen en valt buiten de module (een handmatige Odoo.sh-backup vóór afsluiten is de operationele veiligheidsstap).
- AR011: **Sluitend per constructie (AD-10)** — de grootboeknummers zijn indicatief, per bedrijf toegewezen bij onboarding.
- AR012: **Geld en afronding (AD-12)** — valuta XCG; afronden op 2 decimalen; voor loonbelasting retourneert `lookup_loonbelasting` het bedrag direct uit de lb-*tabel (afgerond op 2 decimalen, ook boven het plafond); SVB-premieregels lezen tarief-/plafondvelden uit het record per jaar (`hr.svb.parameters`); `lookup_marginal_rate` geeft het bijzondere-beloningschijftarief; `compute_tax` geeft de gedateerde Belastingdienst-scalairen (basiskorting, verwervingskosten, toeslagen). Aangiftes tonen hele XCG (decimalen weggelaten), terwijl loonstroken en het journaal de werkelijke bedragen met 2 decimalen behouden.
- AR013: **Standaardkortingen gelden altijd (AD-13)** — de verwervingskosten (41,67/mnd, een aftrekpost op het belastbaar inkomen vóór de tabel bij `TAX_INC`/Seq 80; wettelijk forfait, max 500/jr) en de basiskorting (2.915/jr = 242,92/mnd volgens de officiële Belastingdienst *Loonbelastingverklaring 2026*, een heffingskorting op het belastingbedrag ná de tabel bij Seq 100) gelden automatisch voor elke medewerker in v1.0R. (Het bedrag 3.247,35 was een inkomstenbelastingbedrag, niet de loonbelasting-basiskorting.)
- AR019: **Senior-only distributiegate (AD-16)** — loonstrookdistributie is een afzonderlijke actie die beperkt is tot de meest senior bestaande rol, de Salarisbeheerder-groep (`group_l10n_cw_payroll_manager`); er wordt geen nieuwe groep toegevoegd; alleen toegestaan na afsluiten plus een bevestiging "geen restore nodig"; het verzendkanaal is uitgesteld (OQ-01).
- AR020: **Canonieke peildatum (AD-17)** — elke gedateerde-tariefopzoeking, de belastingmethode (`compute_tax`) en de loonbelastingopzoeking (`lookup_loonbelasting`) gebruiken de einddatum van de loonstrookperiode (`payslip.date_to`), nooit `today()`; zo reproduceert een historische herberekening de tarieven van die periode.
- AR021: **Hard falen bij ontbrekende wettelijke data (AD-18)** — een vereist wettelijk tarief of loonbelastingtabel die voor de peildatum ontbreekt geeft een blokkerende fout (`UserError`), nooit een stille 0 (anders dan een bewust uitgezette premie).
- AR022: **Bedrijfsscoping (AD-19)** — nationale wettelijke data (het Belastingschijf-model, het Loonbelastingtabel-model (`hr.loonbelasting.tabel`), salarisregels, categorieën, structuren) is globaal; operationele data (looncomponentsets/-regels, jaar-tot-datum, loonstroken/runs, journaal) is bedrijfsgebonden via `company_id`. Multi-company-activering is een openstaande vraag.
- AR023: **Schema-migratiediscipline** — schemawijzigingen (bijv. de `tax_type`-uitbreiding in AR006) leveren migratiescripts die historische loonstroken en afgesloten jaar-tot-datum behouden; verwijder of herschrijf nooit destructief historische wettelijke records.
- AR024: **Loonbelastingtabelmodel (AD-20)** — loonbelasting wordt opgezocht in `hr.loonbelasting.tabel` (koptekst) / `hr.loonbelasting.tabel.lijn` (rijen); één rij per `(tabel_id, wage_from)`. Koptekstvelden: `name`, `period_type`, `year` (geheel getal), `valid_from`, `valid_to` (leeg = nog actief), `active`. **Selectieregel:** onder alle `active=True`-kopteksten waarbij `period_type` overeenkomt, `year = datum.year`, en `valid_from ≤ payslip.date_to`, kies de versie met de meest recente `valid_from`; bij gelijke `valid_from` wint het record met het hoogste `id` (meest recent geüpload). Dit dekt zowel jaarlijkse uploads als correcties gedurende het jaar zonder dat de oude tabel eerst gearchiveerd hoeft te worden. Opzoeksleutel = `floor(TAX_INC / 5,00) * 5,00` (maandtabel). Boven het tabelplafond: `plafondbelasting + (TAX_INC − plafond) × 46,5%` (MR 144 § Algemeen). Ontbrekende tabel geeft een blokkerende fout (`UserError`, AD-18). Geen annualisatie (AD-4 uitzondering). Peildatum = `payslip.date_to` (AD-17). Globale scope, geen `company_id` (AD-19). Rijen worden nooit verwijderd; vervangen kopteksten bewaard voor audit.

**Manifest en seed-data (Technisch Ontwerp §13):**

- AR014: **Manifest** — afhankelijk van (`hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance`) zonder thema-afhankelijkheid; version `19.0.0.1.0`; country `cw`; license `OPL-1`; geen app en niet automatisch geïnstalleerd (`application=False, auto_install=False`); plus een assets-vermelding (`assets`) die het themastylesheet (`static/src/scss/cw_theme_prl10n.scss`) in de backend-bundel (`web.assets_backend`) laadt — zie UX-DR001.
- AR015: **Seed-data** — lever het maandstructuurtype (`CWMONTHLY`), de standaard-staf-structuur (`CWSTAFF`), de salarisregelcategorieën, alle CW-salarisregels, het **`hr.svb.parameters`-record van 2026** (één per jaar: alle SVB-premietarieven, de AOV-toeslag en de plafonds), de bijzondere-beloningstariefrecords (zes correcte schijven volgens de officiële PDF van 2026), de Belastingdienst-scalairen (basiskorting 2.915/jr, verwervingskosten 500/jr, toeslagen), plus de lb-maandtabelgegevens van 2026 (≈ 3.335 rijen, `period_type = maand`, `valid_from = 2026-01-01`, via `data/hr.loonbelasting.tabel.lijn.csv`).
- AR016: **Vertalingen** — lever het Nederlandse interfacevertaalbestand (`i18n/nl.po`).

**Opgeloste / uitgestelde openstaande vragen:**

- AR017 (**OPGELOST — bevestigd door de product owner**): AD-14 — overuren zijn opgenomen in de premiegrondslag. Bevestigd door onderzoek (~90% van de gevallen vereist het; aangenomen voor allen). Premiegrondslagen komen uit de basis- en toeslagencategorieën (`categories.BASIC + categories.ALW`). Niet langer blokkerend; AD-14 is nu aangenomen in de spine.
- AR018 (uitgesteld, niet-blokkerend): OQ-01 distributie loonstrook; OQ-03 bevestig de standaard overurentarieven (150/150/200/200); OQ-04 fijnmazige rechten per rol; OQ-05 definitieve grootboeknummers; OQ-07 het SVB-gevarenklassemodel (tijdelijk gewoon getalveld → toekomstige dropdown-koppeling, Many2one). Buiten scope voor v1.0R: een custom payroll-snapshot/restore op applicatieniveau (v1.1R+; v1.0R steunt op de gecontroleerde reopen (AD-9), de concept-batch als checkpoint, een handmatige Odoo.sh-backup vóór afsluiten, en Odoo.sh Staging voor testen); uurloon uit gewerkte uren (v1.0R gebruikt het vaste maandloon; medewerkers zonder gewerkte uren worden automatisch weggelaten, FR028); extra loonperiodes, ZV-ziekengeld, leningen/loonbeslag, de jaarlijkse verzamelloonstaat / jaaropgaaf-CSV, elektronische aangifte, DGA-loon en Aruba/Sint Maarten.

### UX-ontwerpeisen

De module gebruikt de standaardschermen van Odoo (lijst-/formulier-/menuweergaven), met een custom gescopeerd stylesheet-thema voor de eigen schermen van de module. Referentie (alleen-lezen, geen afhankelijkheid): `/home/nroosje/dev/odoo-sh/odoo-cbw-ent/service-business-suite/cw_theme`.

- UX-DR001: Lever een gescopeerd stylesheet-thema genaamd `cw_theme_prl10n`, gebundeld **binnen** de module als stylesheetbestand (`static/src/scss/cw_theme_prl10n.scss`) en geladen via de manifest-assets-vermelding (`assets`) in de backend-bundel (`web.assets_backend`) — niet de data-lijst. Geen nieuwe module en geen nieuwe afhankelijkheid.
- UX-DR002: Plaats **elke** themaregel onder één wrapper-CSS-klasse (`.cw_theme_prl10n`), alleen toegepast op de eigen modelschermen van de module (de Belastingschijf-, Looncomponentset- en Medewerker-loonregel-weergaven, en CW-eigen loonstrook-/runweergaven en -rapporten). Voeg de wrapper **nooit** toe aan uitgebreide Odoo-weergaven (Medewerker, Contract, Salarisregel) — Odoo's eigen pagina's moeten er ongewijzigd uitzien.
- UX-DR003: Definieer de pastelkleuren als CSS-variabelen voor lichte modus (de paginaroot, `:root`) en donkere modus (Odoo's donkere-modusklasse, `.o_dark_mode`), met hergebruik van het palet van cw_theme (lavendel/violet accent; mint/perzik/lucht/roze ondersteunende tinten). De kleuren worden naar deze module gekopieerd; cw_theme blijft alleen een referentie, geen afhankelijkheid.
- UX-DR004 (uitgesteld): Portalpaginastyling (de portal-tegenhanger in cw_theme, `.cw-portal`) valt buiten scope voor v1.0R en wordt heroverwogen bij distributie van loonstroken (OQ-01); alleen backend-styling wordt in v1.0R geleverd.

### FR-dekkingskaart

{{requirements_coverage_map}}

## Epic-lijst

{{epics_list}}

# Definities

## Afkortingen

- AOV — Algemene Ouderdomsverzekering.
- AWW — Algemene Weduwen- en Wezenverzekering.
- AVBZ — Algemene Verzekering Bijzondere Ziektekosten (langdurige zorg).
- BVZ — Basisverzekering Ziektekosten.
- ZV — Ziekteverzekering (alleen werkgever).
- OV — Ongevallenverzekering (alleen werkgever, per gevarenklasse).
- SVB — Sociale Verzekeringsbank.
- DGA — Directeur-grootaandeelhouder.
- XCG — Caribische gulden (de valuta van de module).
- GL — Grootboek (General Ledger).
- YTD — Jaar-tot-datum (Year-to-Date).
- PRD — Product Requirements Document.
- AD — Architecture Decision (een genummerde invariant in de Architecture Spine).
- FR / NFR — Functionele / niet-functionele eis.
- AR — Aanvullende eis (architectuur-gedreven).
- UX-DR — UX-ontwerpeis.
- OQ — Openstaande vraag (Open Question).
- UI / UX — gebruikersinterface / gebruikerservaring.
- SCSS / CSS — stylesheet-talen (Sassy CSS / Cascading Style Sheets).
- PDF / CSV — document- / comma-separated-values-bestandsformaten.
- Tier 1/2/3 — de drie lagen van het looncomponentmodel (globale regels / sjabloonsets / loonregels per medewerker).
- v1.0R — de eerste productierelease (manifestversie 19.0.1.0.0).

## Wettelijke en domeintermen

- loonbelasting — periodieke inhouding op loon door de werkgever (voorheffing op de inkomstenbelasting). Wordt bepaald via opzoeking in de officiële lb-*tabel, jaarlijks gepubliceerd door de Belastingdienst Curaçao via Ministeriële Regeling (MR 144). Zie ook: inkomstenbelasting.
- inkomstenbelasting — jaarlijkse belasting op alle inkomsten (loon, bankrente, verhuurinkomsten enz.), geheven via de Schijventarief. De loonbelasting is een voorheffing hierop; de werknemer verrekent ingehouden loonbelasting bij zijn jaarlijkse aangifte inkomstenbelasting.
- loonbelastingkaart — jaarlijks overzicht per medewerker van ingehouden loonbelasting, samengesteld vanuit de jaar-tot-datum-totalen (`hr.wage.component.ytd`); bron voor de verzamelloonstaat en de individuele aangifte (beide uitgesteld naar v1.1R, maar de YTD-data worden al opgebouwd vanaf v1.0R).
- basiskorting — standaard belastingkorting voor elke medewerker.
- toeslagen — belastingkortingen die van de berekende belasting worden afgetrokken (alleenverdieners-, kinder-, ouderentoeslag).
- bijzondere beloningen — bijzondere (niet-periodieke) beloning, belast via een eigen tabel.
- verwervingskosten — vaste forfaitaire aftrek voor verwervingskosten.
- gevarenklasse — SVB-risicoklasse die het OV-percentage bepaalt.
- natura-loon / loon in natura — loon in natura.
- beschikking — individuele beschikking van de Belastingdienst.
- onbelaste vergoedingen — niet-belaste vergoedingen.
- herberekening — herberekening van een run vóór afsluiten.
- verzamelloonstaat / jaaropgaaf — jaarlijkse verzamelloonstaat / jaaropgaaf (beide uitgesteld).
- Belastingdienst — de belastingautoriteit van Curaçao.
- Landsverordening bescherming persoonsgegevens — Curaçaose verordening gegevensbescherming.
- Run-/loonstrookfasen — CONCEPT, TE CONTROLEREN (run afgesloten = AFGESLOTEN), BEVESTIGD (loonstrook bevestigd).

## Modellen en technische identifiers

- `hr.salary.rule` — Salarisregel-model (één berekeningsstap).
- `hr.wage.component.set` — Looncomponentset-model (Tier 2-sjabloon).
- `hr.employee.wage.line` — Medewerker-loonregel-model (Tier 3, per medewerker).
- `hr.tax.bracket` — Belastingschijf-model (gedateerde wettelijke data voor bijzondere-beloningstarieven en de Belastingdienst-scalairen: basiskorting, verwervingskosten, toeslagen). SVB-premies staan hier niet — zie `hr.svb.parameters`.
- `hr.svb.parameters` — SVB-parameterrecord per jaar (één per jaar): alle SVB-premietarieven, de AOV-toeslag en de plafonds, conform de jaarlijkse SVB-tabel (AD-22).
- `hr.loonbelasting.tabel` — Loonbelastingtabel-model, koptekst per tabelversie (velden: `name`, `period_type`, `year`, `valid_from`, `valid_to`, `active`); meerdere versies per periode + jaar zijn mogelijk voor correcties.
- `hr.loonbelasting.tabel.lijn` — Loonbelastingtabelrij: één record per loonstap (`wage_from` → `loonbelasting`).
- `hr.wage.component.ytd` — Jaar-tot-datum-totalenmodel.
- `account.move` — Odoo-journaalpost.
- `mail.thread` — Odoo-mixin die de wijzigingslog (chatter) levert.
- Salarisregelcodes — `TOTAL_LOON` (brutoloon), `NET` (nettoloon), `NONTAXED` (onbelaste vergoedingen), `TOTAL_ER_COST` (werkgeverskosten), en de verborgen grondslagen `BVZ_PREM_INC`, `AOV_PREM_INC`, `TAX_INC`, `LOONBEL_RAW`.
- Categorieën — `BASIC` (basisloon), `ALW` (toeslagen), `DED` (inhoudingen), `ER` (werkgeverskosten).
- Velden en vlaggen — `appears_on_payslip` (toon op loonstrook), `enabled` (telt mee in de berekening), `active` (zichtbaar), `valid_from` / `valid_to` (geldigheidsdatums tarief), `salary_rule_id` (gekoppelde regel), `tax_type` (tarieftype), `employee_id.user_id` (eigenaarskoppeling voor de recordregel).
- `tax_type`-waarden — `bijzondere_beloning`, `basiskorting`, `verwervingskosten` en de toeslagtypes. (SVB-premies zijn geen `tax_type`-waarden meer — die zijn verplaatst naar `hr.svb.parameters`, AD-22. Loonbelasting gebruikt `hr.loonbelasting.tabel`.)
- `compute_tax` — methode op `hr.tax.bracket` die de gedateerde Belastingdienst-scalair (basiskorting, verwervingskosten, toeslag) voor een `tax_type` en datum teruggeeft.
- `lookup_marginal_rate` — methode op `hr.tax.bracket` die het enkele bijzondere-beloningschijftarief teruggeeft waarvan het bereik het jaarloon bevat (geen accumulatie); gebruikt door EXTRA_TAX (AD-21).
- `lookup_loonbelasting` — methode op `hr.loonbelasting.tabel` die het periodieke loonbelastingbedrag teruggeeft voor een gegeven loon, periodetype en peildatum. Selecteert de actieve tabelversie op `valid_from desc, id desc` (meest recente ingangsdatum, daarna meest recente upload); past de boven-plafond-regel toe indien nodig; geeft een `UserError` als geen tabel gevonden wordt.
- `action_close()` — de run-afsluitactie; het enige vastlegpunt.
- `CWMONTHLY` / `CWSTAFF` — het maandstructuurtype / de standaard-staf-salarisstructuur.
- Manifestsleutels — `depends`, `version`, `country`, `license`, `application`, `auto_install`, `assets`, `data`.
- `web.assets_backend` — Odoo backend-assetbundel.
- `.cw_theme_prl10n` — thema-wrapper-CSS-klasse; `:root` / `.o_dark_mode` — token-scopes voor lichte / donkere modus; `.cw-portal` — portal-scope (uitgesteld).
- `static/src/scss/cw_theme_prl10n.scss` — het themastylesheet; `i18n/nl.po` — het Nederlandse vertaalbestand.
