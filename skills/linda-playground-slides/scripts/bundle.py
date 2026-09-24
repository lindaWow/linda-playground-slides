#!/usr/bin/env python3
"""Inline local assets into standalone HTML. Classic scripts only; no network fetches."""
from __future__ import annotations
import argparse
import base64
import html
import mimetypes
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
from prepare_fonts import prepare

JS_TYPES={'','text/javascript','application/javascript'}

class Bundler(HTMLParser):
    def __init__(self,entry:Path):
        super().__init__(convert_charrefs=False)
        self.entry=entry.resolve();self.root=self.entry.parent
        self.parts=[];self.scripts=[];self.capture=None;self.payload=[];self.script_attrs={};self.count=0

    def local(self,url:str,base:Path)->Path:
        info=urlsplit(url)
        if info.scheme or info.netloc or url.startswith('/'):
            raise ValueError(f'Copy the remote/absolute asset into the project first: {url[:160]}')
        path=(base/unquote(info.path)).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f'Asset is outside the project: {url}')
        if not path.is_file():
            raise ValueError(f'Asset does not exist: {path}')
        return path

    def data_url(self,url:str,base:Path)->str:
        if url.startswith(('data:','#')):return url
        path=self.local(url,base)
        mime={'.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf','.svg':'image/svg+xml'}.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        self.count+=1
        fragment=urlsplit(url).fragment
        return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode('ascii')+('#'+fragment if fragment else '')

    def css(self,text:str,base:Path)->str:
        if re.search(r'@import\b',text,re.I):
            raise ValueError('Flatten CSS @import statements before bundling.')
        pattern=r'url\(\s*([\"\']?)(.*?)\1\s*\)'
        # Callback replacement intentionally preserves literal dollars and backslashes.
        return re.sub(pattern,lambda m:'url("'+self.data_url(m[2],base)+'")',text,flags=re.S|re.I)

    @staticmethod
    def attrs(attrs):
        return ''.join(' '+key if value is None else ' '+key+'="'+html.escape(value,quote=True)+'"' for key,value in attrs)

    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=='base':raise ValueError('Remove <base>; standalone documents resolve their own anchors.')
        if tag=='script':
            kind=values.get('type','').lower()
            if kind=='module':raise ValueError('Prebundle ES modules to one classic script before HTML export.')
            self.capture='script';self.payload=[];self.script_attrs=values;return
        if tag=='style':
            self.capture='style';self.payload=[];self.style_attrs=attrs;return
        if tag=='link':
            rel=values.get('rel','').lower().split()
            if 'stylesheet' in rel:
                path=self.local(values.get('href',''),self.root)
                extra=[(k,v) for k,v in attrs if k in {'media','title'}]
                content=self.css(path.read_text(encoding='utf-8'),path.parent)
                self.parts.append('<style'+self.attrs(extra)+'>'+content+'</style>');return
            if any(r in rel for r in ('preconnect','dns-prefetch','preload','prefetch','modulepreload')):return
            if 'icon' in rel and values.get('href'):
                attrs=[(k,self.data_url(v,self.root) if k=='href' else v) for k,v in attrs]
        resource_tags={'img','source','video','audio','track','iframe','embed','input'}
        updated=[]
        for key,value in attrs:
            if key=='srcset' and value:raise ValueError('Resolve responsive srcset assets to explicit embedded sources before bundling.')
            if key=='style' and value:value=self.css(value,self.root)
            if value and ((key=='src' and tag in resource_tags) or (key=='poster' and tag=='video') or (key in {'href','xlink:href'} and tag in {'image','use'})):
                if tag in {'iframe','embed'} and not value.startswith('data:'):
                    raise ValueError('Embedded live frames are not self-contained; supply an offline fallback.')
                value=self.data_url(value,self.root)
            updated.append((key,value))
        self.parts.append('<'+tag+self.attrs(updated)+'>')

    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.handle_endtag(tag)

    def handle_endtag(self,tag):
        if self.capture=='script' and tag=='script':
            attrs=self.script_attrs;kind=attrs.get('type','').lower();text=''.join(self.payload)
            if kind in JS_TYPES:
                if 'async' in attrs:raise ValueError('Normalize async scripts to an explicit dependency order before export.')
                if attrs.get('src'):text=self.local(attrs['src'],self.root).read_text(encoding='utf-8')
                if re.search(r'\b(import\s*\(|document\.write\s*\()',text):
                    raise ValueError('Prebundle dynamic imports and remove document.write before export.')
                text=re.sub(r'^[ \t]*//[#@] sourceMappingURL=.*$', '',text,flags=re.M)
                text=re.sub(r'</script',lambda m:'<\\/script',text,flags=re.I)
                self.scripts.append('<script>\n'+text+'\n</script>')
            else:
                if attrs.get('src'):raise ValueError('Inline data-script sources explicitly before export.')
                self.parts.append('<script'+self.attrs(attrs.items())+'>'+text+'</script>')
            self.capture=None;self.payload=[];return
        if self.capture=='style' and tag=='style':
            self.parts.append('<style'+self.attrs(self.style_attrs)+'>'+self.css(''.join(self.payload),self.root)+'</style>')
            self.capture=None;self.payload=[];return
        if tag=='body':
            self.parts.extend(self.scripts);self.scripts=[]
        self.parts.append('</'+tag+'>')

    def handle_data(self,data):
        (self.payload if self.capture else self.parts).append(data)
    def handle_entityref(self,name):self.handle_data('&'+name+';')
    def handle_charref(self,name):self.handle_data('&#'+name+';')
    def handle_comment(self,data):self.parts.append('<!--'+data+'-->')
    def handle_decl(self,decl):self.parts.append('<!'+decl+'>')

    def result(self):
        if self.capture:raise ValueError('Unclosed script/style tag.')
        if self.scripts:raise ValueError('A complete document with a closing body tag is required.')
        license_files=sorted((self.root/'fonts').glob('*OFL*.txt'))
        notices='\n\n'.join(path.read_text(encoding='utf-8') for path in license_files)
        if notices:self.parts.append('\n<!-- Embedded font licenses\n'+notices.replace('--','—')+'\n-->')
        return ''.join(self.parts)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entry',type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--no-font-refresh',action='store_true',help='Use only when preparing custom fonts separately.')
    parser.add_argument('--corpus',type=Path,help='Extra dynamically generated text for font coverage.')
    args=parser.parse_args()
    entry=args.entry.resolve();out=args.out.resolve()
    if entry==out:parser.exit(1,'Output must be different from the editable source file.\n')
    try:
        if not args.no_font_refresh and (entry.parent/'fonts'/'RobotoFlex-OFL.txt').exists():
            prepare(entry.parent,args.corpus)
        bundle=Bundler(entry);bundle.feed(entry.read_text(encoding='utf-8'));bundle.close();result=bundle.result()
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(result,encoding='utf-8')
    except (ValueError,RuntimeError,OSError) as exc:
        parser.exit(1,f'Export failed: {exc}\n')
    print(f'Created {out} ({out.stat().st_size:,} bytes), embedded {bundle.count} asset references. Run audit.py and verify this exact file in a browser.')

if __name__=='__main__':
    main()
