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
- FR005: Bereken de BVZ-zorgpremie — werkgever vast 9,3% en werknemer glijdend 0%–4,3% — over de jaarlijks afgetopte BVZ-grondslag.
- FR006: Bereken de AOV/AWW-premie (ouderdom en nabestaanden) — werknemer 6,5% en werkgever 9,5% tot het plafond — plus een werknemerstoeslag van 1% over inkomen boven het plafond.
- FR007: Bereken de AVBZ-premie (langdurige zorg) — werknemer glijdend 0,5%/1,5% op basis van de lage-inkomensgrens, werkgever vast 0,5% — over de AOV-grondslag afgetopt op het AVBZ-plafond.
- FR008: Bereken de loonbelasting via de belastingberekenmethode (`compute_tax`) met de progressieve schijventabel, die de ruwe belasting teruggeeft; trek vervolgens de toeslagen af als geld van het belastingbedrag (niet van het belastbaar inkomen), met een ondergrens van nul.
- FR009: Pas de basiskorting automatisch toe op elke medewerker; pas de alleenverdieners-, kinder- en ouderentoeslag toe vanuit velden op de medewerker.
- FR010: Bereken de extra belasting op bijzondere beloningen met de eigen marginale-tarieftabel (de variant "exclusief basiskorting"), alleen toegepast op het bedrag van de bijzondere beloning.
- FR011: Bereken de ZV-premie (ziekte, werkgever 1,9%) en de OV-premie (ongevallen, werkgever, variabel per gevarenklasse) over het gedeelde ZV/OV-loonplafond, op basis van het contractbasisloon (exclusief loon in natura).
- FR012: Bereken het nettoloon — de nettoloonregel (`NET`) = categorieën basis + toeslagen + inhoudingen (`BASIC + ALW + DED`) — en onbelaste vergoedingen als afzonderlijke regel na netto via de onbelaste-regel (`NONTAXED`); uitbetaald bedrag = netto + onbelast.
- FR013: Bereken de totale werkgeverskosten als informatief totaal via de werkgeverskostenregel (`TOTAL_ER_COST`).
- FR014: Laat de salarisadministrateur afzonderlijke premies en belastingen per medewerker aan- of uitzetten via de aan/uit-vlag (`enabled`) op de loonregel van de medewerker; een uitgezette regel geeft 0,00 terug zonder de keten te breken, terwijl de gedeelde basisregels altijd draaien.

**Looncomponentmodel en configuratie**

- FR015: Lever het drielaags looncomponentmodel — Tier 1 globale regels (het Salarisregel-model, `hr.salary.rule`), Tier 2 bedrijfssjabloonsets (het Looncomponentset-model, `hr.wage.component.set`, met zijn regels) en Tier 3 loonregels per medewerker (het Medewerker-loonregel-model, `hr.employee.wage.line`).
- FR016: Pas een Tier 2-sjabloonset toe op één of meer medewerkers via de toepaswizard, waarbij onafhankelijke Tier 3-loonregels worden aangemaakt die niet meewijzigen als de set later wordt bewerkt.
- FR017: Sla elk wettelijk tarief, plafond en grens op als gedateerde records in het Belastingschijf-model (`hr.tax.bracket`); wijzig een tarief door het oude record af te sluiten (zet de geldig-tot-datum, `valid_to`) en een nieuw gedateerd record toe te voegen — zonder code-implementatie.
- FR018: Houd een lopend jaar-tot-datum-totaal bij per medewerker, per component, per jaar in het Jaar-tot-datum-model (`hr.wage.component.ytd`), bijgewerkt bij het afsluiten van een run en bewaard over jaren heen.
- FR019: Lever de toeslagvelden en de beschikkingsinvoer (beschikking) op de medewerker, en een gevarenklasse-percentage (OV%) op het contract.

**Runlevenscyclus en boekhouding**

- FR020: Stuur de run door zijn fasen (Concept → Te controleren → Afgesloten / CONCEPT → TE CONTROLEREN → AFGESLOTEN) en elke loonstrook door zijn fasen (Concept → Te controleren → Bevestigd / CONCEPT → TE CONTROLEREN → BEVESTIGD, met annuleren), waarbij herberekening vóór afsluiten is toegestaan.
- FR021: Bevestig en vergrendel bij afsluiten de loonstroken, herbereken de jaar-tot-datum-totalen, boek de journaalpost en stel de run-rapporten beschikbaar — dit afsluiten is het enige punt waarop resultaten worden vastgelegd.
- FR022: Genereer bij afsluiten een sluitende journaalpost (de boekingspost, `account.move`) waarbij totaal debet gelijk is aan totaal credit per constructie, met de configureerbare grootboekmapping.

**Rapporten**

- FR023: Produceer de loonstrook-PDF (rapport A-01) in Curaçaose lay-out.
- FR024: Produceer de maandelijkse aangifte loonbelasting (rapport B-01) en de aangifte SVB-premies (rapport B-02) per run.
- FR025: Produceer het sluitende loonjournaalpost-overzicht (rapport B-05) per run.

**Beveiliging en toegang**

- FR026: Lever vier beveiligingsrollen (Medewerker, Salarisgebruiker, Salarisbeheerder, Accountant) met minimale rechten.
- FR027: Beperk elke medewerker tot zijn eigen loonstroken met een recordregel die de ingelogde gebruiker matcht (`employee_id.user_id = user`).

**Run-lidmaatschap en contractperiode**

- FR028: Een loonrun laat een medewerker voor een periode **automatisch** weg wanneer (a) hij geen gewerkte uren in die periode heeft, of (b) hij niet langer in dienst is (contract beëindigd op of vóór de periode). Dit is automatisch — nooit een handmatige stap; weggelaten medewerkers krijgen geen loonstrook en komen niet voor in de runtotalen of de journaalpost.
- FR029: Elk arbeidscontract heeft een verplichte begindatum en een optionele einddatum; het invoeren van een einddatum bepaalt wanneer de medewerker uit dienst gaat. De run gebruikt deze datums om te bepalen of een medewerker in de periode in dienst is (zie FR028). Vaste contracten zonder einddatum zijn toegestaan.

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

**Uit de Architecture Spine (invarianten AD-1…AD-15) — deze gelden voor elke berekenings-story:**

- AR001: **Geen starter-template.** Dit is een nieuwe (greenfield) Odoo-module; de eerste epic zet de module-steiger op volgens Technisch Ontwerp §13 (manifest, packagelay-out en de laaggrenzen, AD-11).
- AR002: **Tekenconventie (AD-1)** — werknemersinhoudingen en -premies zijn negatief; werkgeverskosten en basisbedragen zijn positief.
- AR003: **Categorieregels (AD-2)** — netto = basis + toeslagen + inhoudingen (`BASIC + ALW + DED`, met inhoudingen negatief); werkgeverskosten staan in de werkgeverscategorie (`ER`) en blijven buiten netto; overuren gaan in toeslagen (`ALW`); onbelaste vergoedingen (`NONTAXED`) zijn een afzonderlijke regel na netto.
- AR004: **Strikte volgorde en referentiediscipline (AD-3)** — vaste oplopende volgorde; een regel mag alleen eerdere resultaten lezen — eerdere regelbedragen (`rules.CODE.amount`) en categorietotalen (`categories.X`).
- AR005: **Annualisatie (AD-4)** — vermenigvuldig de maandgrondslag met 12, pas het jaarplafond/-schaal/-schijf toe, deel daarna terug door 12.
- AR006: **Tarieven zijn data (AD-5)** — elk wettelijk tarief en plafond (premies inbegrepen) staat in het Belastingschijf-model (`hr.tax.bracket`); geen tariefwaarden hardgecodeerd in rule-Python (dit overschrijft de hardgecodeerde v3.0D-listings). Vereist een seed-wijziging: splits het tarieftype-veld (`tax_type`) in specifieke waarden per verzekering en betaler (`bvz_emp`, `bvz_er`, `avbz_emp`, `avbz_er`, `aov_aww_emp`, `aov_aww_er`, `aov_aww_surcharge`, `zv`, `ov`, `loonbelasting`, `bijzondere_beloning`), elk met een gedefinieerde manier om het te lezen.
- AR007: **Aan/uit-gate en never-gate-set (AD-6)** — zet de gedeelde basisregels nooit uit: de BVZ-grondslag (`BVZ_PREM_INC`), de AOV-grondslag (`AOV_PREM_INC`), de belastinggrondslag (`TAX_INC`), de ruwe belasting (`LOONBEL_RAW`), netto (`NET`) en werkgeverskosten (`TOTAL_ER_COST`).
- AR008: **Zichtbaar versus meegeteld in de berekening (AD-7)** — een audit-vrijstelling houdt de regel zichtbaar maar buiten de berekening (zichtbaarheidsvlag aan, berekeningsvlag uit: `active=True, enabled=False`).
- AR009: **Drielaagse ontkoppeling (AD-8)** — een set toepassen is een eenmalige kopie; de gekoppelde regel op een Tier 3-loonregel (`salary_rule_id`) is alleen-lezen na aanmaak.
- AR010: **Eén vastlegpunt (AD-9)** — alleen de run-afsluitactie (`action_close()`) wijzigt de jaar-tot-datum-totalen en het journaal; de totalen worden herberekend (niet blind opgeteld) zodat opnieuw openen en afsluiten correct blijft, en opnieuw openen draait de journaalpost (`account.move`) terug.
- AR011: **Sluitend per constructie (AD-10)** — de grootboeknummers zijn indicatief, per bedrijf toegewezen bij onboarding.
- AR012: **Geld en afronding (AD-12)** — valuta XCG; afronden op 2 decimalen; de belastingberekenmethode (`compute_tax`) geeft de ruwe belasting vóór toeslagen.
- AR013: **Standaardkortingen gelden altijd (AD-13)** — de verwervingskosten (41.67/mnd) en de basiskorting (2 915/jr) gelden automatisch voor elke medewerker in v1.0R.

**Manifest en seed-data (Technisch Ontwerp §13):**

- AR014: **Manifest** — afhankelijk van (`hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance`) zonder thema-afhankelijkheid; version `19.0.0.1.0`; country `cw`; license `OPL-1`; geen app en niet automatisch geïnstalleerd (`application=False, auto_install=False`); plus een assets-vermelding (`assets`) die het themastylesheet (`static/src/scss/cw_theme_prl10n.scss`) in de backend-bundel (`web.assets_backend`) laadt — zie UX-DR001.
- AR015: **Seed-data** — lever het maandstructuurtype (`CWMONTHLY`), de standaard-staf-structuur (`CWSTAFF`), de salarisregelcategorieën, alle CW-salarisregels en de gedateerde tariefrecords van 2026 (loonbelastingschijven, SVB-premies en -plafonds, bijzondere-beloningstarieven, toeslagen).
- AR016: **Vertalingen** — lever het Nederlandse interfacevertaalbestand (`i18n/nl.po`).

**Opgeloste / uitgestelde openstaande vragen:**

- AR017 (**OPGELOST — bevestigd door de product owner**): AD-14 — overuren zijn opgenomen in de premiegrondslag. Bevestigd door onderzoek (~90% van de gevallen vereist het; aangenomen voor allen). Premiegrondslagen komen uit de basis- en toeslagencategorieën (`categories.BASIC + categories.ALW`). Niet langer blokkerend; AD-14 is nu aangenomen in de spine.
- AR018 (uitgesteld, niet-blokkerend): OQ-01 distributie loonstrook; OQ-03 bevestig de standaard overurentarieven (150/150/200/200); OQ-04 fijnmazige rechten per rol; OQ-05 definitieve grootboeknummers; OQ-07 het SVB-gevarenklassemodel (tijdelijk gewoon getalveld → toekomstige dropdown-koppeling, Many2one). Buiten scope voor v1.0R: uurloon uit gewerkte uren (v1.0R gebruikt het vaste maandloon; medewerkers zonder gewerkte uren worden automatisch weggelaten, FR028); extra loonperiodes, ZV-ziekengeld, leningen/loonbeslag, de jaarlijkse verzamelloonstaat / jaaropgaaf-CSV, elektronische aangifte, DGA-loon en Aruba/Sint Maarten.

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

- loonbelasting — belasting op loon.
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
- `hr.tax.bracket` — Belastingschijf-model (gedateerde wettelijke tarieven).
- `hr.wage.component.ytd` — Jaar-tot-datum-totalenmodel.
- `account.move` — Odoo-journaalpost.
- `mail.thread` — Odoo-mixin die de wijzigingslog (chatter) levert.
- Salarisregelcodes — `TOTAL_LOON` (brutoloon), `NET` (nettoloon), `NONTAXED` (onbelaste vergoedingen), `TOTAL_ER_COST` (werkgeverskosten), en de verborgen grondslagen `BVZ_PREM_INC`, `AOV_PREM_INC`, `TAX_INC`, `LOONBEL_RAW`.
- Categorieën — `BASIC` (basisloon), `ALW` (toeslagen), `DED` (inhoudingen), `ER` (werkgeverskosten).
- Velden en vlaggen — `appears_on_payslip` (toon op loonstrook), `enabled` (telt mee in de berekening), `active` (zichtbaar), `valid_from` / `valid_to` (geldigheidsdatums tarief), `salary_rule_id` (gekoppelde regel), `tax_type` (tarieftype), `employee_id.user_id` (eigenaarskoppeling voor de recordregel).
- `tax_type`-waarden — `loonbelasting`, `bijzondere_beloning`, `bvz_emp`, `bvz_er`, `avbz_emp`, `avbz_er`, `aov_aww_emp`, `aov_aww_er`, `aov_aww_surcharge`, `zv`, `ov`.
- `compute_tax` — methode die de ruwe belasting uit de schijventabel teruggeeft.
- `action_close()` — de run-afsluitactie; het enige vastlegpunt.
- `CWMONTHLY` / `CWSTAFF` — het maandstructuurtype / de standaard-staf-salarisstructuur.
- Manifestsleutels — `depends`, `version`, `country`, `license`, `application`, `auto_install`, `assets`, `data`.
- `web.assets_backend` — Odoo backend-assetbundel.
- `.cw_theme_prl10n` — thema-wrapper-CSS-klasse; `:root` / `.o_dark_mode` — token-scopes voor lichte / donkere modus; `.cw-portal` — portal-scope (uitgesteld).
- `static/src/scss/cw_theme_prl10n.scss` — het themastylesheet; `i18n/nl.po` — het Nederlandse vertaalbestand.
