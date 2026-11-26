const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const assets = path.join(__dirname, 'app');
fs.mkdirSync(assets, {recursive: true});
fs.copyFileSync(path.join(root, '全景建筑版', '深圳湾_全景建筑.html'), path.join(assets, 'index.html'));
