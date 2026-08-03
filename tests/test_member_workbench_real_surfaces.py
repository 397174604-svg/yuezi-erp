from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src' / 'views' / 'erp' / 'member-workbench' / 'index.vue').read_text(encoding='utf-8')


def test_required_feature_surfaces_have_distinct_real_definitions():
    for feature_id, title in [
        ('F006', '会员来源分析'),
        ('F040', '积分体系'),
        ('F060', '次卡价值分析'),
        ('F087', '会员等级体系'),
        ('F088', '会员标签与智能分群'),
    ]:
        assert feature_id in SOURCE
        assert title in SOURCE


def test_member_workbench_uses_live_asset_reads_and_safe_empty_states():
    assert "getAssetList('accounts'" in SOURCE
    assert "getAssetList('cards'" in SOURCE
    assert '暂无会员主档数据' in SOURCE
    assert '暂无会员等级或权益规则数据' in SOURCE
    assert '暂无标签或分群数据' in SOURCE


def test_member_workbench_has_no_legacy_fake_kpis_or_example_rows():
    for forbidden in ('示例业务', '12,860', '486', '6,842', 'R-260801', 'M-10028'):
        assert forbidden not in SOURCE
