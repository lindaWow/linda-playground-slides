/* Original, dependency-free interaction helpers. Load after the scene markup. */
(() => {
  'use strict';
  const root = document.documentElement;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const clamp = (v, min, max) => Math.min(max, Math.max(min, v));
  let paused = false;
  const mayMove = () => !reduced.matches && !paused && !document.hidden;
  const paletteKeys = ['blue-03','blue-02','blue-01','blue-00','yellow-01','yellow-02','orange-01','red-01','pink','green','black','white'];
  const css = getComputedStyle(root);
  const palette = Object.fromEntries(paletteKeys.map(key => [key, css.getPropertyValue('--' + key).trim()]));
  const luminance = hex => {
    const values = hex.replace('#','').match(/.{2}/g).map(v => parseInt(v,16)/255).map(v => v <= .04045 ? v/12.92 : ((v+.055)/1.055)**2.4);
    return values[0]*.2126 + values[1]*.7152 + values[2]*.0722;
  };
  const ratio = (a,b) => (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  function surface(el, key, prefix) {
    if (!palette[key] || !/^#[\da-f]{6}$/i.test(palette[key])) return;
    const l = luminance(palette[key]);
    const dark = ratio(l,luminance(palette.black));
    const light = ratio(l,luminance(palette.white));
    const ink = dark >= light ? 'black' : 'white';
    const needsBacking = Math.max(dark,light) < 4.5;
    el.style.setProperty('--' + prefix + 'surface', palette[key]);
    el.style.setProperty('--' + prefix + 'ink', palette[ink]);
    el.style.setProperty('--' + prefix + 'small-bg', needsBacking ? palette.white : palette[key]);
    el.style.setProperty('--' + prefix + 'small-ink', needsBacking ? palette.black : palette[ink]);
  }
  $$('[data-surface]').forEach(el => surface(el,el.dataset.surface,''));
  $$('[data-hover-surface]').forEach(el => surface(el,el.dataset.hoverSurface,'hover-'));

  const words = 'Segmenter' in Intl ? new Intl.Segmenter(document.documentElement.lang,{granularity:'word'}) : null;
  const glyphs = 'Segmenter' in Intl ? new Intl.Segmenter(document.documentElement.lang,{granularity:'grapheme'}) : null;
  const segment = (text, engine) => engine ? Array.from(engine.segment(text),item => item.segment) : Array.from(text);
  $$('[data-split]').forEach(el => {
    if (el.dataset.splitReady) return;
    const original = el.textContent;
    const nodes = Array.from(el.childNodes);
    const semantic = document.createElement('span');
    semantic.className = 'sr-only'; semantic.textContent = original;
    const visual = document.createElement('span'); visual.setAttribute('aria-hidden','true');
    let i = 0;
    function copy(node, parent) {
      if (node.nodeType === Node.TEXT_NODE) {
        for (const word of segment(node.textContent,words)) {
          const group = document.createElement('span'); group.className = 'split-word';
          for (const glyph of segment(word,glyphs)) {
            const mask = document.createElement('span'); mask.className = 'char-mask';
            const char = document.createElement('span'); char.className = 'char';
            char.style.setProperty('--i', String(i++ % 14)); char.textContent = glyph;
            mask.append(char); group.append(mask);
          }
          parent.append(group);
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        const clone = node.cloneNode(false); clone.removeAttribute('id');
        for (const child of node.childNodes) copy(child,clone);
        parent.append(clone);
      }
    }
    nodes.forEach(node => copy(node,visual));
    el.replaceChildren(semantic,visual); el.dataset.splitReady = 'true';
  });
  $$('.reveal-grid').forEach(grid => Array.from(grid.children).forEach((el,i) => el.style.setProperty('--order',String(i))));

  $$('[data-type-lab]').forEach(lab => {
    const sample = $('[data-type-sample]',lab);
    $$('input[data-axis]',lab).forEach(input => {
      const update = () => {
        if (!['wght','wdth','opsz'].includes(input.dataset.axis) || !sample) return;
        sample.style.setProperty('--type-' + input.dataset.axis, input.value);
        const out = $('[data-axis-output="' + input.dataset.axis + '"]',lab);
        if (out) out.textContent = input.value;
      };
      input.addEventListener('input',update); update();
    });
  });

  const scenes = $$('[data-scene]');
  const moving = new Set();
  let sceneObserver = null;
  if ('IntersectionObserver' in window) {
    sceneObserver = new IntersectionObserver(entries => {
      for (const entry of entries) {
        entry.target.classList.toggle('in-view',entry.isIntersecting);
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible'); moving.add(entry.target);
        } else moving.delete(entry.target);
      }
      requestScrollFrame();
    }, {threshold:0});
    scenes.forEach(scene => sceneObserver.observe(scene));
  } else scenes.forEach(scene => {scene.classList.add('is-visible','in-view');moving.add(scene);});
  // Enhancement is enabled only after observers are attached; without JS text stays visible.
  root.classList.add('enhanced');

  const fields = new Map();
  $$('[data-glyph-field]').forEach(field => {
    const chars = segment(field.dataset.glyphField || 'Aa',glyphs);
    field.setAttribute('aria-hidden','true');
    for (let i=0;i<54;i++) {
      const cell = document.createElement('span'); cell.className = 'glyph-cell';
      cell.textContent = chars[i % chars.length]; field.append(cell);
    }
    const cells = Array.from(field.children);
    let rect, centers = [], pointer = null, frame = 0, alternate = false;
    const bands = ['blue-03','blue-02','blue-01','yellow-01','yellow-02','orange-01','red-01'];
    function measure() {
      rect = field.getBoundingClientRect();
      centers = cells.map(cell => ({x:cell.offsetLeft + cell.offsetWidth/2,y:cell.offsetTop + cell.offsetHeight/2}));
    }
    function draw() {
      frame = 0;
      const radius = Math.max(field.clientWidth * .65,1);
      cells.forEach((cell,i) => {
        const center = centers[i];
        const distance = pointer && center ? Math.hypot(center.x-pointer.x,center.y-pointer.y) / radius : 1;
        const d = clamp(distance,0,1);
        const power = pointer ? (1-d)**2 : alternate ? (i%7)/6 : .2;
        cell.style.fontVariationSettings = '"wght" ' + Math.round(200 + power*750);
        cell.style.color = palette[bands[clamp(Math.floor(power*7),0,6)]];
      });
    }
    const schedule = () => { if (!frame) frame = requestAnimationFrame(draw); };
    field.addEventListener('pointermove',e => {
      if (!fine.matches || !mayMove()) return;
      rect = field.getBoundingClientRect(); pointer = {x:e.clientX-rect.left,y:e.clientY-rect.top}; schedule();
    });
    field.addEventListener('pointerleave',() => {pointer=null;schedule();});
    const reset = () => {pointer=null;draw();};
    fields.set(field.id,{toggle:()=>{alternate=!alternate;reset();},reset});
    new ResizeObserver(()=>{measure();schedule();}).observe(field);
    measure();draw();
  });
  $$('[data-field-toggle]').forEach(button => button.addEventListener('click',() => fields.get(button.dataset.fieldToggle)?.toggle()));

  const rings = $$('[data-ring]').map(frame => {
    const source = $('.ring-source',frame);
    if (!source) return null;
    const stage = document.createElement('div'); stage.className='ring-stage';stage.setAttribute('aria-hidden','true');
    const labels = Array.from(source.children);
    labels.forEach((item,i) => {
      const label = document.createElement('span'); label.className='ring-label';label.textContent=item.textContent;
      label.style.setProperty('--ring-slot',(i*360/labels.length)+'deg');stage.append(label);
    });
    frame.append(stage);
    function measure() {
      frame.style.setProperty('--ring-radius',Math.min(frame.clientWidth*.22,frame.clientHeight*.4,150)+'px');
    }
    new ResizeObserver(measure).observe(frame);measure();
    const configure = () => {
      const display3d = !reduced.matches && fine.matches;
      source.classList.toggle('sr-only',display3d);stage.hidden=!display3d;
    };
    reduced.addEventListener('change',configure);fine.addEventListener('change',configure);configure();
    return {frame,stage};
  }).filter(Boolean);
  const velocityEls = $$('[data-velocity]');
  let scrollFrame=0, lastY=scrollY, lastTime=performance.now(), velocity=0;
  function requestScrollFrame() {if (!scrollFrame && !document.hidden) scrollFrame=requestAnimationFrame(renderScroll);}
  function renderScroll(now) {
    scrollFrame=0;
    const y=scrollY, delta=y-lastY, dt=Math.max(now-lastTime,16);
    velocity=velocity*.68 + clamp(delta/dt,-3,3)*.32;lastY=y;lastTime=now;
    const animate=mayMove();
    for (const {frame,stage} of rings) {
      if (stage.hidden || !moving.has(frame.closest('[data-scene]'))) continue;
      const rect=frame.getBoundingClientRect();
      const progress=clamp((innerHeight-rect.top)/(innerHeight+rect.height),0,1);
      if (animate) stage.style.setProperty('--ring-angle',(-progress*180)+'deg');
    }
    for (const el of velocityEls) {
      const active=moving.has(el.closest('[data-scene]'));
      el.style.display='inline-block';
      el.style.transform=animate && active ? 'skewX('+clamp(velocity*2,-6,6)+'deg)' : '';
    }
    if (animate && Math.abs(velocity)>.015 && moving.size) requestScrollFrame();
  }
  addEventListener('scroll',requestScrollFrame,{passive:true});
  addEventListener('resize',requestScrollFrame,{passive:true});

  function pointerEffect(el, render) {
    let frame=0, point=null;
    const paint=()=>{frame=0;render(point);};
    el.addEventListener('pointermove',e=>{
      if (!fine.matches || !mayMove()) return;
      const r=el.getBoundingClientRect();point={x:(e.clientX-r.left)/r.width-.5,y:(e.clientY-r.top)/r.height-.5};
      if(!frame)frame=requestAnimationFrame(paint);
    });
    const reset=()=>{point=null;if(frame)cancelAnimationFrame(frame);frame=0;render(null);};
    el.addEventListener('pointerleave',reset);reduced.addEventListener('change',reset);
    document.addEventListener('kinetic:pause',reset);
  }
  $$('[data-magnetic]').forEach(el=>{
    const inner=$('[data-magnetic-inner]',el);if(!inner)return;
    pointerEffect(el,p=>{inner.style.transform=p?'translate('+p.x*12+'px,'+p.y*10+'px)':'';});
  });
  $$('[data-tilt]').forEach(el=>pointerEffect(el,p=>{
    el.style.setProperty('--tilt-x',(p?-p.y*4:0)+'deg');el.style.setProperty('--tilt-y',(p?p.x*4:0)+'deg');
  }));

  const openers=new WeakMap();
  document.addEventListener('click',e=>{
    const opener=e.target.closest('[data-open]');
    if(opener){
      const dialog=document.getElementById(opener.dataset.open);
      if(dialog instanceof HTMLDialogElement){openers.set(dialog,opener);dialog.showModal();root.classList.add('dialog-open');}
    }
    const anchor=e.target.closest('a[href^="#"]');
    if(anchor){
      const id=decodeURIComponent(anchor.hash.slice(1));const target=document.getElementById(id);
      if(target){
        e.preventDefault();target.scrollIntoView({behavior:mayMove()?'smooth':'instant',block:'start'});
        if(!target.hasAttribute('tabindex'))target.setAttribute('tabindex','-1');target.focus({preventScroll:true});
        try{history.replaceState(null,'','#'+encodeURIComponent(id));}catch{/* file/data URL history may be restricted */}
      }
    }
  });
  $$('dialog').forEach(dialog=>{
    dialog.addEventListener('close',()=>{
      if(!$('dialog[open]'))root.classList.remove('dialog-open');openers.get(dialog)?.focus({preventScroll:true});
    });
  });
  $$('[data-chat-demo]').forEach(form=>form.addEventListener('submit',e=>{
    e.preventDefault();const input=$('[name="idea"]',form),preview=$('[data-preview-text]',form),status=$('[data-demo-status]',form);
    const value=input.value.trim();
    if(!value){input.focus();if(status)status.textContent='先写下一句话';return;}
    preview.textContent=value;if(status)status.textContent='已在本地更新版式';
    if(mayMove())preview.animate([{opacity:0,transform:'translateY(16px)'},{opacity:1,transform:'none'}],{duration:500,easing:'cubic-bezier(.2,.75,.2,1)'});
  }));

  function updateMotion(){
    root.classList.toggle('motion-paused',paused || document.hidden);
    $$('[data-motion-toggle]').forEach(button=>{button.setAttribute('aria-pressed',String(paused));button.textContent=paused?'继续动态':'暂停动态';});
    fields.forEach(field=>field.reset());document.dispatchEvent(new Event('kinetic:pause'));requestScrollFrame();
  }
  $$('[data-motion-toggle]').forEach(button=>button.addEventListener('click',()=>{paused=!paused;updateMotion();}));
  document.addEventListener('visibilitychange',updateMotion);reduced.addEventListener('change',updateMotion);
  updateMotion();
})();
