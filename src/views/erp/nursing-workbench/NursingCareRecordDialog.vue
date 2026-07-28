<template>
  <el-dialog
    :title="dialogTitle"
    :visible.sync="innerVisible"
    width="1180px"
    top="3vh"
    append-to-body
    :close-on-click-modal="false"
  >
    <div class="context-grid">
      <div><span>房间号：</span><b>{{ client.room || '—' }}</b></div>
      <div><span>客户姓名：</span><b>{{ client.customerName || '—' }}</b></div>
      <template v-if="recordType === 'mother'">
        <div><span>分娩方式：</span><b>{{ client.delivery || '—' }}</b></div>
        <div><span>入住时间：</span><b>{{ client.checkInAt || '—' }}</b></div>
        <div><span>入住天数：</span><b>{{ client.stayDays || '—' }}</b></div>
        <div><span>离开时间：</span><b>{{ client.checkOutAt || '—' }}</b></div>
        <div><span>护理类型：</span><b>{{ client.careType || '—' }}</b></div>
        <div><span>客户备注：</span><b>{{ client.customerRemark || '—' }}</b></div>
        <div><span>风险评估：</span><b>{{ client.riskAssessment || '—' }}</b></div>
        <div><span>宝宝姓名：</span><b>{{ primaryBaby.name || '无' }}</b></div>
        <div><span>宝宝性别：</span><b>{{ primaryBaby.gender || '—' }}</b></div>
        <div><span>出生天数：</span><b>{{ primaryBaby.ageDays || 0 }}天</b></div>
        <div><span>宝宝生日：</span><b>{{ primaryBaby.birthDate || '—' }}</b></div>
        <div><span>护理注意：</span><b>{{ client.careNotice || '—' }}</b></div>
      </template>
      <template v-else>
        <div><span>宝宝姓名：</span><b>{{ primaryBaby.name || '—' }}</b></div>
        <div><span>宝宝性别：</span><b>{{ primaryBaby.gender || '—' }}</b></div>
        <div><span>出生日期：</span><b>{{ primaryBaby.birthDate || '—' }}</b></div>
        <div><span>宝宝日龄：</span><b>{{ primaryBaby.ageDays || 0 }}天</b></div>
      </template>
    </div>

    <el-alert
      title="当前为脱敏演示表单，保存不会写入原妈妈宝盒 ERP。"
      type="warning"
      :closable="false"
      show-icon
      class="demo-alert"
    />

    <template v-if="recordType === 'mother'">
      <section v-for="group in maternalGroups" :key="group.title" class="form-section">
        <h3>{{ group.title }}</h3>
        <el-form label-width="126px" size="small">
          <el-row :gutter="14">
            <el-col v-for="field in group.fields" :key="field.key" :span="field.span || 8">
              <el-form-item :label="field.label">
                <el-input
                  v-if="field.type === 'input'"
                  v-model="form[field.key]"
                  :disabled="field.disabled"
                  :placeholder="field.placeholder || ''"
                >
                  <template v-if="field.unit" slot="append">{{ field.unit }}</template>
                </el-input>
                <el-select
                  v-else-if="field.type === 'select'"
                  v-model="form[field.key]"
                  class="full-control"
                  clearable
                >
                  <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
                </el-select>
                <el-date-picker
                  v-else-if="field.type === 'date'"
                  v-model="form[field.key]"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm"
                  class="full-control"
                />
                <el-checkbox-group
                  v-else-if="field.type === 'checkboxGroup'"
                  v-model="form[field.key]"
                  class="checkbox-grid"
                >
                  <el-checkbox v-for="option in field.options" :key="option" :label="option" />
                </el-checkbox-group>
                <el-input
                  v-else-if="field.type === 'textarea'"
                  v-model="form[field.key]"
                  type="textarea"
                  :rows="field.rows || 3"
                />
                <el-upload
                  v-else-if="field.type === 'upload'"
                  action="#"
                  :auto-upload="false"
                  :file-list="fileList"
                  :on-change="handleFileChange"
                >
                  <el-button size="small" icon="el-icon-upload2">选择文件</el-button>
                </el-upload>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </section>
    </template>

    <template v-else>
      <section class="form-section">
        <h3>宝宝护理记录表</h3>
        <el-form label-width="126px" size="small">
          <el-row :gutter="14">
            <el-col v-for="field in babyRecordFields" :key="field.key" :span="field.span || 8">
              <el-form-item :label="field.label">
                <el-input v-if="field.type === 'input'" v-model="form[field.key]">
                  <template v-if="field.unit" slot="append">{{ field.unit }}</template>
                </el-input>
                <el-select v-else-if="field.type === 'select'" v-model="form[field.key]" class="full-control" clearable>
                  <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
                </el-select>
                <el-date-picker
                  v-else-if="field.type === 'date'"
                  v-model="form[field.key]"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm"
                  class="full-control"
                />
                <el-checkbox-group
                  v-else-if="field.type === 'checkboxGroup'"
                  v-model="form[field.key]"
                  class="checkbox-grid"
                >
                  <el-checkbox v-for="option in field.options" :key="option" :label="option" />
                </el-checkbox-group>
                <el-input v-else v-model="form[field.key]" type="textarea" :rows="3" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </section>

      <el-tabs v-model="activeBabyTab" type="border-card" class="baby-tabs">
        <el-tab-pane v-for="group in babyGroups" :key="group.key" :label="group.title" :name="group.key">
          <el-form label-width="132px" size="small">
            <el-row :gutter="14">
              <el-col v-for="field in group.fields" :key="field.key" :span="field.span || 8">
                <el-form-item :label="field.label">
                  <el-input v-if="field.type === 'input'" v-model="form[field.key]">
                    <template v-if="field.unit" slot="append">{{ field.unit }}</template>
                  </el-input>
                  <el-select v-else-if="field.type === 'select'" v-model="form[field.key]" class="full-control" clearable>
                    <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
                  </el-select>
                  <el-date-picker
                    v-else-if="field.type === 'date'"
                    v-model="form[field.key]"
                    type="datetime"
                    value-format="yyyy-MM-dd HH:mm"
                    class="full-control"
                  />
                  <el-checkbox-group
                    v-else-if="field.type === 'checkboxGroup'"
                    v-model="form[field.key]"
                    class="checkbox-grid"
                  >
                    <el-checkbox v-for="option in field.options" :key="option" :label="option" />
                  </el-checkbox-group>
                  <el-upload
                    v-else-if="field.type === 'upload'"
                    action="#"
                    :auto-upload="false"
                    :file-list="fileList"
                    :on-change="handleFileChange"
                  >
                    <el-button size="small" icon="el-icon-upload2">选择文件</el-button>
                  </el-upload>
                  <el-input v-else v-model="form[field.key]" type="textarea" :rows="3" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </template>

    <div slot="footer">
      <el-button type="primary" @click="save">保存</el-button>
      <el-button @click="innerVisible = false">关闭</el-button>
    </div>
  </el-dialog>
</template>

<script>
const input = (key, label, unit = '', span = 8) => ({ key, label, type: 'input', unit, span })
const select = (key, label, options, span = 8) => ({ key, label, type: 'select', options, span })
const date = (key, label, span = 8) => ({ key, label, type: 'date', span })
const textarea = (key, label, span = 24) => ({ key, label, type: 'textarea', span })
const checks = (key, label, options, span = 24) => ({ key, label, type: 'checkboxGroup', options, span })
const upload = (key, label, span = 24) => ({ key, label, type: 'upload', span })

const maternalGroups = [
  {
    title: '异常情况与记录信息',
    fields: [
      checks('motherRisk', '异常情况：', ['异常', '危险'], 8),
      textarea('motherRiskDetail', '异常详情：', 16),
      input('motherDutyStaff', '值班人员：'),
      input('motherReminder', '提醒人员：'),
      input('motherReminderHours', '默认提醒：', '小时后'),
      date('motherRecordedAt', '记录日期：'),
      input('postpartumDays', '产后天数：', '天')
    ]
  },
  {
    title: '体征信息',
    fields: [
      input('motherTemperature', '体温：', '℃'),
      input('motherWeight', '体重：', 'kg'),
      input('motherPulse', '脉搏：', '次/分'),
      input('motherBloodPressure', '血压：', 'mmHg'),
      input('motherRespiration', '呼吸：'),
      input('motherHeartRate', '心率：')
    ]
  },
  {
    title: '护理信息',
    fields: [
      select('milkAmount', '乳汁(奶量)：', ['无', '多', '偏少', '适中', '充足']),
      select('leftNipple', '左乳头：', ['无', '凹', '凸', '平']),
      select('rightNipple', '右乳头：', ['无', '凹', '凸', '平']),
      select('breastPain', '红肿胀痛：', ['无', '左乳', '右乳', '都有']),
      select('breastLump', '乳房是否肿块：', ['否', '是', '左乳', '右乳']),
      input('breastCondition', '乳房情况：'),
      select('lochiaColor', '恶露颜色：', ['无', '红', '淡红', '白', '褐红']),
      select('lochiaAmount', '恶露量：', ['无', '多', '少', '正常', '不正常']),
      select('uterineFundus', '子宫底位置：', ['脐上1指', '平脐', '脐下1指', '脐下2指', '脐下3指', '脐下4指']),
      select('perineum', '会阴：', ['无', '正常', '侧切', '感染', '撕裂', '渗血', '渗液', '脓性分泌物']),
      select('abdominalIncision', '腹部切口：', ['无', '有', '正常', '渗血', '渗液']),
      select('stool', '大便：', ['正常', '异常', '黑便']),
      input('stoolTimes', '大便次数：', '次'),
      select('emotion', '情绪反应：', ['轻松愉快', '平和', '郁闷哭泣', '紧张焦虑']),
      checks('waterContact', '沾水情况：', ['有自行泡脚', '有自行洗头', '有自行沐浴', '有无']),
      checks('careMeasures', '护理措施：', ['会阴擦洗', '会阴湿热敷', '红外线照射伤口', '母乳喂养指导', '产后运动方法指导'])
    ]
  },
  {
    title: '护理补充',
    fields: [
      textarea('allergyHistory', '既往史/过敏史：', 12),
      textarea('motherRemark', '备注：', 12),
      input('perinealWoundCare', '会阴伤口护理：'),
      input('abdominalWoundCare', '腹部伤口护理：'),
      input('treatmentContent', '处理内容：'),
      input('medicineRecord', '药物服用记录：'),
      input('motherTest', '测试：'),
      select('skinType', '肤质：', ['干性', '油性']),
      upload('motherAttachment', '附件：')
    ]
  }
]

const babyRecordFields = [
  checks('babyRisk', '异常情况：', ['异常', '危险'], 8),
  textarea('babyRiskDetail', '异常详情：', 16),
  date('babyRecordedAt', '记录日期：'),
  select('babyShift', '班次：', ['早班', '中班', '晚班', '全班']),
  input('babyDutyStaff', '值班人员：'),
  input('babyReminder', '提醒人员：'),
  input('babyReminderHours', '默认提醒：', '小时后'),
  textarea('babyRemark', '备注：', 16)
]

const babyGroups = [
  {
    key: 'vitals',
    title: '体征记录',
    fields: [
      input('babyTemperature', '宝宝体温：', '℃'), date('babyTemperatureAt', '体温测量时间：'),
      input('babyWeight', '宝宝体重：', 'g'), date('babyWeightAt', '体重测量时间：'),
      input('babyHeadCircumference', '宝宝头围：', 'cm'), date('babyHeadAt', '头围测量时间：'),
      input('babyHeartRate', '宝宝心跳：', '次/分'), date('babyHeartAt', '心跳测量时间：'),
      input('babyJaundice', '宝宝黄疸：', 'mg/dl'), date('babyJaundiceAt', '黄疸测量时间：'),
      input('babyHeight', '宝宝身高：', 'cm'), date('babyHeightAt', '身高测量时间：'),
      input('babyChest', '宝宝胸围：', 'cm'), date('babyChestAt', '胸围测量时间：'),
      input('babyRespiration', '呼吸频率：'), date('babyRespirationAt', '呼吸测量时间：'),
      select('babyVoice', '宝宝声音：', ['响亮', '低沉', '嘶哑', '尖叫']),
      select('babySkinColor', '宝宝肤色：', ['黄', '粉红', '粉黄', '异常'])
    ]
  },
  {
    key: 'feeding',
    title: '宝宝进食',
    fields: [
      select('feedingMode', '进食方式：', ['母乳喂养', '人工喂养', '混合喂养']),
      input('breastMilk', '母乳量：', 'ml'), input('formulaMilk', '牛奶量：', 'ml'), input('waterAmount', '进水量：', 'ml'),
      select('suckingStrength', '吸吞力：', ['强', '中', '弱']),
      input('feedingDuration', '进食时长：', '分钟'), input('feedingTimes', '进食次数：', '次'),
      input('leftBreast', '哺乳左：'), input('rightBreast', '哺乳右：'), date('feedingAt', '进食时间：')
    ]
  },
  {
    key: 'diaper',
    title: '更换尿布',
    fields: [
      select('urination', '小便：', ['有', '无', '多', '少']), input('urinationTimes', '小便次数：', '次'),
      input('stoolColor', '大便颜色：'), input('stoolTexture', '大便性状：'),
      input('stoolAmount', '大便量：'), input('babyStoolTimes', '大便次数：', '次')
    ]
  },
  {
    key: 'bath',
    title: '洗澡游泳',
    fields: [
      date('bathAt', '洗澡时间：'), input('bathDuration', '洗澡时长：', '分钟'),
      date('swimmingAt', '游泳时间：'), input('swimmingDuration', '游泳时长：', '分钟'),
      date('touchAt', '抚摸时间：'), input('touchDuration', '抚摸时长：', '分钟'),
      checks('dailyCare', '日常护理：', ['眼睛护理', '口腔护理', '鼻腔护理', '脖子腋下', '耳朵护理', '剪指甲', '被动操']),
      input('earlyEducation', '早教：')
    ]
  },
  {
    key: 'medicine',
    title: '宝宝用药',
    fields: [
      select('medicineAt', '用药时间：', ['早', '中', '晚', '睡前', '餐前', '餐后']),
      input('medicineName', '药名：'), input('medicineAmount', '用量：'),
      input('milkInterval', '间隔奶时间：', '小时'), input('medicineWater', '用水冲服：'),
      input('trusteeshipTime', '托管时间：')
    ]
  },
  {
    key: 'handover',
    title: '护理交接',
    fields: [
      select('handoverShift', '接班班次：', ['早班', '中班', '晚班', '全班']), input('handoverStaff', '接班人员：'),
      checks('umbilicalStatus', '脐部护理状态：', ['正常', '分泌物', '血痂', '粘液', '脓性', '脱落', '湿', '干', '渗液', '渗血']),
      input('umbilicalTimes', '脐部护理次数：', '次'),
      checks('hipStatus', '臀部护理状态：', ['臀部正常', '红臀', '臀部红肿', '臀部破皮外搽药膏', '红疹']),
      textarea('umbilicalRemark', '脐部备注：', 12), textarea('hipRemark', '臀部备注：', 12),
      date('sunBathAt', '日光浴时间：'), input('sunBathDuration', '日光浴时长：', '分钟'),
      select('abdomen', '腹部：', ['柔软', '腹胀']), input('eyeSecretion', '眼部分泌物：'),
      input('rash', '红疹：'), input('spitMilk', '吐奶：'), input('overflowMilk', '溢奶：'),
      input('vomiting', '呕吐：'), input('thrush', '鹅口疮：'),
      select('spirit', '精神：', ['好', '一般', '差']), input('otherCondition', '其他：'),
      select('careOrderLevel', '护嘱等级：', ['1', '2', '3', '4', '5']),
      textarea('careOrderContent', '护嘱内容：'), input('leftEye', '左眼：'), input('rightEye', '右眼：'),
      upload('babyAttachment', '附件：')
    ]
  }
]

export default {
  name: 'NursingCareRecordDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    recordType: {
      type: String,
      default: 'mother'
    },
    client: {
      type: Object,
      default: () => ({})
    },
    baby: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      form: {},
      fileList: [],
      activeBabyTab: 'vitals',
      maternalGroups,
      babyRecordFields,
      babyGroups
    }
  },
  computed: {
    innerVisible: {
      get() {
        return this.visible
      },
      set(value) {
        this.$emit('update:visible', value)
      }
    },
    dialogTitle() {
      return this.recordType === 'mother' ? '新增新妈妈护理记录' : '宝宝护理记录表'
    },
    primaryBaby() {
      return this.baby.id ? this.baby : (this.client.babies && this.client.babies[0]) || {}
    }
  },
  watch: {
    visible(value) {
      if (value) this.resetForm()
    }
  },
  methods: {
    resetForm() {
      const groups = this.recordType === 'mother'
        ? this.maternalGroups
        : [{ fields: this.babyRecordFields }, ...this.babyGroups]
      const next = {}
      groups.forEach(group => {
        group.fields.forEach(field => {
          next[field.key] = field.type === 'checkboxGroup' ? [] : ''
        })
      })
      this.form = next
      this.fileList = []
      this.activeBabyTab = 'vitals'
    },
    handleFileChange(file, fileList) {
      this.fileList = fileList.slice(-5)
    },
    save() {
      this.$message.success(`${this.dialogTitle}已保存为脱敏演示记录`)
      this.innerVisible = false
    }
  }
}
</script>

<style lang="scss" scoped>
.context-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px 16px;
  padding: 12px 16px;
  border: 1px solid #e6eaf0;
  border-radius: 5px;
  background: #f8fafc;
  font-size: 13px;
}
.context-grid span { color: #7c8796; }
.context-grid b { color: #344257; font-weight: 500; }
.demo-alert { margin: 14px 0; }
.form-section { margin-top: 14px; padding: 0 16px 3px; border: 1px solid #e7ebf0; border-radius: 6px; }
.form-section h3 { margin: 0 -16px 14px; padding: 10px 15px; border-bottom: 1px solid #e7ebf0; color: #47566a; background: #f7f9fb; font-size: 14px; }
.form-section ::v-deep .el-form-item { margin-bottom: 14px; }
.form-section ::v-deep .el-form-item__label, .baby-tabs ::v-deep .el-form-item__label { color: #5d6c7f; font-size: 12px; }
.full-control { width: 100%; }
.checkbox-grid { display: flex; flex-wrap: wrap; gap: 3px 14px; min-height: 32px; align-items: center; }
.checkbox-grid ::v-deep .el-checkbox { margin-right: 0; }
.baby-tabs { margin-top: 14px; }
.baby-tabs ::v-deep .el-form-item { margin-bottom: 14px; }
@media (max-width: 900px) {
  .context-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
