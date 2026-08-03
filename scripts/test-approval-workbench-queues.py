from pathlib import Path


config = Path('src/config/approval-pages.js').read_text(encoding='utf-8')
page = Path('src/views/erp/approval-workbench/index.vue').read_text(encoding='utf-8')

for token in ('合同审批', '收款确认', '退款与结算', '门店申请', '合同编号', '收款单号', '结算单号', '申请单号'):
    assert token in config, f'missing approval queue definition: {token}'

for token in ('queue-lanes', 'queue-lane', '审批轨迹', 'notifyPending'):
    assert token in page, f'missing approval workbench structure: {token}'

assert '审批聚合接口待接入' in config

for prohibited in ('示例业务', '演示数据', '$message.success'):
    assert prohibited not in page, f'prohibited fake approval content: {prohibited}'

print('approval queue workbench static checks: OK')
