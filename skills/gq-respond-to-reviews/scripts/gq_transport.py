"""GuildQuality review-only HTTPS transport with private credentials."""
import argparse
import getpass
from http.client import HTTPException
import json
import os
from pathlib import Path
import stat
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
BASE_URL = 'https://www.guildquality.com/company-api/v3'
BASE_PATH = '/company-api/v3/'
TOKEN_ENV = 'GUILDQUALITY_API_TOKEN'
FILE_ENV = 'GUILDQUALITY_API_TOKEN_FILE'

class ClientError(Exception):
    """A message safe to show without server bodies, headers, URLs, or credentials."""

def safe_url(value, current=None, base_url=BASE_URL):
    base_path = urlsplit(base_url).path.rstrip('/') + '/'
    origin = urlsplit(base_url).netloc
    if not isinstance(value, str) or not value or any((c.isspace() for c in value)):
        raise ClientError('Expected a nonempty API path without whitespace.')
    if current:
        try:
            candidate = urljoin(current, value)
        except ValueError:
            raise ClientError('Request refused: malformed URL.') from None
    elif value.startswith('https://'):
        candidate = value
    elif value.startswith('/') and (not value.startswith('//')):
        candidate = base_url + value
    else:
        raise ClientError('Use an API path beginning with /, such as /surveys.')
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        raise ClientError('Request refused: malformed URL.') from None
    if parsed.scheme != 'https' or parsed.netloc != origin or parsed.username or parsed.password or parsed.fragment or (not parsed.path.startswith(base_path)):
        raise ClientError('Request refused: URL must stay on the GuildQuality HTTPS API origin and base path.')
    decoded = parsed.path
    for _ in range(5):
        next_decoded = unquote(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    if '%' in decoded or '\\' in decoded or '//' in decoded or any((part in ('.', '..') for part in decoded.split('/'))) or any((ord(c) < 32 or ord(c) == 127 for c in decoded)):
        raise ClientError('Request refused: ambiguous or traversing API path.')
    try:
        raw_path = urlsplit(value).path
    except ValueError:
        raise ClientError('Request refused: malformed URL.') from None
    if any((part in ('.', '..') for part in raw_path.split('/'))):
        raise ClientError('Request refused: traversing API path.')
    return candidate

def _private_stat(info, directory=False):
    if os.name != 'posix':
        raise ClientError('Private-file credentials require POSIX permissions; use secret-manager environment injection on this platform.')
    expected = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if not expected or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 63:
        raise ClientError('Credential file and its containing directory must be owned by you and inaccessible to other users (directory 0700, file 0600).')

def _validate_token(token):
    token = token.strip()
    if not token or any((c.isspace() or ord(c) < 32 or ord(c) == 127 for c in token)):
        raise ClientError('Credential is missing or invalid; configure it privately outside chat.')
    return token

def load_token():
    if TOKEN_ENV in os.environ:
        return _validate_token(os.environ[TOKEN_ENV])
    source = os.environ.get(FILE_ENV)
    if not source:
        raise ClientError('No credential configured. Use GUILDQUALITY_API_TOKEN or GUILDQUALITY_API_TOKEN_FILE; never paste the token into chat.')
    if os.name != 'posix':
        raise ClientError('Private-file credentials require POSIX permissions; use secret-manager environment injection on this platform.')
    path = Path(source).expanduser()
    try:
        _private_stat(path.parent.lstat(), directory=True)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            _private_stat(os.fstat(stream.fileno()))
            token = stream.read(16385)
            if len(token) > 16384:
                raise ClientError('Credential file is unexpectedly large.')
            return _validate_token(token)
    except (OSError, UnicodeError):
        raise ClientError('Could not read a private credential file; check its path, ownership, and permissions.') from None

def setup_token(filename):
    if os.name != 'posix':
        raise ClientError('Private-file setup requires POSIX permissions; use your OS secret manager to inject GUILDQUALITY_API_TOKEN.')
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise ClientError('Run setup-token yourself in a local interactive terminal; it will not accept piped or chat-supplied secrets.')
    path = Path(filename).expanduser()
    try:
        path.parent.mkdir(mode=448, parents=True, exist_ok=True)
        _private_stat(path.parent.lstat(), directory=True)
        if path.exists() or path.is_symlink():
            raise ClientError('Credential file already exists; setup never overwrites it.')
        token = _validate_token(getpass.getpass('GuildQuality API token (hidden): '))
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 384)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            os.fchmod(stream.fileno(), 384)
            stream.write(token + '\n')
        return {'saved': True, 'next_step': 'Set the environment-specific file_env variable from your environment manifest to this private file path. The key itself is not printed.'}
    except (OSError, EOFError):
        raise ClientError('Could not save the credential privately. No existing file was overwritten.') from None

class NoRedirect(HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ClientError('Redirect refused; credentials were not forwarded. Verify the API endpoint.')

def request_json(method, url, token, body=None, *, base_url=BASE_URL, timeout=30, max_bytes=4000000):
    url = safe_url(url, base_url=base_url)
    parsed = urlsplit(url)
    relative = parsed.path[len('/company-api/v3'):]
    decoded = relative
    for _ in range(5):
        decoded = unquote(decoded)
    parts = decoded.strip('/').split('/')
    review_detail = len(parts) == 2 and parts[0] == 'reviews' and parts[1].isdigit() and (int(parts[1]) > 0)
    if method == 'GET':
        if body is not None or (decoded not in ('/reviews', '/reports', '/children') and (not review_detail)):
            raise ClientError('The review transport permits only review reads and account verification.')
    elif method == 'POST':
        if decoded != '/review/response' or parsed.query or (not isinstance(body, dict)) or (set(body) != {'reviewId', 'response', 'responseDate'}) or (type(body['reviewId']) is not int) or (body['reviewId'] <= 0) or (not isinstance(body['response'], str)) or (not isinstance(body['responseDate'], str)):
            raise ClientError('The review transport permits only a specific GuildQuality review response.')
    else:
        raise ClientError('The review transport does not support this method.')
    data = None if body is None else json.dumps(body, allow_nan=False).encode('utf-8')
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'User-Agent': 'guildquality-skills/0.2'}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ClientError('API response exceeded the configured byte budget.')
            if not raw:
                return None
            try:
                return json.loads(raw)
            except (ValueError, UnicodeError):
                raise ClientError('API returned an unexpected non-JSON response.') from None
    except HTTPError as error:
        if error.code in (401, 403):
            message = 'Authentication or account access was refused; check the configured token and account permissions.'
        elif error.code == 429:
            message = 'Rate limit reached; stop and retry later.'
        elif 300 <= error.code < 400:
            message = 'Redirect refused; verify the API endpoint.'
        else:
            message = 'Request failed; inspect the approved request and current API documentation.'
        error.close()
        raise ClientError('HTTP {}. {}'.format(error.code, message)) from None
    except (URLError, OSError, TimeoutError, HTTPException):
        raise ClientError('Network request failed or timed out. For writes, outcome is unknown: read back before considering another attempt.') from None
