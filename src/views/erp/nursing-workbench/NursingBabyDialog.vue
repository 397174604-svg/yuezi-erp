<template>
  <el-dialog
    title="新增宝宝信息"
    :visible.sync="innerVisible"
    width="760px"
    top="7vh"
    append-to-body
    :close-on-click-modal="false"
  >
    <el-alert
      title="如果新增的宝宝与即将签署的合同宝宝一致，请先录入合同后再录入宝宝信息；否则将会有两个宝宝信息，需要删除一个。"
      type="warning"
      :closable="false"
      show-icon
      class="baby-tip"
    />

    <el-form label-width="110px" size="small">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="选择客户：">
            <el-input :value="client.customerName" readonly />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="宝宝姓名：" required>
            <el-input v-model.trim="form.babyName" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="宝宝性别：">
            <el-select v-model="form.gender" class="full-control">
              <el-option label="男" value="男" />
              <el-option label="女" value="女" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="出生日期：">
            <el-date-picker
              v-model="form.birthDate"
              type="datetime"
              value-format="yyyy-MM-dd HH:mm"
              class="full-control"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="怀孕周期：">
            <div class="gestation-row">
              <el-input v-model="form.gestationalWeek"><template slot="append">周</template></el-input>
              <el-input v-model="form.gestationalDay"><template slot="append">天</template></el-input>
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="分娩方式：">
            <el-select v-model="form.deliveryMode" class="full-control">
              <el-option v-for="option in deliveryOptions" :key="option" :label="option" :value="option" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="分娩医院：">
            <el-select v-model="form.hospital" class="full-control">
              <el-option v-for="option in hospitalOptions" :key="option" :label="option" :value="option" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col v-if="form.hospital === '-其他-'" :span="12">
          <el-form-item label="其他医院：">
            <el-input v-model.trim="form.otherHospital" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="宝宝身高：">
            <el-input v-model="form.height"><template slot="append">cm</template></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="宝宝体重：">
            <el-input v-model="form.weight"><template slot="append">kg</template></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="过敏史：">
            <el-input v-model.trim="form.allergyHistory" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="备注：">
            <el-input v-model.trim="form.remark" type="textarea" :rows="3" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="出院诊断：">
            <el-input v-model.trim="form.dischargeDiagnosis" type="textarea" :rows="3" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <div slot="footer">
      <el-button type="primary" @click="save">保存</el-button>
      <el-button @click="innerVisible = false">关闭</el-button>
    </div>
  </el-dialog>
</template>

<script>
const DELIVERY_OPTIONS = ['顺产分娩', '剖宫产分娩', '小月子', '未生产']
const HOSPITAL_OPTIONS = [
  '-其他-', '濮阳市妇幼保健院', '濮阳市人民医院', '濮阳市油田总医院', '濮阳市中医院',
  '濮阳市第三人民医院', '濮阳县人民医院', '濮阳县第二人民医院', '濮阳县妇幼保健院'
]

export default {
  name: 'NursingBabyDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    client: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      deliveryOptions: DELIVERY_OPTIONS,
      hospitalOptions: HOSPITAL_OPTIONS,
      form: this.emptyForm()
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
    }
  },
  watch: {
    visible(value) {
      if (value) this.form = this.emptyForm()
    }
  },
  methods: {
    emptyForm() {
      return {
        babyName: '',
        gender: '男',
        birthDate: '',
        gestationalWeek: '',
        gestationalDay: '',
        deliveryMode: '顺产分娩',
        hospital: '-其他-',
        otherHospital: '',
        height: '',
        weight: '',
        allergyHistory: '',
        remark: '',
        dischargeDiagnosis: ''
      }
    },
    save() {
      if (!this.form.babyName) {
        this.$message.warning('请填写宝宝姓名')
        return
      }
      this.$emit('saved', { ...this.form })
      this.innerVisible = false
    }
  }
}
</script>

<style lang="scss" scoped>
.baby-tip { margin-bottom: 18px; }
.full-control { width: 100%; }
.gestation-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.demo-note { margin: 0; color: #9a6e45; font-size: 12px; text-align: right; }
</style>
