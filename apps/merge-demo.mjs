// 两端合一：把 staff/mom 迁入 apps/demo，加端前缀隔离 + 废原生 tabBar 改自绘底栏。
// （产康已并入员工端 staff，美容 beauty 移出为独立项目——两者均不再进演示聚合。）
// 幂等：每次全量重建 demo/pages/{end} 与 demo/common/{end}，再生成 App.vue + pages.json。
import fs from 'node:fs';
import path from 'node:path';

const APPS = path.resolve('.');                 // 运行目录 = apps/
const DEMO = path.join(APPS, 'demo');
// 小程序端后端地址（mp 无 location，需注入固定地址）：默认本机；出局域网/真机包时传 DEMO_API=http://<局域网IP>:8799
const DEMO_API = process.env.DEMO_API || 'http://127.0.0.1:8799';
const ENDS = ['staff', 'mom'];
// 各端 tab 页（与原 pages.json tabBar.list 一致），供注入自绘底栏时标记 active
const TAB_PAGES = {
  staff: ['home/home', 'clients/clients', 'round/round', 'me/me'],
  mom: ['home/home', 'diet/diet', 'mall/mall', 'me/me'],
};

const rmrf = (p) => fs.existsSync(p) && fs.rmSync(p, { recursive: true, force: true });
const cpdir = (s, d) => fs.cpSync(s, d, { recursive: true });
const walk = (dir, ext) => {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(p, ext));
    else if (p.endsWith(ext)) out.push(p);
  }
  return out;
};

// 1) 复制 + 重写各端 pages/common
const allPages = [{ path: 'pages/launch/launch', style: { navigationStyle: 'custom' } }];
for (const end of ENDS) {
  rmrf(path.join(DEMO, 'pages', end));
  rmrf(path.join(DEMO, 'common', end));
  cpdir(path.join(APPS, end, 'pages'), path.join(DEMO, 'pages', end));
  cpdir(path.join(APPS, end, 'common'), path.join(DEMO, 'common', end));

  // 页面重写
  for (const f of walk(path.join(DEMO, 'pages', end), '.vue')) {
    let s = fs.readFileSync(f, 'utf8');
    s = s.replace(/@\/common\//g, `@/common/${end}/`);           // common 隔离
    s = s.replace(/uni\.switchTab\(/g, 'uni.reLaunch(');          // 废原生 tabBar → reLaunch
    s = s.replace(/(url:\s*['"`])\/pages\//g, `$1/pages/${end}/`); // 页面跳转加端前缀
    // 若为 tab 页 → 注入自绘底栏（根 view 闭合前）
    const rel = path.relative(path.join(DEMO, 'pages', end), f).replace(/\\/g, '/').replace(/\.vue$/, '');
    if (TAB_PAGES[end].includes(rel)) {
      const bar = `  <demo-tabbar end="${end}" active="${rel}" />\n`;
      s = s.replace(/<\/view>(\s*)<\/template>/, `</view>\n${bar}</template>`);
      // 给根容器留出底栏高度，避免内容被遮（补一段作用于本页根类的兜底样式）
      s = s.replace(/<\/style>\s*$/, `\n.screen, .page, .wrap { padding-bottom: 140rpx; }\n</style>\n`);
    }
    fs.writeFileSync(f, s, 'utf8');
  }
  // common js 里的 @/common 也隔离（一般相对 import，此为保险）
  for (const f of walk(path.join(DEMO, 'common', end), '.js')) {
    let s = fs.readFileSync(f, 'utf8');
    const s2 = s.replace(/@\/common\//g, `@/common/${end}/`);
    if (s2 !== s) fs.writeFileSync(f, s2, 'utf8');
  }

  // 收集页面进 pages.json（保留各自 style）
  const srcPagesJson = JSON.parse(fs.readFileSync(path.join(APPS, end, 'pages.json'), 'utf8'));
  for (const pg of srcPagesJson.pages) {
    allPages.push({ path: `pages/${end}/${pg.path.replace(/^pages\//, '')}`, style: pg.style });
  }
}

// 2) 生成 App.vue（注入四端 baseUrl + 合并四端 EMPTY 作 globalData 兜底空壳，避免页面 data() 初始读 globalData.data.* 崩）
const imports = ENDS.map((e) => `import { REMOTE as R_${e} } from '@/common/${e}/remote.js'`).join('\n')
  + '\n' + ENDS.map((e) => `import { EMPTY as E_${e} } from '@/common/${e}/data.js'`).join('\n');
const appVue = `<script>
${imports}
export default {
  globalData: { data: { ${ENDS.map((e) => '...E_' + e).join(', ')} }, live: false },
  onLaunch() {
    let base = '${DEMO_API}'  // 小程序端后端地址（构建时注入；开发者工具/真机连本机局域网 IP）
    // #ifdef H5
    const q = new URLSearchParams(location.search).get('api')
    // 生产走同域；若应用挂在 /yuezi 子路径，API 用同前缀（nginx 反代该前缀→后端）。本地 dev 连 :8799。
    const seg = location.pathname.split('/').filter(Boolean)[0]
    const pfx = (seg && seg !== 'admin' && seg.indexOf('.') < 0) ? '/' + seg : ''
    base = q || (/^5\\d\\d\\d$/.test(location.port) ? ('http://' + (location.hostname || '127.0.0.1') + ':8799') : (location.origin + pfx))
    // #endif
    ;[${ENDS.map((e) => 'R_' + e).join(', ')}].forEach((r) => { if (!r.baseUrl) r.baseUrl = base })
  }
}
</script>

<style lang="scss">
/* #ifdef H5 */
@media screen and (min-width: 500px) {
  uni-app { max-width: 480px; margin: 0 auto; box-shadow: 0 0 0 1px rgba(74,56,24,.06), 0 24rpx 80rpx rgba(74,56,24,.10); background: $ivory; }
  uni-tabbar.uni-tabbar-bottom, .uni-tabbar, .cartbar, .mask { left: 50% !important; right: auto !important; width: 480px !important; margin-left: -240px !important; box-sizing: border-box; }
}
/* #endif */
page { background: $ivory; color: $ink; font-family: $font-sans; font-size: 28rpx; line-height: 1.6; }
.yz-card { background: $paper; border: 1rpx solid $hair; border-radius: $radius-md; padding: 28rpx; box-shadow: 0 20rpx 60rpx -36rpx rgba(74,56,24,.45); }
.yz-serif { font-family: $font-display; color: $gold-deep; }
.yz-tag { font-size: 21rpx; padding: 8rpx 16rpx; border-radius: 40rpx; border: 1rpx solid $hair-s; color: $gold-deep; }
.yz-tag--solid { background: linear-gradient(135deg,#E9D4A4,#9C7838); color: #fff; border: none; }
</style>
`;
fs.writeFileSync(path.join(DEMO, 'App.vue'), appVue, 'utf8');

// 3) 生成 pages.json（launch 首页 + 四端页面；easycom 引 demo-tabbar；无原生 tabBar）
const pagesJson = {
  easycom: { autoscan: true, custom: { '^demo-(.*)': '@/components/demo-$1/demo-$1.vue' } },
  pages: allPages,
  globalStyle: {
    navigationBarTextStyle: 'black',
    navigationBarTitleText: '奇德芬芳 · 演示',
    navigationBarBackgroundColor: '#FBF7F0',
    backgroundColor: '#FBF7F0',
    rpxCalcMaxDeviceWidth: 480, rpxCalcBaseDeviceWidth: 375,
  },
};
fs.writeFileSync(path.join(DEMO, 'pages.json'), JSON.stringify(pagesJson, null, 2), 'utf8');

console.log('迁移完成：', allPages.length, '页（含 launch）；四端 common 已隔离；App.vue/pages.json 已生成');
