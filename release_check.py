"""Check package completeness before importing structural UI modules."""
import hashlib
import json
from pathlib import Path


def problems(root, expected_version):
    root=Path(root).resolve()
    try:
        manifest=json.loads((root/'release_manifest.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return ['release_manifest.json (ausente ou inválido)']
    if manifest.get('version')!=expected_version:return ['release_manifest.json (versão diferente)']
    files=manifest.get('files')
    if not isinstance(files,dict) or not files:return ['release_manifest.json (sem lista de arquivos)']
    failures=[]
    for name,expected in files.items():
        path=(root/name).resolve()
        if not path.is_relative_to(root):
            failures.append('release_manifest.json (caminho inválido)');continue
        try:actual=hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            failures.append(name+' (ausente)');continue
        if actual!=expected:failures.append(name+' (versão diferente ou conteúdo alterado)')
    return failures
