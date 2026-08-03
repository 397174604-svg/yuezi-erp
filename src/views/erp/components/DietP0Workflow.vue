<template>
  <el-card class="diet-workflow" shadow="never">
    <template v-if="resource === 'meal-orders'">
      <div slot="header">订餐配送履约看板</div>
      <div class="order-lanes">
        <section v-for="lane in orderLanes" :key="lane.label"><header>{{ lane.label }} <el-tag size="mini">{{ lane.rows.length }}</el-tag></header>
          <button v-for="row in lane.rows.slice(0, 4)" :key="row.recordId || row.id" type="button" @click="$emit('select', row)">{{ row.customerName || '未关联客户' }} · {{ row.room || '未分房' }}<small>{{ row.dishName || '待选菜品' }}</small></button>
        </section>
      </div>
    </template>
    <template v-else-if="resource === 'dishes'">
      <div slot="header">月子餐库</div>
      <div class="dish-catalog"><button v-for="row in rows.slice(0, 12)" :key="row.recordId || row.id" type="button" @click="$emit('select', row)"><strong>{{ row.dishName }}</strong><span>{{ row.dishCategory || '未分类' }} · {{ row.mealType || '餐次待设' }}</span><small>{{ row.ingredients || '食材说明待维护' }}</small></button></div>
    </template>
    <template v-else>
      <div slot="header">膳食制作与配送完成情况</div>
      <div class="stat-bars"><div v-for="row in rows.slice(0, 6)" :key="row.id"><span>{{ row.statDate || row.deliveryDate }} · {{ row.mealType }}</span><el-progress :percentage="rate(row)" :stroke-width="12" /><small>计划 {{ row.plannedCount || 0 }} · 签收 {{ row.signedCount || 0 }} · 退餐 {{ row.returnedCount || 0 }}</small></div></div>
    </template>
  </el-card>
</template>

<script>
export default {
  name: 'DietP0Workflow',
  props: { resource: { type: String, default: '' }, rows: { type: Array, default: () => [] }},
  computed: {
    orderLanes() {
      const lanes = [['待备餐', /待确认|待备餐/], ['备餐中', /备餐中/], ['配送中', /配送中/], ['已签收/退餐', /已签收|已退餐/]]
      return lanes.map(([label, pattern]) => ({ label, rows: this.rows.filter(row => pattern.test(row.orderStatus || row.status || '')) }))
    }
  },
  methods: { rate(row) { return Math.min(100, Math.round(Number(row.completionRate || String((Number(row.signedCount || 0) / Math.max(Number(row.plannedCount || 0), 1)) * 100).toFixed(0)).toString().replace('%', ''))) } }
}
</script>

<style lang="scss" scoped>
.diet-workflow { margin-bottom: 14px; }.order-lanes { display:grid; grid-template-columns:repeat(4,minmax(160px,1fr)); gap:10px; overflow-x:auto; }.order-lanes section { min-width:160px; padding:10px; background:#f7fcf8; border:1px solid #dceee0; border-radius:6px; }.order-lanes header { display:flex; justify-content:space-between; margin-bottom:8px; color:#2f7041; font-weight:600; }.order-lanes button,.dish-catalog button { display:block; width:100%; margin:6px 0; padding:8px; border:1px solid #e2e8e3; border-radius:4px; background:#fff; text-align:left; cursor:pointer; }.order-lanes small,.dish-catalog span,.dish-catalog small { display:block; margin-top:3px; color:#7a8495; font-size:12px; }.dish-catalog { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; }.stat-bars { display:grid; gap:10px; }.stat-bars span,.stat-bars small { display:block; margin-bottom:4px; color:#596579; font-size:12px; }
</style>
