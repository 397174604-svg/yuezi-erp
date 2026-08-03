<template>
  <el-card class="inventory-workflow" shadow="never">
    <template v-if="resource === 'purchase-orders'">
      <div slot="header">采购订单履约</div><el-steps :active="purchaseStep" finish-status="success" align-center><el-step title="建单" /><el-step title="审核" /><el-step title="到货入库" /></el-steps><div class="workflow-list"><button v-for="row in rows.slice(0, 5)" :key="row.recordId || row.id" type="button" @click="$emit('select', row)">{{ row.purchaseNo || row.orderNo }} · {{ row.supplier || '待选供应商' }}<small>{{ row.materialName }} · {{ row.auditStatus || row.status }} / {{ row.arrivalStatus || '待到货' }}</small></button></div>
    </template>
    <template v-else-if="resource === 'stock-transfers'">
      <div slot="header">跨店调拨双端跟踪</div><div class="transfer-flow"><article v-for="row in rows.slice(0, 6)" :key="row.recordId || row.id" @click="$emit('select', row)"><strong>{{ row.sourceWarehouse || '调出门店' }}</strong><i class="el-icon-right" /><strong>{{ row.targetWarehouse || '调入门店' }}</strong><p>{{ row.materialName }} × {{ row.quantity }}</p><el-tag size="mini">{{ row.transferStatus || row.status }}</el-tag></article></div>
    </template>
    <template v-else-if="resource === 'stocktakes'">
      <div slot="header">库存盘点差异处理</div><el-table :data="rows.slice(0, 6)" size="mini" border @current-change="$emit('select', $event)"><el-table-column prop="materialName" label="物料" /><el-table-column prop="bookQuantity" label="账面" width="80" /><el-table-column prop="actualQuantity" label="实盘" width="80" /><el-table-column prop="differenceQuantity" label="差异" width="80" /><el-table-column prop="stocktakeStatus" label="状态" width="105" /></el-table>
    </template>
    <template v-else-if="resource === 'stock-warnings'">
      <div slot="header">库存预警处置队列</div><div class="warning-grid"><button v-for="row in rows.slice(0, 8)" :key="row.recordId || row.id" type="button" @click="$emit('select', row)"><el-tag size="mini" :type="tagType(row.warningType)">{{ row.warningType }}</el-tag><strong>{{ row.materialName }}</strong><small>现存 {{ row.currentQuantity }} · 安全 {{ row.safetyQuantity }} · {{ row.expiryDate || '无效期' }}</small></button></div>
    </template>
    <template v-else><div slot="header">库房可用量与估值</div><div class="stock-grid"><div v-for="item in stockMetrics" :key="item.label"><strong>{{ item.value }}</strong><span>{{ item.label }}</span></div></div><p class="note">库存查询、估值和批次效期共用已授权门店库存读模型，但操作入口与字段目的不同。</p></template>
  </el-card>
</template>

<script>
export default { name: 'InventoryP0Workflow', props: { resource: { type: String, default: '' }, rows: { type: Array, default: () => [] }}, computed: { purchaseStep() { if (this.rows.some(row => /已到货|已完成/.test(row.arrivalStatus || row.status || ''))) return 3; if (this.rows.some(row => /已审核/.test(row.auditStatus || row.status || ''))) return 2; return 1 }, stockMetrics() { return [{ label: '物料品种', value: this.rows.length }, { label: '可用数量', value: this.rows.reduce((sum, row) => sum + Number(row.availableQuantity || 0), 0) }, { label: '库存金额', value: this.rows.reduce((sum, row) => sum + Number(row.stockAmount || row.amount || 0), 0).toFixed(2) }] } }, methods: { tagType(value) { return /过期|不足|零/.test(value || '') ? 'danger' : /临期/.test(value || '') ? 'warning' : 'info' } }
}
</script>

<style lang="scss" scoped>
.inventory-workflow { margin-bottom:14px; }.workflow-list { display:grid; gap:7px; margin-top:14px; }.workflow-list button,.warning-grid button { padding:9px; border:1px solid #dfe7f4; border-radius:5px; background:#fff; text-align:left; cursor:pointer; }.workflow-list small,.warning-grid small { display:block; margin-top:4px; color:#738098; }.transfer-flow { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; margin-top:14px; }.transfer-flow article { padding:12px; border:1px solid #dce7f8; border-radius:6px; cursor:pointer; }.transfer-flow i { margin:0 8px; color:#5886d6; }.transfer-flow p,.note { color:#738098; font-size:12px; }.warning-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:8px; }.warning-grid strong { margin-left:7px; }.stock-grid { display:flex; gap:12px; }.stock-grid div { flex:1; padding:12px; background:#f4f8ff; border-radius:6px; }.stock-grid strong,.stock-grid span { display:block; }.stock-grid strong { color:#3f6aa5; font-size:22px; }.stock-grid span { color:#738098; font-size:12px; }
</style>
