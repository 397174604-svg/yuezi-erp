<template>
  <el-dialog
    :title="dialogTitle"
    :visible.sync="innerVisible"
    width="980px"
    top="4vh"
    append-to-body
    :close-on-click-modal="false"
    custom-class="nursing-toolbar-dialog"
  >
    <el-alert
      title="当前为脱敏交互演示，确定操作不会写入原妈妈宝盒 ERP。"
      type="warning"
      :closable="false"
      show-icon
      class="mock-tip"
    />

    <template v-if="isPlanForm">
      <el-form label-width="126px" size="small">
        <el-row :gutter="14">
          <el-col v-if="action === '添加'" :span="12">
            <el-form-item label="选择客户：" required>
              <el-input v-model="form.customerName" readonly>
                <el-button slot="append" @click="pickerVisible = true">选择</el-button>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col v-for="field in planRoleFields" :key="field.key" :span="12">
            <el-form-item :label="field.label">
              <el-input v-model="form[field.key]" readonly>
                <el-button slot="append" @click="selectDemoStaff(field.key)">选择</el-button>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注："><el-input v-model="form.remark" type="textarea" :rows="3" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="产妇出院诊断："><el-input v-model="form.diagnosis" type="textarea" :rows="3" /></el-form-item>
          </el-col>
          <el-col :span="12"><el-form-item label="制单人："><el-input value="admin（演示）" readonly /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="制单日期："><el-input value="2026-07-24" readonly /></el-form-item></el-col>
        </el-row>
      </el-form>
    </template>

    <template v-else-if="action === '设置' && pageTitle === '护理计划'">
      <el-tabs v-model="settingTab" type="border-card">
        <el-tab-pane v-for="tab in settingTabs" :key="tab" :label="tab" :name="tab">
          <el-table :data="projectRows" border size="mini" highlight-current-row @current-change="settingProject = $event">
            <el-table-column type="index" label="序号" width="55" />
            <el-table-column prop="projectName" label="项目名称" min-width="150" />
            <el-table-column prop="projectType" label="项目类型" min-width="100" />
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="remaining" label="剩余次数" width="90" />
            <el-table-column prop="validDays" label="有效天数" width="90" />
            <el-table-column prop="startDate" label="开始日期" width="110" />
            <el-table-column prop="remainingDays" label="剩余天数" width="90" />
            <el-table-column label="操作" width="80"><template><el-button type="text" size="mini">修改</el-button></template></el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <el-form label-width="105px" size="small" class="setting-form">
        <el-row :gutter="14">
          <el-col :span="12"><el-form-item label="项目名称："><el-input :value="settingProject ? settingProject.projectName : ''" readonly /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="开始日期："><el-date-picker v-model="form.startDate" type="date" value-format="yyyy-MM-dd" class="full-control" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="有效天数："><el-input-number v-model="form.validDays" :min="0" class="full-control" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="次数："><el-input-number v-model="form.quantity" :min="0" class="full-control" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注："><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
    </template>

    <template v-else-if="action === '月嫂分配'">
      <el-form label-width="118px" size="small">
        <el-row :gutter="14">
          <el-col :span="12"><el-form-item label="选择客户：" required><el-input :value="row.customerName || '演示客户'" readonly /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="服务分店：" required><el-select v-model="form.store" class="full-control"><el-option v-for="item in stores" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="选择护理师：" required><el-input v-model="form.matronName" readonly><el-button slot="append" @click="form.matronName = '演示护理师01'">选择</el-button></el-input></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="联系方式：" required><el-input v-model="form.phone" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="服务类型：" required><el-checkbox-group v-model="form.serviceTypes"><el-checkbox label="会所入住" /><el-checkbox label="到家服务" /><el-checkbox label="医院陪护" /></el-checkbox-group></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="服务形式：" required><el-select v-model="form.serviceForm" class="full-control"><el-option v-for="item in ['请选择', '8', '10', '12', '24']" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="执业类型：" required><el-select v-model="form.practiceType" class="full-control"><el-option v-for="item in ['月嫂', '育儿嫂', '催乳师', '小儿推拿师', '导乐师']" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="服务时间：" required><el-date-picker v-model="form.serviceStart" type="datetime" value-format="yyyy-MM-dd HH:00" class="full-control" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="到" required><el-date-picker v-model="form.serviceEnd" type="datetime" value-format="yyyy-MM-dd HH:00" class="full-control" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="服务天数：" required><el-input-number v-model="form.serviceDays" :min="1" class="full-control" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注说明："><el-input v-model="form.remark" type="textarea" :rows="3" /></el-form-item></el-col>
        </el-row>
      </el-form>
    </template>

    <template v-else-if="action === '移动'">
      <div class="move-layout">
        <section>
          <h3>当前护理计划项目</h3>
          <el-checkbox-group v-model="form.moveProjects">
            <el-checkbox v-for="item in moveProjects" :key="item" :label="item" />
          </el-checkbox-group>
        </section>
        <div class="move-arrow"><i class="el-icon-right" /></div>
        <section>
          <h3>项目移动的目标框</h3>
          <el-radio-group v-model="form.moveTarget">
            <el-radio v-for="item in moveTargets" :key="item" :label="item">{{ item }}</el-radio>
          </el-radio-group>
        </section>
      </div>
    </template>

    <template v-else>
      <el-form label-width="128px" size="small">
        <el-row :gutter="14">
          <el-col v-for="field in genericFields" :key="field.key" :span="field.span || 12">
            <el-form-item :label="field.label" :required="field.required">
              <el-input v-if="field.type === 'input'" v-model="form[field.key]" />
              <el-input v-else-if="field.type === 'textarea'" v-model="form[field.key]" type="textarea" :rows="3" />
              <el-select v-else-if="field.type === 'select'" v-model="form[field.key]" class="full-control">
                <el-option v-for="item in field.options" :key="item" :label="item" :value="item" />
              </el-select>
              <el-date-picker v-else-if="field.type === 'date'" v-model="form[field.key]" type="datetime" value-format="yyyy-MM-dd HH:mm" class="full-control" />
              <el-checkbox v-else-if="field.type === 'checkbox'" v-model="form[field.key]">{{ field.text }}</el-checkbox>
              <el-upload v-else-if="field.type === 'upload'" action="#" :auto-upload="false"><el-button size="small">选择文件</el-button></el-upload>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </template>

    <el-dialog title="选择现有客户" :visible.sync="pickerVisible" width="720px" append-to-body>
      <el-form :inline="true" size="small">
        <el-form-item label="客户名称："><el-input /></el-form-item>
        <el-form-item label="手机号码："><el-input /></el-form-item>
        <el-form-item label="房间号："><el-input /></el-form-item>
        <el-button size="small" type="primary">搜 索</el-button>
      </el-form>
      <el-table :data="customerRows" border size="mini" highlight-current-row @current-change="selectedCustomer = $event">
        <el-table-column type="index" label="序号" width="55" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column prop="room" label="房间号" />
        <el-table-column prop="status" label="客户状态" />
      </el-table>
      <div slot="footer">
        <el-button @click="pickerVisible = false">取消</el-button>
        <el-button type="primary" @click="chooseCustomer">确 定</el-button>
      </div>
    </el-dialog>

    <div slot="footer">
      <el-button @click="innerVisible = false">关闭</el-button>
      <el-button type="primary" @click="save">确定</el-button>
    </div>
  </el-dialog>
</template>

<script>
const stores = ['中心广场旗舰店', '黄河路轻奢店']

const pageFields = {
  护理部排班第二版: [
    { key: 'employee', label: '护理人员：', type: 'input', required: true },
    { key: 'shiftDate', label: '排班日期：', type: 'date', required: true },
    { key: 'shift', label: '班次：', type: 'select', options: ['白班', '休班', '晚班', '行政班'], required: true },
    { key: 'store', label: '门店：', type: 'select', options: stores, required: true },
    { key: 'remark', label: '备注：', type: 'textarea', span: 24 }
  ],
  宝宝档案: [
    { key: 'customerName', label: '选择客户：', type: 'input', required: true },
    { key: 'babyName', label: '宝宝姓名：', type: 'input', required: true },
    { key: 'gender', label: '宝宝性别：', type: 'select', options: ['男', '女'] },
    { key: 'birthAt', label: '出生日期：', type: 'date' },
    { key: 'gestation', label: '怀孕周期：', type: 'input' },
    { key: 'deliveryMode', label: '分娩方式：', type: 'select', options: ['顺产', '剖宫产', '小月子'] },
    { key: 'birthWeight', label: '出生体重：', type: 'input' },
    { key: 'remark', label: '备注：', type: 'textarea', span: 24 }
  ],
  健康评估: [
    { key: 'customerName', label: '客户姓名：', type: 'input', required: true },
    { key: 'babyName', label: '宝宝姓名：', type: 'input' },
    { key: 'assessmentAt', label: '评估时间：', type: 'date', required: true },
    { key: 'assessor', label: '评估人员：', type: 'input', required: true },
    { key: 'risk', label: '评估结果：', type: 'select', options: ['正常', '异常', '危险'] },
    { key: 'content', label: '评估内容：', type: 'textarea', span: 24 },
    { key: 'guidance', label: '指导建议：', type: 'textarea', span: 24 }
  ],
  膳食评估: [
    { key: 'customerName', label: '客户姓名：', type: 'input', required: true },
    { key: 'room', label: '房间号：', type: 'input' },
    { key: 'assessmentAt', label: '评估时间：', type: 'date', required: true },
    { key: 'dietType', label: '膳食类型：', type: 'input' },
    { key: 'taboo', label: '饮食禁忌：', type: 'textarea', span: 24 },
    { key: 'goal', label: '营养目标：', type: 'textarea', span: 24 }
  ],
  自定义查房: [
    { key: 'customerName', label: '客户姓名：', type: 'input', required: true },
    { key: 'room', label: '房间号：', type: 'input' },
    { key: 'roundType', label: '查房类型：', type: 'input' },
    { key: 'roundAt', label: '查房时间：', type: 'date' },
    { key: 'rounder', label: '查房人员：', type: 'input' },
    { key: 'content', label: '查房情况：', type: 'textarea', span: 24 },
    { key: 'reply', label: '护士回复：', type: 'textarea', span: 24 }
  ],
  医生查房记录: [
    { key: 'customerName', label: '客户姓名：', type: 'input', required: true },
    { key: 'babyName', label: '宝宝姓名：', type: 'input' },
    { key: 'department', label: '科别：', type: 'select', options: ['妇科', '儿科', '客房管家查房'] },
    { key: 'roundAt', label: '查房时间：', type: 'date' },
    { key: 'doctor', label: '查房人姓名：', type: 'input' },
    { key: 'general', label: '一般情况：', type: 'textarea', span: 24 },
    { key: 'handling', label: '处理情况：', type: 'textarea', span: 24 },
    { key: 'reply', label: '护士回复：', type: 'textarea', span: 24 }
  ],
  膳食禁忌查房: [
    { key: 'customerName', label: '客户姓名：', type: 'input', required: true },
    { key: 'room', label: '房间号：', type: 'input' },
    { key: 'roundAt', label: '查房时间：', type: 'date' },
    { key: 'taboo', label: '饮食禁忌：', type: 'textarea', span: 24 },
    { key: 'finding', label: '查房发现：', type: 'textarea', span: 24 },
    { key: 'adjustment', label: '调整建议：', type: 'textarea', span: 24 }
  ],
  护理项目记录: [
    { key: 'customerName', label: '客户姓名：', type: 'input' },
    { key: 'projectName', label: '项目名称：', type: 'input', required: true },
    { key: 'serviceAt', label: '服务时间：', type: 'date' },
    { key: 'nurse', label: '执行人员：', type: 'input' },
    { key: 'count', label: '完成次数：', type: 'input' },
    { key: 'result', label: '执行结果：', type: 'textarea', span: 24 }
  ],
  妈妈护理记录: [
    { key: 'recordAt', label: '记录日期：', type: 'date' },
    { key: 'postpartumDays', label: '产后天数：', type: 'input' },
    { key: 'temperature', label: '体温(C°)：', type: 'input' },
    { key: 'weight', label: '体重(kg)：', type: 'input' },
    { key: 'pulse', label: '脉搏(次/分)：', type: 'input' },
    { key: 'bloodPressure', label: '血压(mmHg)：', type: 'input' },
    { key: 'content', label: '护理记录：', type: 'textarea', span: 24 },
    { key: 'attachment', label: '附件：', type: 'upload', span: 24 }
  ],
  宝宝护理记录: [
    { key: 'recordAt', label: '记录日期：', type: 'date' },
    { key: 'babyName', label: '宝宝姓名：', type: 'input' },
    { key: 'temperature', label: '体温(C°)：', type: 'input' },
    { key: 'weight', label: '体重(kg)：', type: 'input' },
    { key: 'feeding', label: '宝宝进食：', type: 'textarea', span: 24 },
    { key: 'diaper', label: '更换尿布：', type: 'textarea', span: 24 },
    { key: 'bath', label: '洗澡游泳：', type: 'textarea', span: 24 },
    { key: 'medication', label: '宝宝用药：', type: 'textarea', span: 24 }
  ],
  护理部排班表: [
    { key: 'employee', label: '护理人员：', type: 'input', required: true },
    { key: 'shiftAt', label: '排班日期：', type: 'date' },
    { key: 'shift', label: '班次：', type: 'select', options: ['白班', '休班', '晚班', '行政班'] },
    { key: 'area', label: '负责区域：', type: 'input' },
    { key: 'roomRange', label: '负责房间：', type: 'input' },
    { key: 'remark', label: '备注：', type: 'textarea', span: 24 }
  ],
  入住物品交接: [
    { key: 'customerName', label: '客户姓名：', type: 'input', required: true },
    { key: 'room', label: '房间号：', type: 'input' },
    { key: 'handoverAt', label: '交接日期：', type: 'date' },
    { key: 'items', label: '交接物品：', type: 'textarea', span: 24 },
    { key: 'staff', label: '交接人员：', type: 'input' },
    { key: 'customerConfirm', label: '客户确认：', type: 'checkbox', text: '客户已确认签收' },
    { key: 'remark', label: '备注：', type: 'textarea', span: 24 }
  ]
}

export default {
  name: 'NursingToolbarDialog',
  props: {
    visible: { type: Boolean, default: false },
    pageTitle: { type: String, default: '' },
    action: { type: String, default: '' },
    row: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      stores,
      form: {},
      pickerVisible: false,
      selectedCustomer: null,
      settingTab: '套餐内服务',
      settingTabs: ['套餐内服务', '套餐外服务', '额外购买', '项目卡', '储值卡'],
      settingProject: null,
      projectRows: [
        { projectName: '母婴基础护理（演示）', projectType: '护理服务', quantity: 10, remaining: 8, validDays: 28, startDate: '2026-07-18', remainingDays: 22 },
        { projectName: '产后舒缓护理（演示）', projectType: '产康服务', quantity: 6, remaining: 5, validDays: 28, startDate: '2026-07-18', remainingDays: 22 }
      ],
      moveProjects: ['妈妈护理项目', '宝宝护理项目', '产后康复项目', '膳食服务项目'],
      moveTargets: ['护理计划框A', '护理计划框B', '护理计划框C'],
      customerRows: [
        { name: '演示客户01', phone: '138****0000', room: 'A301', status: '已入住' },
        { name: '演示客户02', phone: '139****0000', room: 'A306', status: '已入住' }
      ],
      planRoleFields: [
        { key: 'nursingDirector', label: '护理总监：' },
        { key: 'nursingManager', label: '护理主任：' },
        { key: 'housekeeper', label: '生活管家：' },
        { key: 'gyneDoctor', label: '妇科保健医：' },
        { key: 'pediatricDoctor', label: '儿科保健医：' },
        { key: 'rehabNurse', label: '产后康复：' },
        { key: 'headNurse', label: '责任护士(长)：' },
        { key: 'feedingSpecialist', label: '母婴喂养师：' },
        { key: 'nutritionist', label: '营 养 师：' },
        { key: 'nurseTeam', label: '护士组成员：' },
        { key: 'roomTeam', label: '客房组成员：' }
      ]
    }
  },
  computed: {
    innerVisible: {
      get() { return this.visible },
      set(value) { this.$emit('update:visible', value) }
    },
    isPlanForm() {
      return this.pageTitle === '护理计划' && ['添加', '编辑'].includes(this.action)
    },
    dialogTitle() {
      if (this.pageTitle === '护理计划' && this.action === '添加') return '新增护理计划单'
      if (this.pageTitle === '护理计划' && this.action === '编辑') return '护理计划单修改'
      if (this.pageTitle === '护理计划' && this.action === '设置') return '设置有效期'
      if (this.pageTitle === '护理计划' && this.action === '月嫂分配') return '新增月嫂服务记录'
      if (this.pageTitle === '护理计划' && this.action === '移动') return '调整护理计划'
      return `${this.action}${this.pageTitle}`
    },
    genericFields() {
      if (this.action === '护士回复') {
        return [
          { key: 'replyAt', label: '回复日期：', type: 'date', required: true },
          { key: 'reply', label: '护士回复：', type: 'textarea', span: 24, required: true }
        ]
      }
      if (this.action === '确认签收') {
        return [
          { key: 'customerName', label: '客户姓名：', type: 'input' },
          { key: 'signedAt', label: '签收时间：', type: 'date', required: true },
          { key: 'signer', label: '签收人：', type: 'input', required: true },
          { key: 'customerConfirm', label: '客户确认：', type: 'checkbox', text: '确认已收到全部物品' }
        ]
      }
      return pageFields[this.pageTitle] || [
        { key: 'name', label: '名称：', type: 'input', required: true },
        { key: 'remark', label: '备注：', type: 'textarea', span: 24 }
      ]
    }
  },
  watch: {
    visible(value) {
      if (value) this.reset()
    }
  },
  methods: {
    reset() {
      const next = {
        customerName: this.row.customerName || '',
        room: this.row.room || '',
        store: this.row.store || stores[0],
        serviceTypes: [],
        serviceForm: '请选择',
        practiceType: '月嫂',
        serviceDays: 1,
        validDays: 28,
        quantity: 1,
        moveProjects: [],
        moveTarget: '',
        remark: ''
      }
      this.planRoleFields.forEach(field => { next[field.key] = this.row[field.key] || '' })
      this.form = next
      this.settingProject = null
    },
    selectDemoStaff(key) {
      this.$set(this.form, key, '演示员工01')
    },
    chooseCustomer() {
      if (!this.selectedCustomer) {
        this.$message.warning('请至少选择一条记录！')
        return
      }
      this.$set(this.form, 'customerName', this.selectedCustomer.name)
      this.pickerVisible = false
    },
    save() {
      if (this.action === '移动') {
        if (!this.form.moveProjects.length) return this.$message.warning('请选择要移动的项目')
        if (!this.form.moveTarget) return this.$message.warning('请选择项目移动的目标框')
      }
      if (this.action === '月嫂分配') {
        if (!this.form.matronName) return this.$message.warning('请选择护理师！')
        if (!this.form.serviceTypes.length) return this.$message.warning('请选择服务类型！')
      }
      this.$emit('saved', { action: this.action, form: { ...this.form }})
      this.innerVisible = false
    }
  }
}
</script>

<style lang="scss">
.nursing-toolbar-dialog > .el-dialog__body {
  max-height: 74vh;
  overflow: auto;
}
.nursing-toolbar-dialog .mock-tip {
  margin-bottom: 14px;
}
.nursing-toolbar-dialog .full-control {
  width: 100%;
}
.nursing-toolbar-dialog .setting-form {
  margin-top: 14px;
  padding: 14px 14px 0;
  border: 1px solid #e3e8ed;
  background: #f8fafc;
}
.move-layout {
  display: grid;
  grid-template-columns: 1fr 60px 1fr;
  gap: 12px;
}
.move-layout section {
  min-height: 260px;
  padding: 16px;
  border: 1px solid #dfe4e9;
  background: #fafbfc;
}
.move-layout h3 {
  margin: 0 0 14px;
  font-size: 15px;
}
.move-layout .el-checkbox-group,
.move-layout .el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.move-arrow {
  display: grid;
  place-items: center;
  color: #7698b8;
  font-size: 28px;
}
</style>
