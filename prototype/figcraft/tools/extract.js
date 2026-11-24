() => {
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
const width=innerWidth,height=document.documentElement.scrollHeight;
let parts=[],texts=0,rects=0,icons=[];
const ctx=document.createElement('canvas').getContext('2d');
function visible(el){const c=getComputedStyle(el),r=el.getBoundingClientRect();return c.display!=='none'&&c.visibility!=='hidden'&&+c.opacity!==0&&r.width>0&&r.height>0;}
function walk(el){if(!visible(el)||['SCRIPT','STYLE','LINK'].includes(el.tagName))return;
 const c=getComputedStyle(el),r=el.getBoundingClientRect(),x=r.left+scrollX,y=r.top+scrollY;
 const bg=c.backgroundColor,rad=Math.min(parseFloat(c.borderTopLeftRadius)||0,r.width/2,r.height/2);
 const sides=['Top','Right','Bottom','Left'].map(k=>({w:parseFloat(c['border'+k+'Width'])||0,color:c['border'+k+'Color'],style:c['border'+k+'Style']}));
 if(bg!=='rgba(0, 0, 0, 0)'&&bg!=='transparent'){parts.push(`<rect x="${x}" y="${y}" width="${r.width}" height="${r.height}" rx="${rad}" fill="${bg}"/>`);rects++;}
 if(sides.every(s=>s.w>0&&s.w===sides[0].w&&s.color===sides[0].color)){
  const w=sides[0].w;parts.push(`<rect x="${x+w/2}" y="${y+w/2}" width="${Math.max(0,r.width-w)}" height="${Math.max(0,r.height-w)}" rx="${Math.max(0,rad-w/2)}" fill="none" stroke="${sides[0].color}" stroke-width="${w}"/>`);rects++;
 }else{const coords=[[x,y,x+r.width,y],[x+r.width,y,x+r.width,y+r.height],[x,y+r.height,x+r.width,y+r.height],[x,y,x,y+r.height]];sides.forEach((s,i)=>{if(!s.w)return;const q=coords[i];parts.push(`<line x1="${q[0]}" y1="${q[1]}" x2="${q[2]}" y2="${q[3]}" stroke="${s.color}" stroke-width="${s.w}" ${s.style==='dashed'?'stroke-dasharray="3 3"':''}/>`);});}
 if(el.tagName==='SVG'){const svg=el.cloneNode(true);svg.setAttribute('x',x);svg.setAttribute('y',y);svg.setAttribute('width',r.width);svg.setAttribute('height',r.height);svg.setAttribute('color',c.color);parts.push(new XMLSerializer().serializeToString(svg));return;}
 if(c.fontFamily.includes('Material Symbols')){
  icons.push(el.textContent.trim());let p='M4 10H16M10 4L16 10L10 16';const text=el.textContent.trim();
  if(text==='search')p='M13 13L18 18M14 8A6 6 0 1 1 2 8A6 6 0 1 1 14 8';
  else if(text==='expand_more')p='M4 7L10 13L16 7';
  else if(text==='check_circle')p='M18 10A8 8 0 1 1 2 10A8 8 0 1 1 18 10M6 10L9 13L14 7';
  else if(text!=='arrow_forward')p='M4 4H16V16H4ZM7 8H13M7 12H13';
  parts.push(`<svg x="${x}" y="${y}" width="${r.width}" height="${r.height}" viewBox="0 0 20 20"><path d="${p}" fill="none" stroke="${c.color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`);return;
 }
 for(const node of el.childNodes){if(node.nodeType===1)walk(node);else if(node.nodeType===3&&node.textContent.trim()){
  const range=document.createRange(),lines=[];let current=null;
  for(let i=0;i<node.length;i++){range.setStart(node,i);range.setEnd(node,i+1);const q=range.getBoundingClientRect();if(!q.height||!q.width)continue;
   if(!current||Math.abs(current.y-q.top)>1){current={x:q.left+scrollX,y:q.top,text:''};lines.push(current);}current.text+=node.textContent[i];}
  ctx.font=c.font;const ascent=ctx.measureText('Hg').fontBoundingBoxAscent||parseFloat(c.fontSize);
  for(const line of lines){if(!line.text.trim())continue;parts.push(`<text x="${line.x}" y="${line.y+scrollY+ascent}" font-family="Poppins" font-size="${parseFloat(c.fontSize)}" font-weight="${c.fontWeight}" letter-spacing="${c.letterSpacing==='normal'?0:parseFloat(c.letterSpacing)}" fill="${c.color}" xml:space="preserve">${esc(line.text)}</text>`);texts++;}
 }}
 if(el.tagName==='INPUT'){
 if(el.type==='checkbox'){parts.push(`<rect x="${x}" y="${y}" width="${r.width}" height="${r.height}" rx="3" fill="${el.checked?'#006BEB':'#FFFFFF'}" stroke="#71717A"/>`);if(el.checked)parts.push(`<path d="M${x+4} ${y+10}L${x+8} ${y+14}L${x+16} ${y+5}" fill="none" stroke="#FFFFFF" stroke-width="2"/>`);}
 else{ctx.font=c.font;const value=el.value||el.getAttribute('placeholder')||'';const metrics=ctx.measureText(value);const tx=c.textAlign==='right'?x+r.width-parseFloat(c.paddingRight)-metrics.width:x+parseFloat(c.paddingLeft);parts.push(`<text x="${tx}" y="${y+r.height/2+parseFloat(c.fontSize)*.35}" font-family="Poppins" font-size="${parseFloat(c.fontSize)}" fill="#18181B">${esc(value)}</text>`);texts++;}
 }

}
walk(document.body);
return {svg:`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${parts.join('')}</svg>`,width,height,texts,rects,approximatedIcons:icons};
}