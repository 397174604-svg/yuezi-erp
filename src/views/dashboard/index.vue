<template>
  <div class="dashboard-page">
    <section class="welcome-bar">
      <div><span>2026年7月22日 · 星期三</span><h1>下午好，admin</h1><p>这里是奇德芬芳月子会所今日经营概览。</p></div>
      <div class="welcome-actions"><el-select v-model="store" size="small"><el-option label="中心广场旗舰店" value="中心广场旗舰店" /><el-option label="黄河路轻奢店" value="黄河路轻奢店" /></el-select><el-button size="small" icon="el-icon-refresh" @click="$message.success('数据已刷新')">刷新</el-button></div>
    </section>

    <div class="summary-grid">
      <div v-for="card in summaries" :key="card.label" class="summary-card">
        <div class="summary-icon" :style="{background:card.soft,color:card.color}"><i :class="card.icon" /></div>
        <div><span>{{ card.label }}</span><b>{{ card.value }}<small>{{ card.unit }}</small></b><em :class="card.trend >= 0 ? 'up' : 'down'"><i :class="card.trend >= 0 ? 'el-icon-top' : 'el-icon-bottom'" /> {{ Math.abs(card.trend) }}% 较上月</em></div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :lg="16" :xs="24">
        <el-card shadow="never" class="panel occupancy-panel">
          <div slot="header" class="panel-head"><div><b>房态概览</b><span>实时入住与预订状态</span></div><router-link to="/room/item-1">进入房态图 <i class="el-icon-arrow-right" /></router-link></div>
          <div class="occupancy-top"><div class="rate-ring"><div><b>58.3%</b><span>入住率</span></div></div><div class="room-stats"><div v-for="stat in roomStats" :key="stat.label"><i :style="{background:stat.color}" /><b>{{ stat.value }}</b><span>{{ stat.label }}</span></div></div></div>
          <div class="mini-room-grid"><div v-for="room in rooms" :key="room.no" :class="`mini-room ${room.status}`"><b>{{ room.no }}</b><span>{{ room.label }}</span></div></div>
        </el-card>
      </el-col>
      <el-col :lg="8" :xs="24">
        <el-card shadow="never" class="panel todo-panel">
          <div slot="header" class="panel-head"><div><b>待办流程</b><span>需要您处理的业务</span></div><el-badge :value="750" /></div>
          <div v-for="todo in todos" :key="todo.label" class="todo-row"><span class="todo-icon" :style="{background:todo.soft,color:todo.color}"><i :class="todo.icon" /></span><div><b>{{ todo.label }}</b><span>{{ todo.note }}</span></div><em>{{ todo.value }}</em></div>
          <el-button class="all-todo" plain>查看全部待办</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel warning-panel">
      <div slot="header" class="panel-head"><div><b>预警平台</b><span>跨业务风险与服务提醒</span></div><div class="legend"><span><i class="high" />高优先级</span><span><i class="normal" />一般提醒</span></div></div>
      <div class="warning-groups">
        <div v-for="group in warnings" :key="group.title" class="warning-group"><div class="warning-title"><i :class="group.icon" :style="{color:group.color}" /><span>{{ group.title }}</span><b :style="{color:group.color}">{{ group.total }}</b></div><div class="warning-items"><div v-for="item in group.items" :key="item.name"><span>{{ item.name }}</span><b>{{ item.value }}</b></div></div></div>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :lg="15" :xs="24"><el-card shadow="never" class="panel trend-panel"><div slot="header" class="panel-head"><div><b>经营趋势</b><span>近七月合同回款情况</span></div><el-radio-group v-model="metric" size="mini"><el-radio-button label="合同额" /><el-radio-button label="回款额" /></el-radio-group></div><div class="trend-chart"><div class="chart-labels"><span>30万</span><span>20万</span><span>10万</span><span>0</span></div><div v-for="bar in trendBars" :key="bar.month" class="trend-bar"><div class="bar-pair"><i :style="{height:bar.contract+'%'}" /><i :style="{height:bar.receipt+'%'}" /></div><span>{{ bar.month }}</span></div></div></el-card></el-col>
      <el-col :lg="9" :xs="24"><el-card shadow="never" class="panel source-panel"><div slot="header" class="panel-head"><div><b>客户来源</b><span>本月有效客资渠道</span></div></div><div v-for="source in sources" :key="source.label" class="source-row"><span>{{ source.label }}</span><div><i :style="{width:source.percent+'%',background:source.color}" /></div><b>{{ source.percent }}%</b></div></el-card></el-col>
    </el-row>

    <footer class="dashboard-footer">授权单位：濮阳市奇德芬芳母婴护理有限公司 <span>服务截止日期：2027/6/10</span><span>ERP 演示复刻版 V1.0</span></footer>
  </div>
</template>

<script>
export default {
  name: 'Dashboard',
  data() {
    return {
      store: '中心广场旗舰店',
      metric: '合同额',
      summaries: [
        { label: '账户总收入', value: '248,500', unit: '元', trend: 12.8, icon: 'el-icon-wallet', color: '#B8945A', soft: '#FBF3E5' },
        { label: '客户总数量', value: '326', unit: '人', trend: 8.2, icon: 'el-icon-user', color: '#4f8cf7', soft: '#edf4ff' },
        { label: '已入住客房', value: '21', unit: '间', trend: 11, icon: 'el-icon-house', color: '#45b8ac', soft: '#eaf9f7' },
        { label: '已签合同', value: '8', unit: '份', trend: -3.4, icon: 'el-icon-document-checked', color: '#f5ba35', soft: '#fff8e6' }
      ],
      roomStats: [{ label: '房间总数', value: 36, color: '#cdd5df' }, { label: '在住', value: 21, color: '#45b8ac' }, { label: '预订', value: 9, color: '#6f8ff7' }, { label: '空房', value: 2, color: '#dfe7ee' }, { label: '预退房', value: 1, color: '#f5ba35' }],
      rooms: Array.from({ length: 18 }, (_, i) => ({ no: `${3 + Math.floor(i / 6)}0${i % 6 + 1}`, status: ['occupied', 'occupied', 'reserved', 'cleaning', 'empty'][i % 5], label: ['在住', '在住', '预订', '待清洁', '空闲'][i % 5] })),
      todos: [{ label: '收款审批', note: '合同及卡项收款', value: 748, icon: 'el-icon-bank-card', color: '#B8945A', soft: '#FBF3E5' }, { label: '退款审批', note: '客户退款申请', value: 2, icon: 'el-icon-refresh-left', color: '#f5ba35', soft: '#fff8e6' }, { label: '采购单审批', note: '仓库采购计划', value: 0, icon: 'el-icon-shopping-cart-full', color: '#4f8cf7', soft: '#edf4ff' }, { label: '行政 OA 审批', note: '请假、用车及报修', value: 0, icon: 'el-icon-office-building', color: '#45b8ac', soft: '#eaf9f7' }],
      warnings: [
        { title: '客户预警', total: 24, icon: 'el-icon-user-solid', color: '#45b8ac', items: [{ name: '新增客资', value: 3 }, { name: '预产期提醒', value: 4 }, { name: '妈妈生日', value: 16 }, { name: '宝宝生日', value: 1 }] },
        { title: '财务预警', total: 462, icon: 'el-icon-coin', color: '#dfaa27', items: [{ name: '合同欠款', value: 462 }, { name: '退款待审', value: 2 }, { name: '发票待开', value: 0 }] },
        { title: '客房预警', total: 8, icon: 'el-icon-house', color: '#7e79df', items: [{ name: '待入住', value: 2 }, { name: '退房提醒', value: 1 }, { name: '客房服务', value: 3 }, { name: '客户外出', value: 2 }] },
        { title: '服务预警', total: 272, icon: 'el-icon-first-aid-kit', color: '#B8945A', items: [{ name: '产康预约', value: 6 }, { name: '大于7天未耗卡', value: 266 }, { name: '查看医嘱', value: 0 }] }
      ],
      trendBars: [{ month: '1月', contract: 45, receipt: 35 }, { month: '2月', contract: 62, receipt: 50 }, { month: '3月', contract: 53, receipt: 58 }, { month: '4月', contract: 78, receipt: 61 }, { month: '5月', contract: 67, receipt: 64 }, { month: '6月', contract: 90, receipt: 73 }, { month: '7月', contract: 74, receipt: 69 }],
      sources: [{ label: '朋友推荐', percent: 36, color: '#B8945A' }, { label: '线上咨询', percent: 28, color: '#4f8cf7' }, { label: '到店咨询', percent: 18, color: '#45b8ac' }, { label: '渠道合作', percent: 12, color: '#f5ba35' }, { label: '其他来源', percent: 6, color: '#9aa6b4' }]
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-page{min-height:calc(100vh - 84px);padding:24px;background:#f4f6f9;color:#263445}.welcome-bar{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}.welcome-bar span{font-size:12px;color:#ff6f9c;font-weight:600}.welcome-bar h1{margin:5px 0;font-size:25px}.welcome-bar p{margin:0;color:#8a96a8;font-size:13px}.welcome-actions{display:flex;gap:8px}.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:16px}.summary-card{display:flex;align-items:center;padding:20px;background:#fff;border-radius:10px;box-shadow:0 2px 12px rgba(27,45,75,.055)}.summary-icon{display:grid;place-items:center;width:52px;height:52px;border-radius:14px;margin-right:15px;font-size:23px}.summary-card>div:last-child{display:flex;flex-direction:column}.summary-card span{color:#7c8898;font-size:13px}.summary-card b{font-size:25px;margin:5px 0;color:#263445}.summary-card b small{font-size:12px;margin-left:4px;color:#8d98a8}.summary-card em{font-style:normal;font-size:11px}.summary-card em.up{color:#32af7c}.summary-card em.down{color:#e86b6b}.panel{border:0;border-radius:10px;margin-bottom:16px;box-shadow:0 2px 12px rgba(27,45,75,.055)}.panel-head{display:flex;align-items:center;justify-content:space-between}.panel-head>div:first-child{display:flex;flex-direction:column;gap:4px}.panel-head b{color:#263445}.panel-head span{font-size:11px;color:#9ba5b2}.panel-head a{font-size:12px;color:#ff6f9c}.occupancy-panel,.todo-panel{min-height:400px}.occupancy-top{display:flex;align-items:center;gap:32px}.rate-ring{width:126px;height:126px;padding:11px;border-radius:50%;background:conic-gradient(#45b8ac 0 58.3%,#edf1f5 58.3%)}.rate-ring>div{width:100%;height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:#fff;border-radius:50%}.rate-ring b{font-size:23px}.rate-ring span{font-size:11px;color:#8d98a8}.room-stats{flex:1;display:grid;grid-template-columns:repeat(5,1fr)}.room-stats div{display:flex;flex-direction:column;align-items:center;border-left:1px solid #edf0f4}.room-stats i{width:9px;height:9px;border-radius:50%}.room-stats b{font-size:20px;margin:7px 0 3px}.room-stats span{font-size:11px;color:#8d98a8}.mini-room-grid{display:grid;grid-template-columns:repeat(9,1fr);gap:7px;margin-top:24px}.mini-room{padding:8px 4px;text-align:center;border-radius:6px;background:#f4f6f8;border-top:3px solid #dfe7ee}.mini-room b,.mini-room span{display:block}.mini-room b{font-size:12px}.mini-room span{font-size:9px;margin-top:4px;color:#8591a1}.mini-room.occupied{border-color:#45b8ac;background:#effaf8}.mini-room.reserved{border-color:#6f8ff7;background:#f2f4ff}.mini-room.cleaning{border-color:#f5ba35;background:#fff9eb}.todo-row{display:flex;align-items:center;padding:12px 0;border-bottom:1px solid #f0f2f5}.todo-icon{width:38px;height:38px;display:grid;place-items:center;border-radius:10px;margin-right:12px}.todo-row>div{flex:1;display:flex;flex-direction:column;gap:3px}.todo-row>div b{font-size:13px}.todo-row>div span{font-size:11px;color:#97a1af}.todo-row em{font-style:normal;font-weight:700;color:#ff6f9c}.all-todo{width:100%;margin-top:14px}.legend{display:flex!important;flex-direction:row!important;gap:14px!important}.legend i{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px}.legend i.high{background:#ff6f9c}.legend i.normal{background:#45b8ac}.warning-groups{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.warning-group{padding:16px;border:1px solid #edf0f4;border-radius:8px}.warning-title{display:flex;align-items:center;gap:8px;padding-bottom:13px;border-bottom:1px solid #f0f2f5}.warning-title span{flex:1;font-weight:600}.warning-items>div{display:flex;justify-content:space-between;padding-top:12px;font-size:12px;color:#788596}.warning-items b{color:#37455a}.trend-panel,.source-panel{min-height:390px}.trend-chart{height:280px;padding:20px 18px 25px 52px;display:flex;gap:18px;align-items:flex-end;position:relative;background:repeating-linear-gradient(to top,#f0f2f5 0,#f0f2f5 1px,transparent 1px,transparent 70px)}.chart-labels{position:absolute;left:8px;top:13px;bottom:20px;display:flex;flex-direction:column;justify-content:space-between;color:#a4aeba;font-size:10px}.trend-bar{flex:1;height:100%;display:flex;justify-content:flex-end;align-items:center;flex-direction:column}.bar-pair{height:92%;display:flex;align-items:flex-end;gap:5px}.bar-pair i{width:16px;background:linear-gradient(to top,#ff6f9c,#ffabc5);border-radius:4px 4px 0 0}.bar-pair i+ i{background:linear-gradient(to top,#4f8cf7,#9ebcff)}.trend-bar>span{margin-top:7px;color:#8a96a6;font-size:10px}.source-row{display:grid;grid-template-columns:78px 1fr 38px;align-items:center;gap:10px;padding:15px 0;font-size:12px}.source-row>span{color:#6f7b8b}.source-row>div{height:8px;background:#eef1f4;border-radius:4px;overflow:hidden}.source-row i{display:block;height:100%;border-radius:4px}.source-row b{text-align:right}.dashboard-footer{text-align:center;color:#9aa5b3;font-size:11px;padding:14px}.dashboard-footer span{margin-left:18px}@media(max-width:1100px){.summary-grid{grid-template-columns:repeat(2,1fr)}.warning-groups{grid-template-columns:repeat(2,1fr)}.mini-room-grid{grid-template-columns:repeat(6,1fr)}}@media(max-width:768px){.dashboard-page{padding:14px}.welcome-actions{display:none}.summary-grid{grid-template-columns:1fr}.warning-groups{grid-template-columns:1fr}.occupancy-top{align-items:flex-start}.room-stats{grid-template-columns:repeat(3,1fr);gap:10px}.mini-room-grid{grid-template-columns:repeat(3,1fr)}}
</style>
