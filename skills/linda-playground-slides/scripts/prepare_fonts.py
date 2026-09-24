#!/usr/bin/env python3
"""Regenerate the project font subset from ALL editable HTML/CSS/JS text."""
from __future__ import annotations
import argparse
import html
import hashlib
import json
import re
import shutil
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def collect_text(project: Path, extra: Path | None = None) -> str:
    chunks = []
    for path in sorted(project.rglob('*')):
        if path.suffix.lower() not in {'.html', '.css', '.js', '.json', '.txt'}:
            continue
        if any(p in {'node_modules', '.git', 'fonts', 'dist'} for p in path.relative_to(project).parts):
            continue
        text = path.read_text(encoding='utf-8')
        # Inline fonts/media contain only ASCII; omit their bulk from the corpus.
        text = re.sub(r'data:[^\s\"\'<>)]{100,}', '', text)
        text = re.sub(r'\\u\{([\da-fA-F]{1,6})\}', lambda m: chr(int(m[1],16)), text)
        text = re.sub(r'\\u([\da-fA-F]{4})', lambda m: chr(int(m[1],16)), text)
        chunks.append(html.unescape(text))
    if extra:
        chunks.append(extra.read_text(encoding='utf-8'))
    return '\n'.join(chunks)


def prepare(project: Path, extra: Path | None = None) -> dict:
    project = project.resolve()
    sources = SKILL_ROOT / 'assets' / 'fonts'
    destination = project / 'fonts'
    destination.mkdir(parents=True, exist_ok=True)
    try:
        from fontTools.ttLib import TTFont
        from fontTools import subset
        import brotli  # noqa: F401; WOFF2 writer requirement
    except ImportError:
        # Keep the starter usable in minimal runtimes. The full OFL font is
        # larger than a subset, but it preserves offline output and all glyphs.
        text = collect_text(project, extra)
        for source_name, target_name in (
            ('han-variable-source.woff2', 'han-subset.woff2'),
            ('latin-variable.woff2', 'latin-variable.woff2'),
            ('RobotoFlex-OFL.txt', 'RobotoFlex-OFL.txt'),
            ('NotoSansSC-OFL.txt', 'NotoSansSC-OFL.txt'),
        ):
            shutil.copy2(sources / source_name, destination / target_name)
        return {
            'characters': len({c for c in text if not c.isspace()}),
            'han_bytes': (destination / 'han-subset.woff2').stat().st_size,
            'mode': 'full-font',
        }
    text = collect_text(project,extra)
    cache_path = destination / 'font-coverage.json'
    signature = hashlib.sha256((''.join(sorted(set(text)))).encode('utf-8',errors='surrogatepass') + (sources / 'han-variable-source.woff2').read_bytes() + (sources / 'latin-variable.woff2').read_bytes()).hexdigest()
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding='utf-8'))
            valid = cache.get('signature') == signature and all((destination/name).is_file() and hashlib.sha256((destination/name).read_bytes()).hexdigest() == digest for name,digest in cache['files'].items())
            if valid:
                return cache['result']
        except (ValueError,KeyError,OSError):
            pass
    latin = TTFont(sources / 'latin-variable.woff2')
    han = TTFont(sources / 'han-variable-source.woff2')
    covered = set(latin.getBestCmap()) | set(han.getBestCmap())
    required = {ord(c) for c in text if not c.isspace() and ord(c) >= 32}
    # Format controls and variation selectors affect shaping, not standalone glyphs.
    required -= {0x200b, 0x200c, 0x200d, 0x2060, 0xfe0e, 0xfe0f, 0xfeff}
    missing = sorted(required - covered)
    if missing:
        examples = ', '.join(f'{chr(n)} U+{n:04X}' for n in missing[:30])
        raise ValueError('Unsupported font characters: ' + examples + '. Add a licensed supplementary font and use --no-font-refresh after preparing custom fonts; do not delete meaningful text.')
    options = subset.Options()
    options.flavor = 'woff2'
    options.name_IDs = ['*']
    options.name_legacy = True
    options.name_languages = ['*']
    options.layout_features = ['*']
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=required & set(han.getBestCmap()))
    subsetter.subset(han)
    # Retain author/license records, give the derivative its own family name.
    names = {1:'Kinetic Han Subset',2:'Regular',3:'KineticHanSubset-Variable',4:'Kinetic Han Subset Variable',6:'KineticHanSubset-Variable',16:'Kinetic Han Subset',17:'Regular'}
    for record in han['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding(),errors='replace')
    han.flavor = 'woff2'
    han.save(destination / 'han-subset.woff2')
    for name in ('latin-variable.woff2','RobotoFlex-OFL.txt','NotoSansSC-OFL.txt'):
        shutil.copy2(sources / name, destination / name)
    final = TTFont(destination / 'han-subset.woff2')
    if required - (set(final.getBestCmap()) | set(latin.getBestCmap())):
        raise RuntimeError('The exported font subset lost required glyphs.')
    result = {'characters':len(required),'han_bytes':(destination / 'han-subset.woff2').stat().st_size,'mode':'subset'}
    files = {name:hashlib.sha256((destination/name).read_bytes()).hexdigest() for name in ('han-subset.woff2','latin-variable.woff2','RobotoFlex-OFL.txt','NotoSansSC-OFL.txt')}
    cache_path.write_text(json.dumps({'signature':signature,'files':files,'result':result}),encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--corpus', type=Path, help='Additional runtime text that static source scanning cannot see.')
    args = parser.parse_args()
    try:
        result = prepare(args.project,args.corpus)
    except (ValueError,RuntimeError,OSError) as exc:
        parser.exit(1,f'Font preparation failed: {exc}\n')
    label = 'Chinese subset' if result.get('mode') == 'subset' else 'Chinese full-font fallback'
    print(f'Font coverage checked: {result["characters"]} characters; {label} {result["han_bytes"]:,} bytes.')


if __name__ == '__main__':
    main()
