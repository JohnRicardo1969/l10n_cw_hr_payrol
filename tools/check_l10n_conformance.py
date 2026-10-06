#!/usr/bin/env python3
"""Conformance check of l10n_cw_hr_payroll against official Odoo 19 payroll localizations.

Compares the module with the conventions shared by the 25 official
``l10n_<cc>_hr_payroll`` modules in Odoo 19 Enterprise. Each convention has a
check ID (C-xx); the human-readable reference for every ID is
docs/reference/official-localization-checklist.md.

Deliberate or pending divergences are listed in the divergence register,
docs/reference/official-localization-divergences.md. A failing check is
classified against that register:

    PASS            conforms
    N/A             the artifact the check inspects does not exist yet
    KNOWN-DECIDED   fails, register row says Decided (divergence is intentional)
    KNOWN-OPEN      fails, register row says Open (awaiting a decision)
    NEW             fails and is not in the register - investigate
    STALE           register lists the ID but the check now passes (remove the row)

Usage:
    python3 tools/check_l10n_conformance.py              # compact report
    python3 tools/check_l10n_conformance.py --verbose    # every check with detail
    python3 tools/check_l10n_conformance.py --strict     # exit 1 on any NEW
    python3 tools/check_l10n_conformance.py --module PATH

Exit codes:
    0  always, without --strict (the git pre-commit hook must never block a commit);
       also when the checker itself crashes - it prints a warning instead
    1  only with --strict, when at least one check is NEW

Standard library only: the check must run in any shell, without an Odoo
environment, so Odoo is never imported.
"""

import argparse
import ast
import csv
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODULE = REPO_ROOT / 'l10n_cw_hr_payroll'
DEFAULT_REGISTER = REPO_ROOT / 'docs' / 'reference' / 'official-localization-divergences.md'

# The country code is derived from the folder name in Module; only the display
# name of the country cannot be derived, so it is the one localized constant.
COUNTRY_NAMES = {'cw': 'Curaçao'}

PASS, NA, FAIL = 'PASS', 'N/A', 'FAIL'

# Models whose data official localizations reload on update (C-23).
PAYROLL_LOGIC_MODELS = {
    'hr.salary.rule', 'hr.salary.rule.category', 'hr.rule.parameter',
    'hr.rule.parameter.value', 'hr.payroll.structure', 'hr.payroll.structure.type',
}

CHECKS = []


def check(check_id, description):
    def register(func):
        CHECKS.append((check_id, description, func))
        return func
    return register


class Module:
    """Lazily parsed view of the module, shared by all checks."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        self.name = self.path.name
        match = re.match(r'^l10n_([a-z]{2})_', self.name)
        self.cc = match.group(1) if match else 'cw'
        self.country_name = COUNTRY_NAMES.get(self.cc, self.cc.upper())
        self._manifest = None
        self._xml_records = None
        self._model_classes = None

    @property
    def manifest(self):
        if self._manifest is None:
            source = (self.path / '__manifest__.py').read_text(encoding='utf-8')
            # Parsing the dict node instead of the whole file tolerates leading
            # comment lines and never executes module code.
            tree = ast.parse(source)
            node = next(n.value for n in tree.body if isinstance(n, ast.Expr))
            self._manifest = ast.literal_eval(node)
        return self._manifest

    def py_files(self):
        return sorted(p for p in self.path.rglob('*.py') if '__pycache__' not in p.parts)

    def xml_files(self):
        return sorted(self.path.rglob('*.xml'))

    def rel(self, path):
        return str(Path(path).relative_to(self.path))

    @property
    def xml_records(self):
        """List of dicts: file, id, model, fields {name: element}, noupdate."""
        if self._xml_records is None:
            self._xml_records = []
            for path in self.xml_files():
                root = ET.parse(path).getroot()
                if root.tag != 'odoo':
                    continue
                root_noupdate = root.get('noupdate') in ('1', 'True', 'true')
                blocks = [(root, root_noupdate)]
                for data in root.findall('data'):
                    blocks.append((data, root_noupdate or data.get('noupdate') in ('1', 'True', 'true')))
                for block, noupdate in blocks:
                    for rec in block.findall('record'):
                        self._xml_records.append({
                            'file': path,
                            'id': rec.get('id', ''),
                            'model': rec.get('model', ''),
                            'fields': {f.get('name'): f for f in rec.findall('field')},
                            'noupdate': noupdate,
                        })
        return self._xml_records

    def records(self, model):
        return [r for r in self.xml_records if r['model'] == model]

    @property
    def model_classes(self):
        """List of dicts: file, class, name (_name), inherit (list), fields (names)."""
        if self._model_classes is None:
            self._model_classes = []
            for path in self.py_files():
                if path.parts[len(self.path.parts)] not in ('models', 'wizard', 'wizards', 'report'):
                    continue
                tree = ast.parse(path.read_text(encoding='utf-8'))
                for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
                    info = {'file': path, 'class': cls.name, 'name': None, 'inherit': [], 'fields': []}
                    for stmt in cls.body:
                        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                            continue
                        target = stmt.targets[0]
                        if not isinstance(target, ast.Name):
                            continue
                        if target.id == '_name':
                            info['name'] = _literal(stmt.value)
                        elif target.id == '_inherit':
                            value = _literal(stmt.value)
                            info['inherit'] = [value] if isinstance(value, str) else list(value or [])
                        elif _is_field_call(stmt.value):
                            info['fields'].append(target.id)
                    if info['name'] or info['inherit']:
                        self._model_classes.append(info)
        return self._model_classes

    def new_models(self):
        return [c for c in self.model_classes if c['name'] and c['name'] not in c['inherit']]

    def extended_models(self):
        return [c for c in self.model_classes if not c['name'] or c['name'] in c['inherit']]

    def access_rows(self):
        path = self.path / 'security' / 'ir.model.access.csv'
        if not path.exists():
            return []
        with path.open(newline='', encoding='utf-8') as handle:
            return list(csv.DictReader(handle))


def _literal(node):
    try:
        return ast.literal_eval(node)
    except ValueError:
        return None


def _is_field_call(node):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == 'fields')


def _ref_module(ref):
    """Module part of an XML id, or None when the id is local."""
    return ref.split('.', 1)[0] if ref and '.' in ref else None


def _payroll_data_files(mod):
    return sorted({r['file'] for r in mod.xml_records if r['model'] in PAYROLL_LOGIC_MODELS})


# Checks return (status, detail). Statuses: PASS, NA, FAIL.

@check('C-01', 'Technical name is l10n_<cc>_hr_payroll')
def c01(mod):
    if re.match(r'^l10n_[a-z]{2}_hr_payroll$', mod.name):
        return PASS, mod.name
    return FAIL, f'folder name {mod.name!r} does not match l10n_<cc>_hr_payroll'


@check('C-02', "Display name '<Country> - Payroll'")
def c02(mod):
    expected = f'{mod.country_name} - Payroll'
    name = mod.manifest.get('name')
    if name == expected:
        return PASS, name
    return FAIL, f'name is {name!r}, peers use {expected!r}'


@check('C-03', "category is 'Human Resources/Payroll'")
def c03(mod):
    category = mod.manifest.get('category')
    if category == 'Human Resources/Payroll':
        return PASS, category
    return FAIL, f'category is {category!r}'


@check('C-04', "countries is ['<cc>']")
def c04(mod):
    countries = mod.manifest.get('countries')
    if countries == [mod.cc]:
        return PASS, str(countries)
    return FAIL, f'countries is {countries!r}, expected {[mod.cc]!r}'


@check('C-05', "license is 'OEEL-1'")
def c05(mod):
    license_ = mod.manifest.get('license')
    if license_ == 'OEEL-1':
        return PASS, license_
    return FAIL, f'license is {license_!r}, peers use OEEL-1'


@check('C-06', 'depends includes hr_payroll; never hr, hr_holidays, hr_attendance, hr_payroll_account')
def c06(mod):
    depends = set(mod.manifest.get('depends', []))
    problems = []
    if 'hr_payroll' not in depends:
        problems.append('hr_payroll missing')
    forbidden = sorted(depends & {'hr', 'hr_holidays', 'hr_attendance', 'hr_payroll_account'})
    if forbidden:
        problems.append('depends on ' + ', '.join(forbidden))
    return (FAIL, '; '.join(problems)) if problems else (PASS, ', '.join(sorted(depends)))


@check('C-07', 'Module auto-installs (auto_install truthy)')
def c07(mod):
    value = mod.manifest.get('auto_install')
    if value:
        return PASS, f'auto_install = {value!r}'
    return FAIL, f'auto_install is {value!r}, peers auto-install with hr_payroll'


@check('C-08', "version is '1.0' or absent")
def c08(mod):
    version = mod.manifest.get('version')
    if version in (None, '1.0'):
        return PASS, f'version = {version!r}'
    return FAIL, f'version is {version!r}'


@check('C-09', 'No pre_init / post_init / uninstall hooks')
def c09(mod):
    hooks = [k for k in ('pre_init_hook', 'post_init_hook', 'uninstall_hook') if k in mod.manifest]
    return (FAIL, 'manifest declares ' + ', '.join(hooks)) if hooks else (PASS, 'no hooks')


@check('C-10', 'Standard folders data/, models/, views/, i18n/, tests/ exist')
def c10(mod):
    missing = [d for d in ('data', 'models', 'views', 'i18n', 'tests') if not (mod.path / d).is_dir()]
    return (FAIL, 'missing ' + ', '.join(missing)) if missing else (PASS, 'all present')


@check('C-11', 'One file per model, named after the model')
def c11(mod):
    classes = [c for c in mod.model_classes if c['file'].parent.name == 'models']
    if not classes:
        return NA, 'no model classes yet'
    problems = []
    per_file = {}
    for cls in classes:
        model = cls['name'] or cls['inherit'][0]
        per_file.setdefault(cls['file'], set()).add(model)
        expected = model.replace('.', '_') + '.py'
        if cls['file'].name != expected:
            problems.append(f'{model} in {mod.rel(cls["file"])} (expected models/{expected})')
    for path, models in per_file.items():
        if len(models) > 1:
            problems.append(f'{mod.rel(path)} holds {len(models)} models')
    return (FAIL, '; '.join(problems)) if problems else (PASS, f'{len(classes)} model classes')


@check('C-12', 'Base module does not depend on hr_payroll_account (accounting lives in a bridge)')
def c12(mod):
    if 'hr_payroll_account' in mod.manifest.get('depends', []):
        return FAIL, 'depends on hr_payroll_account; peers ship l10n_<cc>_hr_payroll_account'
    return PASS, 'no hr_payroll_account dependency'


@check('C-14', 'Payslip report action action_report_payslip_<cc> with report_name containing l10n_<cc>')
def c14(mod):
    reports = mod.records('ir.actions.report')
    if not reports:
        return NA, 'no report actions yet'
    wanted = f'action_report_payslip_{mod.cc}'
    action = next((r for r in reports if r['id'] == wanted), None)
    if action is None:
        return FAIL, f'no ir.actions.report with id {wanted}'
    report_name = action['fields'].get('report_name')
    text = (report_name.text or '') if report_name is not None else ''
    if f'l10n_{mod.cc}' not in text:
        return FAIL, f'{wanted}.report_name {text!r} lacks l10n_{mod.cc} (core hides it from structures)'
    structs = mod.records('hr.payroll.structure')
    report_refs = [(r['fields']['report_id'].get('ref') or '') for r in structs if 'report_id' in r['fields']]
    if structs and not any(ref.split('.')[-1] == wanted for ref in report_refs):
        return FAIL, f'no structure sets report_id to {wanted}'
    return PASS, f'{wanted} -> {text}'


@check('C-20', 'Payroll data file names follow peer naming')
def c20(mod):
    data_dir = mod.path / 'data'
    names = sorted(p.name for p in data_dir.glob('*.xml')) if data_dir.is_dir() else []
    if not names:
        return NA, 'no data XML yet'
    expected = {
        'hr_salary_rule_category_data.xml': lambda n: n == 'hr_salary_rule_category_data.xml',
        'hr_payroll_structure_type_data.xml': lambda n: n == 'hr_payroll_structure_type_data.xml',
        'hr_payroll_structure_data.xml': lambda n: n == 'hr_payroll_structure_data.xml',
        'hr_salary_rule*_data.xml': lambda n: re.match(r'^hr_salary_rule(?!_category).*_data\.xml$', n),
    }
    missing = [label for label, matches in expected.items() if not any(matches(n) for n in names)]
    return (FAIL, 'missing ' + ', '.join(missing)) if missing else (PASS, ', '.join(names))


def _data_rank(filename, report_action_files):
    name = Path(filename).name
    # Rank the report slot by content: file names containing "report" are
    # often views or QWeb templates, which belong after the rules.
    if filename in report_action_files:
        return 2
    ordered = [
        (r'salary_rule_category', 0), (r'structure_type', 1),
        (r'payroll_structure', 3), (r'rule_parameter', 4), (r'input_type', 5),
        (r'salary_rule', 6), (r'views|report', 7),
    ]
    for pattern, rank in ordered:
        if re.search(pattern, name):
            return rank
    return None


@check('C-21', 'Manifest data order: categories, structure type, report, structure, parameters, inputs, rules, views')
def c21(mod):
    files = [f for f in mod.manifest.get('data', []) if not f.startswith('security/')]
    report_files = {mod.rel(r['file']) for r in mod.records('ir.actions.report')}
    ranked = [(f, _data_rank(f, report_files)) for f in files]
    ranked = [(f, rank) for f, rank in ranked if rank is not None]
    if not any(f.startswith('data/') for f, _ in ranked):
        return NA, 'no payroll data files in manifest yet'
    for (prev, prev_rank), (cur, cur_rank) in zip(ranked, ranked[1:]):
        if cur_rank < prev_rank:
            return FAIL, f'{cur} is listed after {prev}'
    return PASS, f'{len(ranked)} files in order'


@check('C-23', 'No noupdate on salary rules, categories, structures or parameters')
def c23(mod):
    logic = [r for r in mod.xml_records if r['model'] in PAYROLL_LOGIC_MODELS]
    if not logic:
        return NA, 'no payroll logic records yet'
    frozen = sorted({mod.rel(r['file']) for r in logic if r['noupdate']})
    return (FAIL, 'noupdate payroll logic in ' + ', '.join(frozen)) if frozen else (PASS, f'{len(logic)} records')


@check('C-24', 'XML ids structure_type_employee_<cc>, hr_payroll_structure_<cc>_employee_salary, *_basic_salary_rule')
def c24(mod):
    types = mod.records('hr.payroll.structure.type')
    structs = mod.records('hr.payroll.structure')
    if not types and not structs:
        return NA, 'no structure records yet'
    problems = []
    if f'structure_type_employee_{mod.cc}' not in {r['id'] for r in types}:
        problems.append(f'no structure type id structure_type_employee_{mod.cc}')
    if f'hr_payroll_structure_{mod.cc}_employee_salary' not in {r['id'] for r in structs}:
        problems.append(f'no structure id hr_payroll_structure_{mod.cc}_employee_salary')
    basic = [r for r in mod.records('hr.salary.rule') if _field_text(r, 'code') == 'BASIC']
    if basic and not any(r['id'].endswith('basic_salary_rule') for r in basic):
        problems.append('BASIC rule id does not end with basic_salary_rule')
    return (FAIL, '; '.join(problems)) if problems else (PASS, 'ids conform')


def _field_text(record, name):
    element = record['fields'].get(name)
    return (element.text or '').strip() if element is not None else None


@check('C-30', "Structure type country_id = base.<cc>, name '<Country>: Employee'")
def c30(mod):
    types = [r for r in mod.records('hr.payroll.structure.type') if 'name' in r['fields'] or 'country_id' in r['fields']]
    if not types:
        return NA, 'no structure types yet'
    problems = []
    for rec in types:
        country = rec['fields'].get('country_id')
        if country is None or country.get('ref') != f'base.{mod.cc}':
            problems.append(f'{rec["id"]}: country_id is not base.{mod.cc}')
        name = _field_text(rec, 'name')
        if name != f'{mod.country_name}: Employee':
            problems.append(f'{rec["id"]}: name {name!r}')
    return (FAIL, '; '.join(problems)) if problems else (PASS, f'{len(types)} structure types')


@check('C-31', 'Structure has country_id, type_id, rule_ids eval="[]"; type has default_struct_id')
def c31(mod):
    structs = mod.records('hr.payroll.structure')
    if not structs:
        return NA, 'no structures yet'
    problems = []
    for rec in structs:
        for name in ('country_id', 'type_id'):
            if name not in rec['fields']:
                problems.append(f'{rec["id"]}: no {name}')
        rule_ids = rec['fields'].get('rule_ids')
        if rule_ids is None or (rule_ids.get('eval') or '').replace(' ', '') != '[]':
            problems.append(f'{rec["id"]}: rule_ids eval="[]" missing (core copies default rules)')
    if not any('default_struct_id' in r['fields'] for r in mod.records('hr.payroll.structure.type')):
        problems.append('no structure type sets default_struct_id')
    return (FAIL, '; '.join(problems)) if problems else (PASS, f'{len(structs)} structures')


@check('C-32', 'Structure code <CC>MONTHLY on the structure; structure type has no code')
def c32(mod):
    structs = mod.records('hr.payroll.structure')
    if not structs:
        return NA, 'no structures yet'
    problems = []
    wanted = f'{mod.cc.upper()}MONTHLY'
    codes = [_field_text(r, 'code') for r in structs]
    if wanted not in codes:
        problems.append(f'no structure with code {wanted} (found {codes})')
    typed = [r['id'] for r in mod.records('hr.payroll.structure.type') if 'code' in r['fields']]
    if typed:
        problems.append('structure type sets code: ' + ', '.join(typed))
    return (FAIL, '; '.join(problems)) if problems else (PASS, wanted)


@check('C-33', 'Rule codes BASIC, GROSS, NET exist (core reads them for wage fields)')
def c33(mod):
    rules = mod.records('hr.salary.rule')
    if not rules:
        return NA, 'no salary rules yet'
    codes = {_field_text(r, 'code') for r in rules}
    missing = [c for c in ('BASIC', 'GROSS', 'NET') if c not in codes]
    return (FAIL, 'missing rule codes ' + ', '.join(missing)) if missing else (PASS, 'BASIC, GROSS, NET present')


@check('C-35', 'Every rule has struct_id and sequence; codes uppercase')
def c35(mod):
    rules = mod.records('hr.salary.rule')
    if not rules:
        return NA, 'no salary rules yet'
    problems = []
    for rec in rules:
        for name in ('struct_id', 'sequence'):
            if name not in rec['fields']:
                problems.append(f'{rec["id"]}: no {name}')
        code = _field_text(rec, 'code')
        if code and code != code.upper():
            problems.append(f'{rec["id"]}: code {code!r} not uppercase')
    return (FAIL, '; '.join(problems)) if problems else (PASS, f'{len(rules)} rules')


@check('C-36', 'hr.payslip._get_data_files_to_update lists the payroll data files')
def c36(mod):
    if not _payroll_data_files(mod):
        return NA, 'no payroll data files yet'
    for path in mod.py_files():
        tree = ast.parse(path.read_text(encoding='utf-8'))
        if any(isinstance(n, ast.FunctionDef) and n.name == '_get_data_files_to_update' for n in ast.walk(tree)):
            return PASS, f'defined in {mod.rel(path)}'
    return FAIL, '_get_data_files_to_update not overridden (daily cron will not reload data)'


@check('C-40', 'Rates as hr.rule.parameter records read via payslip._rule_parameter()')
def c40(mod):
    if not mod.records('hr.salary.rule'):
        return NA, 'no salary rules yet'
    params = mod.records('hr.rule.parameter')
    return (PASS, f'{len(params)} rule parameters') if params else (FAIL, 'no hr.rule.parameter records')


@check('C-50', 'No own res.groups')
def c50(mod):
    groups = mod.records('res.groups')
    if groups:
        return FAIL, f'{len(groups)} res.groups records: ' + ', '.join(r['id'] for r in groups)
    return PASS, 'no own groups'


@check('C-51', 'Access rows cover only the module\'s own models')
def c51(mod):
    rows = mod.access_rows()
    foreign = [r['id'] for r in rows if _ref_module(r.get('model_id:id')) not in (None, mod.name)]
    if foreign:
        return FAIL, f'{len(foreign)} rows on core models: ' + ', '.join(foreign)
    return PASS, f'{len(rows)} rows'


@check('C-52', "Record rules only multi-company [('company_id','in',company_ids)] on own models")
def c52(mod):
    rules = mod.records('ir.rule')
    problems = []
    for rec in rules:
        model = rec['fields'].get('model_id')
        if model is not None and _ref_module(model.get('ref')) not in (None, mod.name):
            problems.append(f'{rec["id"]} on core model {model.get("ref")}')
        domain = re.sub(r'\s', '', (_field_text(rec, 'domain_force') or '')).replace('"', "'")
        if domain != "[('company_id','in',company_ids)]":
            problems.append(f'{rec["id"]} is not a multi-company rule')
    return (FAIL, '; '.join(problems)) if problems else (PASS, f'{len(rules)} record rules')


@check('C-53', 'Record-rule files are noupdate="1"')
def c53(mod):
    rules = mod.records('ir.rule')
    loose = sorted({f'{r["id"]} ({mod.rel(r["file"])})' for r in rules if not r['noupdate']})
    return (FAIL, 'not noupdate: ' + ', '.join(loose)) if loose else (PASS, f'{len(rules)} record rules')


@check('C-54', 'Access row for every new model')
def c54(mod):
    new = mod.new_models()
    if not new:
        return NA, 'no new models yet'
    covered = {(r.get('model_id:id') or '').split('.')[-1] for r in mod.access_rows()}
    missing = [c['name'] for c in new if 'model_' + c['name'].replace('.', '_') not in covered]
    return (FAIL, 'no access row for ' + ', '.join(missing)) if missing else (PASS, f'{len(new)} models covered')


@check('C-60', 'English source strings')
def c60(mod):
    return NA, 'manual check (no reliable heuristic for source-string language)'


@check('C-61', 'i18n/<module>.pot exists')
def c61(mod):
    pot = mod.path / 'i18n' / f'{mod.name}.pot'
    return (PASS, mod.rel(pot)) if pot.exists() else (FAIL, f'i18n/{mod.name}.pot missing')


@check('C-62', ".po files exist with header 'Odoo Server 19.0+e'")
def c62(mod):
    pos = sorted((mod.path / 'i18n').glob('*.po'))
    if not pos:
        return FAIL, 'no .po files'
    bad = [p.name for p in pos if 'Project-Id-Version: Odoo Server 19.0+e' not in p.read_text(encoding='utf-8')]
    return (FAIL, 'wrong header in ' + ', '.join(bad)) if bad else (PASS, ', '.join(p.name for p in pos))


@check('C-70', 'Tests live in the base module')
def c70(mod):
    tests = sorted((mod.path / 'tests').glob('test_*.py'))
    return (PASS, f'{len(tests)} test files') if tests else (FAIL, 'no tests/test_*.py')


REQUIRED_TAGS = ('post_install_l10n', 'post_install', '-at_install')


@check('C-71', "Every test class tagged ('post_install_l10n', 'post_install', '-at_install')")
def c71(mod):
    tests = sorted((mod.path / 'tests').glob('test_*.py'))
    if not tests:
        return NA, 'no tests yet'
    problems = []
    for path in tests:
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            tags = None
            for deco in cls.decorator_list:
                if isinstance(deco, ast.Call) and getattr(deco.func, 'id', getattr(deco.func, 'attr', None)) == 'tagged':
                    tags = [a.value for a in deco.args if isinstance(a, ast.Constant)]
            if tags is None:
                if cls.name.startswith('Test'):
                    problems.append(f'{cls.name}: not tagged')
            elif not all(t in tags for t in REQUIRED_TAGS):
                problems.append(f'{cls.name}: tagged {tuple(tags)}')
    return (FAIL, '; '.join(problems)) if problems else (PASS, 'all test classes tagged')


@check('C-81', 'No "# -*- coding: utf-8 -*-" line')
def c81(mod):
    pattern = re.compile(r'^#.*coding[:=]')
    offenders = []
    for path in mod.py_files():
        head = path.read_text(encoding='utf-8').splitlines()[:2]
        if any(pattern.match(line) for line in head):
            offenders.append(mod.rel(path))
    return (FAIL, f'{len(offenders)} files: ' + ', '.join(offenders)) if offenders else (PASS, 'none')


@check('C-82', 'New models named l10n_<cc>.*')
def c82(mod):
    new = [c for c in mod.new_models() if not c['name'].startswith('report.')]
    if not new:
        return NA, 'no new models yet'
    bad = [c['name'] for c in new if not c['name'].startswith(f'l10n_{mod.cc}.')]
    return (FAIL, 'unprefixed: ' + ', '.join(bad)) if bad else (PASS, f'{len(new)} models prefixed')


@check('C-83', 'Fields added to core models prefixed l10n_<cc>_')
def c83(mod):
    extended = [c for c in mod.extended_models() if c['fields']]
    if not extended:
        return NA, 'no fields on inherited models yet'
    bad = [f'{c["inherit"][0]}.{f}' for c in extended for f in c['fields'] if not f.startswith(f'l10n_{mod.cc}_')]
    return (FAIL, 'unprefixed: ' + ', '.join(bad)) if bad else (PASS, 'all prefixed')


def read_register(path):
    """Map check ID -> 'Decided' | 'Open' from the register's Markdown tables."""
    register = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.lstrip().startswith('|'):
            continue
        cells = [c.strip().strip('*`').strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 2 or not re.fullmatch(r'C-\d\d', cells[0]):
            continue
        status = cells[1].capitalize()
        if status in ('Decided', 'Open'):
            register[cells[0]] = status
    return register


COLORS = {'PASS': '32', 'N/A': '2', 'KNOWN-DECIDED': '36', 'KNOWN-OPEN': '33', 'NEW': '31;1', 'STALE': '35', 'ERROR': '31'}


def colorize(text, status, enabled):
    return f'\033[{COLORS[status]}m{text}\033[0m' if enabled else text


def classify(status, check_id, register):
    if status == FAIL:
        return {'Decided': 'KNOWN-DECIDED', 'Open': 'KNOWN-OPEN'}.get(register.get(check_id), 'NEW')
    if status == PASS and check_id in register:
        return 'STALE'
    return status


def run(args):
    color = sys.stdout.isatty()
    mod = Module(args.module)
    if not (mod.path / '__manifest__.py').is_file():
        # Running the checks against a non-module would report bogus PASS/STALE results.
        print(f'WARNING: no __manifest__.py in {mod.path}; l10n conformance check skipped')
        return 0
    register_path = Path(args.register)
    notes = []
    if register_path.exists():
        register = read_register(register_path)
    else:
        register = {}
        notes.append(f'note: divergence register not found ({register_path}); treating it as empty')

    results = []
    for check_id, description, func in CHECKS:
        try:
            status, detail = func(mod)
        except Exception as exc:  # one broken check must not hide the others
            status, detail = 'ERROR', f'{type(exc).__name__}: {exc}'
        results.append((check_id, description, classify(status, check_id, register), detail))

    counts = {}
    for _, _, cls, _ in results:
        counts[cls] = counts.get(cls, 0) + 1
    order = ['PASS', 'N/A', 'KNOWN-DECIDED', 'KNOWN-OPEN', 'NEW', 'STALE', 'ERROR']
    summary = ', '.join(f'{counts[k]} {k}' for k in order if counts.get(k))
    print(f'l10n conformance ({mod.name}, {len(results)} checks): {summary}')
    for note in notes:
        print(note)

    if args.verbose:
        for check_id, description, cls, detail in results:
            print(colorize(f'{cls:<13} {check_id}  {description}', cls, color))
            print(f'{"":<13}       {detail}')
    else:
        for check_id, _, cls, detail in results:
            if cls == 'NEW':
                print(colorize(f'WARNING NEW {check_id}: {detail}', cls, color))
            elif cls == 'ERROR':
                print(colorize(f'WARNING check {check_id} crashed: {detail}', cls, color))
        for check_id, description, cls, _ in results:
            if cls == 'KNOWN-OPEN':
                print(colorize(f'open {check_id}: {description}', cls, color))
        if counts.get('KNOWN-DECIDED'):
            print(colorize(f'{counts["KNOWN-DECIDED"]} known divergences decided (see register)', 'KNOWN-DECIDED', color))
        for check_id, _, cls, _ in results:
            if cls == 'STALE':
                print(colorize(f'STALE {check_id}: now passes; remove its row from the register', cls, color))
    if counts.get('NEW'):
        print('Reference: docs/reference/official-localization-checklist.md')
    return 1 if args.strict and counts.get('NEW') else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--module', default=str(DEFAULT_MODULE), help='module folder (default: %(default)s)')
    parser.add_argument('--verbose', action='store_true', help='print every check with status and detail')
    parser.add_argument('--strict', action='store_true', help='exit 1 when at least one check is NEW')
    parser.add_argument('--register', default=str(DEFAULT_REGISTER), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception:
        # The hook must never block a commit because the checker itself broke.
        print('WARNING: l10n conformance check failed to run:', file=sys.stderr)
        traceback.print_exc()
        return 1 if args.strict else 0


if __name__ == '__main__':
    sys.exit(main())
