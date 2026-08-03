from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE_DIR = ROOT / 'src/views/erp/customer-service'


def _source(name):
    return (SERVICE_DIR / name).read_text(encoding='utf-8')


def test_customer_service_surfaces_keep_distinct_business_definitions():
    satisfaction = _source('satisfaction.vue')
    knowledge = _source('knowledge.vue')
    notification = _source('notification.vue')
    smart_support = _source('smart-support.vue')

    assert "featureCode: 'F005'" in satisfaction and '满意度回访' in satisfaction and '完成回访' in satisfaction
    assert "featureCode: 'F043'" in knowledge and 'AI客服知识库' in knowledge and '审核并发布' in knowledge
    assert "featureCode: 'F084'" in notification and '消息通知中心' in notification and '执行发送' in notification
    assert "featureCode: 'F094'" in smart_support and '智能客服' in smart_support and '人工接单' in smart_support


def test_external_customer_service_features_do_not_claim_false_success():
    assert '不会伪造模型回答' in _source('knowledge.vue')
    assert '待通道配置' in _source('notification.vue')
    assert '不生成虚假回复' in _source('smart-support.vue')
