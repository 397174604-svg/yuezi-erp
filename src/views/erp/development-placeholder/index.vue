<template>
  <div>
    <p1-card-contract-minimal
      v-if="p1Feature"
      :feature-id="featureId"
      :page-title="pageTitle"
    />
    <div v-else class="development-page">
      <section class="status-panel">
        <div class="status-icon"><i class="el-icon-time" /></div>
        <div class="status-content">
          <el-tag type="warning" effect="dark">配置完善中</el-tag>
          <h1>{{ pageTitle }}</h1>
          <p>{{ detail.description }}</p>
        </div>
      </section>

      <el-card shadow="never" class="content-card">
        <div slot="header" class="card-heading">
          <div>
            <h2>业务准备状态</h2>
            <p>该功能已纳入业务菜单，相关规则完成配置后开放办理。</p>
          </div>
          <el-tag type="info" effect="plain">按业务确认进度开放</el-tag>
        </div>
        <el-alert
          :title="detail.blocker"
          type="warning"
          :closable="false"
          show-icon
        />
        <div class="status-grid">
          <div>
            <span>页面与路由</span>
            <strong>可访问，不 404</strong>
          </div>
          <div>
            <span>服务能力</span>
            <strong>配置中</strong>
          </div>
          <div>
            <span>记录规则</span>
            <strong>确认中</strong>
          </div>
          <div>
            <span>当前判定</span>
            <strong>暂未开放办理</strong>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="content-card">
        <div slot="header" class="card-heading">
          <div>
            <h2>业务开放条件</h2>
            <p>以下条件全部满足后开放正式办理。</p>
          </div>
        </div>
        <el-steps direction="vertical" :active="0" finish-status="success">
          <el-step v-for="item in detail.acceptance" :key="item" :title="item" />
        </el-steps>
      </el-card>
    </div>
  </div>
</template>

<script>
import P1CardContractMinimal from '@/views/erp/p1-card-contract-minimal/index'

const details = {
  F080: {
    description: '用于新旧厂商系统并行期间的批量账务差异核对；当前已交付的“交易对账”只支持逐笔手工登记外部流水。',
    blocker: '遗留厂商数据格式、导入模板和差异处理规则尚未确认。',
    acceptance: ['确认旧系统导出字段与唯一键', '完成批量导入、自动匹配和差异清单', '验证重复导入、门店隔离和审计日志']
  },
  F082: {
    description: '用于月子套餐卡、产康次卡和折扣卡的开卡、扣次、到期、转让和退款。',
    blocker: '现有卡类套餐和会员资产只覆盖部分能力，尚未完成统一卡生命周期。',
    acceptance: ['统一卡账户与权益流水模型', '完成开卡、扣次、转让、退款状态机', '验证余额/次数并发扣减和跨店权限']
  },
  F083: {
    description: '用于微信、支付宝及储值余额在线支付；当前系统不会生成任何虚假支付成功结果。',
    blocker: '尚未取得微信/支付宝商户配置、回调验签材料和生产对账文件。',
    acceptance: ['接入真实支付下单与签名', '完成异步回调验签和幂等入账', '完成退款、关单、对账和异常补偿']
  },
  F089: {
    description: '用于储值卡、次卡、折扣卡和微信卡包同步，并提供到期与余额提醒。',
    blocker: '依赖统一卡账户以及微信卡包商户权限，当前均未完成生产验收。',
    acceptance: ['完成统一卡账户和规则引擎', '接入微信卡包真实接口', '验证消费扣减、到期提醒和跨店共享规则']
  },
  F107: {
    description: '用于合同模板、在线电子签署、状态跟踪、到期提醒和归档检索。',
    blocker: '当前合同管理为线下签约业务闭环，尚未接入具备法律效力的电子签服务。',
    acceptance: ['确认电子签服务商与实名认证方案', '完成模板、签署回调、存证和验签', '验证撤销、到期提醒、归档与权限隔离']
  }
}

export default {
  name: 'DevelopmentPlaceholder',
  components: { P1CardContractMinimal },
  computed: {
    pageTitle() {
      return this.$route.meta.title
    },
    featureId() {
      return this.$route.meta.featureId || (this.pageTitle.match(/^F\d{3}/) || [''])[0]
    },
    p1Feature() {
      return ['F082', 'F107'].includes(this.featureId)
    },
    detail() {
      return details[this.featureId] || {
        description: '该功能已建立导航入口，正在完善业务规则和服务配置。',
        blocker: '业务规则和验收口径尚未确认。',
        acceptance: ['确认业务规则', '完成业务服务与记录规则', '完成权限、门店隔离和业务验收']
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.development-page { min-height: calc(100vh - 84px); padding: 24px; color: #26354c; background: #f3f6fa; }
.status-panel { display: flex; align-items: center; gap: 22px; padding: 30px; border-radius: 16px; color: #fff; background: linear-gradient(125deg, #3f382d, #8a6a35); box-shadow: 0 14px 34px rgba(74, 55, 26, .2); }
.status-icon { display: grid; width: 72px; height: 72px; flex: 0 0 72px; place-items: center; border-radius: 18px; background: rgba(255, 255, 255, .14); font-size: 34px; }
.status-content h1 { margin: 12px 0 8px; font-size: 28px; }
.status-content p { max-width: 880px; margin: 0; color: #f8ecd6; line-height: 1.75; }
.content-card { margin-top: 18px; border: 0; border-radius: 12px; }
.card-heading { display: flex; justify-content: space-between; align-items: center; gap: 18px; }
.card-heading h2 { margin: 0 0 5px; font-size: 17px; }
.card-heading p { margin: 0; color: #8491a2; font-size: 12px; }
.status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 20px; }
.status-grid div { padding: 18px; border: 1px solid #ebe4d7; border-radius: 10px; background: #fffaf1; }
.status-grid span { display: block; margin-bottom: 8px; color: #8a7860; font-size: 12px; }
.status-grid strong { color: #5f4b2d; font-size: 15px; }
@media (max-width: 900px) {
  .development-page { padding: 12px; }
  .status-panel, .card-heading { align-items: flex-start; flex-direction: column; }
  .status-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
