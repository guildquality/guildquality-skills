"""GuildQuality reporting-only client with explicit account grants and bounded reads."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
from urllib.parse import parse_qsl, urlencode, urlsplit
import gq_transport as transport
from gq_transport import ClientError
VERSION = '0.3.0-beta.1'
READS = {'reviews', 'reports', 'children'}
SAFE_QUERY = {'since', 'until', 'dateFilter', 'orderBy', 'status', 'reportId', 'questions', 'filterByCompanyIds', 'page', 'contactEmails', 'projectIds', 'contactIds', 'isImported', 'archived'}
SURVEY_STATUS_GROUPS = {'completed': frozenset({'Completed'}), 'in-progress': frozenset({'In progress'}), 'scheduled': frozenset({'Scheduled'}), 'abandoned': frozenset({'Abandoned'}), 'no-response': frozenset({'Abandoned', 'No response'})}

def survey_status_labels(value):
    """Validate case-sensitive query groups and return their exact public labels."""
    if not isinstance(value, str):
        raise ClientError('Survey status must use documented lowercase groups.')
    groups = [part.strip() for part in value.split(',')]
    if not groups or any((group not in SURVEY_STATUS_GROUPS for group in groups)):
        raise ClientError('Unsupported survey status group. Use completed, in-progress, scheduled, abandoned, or no-response; at-risk is not supported by this public path.')
    return frozenset().union(*(SURVEY_STATUS_GROUPS[group] for group in groups))

def query_parameters(query):
    """Preserve PHP array semantics and reject scalar filters that the API ignores."""
    values = {}
    styles = {}
    raw_seen = set()
    arrays = {'projectIds', 'contactIds', 'isImported'}
    for (key, value) in parse_qsl(query, keep_blank_values=True):
        match = re.fullmatch('(projectIds|contactIds|isImported)\\[(\\d*)\\]', key)
        if match:
            (base, index) = match.groups()
            style = 'indexed' if index else 'append'
            if base in styles and styles[base] != style:
                raise ClientError('Mixed array filter syntax is ambiguous.')
            if style == 'indexed' and key in raw_seen:
                raise ClientError('Duplicate array indices are ambiguous.')
            styles[base] = style
            raw_seen.add(key)
            if base == 'isImported':
                if value not in ('0', '1'):
                    raise ClientError('Imported-survey filter must contain 0 or 1.')
            elif not value.isdigit() or int(value) < 1:
                raise ClientError('Record filter arrays require positive numeric IDs.')
            bucket = values.setdefault(base, [])
            if value in bucket or len(bucket) >= 50:
                raise ClientError('Duplicate or excessive array filter values.')
            bucket.append(value)
        else:
            if key in arrays:
                raise ClientError('This API filter requires bracket-array query syntax; a scalar can be ignored.')
            if key in values:
                raise ClientError('Duplicate scalar query parameters are ambiguous.')
            values[key] = value
    return values

def cohort_query(query):
    return sorted(((key, tuple(sorted(value)) if isinstance(value, list) else value) for (key, value) in query_parameters(query).items() if key != 'page'))

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def read_json(path):
    with Path(path).open(encoding='utf-8') as stream:
        return json.load(stream, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))

def private_dir(path):
    path = Path(path).expanduser()
    path.mkdir(mode=448, parents=True, exist_ok=True)
    transport._private_stat(path.lstat(), directory=True)
    return path

def private_write(path, value, exclusive=True):
    path = Path(path)
    private_dir(path.parent)
    serialized = json.dumps(value, indent=2, allow_nan=False) + '\n'
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | (os.O_EXCL if exclusive else 0)
    fd = os.open(path, flags, 384)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        transport._private_stat(os.fstat(stream.fileno()))
        os.ftruncate(stream.fileno(), 0)
        stream.write(serialized)
        stream.flush()
        os.fsync(stream.fileno())

def validate_survey_owner_binding(env):
    binding = env.get('survey_owner_binding')
    if binding is None:
        return None
    required = {'schema_version', 'account_id', 'origin', 'report_id', 'report_name', 'verified_by', 'evidence_ref', 'root_owned_report_verified', 'leaf_account_verified'}
    if not isinstance(binding, dict) or set(binding) != required or binding.get('schema_version') != 1 or (binding.get('root_owned_report_verified') is not True) or (binding.get('leaf_account_verified') is not True) or (type(binding.get('account_id')) is not int) or (type(binding.get('report_id')) is not int) or (binding['account_id'] <= 0) or (binding['report_id'] <= 0) or (not isinstance(binding.get('verified_by'), str)) or (not binding['verified_by'].strip()) or (not isinstance(binding.get('evidence_ref'), str)) or (not binding['evidence_ref'].strip()) or (len(binding['evidence_ref']) > 2000):
        raise ClientError('Single-account survey attribution requires an explicit independently verified administrator binding.')
    if binding['account_id'] != env.get('account_id') or [str(v) for v in env.get('allowed_company_ids', [])] != [str(binding['account_id'])] or binding['origin'] + '/company-api/v3' != env.get('base_url') or ({'report_id': binding['report_id'], 'report_name': binding['report_name']} != env.get('identity_marker')):
        raise ClientError('Single-account survey binding must match the exact origin, root-only scope and independently bound report marker.')
    return copy.deepcopy(binding)

def load_environment(filename, selected, mode):
    if mode != 'reporting':
        raise ClientError('The analysis skill supports reporting only.')
    manifest = read_json(filename)
    if manifest.get('schema_version') != 1:
        raise ClientError('Unsupported environment manifest version.')
    env = copy.deepcopy(manifest.get('environments', {}).get(selected))
    if not isinstance(env, dict) or not env.get('approved') or (not env.get('authorization_ref')):
        raise ClientError('Environment is unknown or lacks operator approval.')
    base = env.get('base_url', '')
    parsed = urlsplit(base)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.query or parsed.fragment or (parsed.path != '/company-api/v3') or (parsed.port is not None) or (manifest.get('approved_origins', {}).get(selected) != 'https://' + parsed.netloc):
        raise ClientError('Environment origin does not match its approved exact HTTPS mapping.')
    if not parsed.netloc or env.get('kind') not in ('staging', 'production'):
        raise ClientError('Environment kind or origin is invalid.')
    if (env['kind'] == 'staging') == (parsed.netloc == 'www.guildquality.com'):
        raise ClientError('Environment kind and production origin disagree.')
    if mode == 'actions' and (env['kind'] != 'staging' or not env.get('actions_authorized')):
        raise ClientError('Actions require specifically authorized staging records.')
    for field in ('account_id', 'allowed_company_ids', 'credential', 'identity_marker', 'state_dir'):
        if not env.get(field):
            raise ClientError('Environment is missing account, credential, marker, or private-state binding.')
    if str(env['account_id']) not in [str(v) for v in env['allowed_company_ids']]:
        raise ClientError('The root account must be included in the explicit account grant.')
    marker = env['identity_marker']
    if set(marker) != {'report_id', 'report_name'} or not all(marker.values()):
        raise ClientError('Identity binding requires an expected report ID and exact report name.')
    credential = env['credential']
    if set(credential) not in ({'env'}, {'file_env'}):
        raise ClientError('Use exactly one environment-specific private credential reference.')
    ref = next(iter(credential.values()))
    if not isinstance(ref, str) or not re.fullmatch('[A-Z][A-Z0-9_]{2,100}', ref):
        raise ClientError('Credential reference must be a named environment variable, never a token.')
    for (name, other) in manifest['environments'].items():
        if name != selected and other.get('credential') == credential:
            raise ClientError('Each environment requires a distinct credential reference.')
    validate_survey_owner_binding(env)
    env['id'] = selected
    defaults = {'max_pages': 20, 'max_rows': 2000, 'max_seconds': 60, 'max_bytes': 4000000, 'request_timeout': 15, 'pace_seconds': 0.25}
    defaults.update(env.get('limits', {}))
    caps = {'max_pages': 100, 'max_rows': 10000, 'max_seconds': 300, 'max_bytes': 16000000, 'request_timeout': 30, 'pace_seconds': 5}
    for (key, value) in defaults.items():
        if key not in caps or not isinstance(value, (int, float)) or isinstance(value, bool) or (not 0 < value <= caps[key]):
            raise ClientError('Invalid or excessive request budget.')
    if defaults['pace_seconds'] < 0.25:
        raise ClientError('Request pacing must remain at least 250ms.')
    env['limits'] = defaults
    return env

def credential_for(env):
    binding = env['credential']
    if 'env' in binding:
        return transport._validate_token(os.environ.get(binding['env'], ''))
    variable = binding['file_env']
    filename = os.environ.get(variable)
    if not filename:
        raise ClientError('Selected environment credential is missing; configure it privately outside chat.')
    path = Path(filename).expanduser()
    try:
        transport._private_stat(path.parent.lstat(), directory=True)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, encoding='utf-8') as stream:
            transport._private_stat(os.fstat(stream.fileno()))
            value = stream.read(16385)
            if len(value) > 16384:
                raise ClientError('Credential file exceeds the permitted size.')
            return transport._validate_token(value)
    except (OSError, UnicodeError):
        raise ClientError('Could not read the selected private credential.') from None

def records(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get('data'), list):
        return payload['data']
    return []

def record_id(row):
    return row.get('id', row.get('reviewId'))

def owner(row):
    company = row.get('company')
    return row.get('companyId', company.get('id') if isinstance(company, dict) else None)

class Client:

    def __init__(self, manifest_path, environment_id, mode='reporting', transport_fn=None):
        if mode != 'reporting':
            raise ClientError('The analysis skill supports reporting only.')
        self.env = load_environment(manifest_path, environment_id, mode)
        self.mode = mode
        self.transport_fn = transport_fn
        self.verified = False
        self._survey_owner_proof = None
        self._inferred_survey_ids = set()
        self._bound_credential_hash = None
        self.calls = []
        self._last_request = 0

    def url(self, path, current=None):
        return transport.safe_url(path, current=current, base_url=self.env['base_url'])

    def authorize(self, method, url, body=None):
        parsed = urlsplit(self.url(url))
        path = parsed.path[len('/company-api/v3'):]
        query = parse_qsl(parsed.query, keep_blank_values=True)
        if method == 'GET':
            endpoint = path.strip('/')
            detail = re.fullmatch('(reviews)/([A-Za-z0-9_-]+)', endpoint)
            if endpoint == 'survey-templates' and self.mode == 'actions' and (self.env.get('template_initialization_authorized') is True):
                endpoint = 'reports'
            if endpoint not in READS and (not detail):
                raise ClientError('Read endpoint is outside the supported operation grant.')
            if detail and detail[2] not in [str(v) for v in self.env.get('read_record_ids', {}).get(detail[1], [])]:
                raise ClientError('Record ID is outside the explicit account grant.')
            params = query_parameters(parsed.query)
            if any((k not in SAFE_QUERY for k in params)):
                raise ClientError('Unknown query parameters are refused.')
            if 'filterByCompanyIds' in params:
                if not set(params['filterByCompanyIds'].split(',')) <= {str(v) for v in self.env['allowed_company_ids']}:
                    raise ClientError('Requested company is outside the account grant.')
            if 'reportId' in params and params['reportId'] not in [str(v) for v in self.env.get('allowed_report_ids', [])]:
                raise ClientError('Saved report is outside the vetted cohort grant.')
            if 'questions' in params and params['questions'] not in ('0', '1'):
                raise ClientError('Question inclusion must be 0 or 1.')
            fields = {'reviews': {'reviewedAt', 'lastActivityAt'}, 'surveys': {'endedAt', 'sendAt', 'createdAt', 'updatedAt', 'lastActivityAt'}}
            resource = path.strip('/').split('/')[0]
            for key in ('dateFilter', 'orderBy'):
                if key in params and params[key] not in fields.get(resource, set()):
                    raise ClientError('Unsupported date or ordering field; refusing a potentially ignored filter.')
            admitted = {'surveys': {'since', 'until', 'dateFilter', 'orderBy', 'status', 'reportId', 'questions', 'filterByCompanyIds', 'page', 'projectIds', 'contactIds', 'isImported'}, 'reviews': {'since', 'until', 'dateFilter', 'filterByCompanyIds', 'page'}, 'contacts': {'contactEmails', 'since', 'until'}, 'survey-templates': {'archived'}}
            if set(params) - admitted.get(resource, set()):
                raise ClientError("Query parameter is not admitted by this endpoint's public contract.")
            if 'status' in params:
                if path != '/surveys':
                    raise ClientError('Status groups apply only to the survey list; detail requests do not admit this filter.')
                survey_status_labels(params['status'])
            constraints = self.env.get('query_constraints', {}).get(path, {})
            for (key, allowed) in constraints.items():
                selected = params.get(key)
                if isinstance(selected, list) and (not set(selected) <= set(allowed)) or (not isinstance(selected, list) and selected not in allowed):
                    raise ClientError('Request does not match the approved query constraints.')
            for key in ('since', 'until'):
                if key in params and (not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', params[key])):
                    raise ClientError('Dates must use YYYY-MM-DD.')
            if 'page' in params and (not params['page'].isdigit() or not 1 <= int(params['page']) <= 20000):
                raise ClientError('Invalid pagination page.')
            if body is not None:
                raise ClientError('GET requests must not include a payload.')
        else:
            raise ClientError('The analysis skill permits GET requests only.')
        return path

    def _request(self, method, url, body=None, timeout=None):
        self.authorize(method, url, body)
        delay = self.env['limits']['pace_seconds'] - (time.monotonic() - self._last_request)
        if delay > 0:
            time.sleep(delay)
        self._last_request = time.monotonic()
        self.calls.append({'method': method, 'path': urlsplit(url).path, 'at': time.time()})
        if self.transport_fn:
            return self.transport_fn(method, url, body)
        token = credential_for(self.env)
        if self.env.get('survey_owner_binding'):
            current_hash = hashlib.sha256(token.encode()).digest()
            if self._bound_credential_hash is not None and self._bound_credential_hash != current_hash:
                self.verified = False
                self._survey_owner_proof = None
                raise ClientError('Private credential changed during account verification; start a fresh connection check.')
            self._bound_credential_hash = current_hash
        payload = transport.request_json(method, url, token, body, base_url=self.env['base_url'], timeout=timeout or self.env['limits']['request_timeout'], max_bytes=self.env['limits']['max_bytes'])

        def redact(value):
            if isinstance(value, str):
                return value.replace(token, '[REDACTED]')
            if isinstance(value, list):
                return [redact(v) for v in value]
            if isinstance(value, dict):
                return {k: '[REDACTED]' if k.lower() in ('authorization', 'token', 'api_token', 'access_token') else redact(v) for (k, v) in value.items()}
            return value
        return redact(payload)

    def preflight(self):
        self.verified = False
        self._survey_owner_proof = None
        self._bound_credential_hash = None
        binding = validate_survey_owner_binding(self.env)
        payload = self._request('GET', self.url('/reports'))
        marker = self.env['identity_marker']
        matches = [r for r in records(payload) if isinstance(r, dict) and str(r.get('id')) == str(marker['report_id']) and (r.get('name') == marker['report_name'])]
        if len(matches) != 1:
            raise ClientError('Account/report identity marker did not match; no task request was made.')
        if binding:
            children = self._request('GET', self.url('/children'))
            if children != [] and children != {'data': []}:
                raise ClientError('Single-account survey attribution needs a fresh complete empty children response.')
            self._survey_owner_proof = {'account_id': binding['account_id'], 'basis': 'independent administrator account/report binding plus fresh API report match and empty children', 'evidence_ref': binding['evidence_ref'], 'verified_by': binding['verified_by'], 'report_id': binding['report_id'], 'report_name': binding['report_name'], 'children_empty_verified': True, 'server_fields_modified': False}
        self.verified = True
        checked = {'verified': True, 'environment_id': self.env['id'], 'account_id': self.env['account_id'], 'authorization_ref': self.env['authorization_ref'], 'identity_basis': 'operator binding plus exact saved-report marker'}
        if self._survey_owner_proof:
            checked['survey_owner_attribution'] = copy.deepcopy(self._survey_owner_proof)
        return checked

    def check_rows(self, path, payload):
        resource = urlsplit(path).path[len('/company-api/v3'):].strip('/').split('/')[0]
        rows = records(payload)
        if resource in ('surveys', 'reviews'):
            data = payload.get('data', payload) if isinstance(payload, dict) else payload
            if isinstance(data, dict):
                rows = [data]
            allowed = {str(v) for v in self.env['allowed_company_ids']}
            params = query_parameters(urlsplit(path).query)
            selected_statuses = survey_status_labels(params['status']) if resource == 'surveys' and 'status' in params else None
            for row in rows:
                inferred = isinstance(row, dict) and resource == 'surveys' and ('companyId' not in row) and ('company' not in row) and (self._survey_owner_proof is not None)
                response_owner = self.env['account_id'] if inferred else owner(row) if isinstance(row, dict) else None
                explicit = [row['companyId']] if isinstance(row, dict) and 'companyId' in row else []
                if isinstance(row, dict) and isinstance(row.get('company'), dict) and ('id' in row['company']):
                    explicit.append(row['company']['id'])
                if not isinstance(row, dict) or response_owner is None or str(response_owner) not in allowed or any((value is None or str(value) != str(response_owner) for value in explicit)):
                    raise ClientError('Response has an unknown or unauthorized owner; rows withheld.')
                if inferred:
                    self._inferred_survey_ids.add(str(record_id(row)))
                target = urlsplit(path).path[len('/company-api/v3'):].strip('/').split('/')
                if len(target) == 2 and str(record_id(row)) != target[1]:
                    raise ClientError('Response record identity does not match the requested target.')
                if 'filterByCompanyIds' in params and str(response_owner) not in params['filterByCompanyIds'].split(','):
                    raise ClientError('Response does not match the selected company cohort; rows withheld.')
                if 'isImported' in params and (not isinstance(row.get('isImported'), bool) or str(int(row['isImported'])) not in params['isImported']):
                    raise ClientError('Response does not match the selected imported-survey cohort; rows withheld.')
                if selected_statuses is not None and (not isinstance(row.get('status'), str) or row['status'] not in selected_statuses):
                    raise ClientError('Response does not match the selected survey lifecycle groups; rows withheld.')
                for (field, container) in (('projectIds', 'project'), ('contactIds', 'contact')):
                    if field in params and str((row.get(container) or {}).get('id')) not in params[field]:
                        raise ClientError('Response does not match the selected record cohort; rows withheld.')
        if resource == 'children':

            def walk(items):
                for row in items:
                    if not isinstance(row, dict) or str(row.get('id')) not in {str(v) for v in self.env['allowed_company_ids']}:
                        raise ClientError('Hierarchy includes an account outside the explicit grant; rows withheld.')
                    walk(row.get('children', []))
            walk(rows)

    def get(self, path, all_pages=False):
        self._inferred_survey_ids = set()
        if not self.verified or (self.env.get('survey_owner_binding') and urlsplit(self.url(path)).path.removeprefix('/company-api/v3/').split('/')[0] == 'surveys'):
            self.preflight()
        task_owner_proof = copy.deepcopy(self._survey_owner_proof)
        url = self.url(path)
        self.authorize('GET', url)
        original = urlsplit(url)
        original_query = cohort_query(original.query)
        result = {'data': [], 'pages_fetched': 0, 'pagination_complete': None, 'stop_reason': None, 'source_ids': [], 'environment_id': self.env['id']}
        seen = set()
        seen_ids = set()
        start = time.monotonic()
        budget = self.env['limits']
        while True:
            if url in seen:
                result.update(pagination_complete=False, stop_reason='pagination_loop')
                break
            remaining = budget['max_seconds'] - (time.monotonic() - start)
            if remaining <= 0:
                result.update(pagination_complete=False, stop_reason='time_budget')
                break
            seen.add(url)
            try:
                payload = self._request('GET', url, timeout=min(remaining, budget['request_timeout']))
                if isinstance(payload, dict) and (isinstance(payload.get('data'), (dict, list)) or record_id(payload) is not None):
                    self.check_rows(url, payload)
                elif urlsplit(url).path.endswith(('/surveys', '/reviews')) and (not (isinstance(payload, dict) and isinstance(payload.get('data'), list))):
                    raise ClientError('Unexpected record response shape; rows withheld.')
            except ClientError as error:
                result.update(pagination_complete=False, stop_reason='request_failed', error=str(error))
                break
            result['pages_fetched'] += 1
            rows = records(payload)
            is_list = isinstance(payload, dict) and isinstance(payload.get('data'), list)
            if not is_list:
                if result['pages_fetched'] > 1:
                    result.update(pagination_complete=False, stop_reason='unexpected_page_shape')
                else:
                    result.update(data=payload, stop_reason='pagination_metadata_absent')
                break
            ids = [str(record_id(row)) for row in rows if isinstance(row, dict) and record_id(row) is not None]
            if len(ids) != len(set(ids)) or seen_ids.intersection(ids):
                result.update(pagination_complete=False, stop_reason='duplicate_source_ids')
                break
            seen_ids.update(ids)
            room = budget['max_rows'] - len(result['data'])
            result['data'].extend(rows[:room])
            if len(rows) > room:
                result.update(pagination_complete=False, stop_reason='row_budget')
                break
            links = payload.get('links')
            if not isinstance(links, dict) or 'next' not in links:
                result.update(stop_reason='pagination_metadata_absent')
                break
            if links['next'] is None:
                result.update(pagination_complete=True, stop_reason='end_of_pages')
                break
            result['pagination_complete'] = False
            if not all_pages:
                result['stop_reason'] = 'single_page_requested'
                break
            if result['pages_fetched'] >= budget['max_pages'] or len(result['data']) >= budget['max_rows']:
                result['stop_reason'] = 'retrieval_budget'
                break
            try:
                next_url = self.url(links['next'], current=url)
                parsed = urlsplit(next_url)
                next_query = cohort_query(parsed.query)
                self.authorize('GET', next_url)
                if parsed.path != original.path or next_query != original_query:
                    raise ClientError('Pagination changed the endpoint or query cohort.')
                url = next_url
            except ClientError as error:
                result.update(stop_reason='unsafe_next_link', error=str(error))
                break
        data = result['data']
        result['source_ids'] = [record_id(r) for r in (data if isinstance(data, list) else records(data)) if isinstance(r, dict) and record_id(r) is not None]
        inferred_ids = [identifier for identifier in result['source_ids'] if str(identifier) in self._inferred_survey_ids]
        detail_data = data.get('data', data) if isinstance(data, dict) else None
        if isinstance(detail_data, dict) and record_id(detail_data) is not None and (str(record_id(detail_data)) in self._inferred_survey_ids):
            inferred_ids = [record_id(detail_data)]
        if inferred_ids:
            result['survey_owner_attribution'] = dict(task_owner_proof, inferred_source_ids=inferred_ids)
        result['elapsed_seconds'] = round(time.monotonic() - start, 6)
        return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--environment')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('preflight')
    get = commands.add_parser('get')
    get.add_argument('path')
    get.add_argument('--all-pages', action='store_true')
    setup = commands.add_parser('setup-token')
    setup.add_argument('--file', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'setup-token':
            result = transport.setup_token(args.file)
        else:
            if not args.manifest or not args.environment:
                raise ClientError('Select the explicit manifest and environment; no fallback exists.')
            client = Client(args.manifest, args.environment, 'reporting')
            result = client.preflight() if args.command == 'preflight' else client.get(args.path, args.all_pages)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 2 if result.get('error') or result.get('pagination_complete') is False else 0
    except (ClientError, OSError, ValueError, TypeError, KeyError):
        print(json.dumps({'error': 'Reporting request refused or failed. Check the explicit account, private credential, scope and source completeness; no fallback or retry occurred.'}))
        return 2
if __name__ == '__main__':
    raise SystemExit(main())
