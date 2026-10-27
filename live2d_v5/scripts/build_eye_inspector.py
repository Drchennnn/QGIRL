"""Create a self-contained high-resolution, ten-component art inspection page."""
from pathlib import Path
from io import BytesIO
import base64,json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'eye_manifest.json').read_text())
items=[]
labels={'upper_lid':'上眼睑／上睫毛','lower_lid':'下眼睑／下睫毛','eyewhite':'完整眼白底图','iris_full':'完整虹膜','brow':'眉毛'}
for kind in ['upper_lid','lower_lid','eyewhite','iris_full','brow']:
 for side in ['screen_left','screen_right']:
  name=f'{kind}_{side}';entry=manifest['artwork']['components'][name]
  src=Image.open(ROOT/entry['cleanedSource']).convert('RGBA')
  bbox=src.getbbox();pad=10
  src=src.crop((max(0,bbox[0]-pad),max(0,bbox[1]-pad),min(src.width,bbox[2]+pad),min(src.height,bbox[3]+pad)))
  src.thumbnail((1000,700),Image.Resampling.LANCZOS)
  buf=BytesIO();src.save(buf,format='PNG')
  native=Image.open(ROOT/entry['registeredFile']).convert('RGBA');box=native.getbbox();native=native.crop((box[0]-2,box[1]-2,box[2]+2,box[3]+2));nbuf=BytesIO();native.save(nbuf,format='PNG')
  items.append({'name':name,'label':('屏幕左侧' if side=='screen_left' else '屏幕右侧')+' · '+labels[kind],
   'src':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),
   'native':'data:image/png;base64,'+base64.b64encode(nbuf.getvalue()).decode(),
   'size':[box[2]-box[0],box[3]-box[1]],'source':entry['generatedSource']})
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>眼部第一组 · 独立分件检查</title>
<style>*{box-sizing:border-box}body{margin:0;background:#151b23;color:#edf2fa;font:15px system-ui}header{position:sticky;top:0;background:#1a222eee;padding:18px 24px;border-bottom:1px solid #35404e;z-index:2}h1{margin:0 0 8px;font-size:21px}p{margin:8px 0;color:#bfccdc;line-height:1.6}button{font:inherit;border:1px solid #576679;border-radius:6px;background:#283446;color:#fff;padding:7px 12px;cursor:pointer;margin:4px 8px 0 0}button[aria-pressed=true]{border-color:#67d9c4;box-shadow:0 0 0 1px #67d9c4}main{padding:22px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}article{background:#202a37;border:1px solid #374555;border-radius:10px;overflow:hidden}h2{font-size:17px;margin:14px 16px 6px}code{font-size:12px;color:#a8c5e6;overflow-wrap:anywhere}.meta{padding:0 16px 12px}.stage{height:270px;display:flex;align-items:center;justify-content:center;overflow:hidden;background-color:#b9c0c8;background-image:conic-gradient(#b9c0c8 25%,#d5dbe1 0 50%,#b9c0c8 0 75%,#d5dbe1 0);background-size:24px 24px}.stage img{max-width:90%;max-height:90%;object-fit:contain}body[data-bg=white] .stage{background:#fff}body[data-bg=dark] .stage{background:#171c25}small{display:block;color:#aebdd0;margin-top:5px}@media(max-width:740px){main{grid-template-columns:1fr;padding:12px}.stage{height:240px}}
</style><header><h1>眼部第一组 · 十个独立分件</h1><p>左右上下眼睑、完整眼白、完整虹膜与眉毛。大图母资产与最终坐标小图可分别检查；这里显示完整分件，眼眶遮罩和中性裁切片由装配导出。</p><div id="background"><button data-bg="checker" aria-pressed="true">棋盘底</button><button data-bg="white" aria-pressed="false">白底</button><button data-bg="dark" aria-pressed="false">深底</button></div><div id="mode"><button data-mode="mother" aria-pressed="true">生成母资产</button><button data-mode="native" aria-pressed="false">原生大小 1×</button><button data-mode="zoom" aria-pressed="false">坐标图 4×</button></div></header><main></main><script>
const items=__ITEMS__;let mode='mother';
const main=document.querySelector('main');for(const item of items){const card=document.createElement('article');card.innerHTML='<h2>'+item.label+'</h2><div class="meta"><code>'+item.name+'</code><small>坐标图有效内容 '+item.size.join(' × ')+' px</small></div><div class="stage"><img alt="'+item.label+'" src="'+item.src+'"></div><div class="meta"><small>'+item.source+'</small></div>';main.append(card)}
function showMode(){for(let i=0;i<items.length;i++){const im=main.children[i].querySelector('img');im.src=mode==='mother'?items[i].src:items[i].native;if(mode==='mother'){im.style.width='';im.style.height=''}else{const scale=mode==='native'?1:4;im.style.width=(items[i].size[0]+4)*scale+'px';im.style.height=(items[i].size[1]+4)*scale+'px'}}}
for(const button of document.querySelectorAll('#background button'))button.onclick=()=>{document.body.dataset.bg=button.dataset.bg;for(const b of document.querySelectorAll('#background button'))b.setAttribute('aria-pressed',String(b===button))};
for(const button of document.querySelectorAll('#mode button'))button.onclick=()=>{mode=button.dataset.mode;showMode();for(const b of document.querySelectorAll('#mode button'))b.setAttribute('aria-pressed',String(b===button))};
window.__eyeInspectorReady=true;
</script></html>'''
(ROOT/'眼部第一组_独立分件检查.html').write_text(page.replace('__ITEMS__',json.dumps(items,ensure_ascii=False)))
print('Built standalone inspector with 10 components')
