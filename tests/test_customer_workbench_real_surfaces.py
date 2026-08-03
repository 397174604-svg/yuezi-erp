from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src/views/erp/customer-workbench/index.vue').read_text(encoding='utf-8')


def test_customer_workbench_does_not_fabricate_clue_status_or_store():
    assert "store: row.store || row.convertStore || ''" in SOURCE
    assert "followStatus: leadFollowStatuses.includes(row.followStatus) ? row.followStatus : ''" in SOURCE
    assert "storeByRouteId[(index % 2) + 1]" not in SOURCE
    assert 'leadFollowStatuses[index % leadFollowStatuses.length]' not in SOURCE


def test_customer_reminders_and_detail_trace_are_data_safe():
    assert 'reminderItems()' in SOURCE
    assert "今日应跟进', count: 12" not in SOURCE
    assert '当前未返回轨迹时不展示推测记录' in SOURCE
    assert '今天 09:30' not in SOURCE
