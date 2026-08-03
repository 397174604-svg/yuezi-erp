from pathlib import Path


config = Path('src/config/baby-pages.js').read_text(encoding='utf-8')
page = Path('src/views/erp/baby-workbench/index.vue').read_text(encoding='utf-8')

features = {
    'F027': '宝宝日志',
    'F069': '宝宝日志补全（睡眠/哭闹/排便量）',
    'F111': '新生儿护理记录',
    'F112': '体温监测与异常预警',
    'F115': '宝宝成长档案',
    'F120': '药品管理',
    'F121': '访客管理',
    'F122': '离所评估与交接',
}

for feature_id, title in features.items():
    assert feature_id in config and title in config, f'missing configuration: {feature_id} {title}'

assert config.count('apiAvailable: false') == len(features), 'all listed baby pages must use the explicit pending path'
assert config.count('当前暂无记录。') >= len(features), 'each listed baby page needs a clear empty-state message'
assert 'if (!this.config.apiAvailable) return' in page, 'unavailable endpoint must not be called'
assert '宝宝照护数据查询失败，未使用演示数据替代。' in page
assert '接口待接入，记录未保存。' in page
assert ':empty-text="emptyText"' in page
assert 'this.rows.unshift(row)' in page, 'available future endpoint should preserve a real save flow'

print('baby workbench availability checks: OK')
