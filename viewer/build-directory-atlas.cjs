const fs = require('node:fs');
const path = require('node:path');
const {gzipSync} = require('node:zlib');
const {patchMetricDirectory} = require('./patch-metric-directory.cjs');

// Keep the delivered metric viewer, including its dimension panel and its landmark presets.
const root = path.join(__dirname, '..');
const folder = process.argv[2]?path.resolve(process.argv[2]):path.join(root, '全景建筑版');
const delivered = path.join(folder, '深圳湾_全景建筑.html');
const panorama = path.join(root, '全景建筑版', '深圳湾_全景建筑.html');
const original = fs.readFileSync([delivered,panorama,path.join(root,'建筑核尺版','深圳湾_建筑核尺.html')].find(f=>fs.existsSync(f)), 'utf8');
const geometry = fs.readFileSync(path.join(folder, '深圳湾_全景建筑.glb'));
const startup = 'mc.get("view")||(Re?"oppo":Ie?"houhai":oe.length?"lakesky":O.mall?"houhai":"bay")';
if (!original.includes(startup) && !original.includes('Ae(mc.get("view")||"all",!0)')) throw Error('Cannot locate the metric atlas default view');
let html = original.replace(startup, 'mc.get("view")||"all"');
html = html.replace('pe("#reset").onclick=()=>Ae("bay")','pe("#reset").onclick=()=>Ae("all")')
  .replace('地图外接矩形 · 净投影面积','部件平面长宽 · 投影面积');
const modelTag = /(<script id="model-data"[^>]*>)[A-Za-z0-9+/=]+(<\/script>)/;
if (!modelTag.test(html)) throw Error('Cannot locate the embedded city');
html = html.replace(modelTag, (_, start, end) => start + gzipSync(geometry,{level:8}).toString('base64') + end);
html = patchMetricDirectory(html);
fs.writeFileSync(delivered, html);
