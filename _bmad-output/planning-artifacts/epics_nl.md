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

Dit document bevat de volledige epic- en story-uitsplitsing voor l10n_cw_hr_payroll en vertaalt de eisen uit de PRD en de Architecture Spine (met het v3.0D Technisch Ontwerp als implementatiereferentie) naar implementeerbare stories. Er is geen apart UX-ontwerpcontract: de module gebruikt Odoo's eigen UI, alleen uitgebreid waar Odoo-modellen worden uitgebreid, plus een gescopeerd in-module SCSS-thema.

## Eisenoverzicht

### Functionele eisen

**Wettelijke berekeningsengine**

- FR001: Bereken de maandelijkse loonadministratie voor alle medewerkers in een run met één actie.
- FR002: Voer de canonieke wettelijke berekening uit als geordende `hr.salary.rule`-records, geëvalueerd in strikt oplopende Sequence 10–150 (de ~21 regels die de 14 wettelijke Stappen afbeelden), waarbij verborgen tussenresultaten `appears_on_payslip = False` dragen.
- FR003: Bereken `TOTAL_LOON` = contractloon + secundaire arbeidsvoorwaarden (loon in natura).
- FR004: Bereken vier overurentypes (doordeweeks, zaterdag, zondag, feestdag) als afzonderlijke benoemde loonstrookregels, op basis van ureninvoer en per medewerker configureerbare tarieven, die bijdragen aan ALW.
- FR005: Bereken BVZ — werkgever vast 9,3% en werknemer glijdend 0%–4,3% — over de geannualiseerde, afgetopte BVZ-premiegrondslag.
- FR006: Bereken AOV/AWW — werknemer 6,5% en werkgever 9,5% tot het plafond, plus een werknemerstoeslag van 1% over inkomen boven het plafond.
- FR007: Bereken AVBZ — werknemer glijdend 0,5%/1,5% op basis van de lage-inkomensgrens en werkgever vast 0,5% — over de AOV-grondslag afgetopt op het AVBZ-plafond.
- FR008: Bereken loonbelasting via de progressieve schijventabel (`compute_tax`), die de ruwe belasting teruggeeft, en pas vervolgens toeslagen toe als monetaire aftrekposten op het belastingbedrag (niet als inkomensverlagingen), afgekapt op nul.
- FR009: Pas basiskorting automatisch toe op alle medewerkers; pas alleenverdieners-, kinder- en ouderentoeslag toe vanuit velden per medewerker.
- FR010: Bereken extra belasting op bijzondere beloningen met de afzonderlijke (exclusief basiskorting) marginale-tarieftabel, alleen toegepast op het bedrag van de bijzondere beloning.
- FR011: Bereken ZV (werkgever 1,9%) en OV (werkgever variabel per gevarenklasse) over het gedeelde ZV/OV-loonplafond, op basis van het contractbasisloon (exclusief secundaire arbeidsvoorwaarden).
- FR012: Bereken `NET` (= BASIC + ALW + DED) en `NONTAXED` (onbelaste vergoedingen) als afzonderlijke regel na NET; uitbetaald bedrag = NET + NONTAXED.
- FR013: Bereken `TOTAL_ER_COST` (informatief totaal werkgeverskosten-aggregaat).
- FR014: Schakel afzonderlijke premies en belastingen per medewerker in/uit via de `enabled`-vlag, met als resultaat 0,00 zonder de berekeningsketen te breken; gedeelde inkomensgrondslag-tussenresultaten worden altijd uitgevoerd.

**Looncomponentmodel & configuratie**

- FR015: Lever het drielaags looncomponentmodel — Tier 1 globale regels (`hr.salary.rule`), Tier 2 bedrijfsspecifieke sjabloonsets (`hr.wage.component.set` + regels), Tier 3 loonregels per medewerker (`hr.employee.wage.line`).
- FR016: Pas een Tier 2-componentset toe op één of meer medewerkers via de toepaswizard, waarbij onafhankelijke Tier 3-records worden aangemaakt die latere wijzigingen aan de set niet overnemen.
- FR017: Sla alle wettelijke tarieven, plafonds en grenzen op als gedateerde `hr.tax.bracket`-records; werk tarieven bij door `valid_to` te zetten en nieuwe gedateerde records in te voegen, zonder code-implementatie.
- FR018: Onderhoud cumulatie per medewerker, per component, per jaar (YTD) (`hr.wage.component.ytd`), bijgewerkt bij het afsluiten van de run en bewaard over jaren heen.
- FR019: Lever toeslagvelden en beschikkingsinvoer per medewerker, en een OV-percentageveld per contract.

**Runlevenscyclus & boekhouding**

- FR020: Stuur de runlevenscyclus CONCEPT → TE CONTROLEREN → AFGESLOTEN en de loonstrooklevenscyclus CONCEPT → TE CONTROLEREN → BEVESTIGD (met annuleren) aan, waarbij herberekening vóór afsluiten is toegestaan.
- FR021: Bevestig en vergrendel bij afsluiten de loonstroken, herbereken YTD, boek de journaalpost en stel run-rapporten beschikbaar — als het enige punt waarop de status wordt vastgelegd.
- FR022: Genereer bij afsluiten een sluitende `account.move` (totaal debet ≡ totaal credit per constructie) met de configureerbare grootboekmapping.

**Rapporten**

- FR023: Produceer de loonstrook-PDF (A-01) in Curaçaose lay-out.
- FR024: Produceer de maandelijkse aangifte loonbelasting (B-01) en de aangifte SVB-premies (B-02) per run.
- FR025: Produceer het sluitende loonjournaalpost-overzicht (B-05) per run.

**Beveiliging & toegang**

- FR026: Lever vier beveiligingsrollen (Medewerker, Salarisgebruiker, Salarisbeheerder, Accountant) met minimale rechten.
- FR027: Beperk medewerkers tot hun eigen loonstroken via een recordregel (`employee_id.user_id = user`).

**Run-lidmaatschap & contractperiode**

- FR028: Een loonrun sluit een medewerker voor een periode **automatisch** uit wanneer (a) de medewerker geen gewerkte uren in die periode heeft, of (b) de medewerker niet langer in dienst is (contract beëindigd op of vóór de periode). Uitsluiting is automatisch — nooit een handmatige actie van de beheerder; uitgesloten medewerkers krijgen geen loonstrook en komen niet voor in de runtotalen of de journaalpost.
- FR029: Elk arbeidscontract heeft een verplichte begindatum en een optionele einddatum; het invoeren van een einddatum bepaalt wanneer de medewerker uit dienst gaat. De run gebruikt deze datums om te bepalen of een medewerker in de periode in dienst is (zie FR028). Openeinde-contracten voor onbepaalde tijd (zonder einddatum) zijn toegestaan.

### Niet-functionele eisen

- NFR001: **Wettelijke correctheid** — berekeningsuitvoer sluit aan op de officiële publicaties van Belastingdienst/SVB 2026 binnen XCG 0,02 (afrondingstolerantie), voor representatieve medewerkers (standaard, BVZ-vrijgesteld, boven plafond, met bijzondere beloning).
- NFR002: **Auditeerbaarheid** — elke berekeningsstap herleidbaar: tussenresultaten gematerialiseerd als regels, tarieven inspecteerbaar als gedateerde records, `mail.thread`-chatter op alle custom modellen, append-only belastingschijf-records.
- NFR003: **Operationele onafhankelijkheid** — maandelijkse loonadministratie volledig binnen Odoo, zonder externe payroll-service of spreadsheet.
- NFR004: **Regelgevende wendbaarheid** — jaarlijkse of ad-hoc tariefwijzigingen vereisen geen code-implementatie; historische records blijven behouden voor correcte herberekening van eerdere perioden.
- NFR005: **Boekhoudkundige integriteit** — elke runafsluiting levert een sluitende journaalpost per constructie.
- NFR006: **Gegevensbescherming** — minimale rechten via groepsgebaseerde toegang, audittrail, append-only wettelijke records, geen verzending van loongegevens naar externe diensten (Landsverordening bescherming persoonsgegevens).
- NFR007: **Platform** — Odoo 19 Enterprise op Odoo.sh of self-hosted Enterprise; Odoo SaaS niet ondersteund.
- NFR008: **Idempotente afsluiting** — een run opnieuw openen en opnieuw afsluiten mag YTD niet dubbel tellen of dubbele/niet-sluitende journaalposten boeken (Architecture AD-9).

### Aanvullende eisen

**Uit de Architecture Spine (invarianten AD-1…AD-15) — deze gelden voor elke berekenings-story:**

- AR001: **Geen starter-template.** Greenfield Odoo-module; de eerste epic zet de module-steiger op volgens Technisch Ontwerp §13 (manifest, packagelay-out, laaggrenzen AD-11).
- AR002: **Tekenconventie (AD-1)** — werknemersaftrekken/-premies negatief; werkgeverskosten en grondslagen positief.
- AR003: **Categorietoewijzingscontract (AD-2)** — NET = BASIC+ALW+DED (DED negatief); ER uitgesloten; overuren in ALW; NONTAXED een afzonderlijke regel na NET.
- AR004: **Strikte volgorde + referentiediscipline (AD-3)** — vaste oplopende Sequence; verwijs alleen naar eerdere resultaten via `rules.CODE.amount` / `categories.X`.
- AR005: **Annualisatieconventie (AD-4)** — ×12 → pas jaarplafond/-schaal/-schijf toe → ÷12.
- AR006: **Gedateerde-tariefautoriteit (AD-5)** — ALLE wettelijke tarieven/plafonds (inclusief premies) staan in `hr.tax.bracket`; **geen tariefliteralen in rule-Python** (overschrijft de hardgecodeerde v3.0D-listings). Vereist een **seed-wijziging**: breid `tax_type` uit naar granulaire per-(verzekering, betaler)-waarden (`bvz_emp`, `bvz_er`, `avbz_emp`, `avbz_er`, `aov_aww_emp`, `aov_aww_er`, `aov_aww_surcharge`, `zv`, `ov`, `loonbelasting`, `bijzondere_beloning`) met een gedefinieerd leescontract per type.
- AR007: **In/uitschakel-gate + never-gate-set (AD-6)** — gate nooit BVZ_PREM_INC, AOV_PREM_INC, TAX_INC, LOONBEL_RAW, NET, TOTAL_ER_COST.
- AR008: **active vs enabled-splitsing (AD-7)** — vrijstelling voor audit = `active=True, enabled=False`.
- AR009: **Drielaagse ontkoppeling (AD-8)** — toepassen is een eenmalige kopie; T3.salary_rule_id alleen-lezen na aanmaak.
- AR010: **Enig punt voor statusvastlegging (AD-9)** — alleen `action_close()` muteert YTD en het journaal; YTD wordt herberekend (niet blind opgeteld) voor idempotent opnieuw openen/afsluiten; opnieuw openen draait de `account.move` terug.
- AR011: **Sluitend per constructie (AD-10)** — grootboeknummers indicatief, per bedrijf toegewezen bij onboarding.
- AR012: **Geld & afronding (AD-12)** — XCG; afronden op 2 decimalen; `compute_tax` geeft ruwe belasting vóór toeslagen.
- AR013: **Wettelijke standaardwaarden onvoorwaardelijk (AD-13)** — verwervingskosten (41.67/mnd) en basiskorting (2 915/jr) automatisch toegepast op alle medewerkers voor v1.0R.

**Manifest & seed-data (Technisch Ontwerp §13):**

- AR014: Manifest — `depends: [hr, hr_contract, hr_holidays, hr_payroll, hr_payroll_account, hr_attendance]` (geen thema-afhankelijkheid toegevoegd), version `19.0.0.1.0`, country `cw`, license `OPL-1`, `application=False`, `auto_install=False`, plus een `assets`-sleutel die `static/src/scss/cw_theme_prl10n.scss` registreert in `web.assets_backend` (zie UX-DR001).
- AR015: Lever seed-data — `CWMONTHLY`-structuurtype, `CWSTAFF`-structuur, salarisregelcategorieën, alle CW-salarisregels, en de gedateerde tariefrecords van 2026 (loonbelastingschijven, SVB-premies/plafonds, bijzondere beloningen, toeslagen).
- AR016: Lever Nederlandse UI-vertalingen (`i18n/nl.po`).

**Opgeloste / uitgestelde openstaande vragen:**

- AR017 (**OPGELOST — bevestigd door de product owner**): AD-14 — overuren zijn opgenomen in de premie-inkomensgrondslag. Bevestigd via onderzoek (~90% van de gevallen vereist opname; aangenomen voor allen). Premiegrondslagen zijn afgeleid van `categories.BASIC + categories.ALW`. Niet langer blokkerend; AD-14 gepromoveerd tot `[ADOPTED]` in de spine.
- AR018 (uitgesteld, niet-blokkerend): OQ-01 distributie loonstrook; OQ-03 bevestig standaard overurentarieven (150/150/200/200); OQ-04 granulaire rechten per groep; OQ-05 definitieve grootboeknummers; OQ-07 SVB-gevarenklassemodel (tijdelijk Float → toekomstige Many2one). Buiten scope voor v1.0R: uurloonberekening op basis van gewerkte uren (v1.0R gebruikt het vaste maandloon; medewerkers zonder gewerkte uren worden automatisch uitgesloten, FR028); aanvullende loonperiodes, ZV-ziekengeld, leningen/loonbeslag, verzamelloonstaat/jaaropgaaf-CSV, elektronische aangifte, DGA, Aruba/Sint Maarten.

### UX-ontwerpeisen

De module gebruikt Odoo's eigen UI (lijst-/formulier-/menuweergaven), met een custom gescopeerd SCSS-thema voor de eigen weergaven van de module. Referentie (alleen-lezen, geen afhankelijkheid): `/home/nroosje/dev/odoo-sh/odoo-cbw-ent/service-business-suite/cw_theme`.

- UX-DR001: Lever een gescopeerd SCSS-thema **`cw_theme_prl10n`** gebundeld **binnen** `l10n_cw_hr_payroll` (`static/src/scss/cw_theme_prl10n.scss`), geregistreerd via de manifest-**`assets`**-sleutel onder `web.assets_backend` (niet de `data`-lijst). Geen nieuwe module en geen nieuwe manifest-afhankelijkheid.
- UX-DR002: Scope **alle** themaregels onder één `.cw_theme_prl10n`-wrapperklasse, alleen toegepast op de eigen custom-modelweergaven van de module (`hr.tax.bracket`, `hr.wage.component.set`, `hr.employee.wage.line`, en CW-eigen loonstrook-/runweergaven/-rapporten). Voeg de wrapper **nooit** toe aan overgeërfde Odoo-modelweergaven (`hr.employee`, `hr.contract`, `hr.salary.rule`-uitbreidingen) — Odoo's eigen pagina's moeten visueel ongewijzigd blijven.
- UX-DR003: Definieer pasteldesigntokens als CSS-variabelen voor **licht** (`:root`) en **donker** (`.o_dark_mode`), met hergebruik van het palet van cw_theme (lavendel/violet accent; mint/perzik/lucht/roze ondersteunende tinten). Tokens worden **gekopieerd** naar deze module; cw_theme blijft alleen referentie, geen runtime-afhankelijkheid.
- UX-DR004 (uitgesteld): Portalpaginastyling (de `.cw-portal`-tegenhanger van cw_theme) valt buiten scope voor v1.0R en wordt heroverwogen bij distributie van loonstroken (OQ-01); alleen backend-styling wordt in v1.0R geleverd.

### FR-dekkingskaart

{{requirements_coverage_map}}

## Epic-lijst

{{epics_list}}
