"""Build the six-component offline inspector and visual review sheets."""
from pathlib import Path
from io import BytesIO
import base64
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT/'face_manifest.json').read_text())
labels = {'face': '完整无五官脸底', 'ear_screen_left': '屏幕左耳', 'ear_screen_right': '屏幕右耳',
          'nose': '鼻部软阴影', 'mouth': '中性闭口线', 'neck_bridge': '头颈连接'}
items = []
sheet = Image.new('RGB', (1080, 760), '#263240')
draw = ImageDraw.Draw(sheet)
for i, (name, entry) in enumerate(manifest['artwork']['components'].items()):
    mother = Image.open(ROOT/entry['cleanedSource']).convert('RGBA')
    box = mother.getbbox(); mother = mother.crop((box[0]-6, box[1]-6, box[2]+6, box[3]+6))
    mother.thumbnail((1000, 700), Image.Resampling.LANCZOS)
    buf = BytesIO(); mother.save(buf, format='PNG')
    native = Image.open(ROOT/entry['registeredFile']).convert('RGBA')
    box = native.getbbox(); native = native.crop((box[0]-2, box[1]-2, box[2]+2, box[3]+2))
    nbuf = BytesIO(); native.save(nbuf, format='PNG')
    items.append({'name': name, 'label': labels[name], 'src': 'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),
                  'native': 'data:image/png;base64,'+base64.b64encode(nbuf.getvalue()).decode(),
                  'size': [box[2]-box[0], box[3]-box[1]], 'source': entry['generatedSource']})
    tile = mother.copy(); tile.thumbnail((305, 300), Image.Resampling.LANCZOS)
    x = i % 3 * 360; y = i // 3 * 380
    draw.text((x+16, y+14), name, fill='white')
    draw.text((x+16, y+36), f'{box[2]-box[0]} x {box[3]-box[1]} px at registration', fill='#bfcbd7')
    sheet.paste(tile, (x+180-tile.width//2, y+214-tile.height//2), tile)
sheet.save(ROOT/'reports/face_group_components.png')
# Share only the inspector UI template; artwork data comes from face_manifest.
eye_builder = (ROOT/'scripts/build_eye_inspector.py').read_text()
page = eye_builder.split("page='''", 1)[1].split("'''\n(ROOT/", 1)[0]
page = page.replace('眼部第一组 · 独立分件检查', '脸部第二组 · 独立分件检查').replace('眼部第一组 · 十个独立分件', '脸部第二组 · 六个独立分件')
page = page.replace('左右上下眼睑、完整眼白、完整虹膜与眉毛。大图母资产与最终坐标小图可分别检查；这里显示完整分件，眼眶遮罩和中性裁切片由装配导出。',
    '完整脸底、左右耳、鼻、闭口嘴与头颈连接。三背景检查生成母资产、最终坐标图；连接件底部透明渐变用于与现有白色颈部衔接。左右耳已分别生成，后续对称部件采用单侧生成后镜像。')
page = page.replace('__eyeInspectorReady', '__faceInspectorReady')
(ROOT/'脸部第二组_独立分件检查.html').write_text(page.replace('__ITEMS__', json.dumps(items, ensure_ascii=False)))

layers = json.loads((ROOT/'manifest.json').read_text())['layers']
head_parts = Image.new('RGBA', (1024, 1536))
for layer in layers:
    if layer['name'] in labels or layer['name'].startswith(('eyewhite_', 'iris_', 'upper_lid_', 'lower_lid_', 'brow_')):
        head_parts.alpha_composite(Image.open(ROOT/layer['file']).convert('RGBA'))
head_parts.crop((395, 20, 625, 315)).save(ROOT/'reports/face_assembly_without_hair.png')
review = Image.new('RGB', (1380, 590))
for i, color in enumerate(['#ffffff', '#171c25', '#b9c0c8']):
    tile = Image.new('RGB', (460, 590), color)
    part = head_parts.crop((395, 20, 625, 315)).resize((460, 590), Image.Resampling.LANCZOS)
    tile.paste(part, mask=part.getchannel('A')); review.paste(tile, (i*460, 0))
review.save(ROOT/'reports/face_assembly_three_backgrounds.png')
current = Image.open(ROOT/'reports/neutral.png').crop((365, 15, 655, 315)).resize((580, 600), Image.Resampling.LANCZOS)
bg = Image.new('RGB', current.size, '#bbc1c7'); bg.paste(current, mask=current.getchannel('A')); bg.save(ROOT/'reports/delivery_head.jpg', quality=95)
old = Image.open(ROOT.parent/'live2d_v4/reports/neutral.png').crop((365, 15, 655, 315)).resize((580, 600), Image.Resampling.LANCZOS)
pair = Image.new('RGB', (1160, 630), '#bbc1c7'); pair.paste(old, (0, 30), old); pair.paste(current, (580, 30), current)
d = ImageDraw.Draw(pair); d.text((15, 10), 'v4', fill='black'); d.text((595, 10), 'v5', fill='black'); pair.save(ROOT/'reports/face_group_before_after.jpg', quality=95)
print('Built standalone face inspector: six images and review sheets')
