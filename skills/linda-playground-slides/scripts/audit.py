#!/usr/bin/env python3
"""Static checks for standalone HTML; not a substitute for visual/browser testing."""
from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.targets=[];self.errors=[];self.warnings=[];self.script=False;self.js=[];self.buffer=[];self.styles=[];self.style=False;self.viewport=False;self.lang=False;self.dialogs=[];self.surface=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag=='html':self.lang=bool(a.get('lang'))
        if tag=='meta' and a.get('name')=='viewport':
            self.viewport=True
            if re.search(r'user-scalable\s*=\s*no|maximum-scale\s*=\s*1(?:\D|$)',a.get('content','')):self.errors.append('Viewport disables user zoom.')
        if tag=='a' and a.get('href','').startswith('#') and a['href']!='#':self.targets.append((a['href'][1:],'anchor'))
        if a.get('data-open'):self.targets.append((a['data-open'],'dialog'))
        if a.get('data-field-toggle'):self.targets.append((a['data-field-toggle'],'field'))
        for key in ('aria-labelledby','aria-describedby'):
            self.targets.extend((target,key) for target in a.get(key,'').split())
        if tag=='dialog' and not (a.get('aria-label') or a.get('aria-labelledby')):self.errors.append('Dialog has no accessible name.')
        for key,value in a.items():
            if key in {'data-surface','data-hover-surface'}:self.surface.append(value)
            if key=='style':self.styles.append(value)
            resource=(key=='src' and tag!='a') or (key=='poster') or (key in {'href','xlink:href'} and tag in {'link','image','use'}) or (key=='data' and tag=='object')
            if resource and value and not value.startswith(('data:','#')):self.errors.append(f'External asset remains: <{tag} {key}="{value[:90]}">')
            if key=='srcset' and value:self.errors.append('srcset needs explicit offline verification.')
        if tag=='script':
            if a.get('type')=='module':self.errors.append('Module script is not supported by the standalone exporter.')
            self.script=a.get('type','') in {'','text/javascript','application/javascript'};self.buffer=[]
        if tag=='style':self.style=True
    def handle_data(self,data):
        if self.script:self.buffer.append(data)
        if self.style:self.styles.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.script:self.js.append(''.join(self.buffer));self.script=False;self.buffer=[]
        if tag=='style':self.style=False

def inspect(path:Path,palette_check:bool=False)->dict:
    audit=Audit();audit.feed(path.read_text(encoding='utf-8'));audit.close()
    ids=set(audit.ids)
    for key,count in Counter(audit.ids).items():
        if count>1:audit.errors.append(f'Duplicate id: {key}')
    for target,kind in audit.targets:
        from urllib.parse import unquote
        if unquote(target) not in ids:audit.errors.append(f'Missing {kind} target: {target}')
    if not audit.viewport:audit.errors.append('Missing viewport meta tag.')
    if not audit.lang:audit.errors.append('Missing document language.')
    css='\n'.join(audit.styles)
    for value in re.findall(r'url\(\s*[\"\']?([^\)\"\']+)',css,re.I):
        if not value.strip().startswith(('data:','#')):audit.errors.append('External CSS asset: '+value[:90])
    if re.search(r'@import\b',css,re.I):audit.errors.append('CSS @import still present.')
    if 'prefers-reduced-motion' not in css:audit.warnings.append('No CSS reduced-motion rule found; verify JS equivalent or add one.')
    if palette_check:
        palette=json.loads((Path(__file__).resolve().parents[1]/'assets'/'palette.json').read_text())['tokens']
        clean=re.sub(r'url\([^)]*\)','',css,flags=re.S)
        # Check declaration values, excluding ID selectors and data URL content.
        values='\n'.join(re.findall(r':([^;{}]+)[;}]',clean))
        for color in set(re.findall(r'#[\da-fA-F]{3,8}\b',values)):
            norm=color.upper()
            if len(norm)==4:norm='#'+''.join(c*2 for c in norm[1:])
            if norm not in set(palette.values()):audit.errors.append('Color outside EXAT palette: '+color)
        for token in set(audit.surface):
            if token not in palette:audit.errors.append('Unknown surface token: '+token)
        if re.search(r'\b(?:rgb|rgba|hsl|hsla|oklch|oklab)\(',values):audit.warnings.append('Functional CSS colors need manual palette review.')
    node=shutil.which('node')
    if node:
        for i,script in enumerate(audit.js):
            with tempfile.NamedTemporaryFile('w',suffix='.js',encoding='utf-8') as temp:
                temp.write(script);temp.flush()
                result=subprocess.run([node,'--check',temp.name],capture_output=True,text=True)
                if result.returncode:audit.errors.append(f'Script {i+1} syntax error: '+result.stderr[:800])
            if re.search(r'\b(fetch\s*\(|XMLHttpRequest|WebSocket|import\s*\()',script):audit.warnings.append(f'Script {i+1} may request external resources; verify offline behavior.')
    else:audit.warnings.append('Node unavailable; JavaScript syntax was not checked.')
    return {'ok':not audit.errors,'errors':audit.errors,'warnings':audit.warnings,'ids_checked':len(ids),'scripts':len(audit.js),'bytes':path.stat().st_size,'limits':'Static checks only. Test layout, touch, motion, focus, contrast, fonts, and offline opening in a browser.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('html',type=Path);parser.add_argument('--palette',action='store_true')
    args=parser.parse_args()
    report=inspect(args.html,args.palette)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report['ok'] else 1)

if __name__=='__main__':main()
