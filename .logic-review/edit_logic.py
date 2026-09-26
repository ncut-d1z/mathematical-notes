"""Apply hash-checked text edits on the review branch only.

The payload is compressed JSON DATA, not executable code. Line edits are
against an exact original Git blob; only the three explicit paths may change.
This temporary script and payload are removed by the workflow after tests.
"""
from pathlib import Path
import base64
import hashlib
import json
import subprocess
import zlib

branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
assert branch == 'proofs/logic-complete-20260927', branch
source = Path('集合论/数理逻辑.tex')
assert not source.is_symlink()
raw = source.read_bytes()
blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
assert blob == '165da8dc25796104bf2068b0c3b4a097d112b9a5', blob
parts = sorted(Path('.logic-review').glob('payload-*.b64'))
assert len(parts) == 2, parts
encoded = ''.join(p.read_text(encoding='ascii').strip() for p in parts)
compressed = base64.b64decode(encoded, validate=True)
assert hashlib.sha256(compressed).hexdigest() == '6d187c93bca847921d3f8bbd7429a3e3e3d1815061e50dcbc578ec2b7e39cc92'
payload = json.loads(zlib.decompress(compressed).decode('utf-8'))
assert set(payload) == {'edits', 'files'}
assert set(payload['files']) == {'tests/check_logic.py', 'tests/check_logic.wl'}
lines = raw.decode('utf-8').splitlines(keepends=True)
previous = 0
for start, end, replacement in payload['edits']:
    assert isinstance(start, int) and isinstance(end, int)
    assert previous <= start <= end <= len(lines)
    assert isinstance(replacement, str)
    previous = end
for start, end, replacement in reversed(payload['edits']):
    lines[start:end] = replacement.splitlines(keepends=True)
new = ''.join(lines).encode('utf-8')
assert hashlib.sha256(new).hexdigest() == '512806c9b087ca9f2000604e98321c0501bf3b2615aa1be5a0783cfd8281a2ca'
for name, content in payload['files'].items():
    path = Path(name)
    assert not path.exists(), f'Refusing to replace pre-existing test: {path}'
    assert isinstance(content, str)
source.write_bytes(new)
for name, content in payload['files'].items():
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
print('Applied', len(payload['edits']), 'guarded text edits and two test files.')
print('Source SHA256:', hashlib.sha256(new).hexdigest())
