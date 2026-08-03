from pathlib import Path


sources = {
    'nursing': Path('src/views/erp/nursing-workbench/index.vue').read_text(encoding='utf-8'),
    'diet': Path('src/views/erp/diet-workbench/index.vue').read_text(encoding='utf-8'),
    'inventory': Path('src/views/erp/inventory-workbench/index.vue').read_text(encoding='utf-8'),
}

expected = {
    'nursing': ('nursing-visual', '护理任务板', '班次排班', '入住交接单'),
    'diet': ('diet-visual', '周餐单视图', '配送任务流', '菜品库'),
    'inventory': ('inventory-visual', '库存总账', '调拨双向确认', '盘点工作台', '效期与库存预警'),
}

for domain, tokens in expected.items():
    source = sources[domain]
    for token in tokens:
        assert token in source, f'{domain}: missing distinct visual structure {token}'
    assert 'rows = this.createDemo' not in source, f'{domain}: load path must not fall back to demo rows'
    assert 'return this.createDemo' not in source, f'{domain}: query path must not return demo rows'

print('P0 nursing/diet/inventory visual checks: OK')
