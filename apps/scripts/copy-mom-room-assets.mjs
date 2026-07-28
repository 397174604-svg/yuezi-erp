import { copyFile, mkdir, readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const out = join(root, 'mpdist', 'mom');
const source = join(root, 'mom', 'static', 'rooms');
const compiled = await readFile(join(out, 'common', 'assets.js'), 'utf8');
const files = [
  'double-room.jpg', 'special-room.jpg', 'small-suite.jpg', 'suite.jpg', 'vip302.jpg', 'vip512.jpg',
  'huanghe/base-room.jpg', 'huanghe/facade.jpg', 'huanghe/presidential-suite.jpg',
  'huanghe/queen-suite.jpg', 'huanghe/rehab-floor.jpg', 'huanghe/repair-suite.jpg',
];

await mkdir(join(out, 'assets'), { recursive: true });
for (const file of files) {
  const stem = file.split(/[\\/]/).pop().replace(/\.jpg$/, '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = compiled.match(new RegExp('/assets/' + stem + '\\.[A-Fa-f0-9]+\\.jpg'));
  if (!match) throw new Error('未找到编译后的房型图片路径：' + file);
  await copyFile(join(source, file), join(out, match[0].replace('/assets/', 'assets/')));
}
console.log(`已复制 ${files.length} 张 MOM 房型照片到 ${join(out, 'assets')}`);
