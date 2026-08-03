from pathlib import Path


SOURCE = Path('src/views/erp/people-workbench/index.vue').read_text(encoding='utf-8')


def expect(value: str) -> None:
    assert value in SOURCE, f'missing: {value}'


for feature_id in ('F025', 'F047', 'F048', 'F049', 'F051', 'F052', 'F053', 'F054', 'F055', 'F096', 'F126'):
    expect(feature_id)

expect("import { getBasicModuleData } from '@/api/erp-basic'")
expect('employee-records')
expect('业务规则正在确认，暂未开放记录办理')
expect('员工组织数据查询失败，请稍后重试。')

for prohibited in ('示例业务', '示例人员', '保存成功（演示数据）', 'DEMO-'):
    assert prohibited not in SOURCE, f'prohibited demo content: {prohibited}'

print('people workbench static checks: OK')
