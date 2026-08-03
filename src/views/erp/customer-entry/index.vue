<template>
  <div class="customer-entry-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">客户管理 · 新增客户档案</div>
        <h1>客户录入</h1>
        <p>客户资料分为 3 个信息分组，共 46 项可见资料，并支持来源、房间、套餐、介绍人与所属业务员联动选择。</p>
      </div>
      <div class="heading-actions">
        <el-button icon="el-icon-document" :loading="draftSaving" @click="handleSaveDraft">保存草稿</el-button>
        <el-button type="primary" icon="el-icon-check" :loading="submitting" @click="handleSubmit">保存客户</el-button>
      </div>
    </div>

    <el-alert
      class="source-alert"
      type="info"
      :closable="false"
      show-icon
      title="原系统规则：客户姓名、客户状态、客户来源必填；手机号与微信号二选一，状态为“同意签合同”时必须补录手机号。"
    />

    <div class="entry-layout">
      <main>
        <el-form ref="customerForm" v-loading="loading" :model="form" :rules="rules" label-width="112px" class="customer-form">
          <el-card id="customer-section" shadow="never" class="form-card">
            <div slot="header" class="section-heading">
              <div><span class="section-index">01</span><div><h2>客户信息</h2><p>身份识别、联系方式、来源与客户分级</p></div></div>
              <span>{{ sectionCompletion.customer.completed }}/{{ sectionCompletion.customer.total }} 已填写</span>
            </div>
            <el-row :gutter="22">
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="客户姓名" prop="name"><el-input v-model.trim="form.name" maxlength="30" show-word-limit placeholder="请输入客户姓名" /></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="客户电话" prop="mobile">
                  <el-input
                    v-model.trim="form.mobile"
                    :maxlength="mobileMaxLength"
                    :placeholder="mobilePlaceholder"
                    inputmode="numeric"
                    @input="handleMobileInput"
                    @blur="handleContactBlur"
                  >
                    <el-select slot="prepend" v-model="form.countryCode" class="country-select" @change="handleCountryCodeChange">
                      <el-option v-for="item in countryCodeOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                    <el-button slot="append" icon="el-icon-search" title="客户查重" @click="handleDuplicateCheck" />
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="QQ 或微信" prop="wechat"><el-input v-model.trim="form.wechat" maxlength="50" placeholder="与手机号二选一填写" @blur="handleContactBlur" /></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="客户状态" prop="status">
                  <el-select v-model="form.status" clearable placeholder="请选择客户状态" class="full-control" @change="handleStatusChange">
                    <el-option v-for="item in customerStatusOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="客户来源" prop="source">
                  <el-input v-model="form.source" readonly placeholder="点击选择客户来源" class="selector-input" @click.native="openSelector('source')">
                    <el-button slot="append" icon="el-icon-more" @click="openSelector('source')" />
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="会员卡号"><el-input v-model.trim="form.memberCard" maxlength="40" placeholder="可稍后绑定会员卡" /></el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="标签内容">
                  <div class="tag-selector">
                    <button v-for="tag in legacyCustomerTags" :key="tag" type="button" :class="{ active: form.tags.includes(tag) }" @click="toggleTag(tag)">
                      <i :class="form.tags.includes(tag) ? 'el-icon-check' : 'el-icon-plus'" />{{ tag }}
                    </button>
                    <small>标签可在“数据字典”中调整</small>
                  </div>
                </el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="是否到店"><el-switch v-model="form.isToStore" active-text="已到店" inactive-text="未到店" @change="handleToStoreChange" /></el-form-item>
              </el-col>
            </el-row>
          </el-card>

          <el-card id="intention-section" shadow="never" class="form-card">
            <div slot="header" class="section-heading">
              <div><span class="section-index intention">02</span><div><h2>意向信息</h2><p>预产期、预住安排、房间、套餐与意向金额</p></div></div>
              <span>{{ sectionCompletion.intention.completed }}/{{ sectionCompletion.intention.total }} 已填写</span>
            </div>
            <el-row :gutter="22">
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="意向分店"><el-select v-model="form.intendedStore" clearable placeholder="请选择" class="full-control" @change="handleIntendedStoreChange"><el-option v-for="item in stores" :key="item" :label="item" :value="item" /></el-select></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="客户预产期"><el-date-picker v-model="form.dueDate" type="date" value-format="yyyy-MM-dd" placeholder="选择预产期" class="full-control" @change="syncPlannedStayDate" /></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="意向天数"><el-input-number v-model="form.intendedDays" :min="1" :max="180" controls-position="right" class="full-control" @change="recalculateAmount" /></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="预住时间"><el-date-picker v-model="form.plannedStayDate" type="date" value-format="yyyy-MM-dd" placeholder="选择预住日期" class="full-control" /></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="意向房间">
                  <el-input v-model="form.room" readonly placeholder="选择可订房间" class="selector-input" @click.native="openSelector('room')"><el-button slot="append" icon="el-icon-office-building" @click.stop="openSelector('room')" /></el-input>
                </el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="意向房型"><el-select v-model="form.roomType" filterable clearable placeholder="请选择房型" class="full-control" @change="recalculateAmount"><el-option v-for="item in roomTypes" :key="item" :label="item" :value="item" /></el-select></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="合同金额"><el-input v-model.trim="form.contractAmount" maxlength="11" placeholder="请输入金额"><template slot="prepend">¥</template></el-input></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="意向套餐">
                  <el-input v-model="form.packageName" readonly placeholder="点击选择套餐" class="selector-input" @click.native="openSelector('package')"><el-button slot="append" icon="el-icon-goods" @click.stop="openSelector('package')" /></el-input>
                </el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="套餐金额"><el-input v-model.trim="form.packageAmount" maxlength="11" placeholder="选择套餐后自动带出"><template slot="prepend">¥</template></el-input></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="膳食套餐"><el-select v-model="form.mealPackage" clearable placeholder="请选择" class="full-control"><el-option v-for="item in mealPackages" :key="item" :label="item" :value="item" /></el-select></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="产康分店"><el-select v-model="form.recoveryStore" clearable placeholder="请选择" class="full-control"><el-option v-for="item in stores" :key="item" :label="item" :value="item" /></el-select></el-form-item>
              </el-col>
            </el-row>
            <div v-if="amountHint" class="amount-hint"><i class="el-icon-magic-stick" /><span>{{ amountHint }}</span><el-button type="text" @click="applyEstimatedAmount">采用估算金额</el-button></div>
          </el-card>

          <el-card id="detail-section" shadow="never" class="form-card">
            <div slot="header" class="section-heading">
              <div><span class="section-index detail">03</span><div><h2>详细信息</h2><p>证件、生产、介绍、业务归属及补充资料</p></div></div>
              <span>{{ sectionCompletion.detail.completed }}/{{ sectionCompletion.detail.total }} 已填写</span>
            </div>
            <el-row :gutter="22">
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="证件类别"><el-select v-model="form.documentType" class="full-control"><el-option v-for="item in documentTypes" :key="item" :label="item" :value="item" /></el-select></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="证件号" prop="documentNo"><el-input v-model.trim="form.documentNo" maxlength="30" placeholder="请输入证件号码" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="分娩方式"><el-select v-model="form.deliveryMethod" clearable placeholder="请选择" class="full-control"><el-option v-for="item in deliveryMethods" :key="item" :label="item" :value="item" /></el-select></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="客户性别"><el-radio-group v-model="form.sex"><el-radio-button label="女" /><el-radio-button label="男" /></el-radio-group></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="客户生日"><el-date-picker v-model="form.birthday" type="date" value-format="yyyy-MM-dd" placeholder="选择生日" class="full-control" @change="calculateAge" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="客户年龄"><el-input v-model="form.age" placeholder="根据生日自动计算"><template slot="append">岁</template></el-input></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="介绍人类型"><el-select v-model="form.introducerType" clearable placeholder="请选择" class="full-control" @change="handleIntroducerTypeChange"><el-option v-for="item in introducerTypes" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24">
                <el-form-item label="介绍人"><el-input v-model.trim="form.introducerName" :readonly="form.introducerType !== '自定义介绍'" :placeholder="form.introducerType ? '请选择或填写介绍人' : '先选择介绍人类型'" @click.native="handleIntroducerFocus"><el-button v-if="form.introducerType && form.introducerType !== '自定义介绍'" slot="append" icon="el-icon-user" @click.stop="openSelector('introducer')" /></el-input></el-form-item>
              </el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="介绍人电话"><el-input v-model.trim="form.introducerPhone" maxlength="20" placeholder="请输入介绍人电话" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="复查时间"><el-date-picker v-model="form.reviewDate" type="date" value-format="yyyy-MM-dd" placeholder="选择复查日期" class="full-control" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="陪护人"><el-input v-model.trim="form.companionName" maxlength="30" placeholder="请输入陪护人姓名" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="陪护人电话"><el-input v-model.trim="form.companionPhone" maxlength="20" placeholder="请输入陪护人电话" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="产检医院"><el-autocomplete v-model="form.prenatalHospital" :fetch-suggestions="queryHospitals" placeholder="请选择或输入医院" class="full-control" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="本次胎型"><el-select v-model="form.fetusType" class="full-control"><el-option v-for="item in fetusTypes" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="本次胎次"><el-select v-model="form.pregnancyCount" class="full-control"><el-option v-for="item in pregnancyCounts" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="客户区域"><el-input v-model="form.area" readonly placeholder="点击选择客户区域" @click.native="openSelector('area')"><el-button slot="append" icon="el-icon-location-outline" @click.stop="openSelector('area')" /></el-input></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="到店时间"><el-date-picker v-model="form.firstVisitAt" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" placeholder="选择到店时间" class="full-control" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="所属业务员" prop="trackerId"><el-input v-model="form.trackerName" readonly placeholder="点击选择所属业务员" @click.native="openSelector('tracker')"><el-button slot="append" icon="el-icon-user-solid" @click.stop="openSelector('tracker')" /></el-input></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="客户民族"><el-input v-model.trim="form.ethnicity" maxlength="20" placeholder="如：汉族" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="客户籍贯"><el-input v-model.trim="form.nativePlace" maxlength="50" placeholder="请输入籍贯" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="工作单位"><el-input v-model.trim="form.workUnit" maxlength="80" placeholder="请输入工作单位" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="客户职业"><el-input v-model.trim="form.occupation" maxlength="40" placeholder="请输入职业" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="电子邮箱" prop="email"><el-input v-model.trim="form.email" maxlength="80" placeholder="请输入电子邮箱" /></el-form-item></el-col>
              <el-col :lg="8" :md="12" :xs="24"><el-form-item label="录入时间"><el-input v-model="form.entryTime" disabled><i slot="prefix" class="el-icon-time" /></el-input></el-form-item></el-col>
              <el-col :span="24"><el-form-item label="现居住址"><el-input v-model.trim="form.address" type="textarea" :rows="2" maxlength="200" show-word-limit placeholder="请输入现居住址" /></el-form-item></el-col>
              <el-col :span="24"><el-form-item label="膳食备注"><el-input v-model.trim="form.dietNote" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="填写过敏原、忌口、宗教饮食、特殊医嘱等" /></el-form-item></el-col>
              <el-col :span="24"><el-form-item label="客户备注"><el-input v-model.trim="form.customerNote" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="填写客户诉求、沟通重点与其他补充信息" /></el-form-item></el-col>
            </el-row>
          </el-card>
        </el-form>

        <div class="form-footer">
          <div><i class="el-icon-lock" /><span>客户证件、电话等敏感信息按当前账号的数据范围保存</span></div>
          <el-button @click="handleReset">清空重填</el-button>
          <el-button :loading="draftSaving" @click="handleSaveDraft">保存草稿</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">保存客户</el-button>
        </div>
      </main>

      <aside>
        <el-card shadow="never" class="side-card progress-card">
          <div class="progress-head"><div><small>资料完整度</small><b>{{ completionRate }}%</b></div><el-progress type="circle" :percentage="completionRate" :width="76" :stroke-width="7" color="#B8945A" :show-text="false" /></div>
          <div v-for="section in progressSections" :key="section.key" class="progress-row" @click="scrollToSection(section.key)">
            <span><i :class="section.icon" />{{ section.label }}</span><b>{{ section.completed }}/{{ section.total }}</b>
          </div>
        </el-card>
        <el-card shadow="never" class="side-card check-card">
          <div slot="header" class="side-title"><span>保存前检查</span><el-tag size="mini" :type="requiredReady ? 'success' : 'warning'">{{ requiredReady ? '已就绪' : '待补充' }}</el-tag></div>
          <div v-for="item in requiredChecks" :key="item.label" class="check-row" :class="{ ready: item.ready }"><i :class="item.ready ? 'el-icon-circle-check' : 'el-icon-warning-outline'" /><span>{{ item.label }}</span></div>
          <el-button class="check-button" type="primary" plain icon="el-icon-search" :loading="duplicateChecking" @click="handleDuplicateCheck">检查重复客户</el-button>
          <div v-if="duplicateChecked" class="duplicate-state" :class="{ danger: duplicateRecords.length }"><i :class="duplicateRecords.length ? 'el-icon-warning' : 'el-icon-success'" />{{ duplicateRecords.length ? `发现 ${duplicateRecords.length} 条疑似重复记录` : '未发现重复客户' }}</div>
        </el-card>
        <el-card shadow="never" class="side-card trace-card">
          <div slot="header" class="side-title"><span>客户归属</span></div>
          <dl><dt>所属业务员</dt><dd>{{ form.trackerName || '未选择' }}</dd><dt>所属部门</dt><dd>{{ form.trackerDepartment || '—' }}</dd><dt>数据范围</dt><dd>本人及所属门店</dd><dt>草稿状态</dt><dd>{{ draftStatus }}</dd></dl>
        </el-card>
      </aside>
    </div>

    <el-dialog :title="selectorTitle" :visible.sync="selectorVisible" width="760px" append-to-body>
      <div class="selector-toolbar"><el-input v-model.trim="selectorKeyword" clearable prefix-icon="el-icon-search" :placeholder="`搜索${selectorTitle}`" /></div>
      <div v-if="selectorType === 'source'" class="source-grid">
        <button v-for="item in filteredSelectorOptions" :key="item.id" type="button" @click="selectOption(item)"><i class="el-icon-connection" /><b>{{ item.name }}</b><small>{{ item.group }}</small></button>
      </div>
      <el-table v-else :data="filteredSelectorOptions" highlight-current-row max-height="400" @row-dblclick="selectOption">
        <el-table-column prop="name" :label="selectorMainLabel" min-width="130" />
        <el-table-column v-if="selectorType === 'room'" prop="type" label="房型" min-width="140" />
        <el-table-column v-if="selectorType === 'room'" prop="store" label="门店" min-width="150" />
        <el-table-column v-if="selectorType === 'room'" prop="status" label="房态" width="90"><template slot-scope="scope"><el-tag size="mini" :type="scope.row.status === '可预订' ? 'success' : 'warning'">{{ scope.row.status }}</el-tag></template></el-table-column>
        <el-table-column v-if="selectorType === 'package'" prop="days" label="天数" width="80" />
        <el-table-column v-if="selectorType === 'package'" prop="amount" label="套餐金额" width="130"><template slot-scope="scope">¥ {{ formatAmount(scope.row.amount) }}</template></el-table-column>
        <el-table-column v-if="selectorType === 'package'" prop="store" label="适用门店" min-width="150" />
        <el-table-column v-if="selectorType === 'package'" prop="versionNo" label="版本" width="90" />
        <el-table-column v-if="selectorType === 'tracker'" prop="department" label="所属部门" min-width="130" />
        <el-table-column v-if="selectorType === 'tracker'" prop="store" label="门店" min-width="150" />
        <el-table-column v-if="selectorType === 'introducer'" prop="type" label="介绍人类型" width="120" />
        <el-table-column v-if="selectorType === 'introducer'" prop="mobile" label="联系电话" width="140" />
        <el-table-column label="操作" width="90" fixed="right"><template slot-scope="scope"><el-button type="text" @click="selectOption(scope.row)">选择</el-button></template></el-table-column>
      </el-table>
      <div v-if="selectorType !== 'source'" class="selector-tip">双击记录可快速选择；列表来自当前账号可访问的业务数据。</div>
    </el-dialog>

    <el-dialog title="客户查重结果" :visible.sync="duplicateDialogVisible" width="680px" append-to-body>
      <el-result v-if="!duplicateRecords.length" icon="success" title="未发现重复客户" sub-title="可继续保存当前客户资料" />
      <div v-else>
        <el-alert type="warning" :closable="false" show-icon title="发现疑似重复客户，请核对后再决定是否继续录入。" />
        <el-table :data="duplicateRecords" class="duplicate-table"><el-table-column prop="code" label="客户编号" width="140" /><el-table-column prop="name" label="客户姓名" /><el-table-column prop="mobile" label="联系电话" /><el-table-column prop="status" label="客户状态" /><el-table-column prop="trackerName" label="所属业务员" /></el-table>
      </div>
      <span slot="footer"><el-button @click="duplicateDialogVisible = false">关闭</el-button><el-button v-if="duplicateRecords.length" type="primary" @click="continueAfterDuplicate">确认继续录入</el-button></span>
    </el-dialog>

    <el-dialog title="客户保存成功" :visible.sync="successVisible" width="520px" append-to-body>
      <div class="success-content"><span><i class="el-icon-check" /></span><h2>客户档案已建立</h2><p>客户编号：<b>{{ submitResult.customerCode }}</b></p><p>当前状态：{{ submitResult.status }}</p></div>
      <span slot="footer"><el-button @click="successVisible = false">继续查看</el-button><el-button type="primary" @click="createAnother">继续录入下一位</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import {
  customerStatusOptions,
  countryCodeOptions,
  legacyCustomerTags,
  legacyCustomerSources,
  stores,
  roomTypes,
  mealPackages,
  documentTypes,
  deliveryMethods,
  introducerTypes,
  fetusTypes,
  pregnancyCounts,
  sectionFieldKeys,
  createEmptyCustomer
} from '@/config/customer-entry'
import { getCustomerEntryOptions, checkCustomerDuplicate, saveCustomerDraft, createCustomer } from '@/api/erp-customer'

const DRAFT_STORAGE_KEY = 'erp-customer-entry-draft'

export default {
  name: 'CustomerEntryPage',
  data() {
    const mobileValidator = (rule, value, callback) => {
      if (!this.form.mobile && !this.form.wechat) return callback(new Error('客户电话与 QQ/微信至少填写一项'))
      if (this.form.status === '同意签合同' && !this.form.mobile) return callback(new Error('同意签合同时必须填写客户电话'))
      if (this.form.mobile) {
        if (this.form.countryCode === '+86' && !/^1[3-9]\d{9}$/.test(this.form.mobile)) {
          return callback(new Error('请输入正确的中国大陆 11 位手机号'))
        }
        if (this.form.countryCode !== '+86' && !/^\d{6,15}$/.test(this.form.mobile)) {
          return callback(new Error('请输入 6—15 位数字联系电话'))
        }
      }
      callback()
    }
    return {
      customerStatusOptions,
      countryCodeOptions,
      legacyCustomerTags,
      stores,
      roomTypes,
      mealPackages,
      documentTypes,
      deliveryMethods,
      introducerTypes,
      fetusTypes,
      pregnancyCounts,
      loading: true,
      draftSaving: false,
      submitting: false,
      duplicateChecking: false,
      form: createEmptyCustomer(this.formatDateTime(new Date())),
      options: { sources: [], rooms: [], packages: [], trackers: [], introducers: [], areas: [], hospitals: [] },
      selectorVisible: false,
      selectorType: '',
      selectorKeyword: '',
      duplicateDialogVisible: false,
      duplicateChecked: false,
      duplicateRecords: [],
      allowDuplicate: false,
      successVisible: false,
      submitResult: {},
      draftId: '',
      lastDraftSavedAt: '',
      estimatedAmount: 0,
      rules: {
        name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
        mobile: [{ validator: mobileValidator, trigger: 'blur' }],
        status: [{ required: true, message: '请选择客户状态', trigger: 'change' }],
        source: [{ required: true, message: '请选择客户来源', trigger: 'change' }],
        trackerId: [{ required: true, message: '请选择所属业务员', trigger: 'change' }],
        documentNo: [{ pattern: /^[0-9A-Za-z()（）-]*$/, message: '证件号格式不正确', trigger: 'blur' }],
        email: [{ type: 'email', message: '电子邮箱格式不正确', trigger: 'blur' }]
      }
    }
  },
  computed: {
    mobileMaxLength() {
      return this.form.countryCode === '+86' ? 11 : 15
    },
    mobilePlaceholder() {
      return this.form.countryCode === '+86' ? '请输入 11 位手机号码' : '请输入 6—15 位数字联系电话'
    },
    sectionCompletion() {
      return Object.keys(sectionFieldKeys).reduce((result, key) => {
        const keys = sectionFieldKeys[key]
        result[key] = { total: keys.length, completed: keys.filter(field => this.hasValue(this.form[field])).length }
        return result
      }, {})
    },
    completionRate() {
      const values = Object.values(this.sectionCompletion)
      const total = values.reduce((sum, item) => sum + item.total, 0)
      const completed = values.reduce((sum, item) => sum + item.completed, 0)
      return Math.round(completed / total * 100)
    },
    progressSections() {
      return [
        { key: 'customer', label: '客户信息', icon: 'el-icon-user', ...this.sectionCompletion.customer },
        { key: 'intention', label: '意向信息', icon: 'el-icon-s-flag', ...this.sectionCompletion.intention },
        { key: 'detail', label: '详细信息', icon: 'el-icon-document', ...this.sectionCompletion.detail }
      ]
    },
    requiredChecks() {
      return [
        { label: '客户姓名', ready: Boolean(this.form.name) },
        { label: '电话或 QQ/微信', ready: Boolean(this.form.mobile || this.form.wechat) },
        { label: '客户状态', ready: Boolean(this.form.status) },
        { label: '客户来源', ready: Boolean(this.form.source) },
        { label: '所属业务员', ready: Boolean(this.form.trackerId) },
        { label: '签约状态已补手机号', ready: this.form.status !== '同意签合同' || Boolean(this.form.mobile) }
      ]
    },
    requiredReady() {
      return this.requiredChecks.every(item => item.ready)
    },
    draftStatus() {
      return this.lastDraftSavedAt ? `已保存 ${this.lastDraftSavedAt}` : '尚未保存'
    },
    selectorTitle() {
      return { source: '客户来源', room: '意向房间', package: '意向套餐', tracker: '所属业务员', introducer: '介绍人', area: '客户区域' }[this.selectorType] || '选择资料'
    },
    selectorMainLabel() {
      return { room: '房间号', package: '套餐名称', tracker: '姓名', introducer: '姓名', area: '区域名称' }[this.selectorType] || '名称'
    },
    selectorOptions() {
      const mapping = { source: 'sources', room: 'rooms', package: 'packages', tracker: 'trackers', introducer: 'introducers', area: 'areas' }
      let rows = this.options[mapping[this.selectorType]] || []
      if (this.selectorType === 'room' && this.form.intendedStore) rows = rows.filter(item => item.store === this.form.intendedStore)
      if (this.selectorType === 'package' && this.form.intendedStore && rows.some(item => item.store)) rows = rows.filter(item => item.store === this.form.intendedStore)
      if (this.selectorType === 'tracker' && this.form.intendedStore && rows.some(item => item.store)) rows = rows.filter(item => item.store === this.form.intendedStore)
      if (this.selectorType === 'introducer' && this.form.introducerType) rows = rows.filter(item => item.type === this.form.introducerType)
      return rows
    },
    filteredSelectorOptions() {
      if (!this.selectorKeyword) return this.selectorOptions
      const keyword = this.selectorKeyword.toLowerCase()
      return this.selectorOptions.filter(item => Object.values(item).some(value => String(value).toLowerCase().includes(keyword)))
    },
    amountHint() {
      return this.estimatedAmount ? `按已选房间日价 × ${this.form.intendedDays || 0} 天，估算合同金额 ¥ ${this.formatAmount(this.estimatedAmount)}` : ''
    }
  },
  created() {
    this.loadOptions()
    this.restoreDraft()
  },
  methods: {
    formatDateTime(date) {
      const pad = value => String(value).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
    },
    formatAmount(value) {
      return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    hasValue(value) {
      if (Array.isArray(value)) return value.length > 0
      if (typeof value === 'boolean') return value
      return value !== '' && value !== null && value !== undefined
    },
    async loadOptions() {
      this.loading = true
      try {
        const response = await getCustomerEntryOptions()
        this.options = {
          ...response.data,
          sources: legacyCustomerSources.map((name, index) => ({
            id: `legacy-source-${index + 1}`,
            name
          }))
        }
        if (this.form.source && !legacyCustomerSources.includes(this.form.source)) {
          this.form.source = ''
          this.form.sourceId = ''
        }
        const allowedStores = (response.data.stores || []).map(item => item.name)
        if (allowedStores.length) {
          if (!allowedStores.includes(this.form.intendedStore)) {
            this.form.intendedStore = allowedStores[0]
            this.form.room = ''
            this.form.roomId = ''
            this.form.roomType = ''
          }
          if (!allowedStores.includes(this.form.recoveryStore)) {
            this.form.recoveryStore = allowedStores[0]
          }
        }
      } finally {
        this.loading = false
      }
    },
    restoreDraft() {
      try {
        const stored = JSON.parse(localStorage.getItem(DRAFT_STORAGE_KEY) || 'null')
        if (!stored || !stored.form) return
        this.form = { ...createEmptyCustomer(this.formatDateTime(new Date())), ...stored.form, entryTime: stored.form.entryTime || this.formatDateTime(new Date()) }
        this.draftId = stored.draftId || ''
        this.lastDraftSavedAt = stored.savedAt || ''
        this.$nextTick(() => this.$message.info('已自动恢复上次未提交的客户草稿'))
      } catch (error) {
        localStorage.removeItem(DRAFT_STORAGE_KEY)
      }
    },
    toggleTag(tag) {
      const index = this.form.tags.indexOf(tag)
      if (index > -1) this.form.tags.splice(index, 1)
      else this.form.tags.push(tag)
    },
    handleStatusChange() {
      this.$refs.customerForm.validateField('mobile')
    },
    handleMobileInput(value) {
      const normalized = String(value || '').replace(/\D/g, '').slice(0, this.mobileMaxLength)
      if (normalized !== this.form.mobile) this.form.mobile = normalized
      this.duplicateChecked = false
      this.allowDuplicate = false
    },
    handleCountryCodeChange() {
      this.handleMobileInput(this.form.mobile)
      this.$nextTick(() => this.$refs.customerForm.validateField('mobile'))
    },
    handleContactBlur() {
      this.$refs.customerForm.validateField('mobile')
      if ((this.form.mobile && this.form.mobile.length >= 7) || this.form.wechat) this.runDuplicateCheck(false)
    },
    handleToStoreChange(value) {
      if (value && !this.form.firstVisitAt) this.form.firstVisitAt = this.formatDateTime(new Date())
    },
    handleIntendedStoreChange() {
      Object.assign(this.form, {
        room: '',
        roomId: '',
        roomType: '',
        roomTypeId: '',
        packageName: '',
        packageId: '',
        packageVersionId: '',
        packagePriceRuleId: '',
        packageAmount: '',
        trackerName: '',
        trackerId: '',
        trackerDepartment: ''
      })
      this.estimatedAmount = 0
      this.$nextTick(() => this.$refs.customerForm.validateField('trackerId'))
    },
    syncPlannedStayDate(value) {
      if (value && !this.form.plannedStayDate) this.form.plannedStayDate = value
    },
    calculateAge(value) {
      if (!value) {
        this.form.age = ''
        return
      }
      const birthday = new Date(`${value}T00:00:00`)
      const today = new Date()
      let age = today.getFullYear() - birthday.getFullYear()
      const monthDiff = today.getMonth() - birthday.getMonth()
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthday.getDate())) age--
      this.form.age = age >= 0 ? age : ''
    },
    handleIntroducerTypeChange() {
      this.form.introducerName = ''
      this.form.introducerId = ''
      this.form.introducerPhone = ''
    },
    handleIntroducerFocus() {
      if (this.form.introducerType && this.form.introducerType !== '自定义介绍') this.openSelector('introducer')
    },
    queryHospitals(query, callback) {
      const rows = this.options.hospitals.filter(item => !query || item.includes(query)).map(value => ({ value }))
      callback(rows)
    },
    openSelector(type) {
      if (type === 'introducer' && !this.form.introducerType) {
        this.$message.warning('请先选择介绍人类型')
        return
      }
      this.selectorType = type
      this.selectorKeyword = ''
      this.selectorVisible = true
    },
    selectOption(item) {
      if (this.selectorType === 'source') Object.assign(this.form, { source: item.name, sourceId: item.id })
      if (this.selectorType === 'room') {
        Object.assign(this.form, { room: item.name, roomId: item.id, roomType: item.type })
        this.recalculateAmount()
      }
      if (this.selectorType === 'package') {
        Object.assign(this.form, {
          packageName: item.name,
          packageId: item.id,
          packageVersionId: item.packageVersionId || '',
          packagePriceRuleId: item.packagePriceRuleId || '',
          packageAmount: String(item.amount),
          intendedDays: item.days,
          roomType: item.roomType,
          roomTypeId: item.roomTypeId || ''
        })
        if (!this.form.contractAmount) this.form.contractAmount = String(item.amount)
      }
      if (this.selectorType === 'tracker') {
        Object.assign(this.form, { trackerName: item.name, trackerId: item.id, trackerDepartment: item.department })
        this.$nextTick(() => this.$refs.customerForm.validateField('trackerId'))
      }
      if (this.selectorType === 'introducer') Object.assign(this.form, { introducerName: item.name, introducerId: item.id, introducerPhone: item.mobile })
      if (this.selectorType === 'area') Object.assign(this.form, { area: item.name, areaId: item.id })
      this.selectorVisible = false
      if (this.selectorType === 'source') this.$nextTick(() => this.$refs.customerForm.validateField('source'))
    },
    recalculateAmount() {
      const selectedRoom = this.options.rooms.find(item => item.id === this.form.roomId)
      this.estimatedAmount = selectedRoom && this.form.intendedDays ? selectedRoom.dailyPrice * this.form.intendedDays : 0
    },
    applyEstimatedAmount() {
      this.form.contractAmount = String(this.estimatedAmount)
      this.$message.success('已采用房间日价估算金额')
    },
    handleDuplicateCheck() {
      this.runDuplicateCheck(true)
    },
    async runDuplicateCheck(showDialog) {
      if (!this.form.mobile && !this.form.wechat) {
        if (showDialog) this.$message.warning('请先填写客户电话或 QQ/微信')
        return
      }
      this.duplicateChecking = true
      try {
        const response = await checkCustomerDuplicate({ mobile: this.form.mobile, wechat: this.form.wechat, name: this.form.name })
        this.duplicateRecords = response.data.records || []
        this.duplicateChecked = true
        this.allowDuplicate = !this.duplicateRecords.length
        if (showDialog || this.duplicateRecords.length) this.duplicateDialogVisible = true
      } catch (error) {
        this.duplicateChecked = false
        this.allowDuplicate = false
      } finally {
        this.duplicateChecking = false
      }
    },
    continueAfterDuplicate() {
      this.allowDuplicate = true
      this.duplicateDialogVisible = false
      this.$message.warning('已标记为人工确认继续录入')
    },
    async handleSaveDraft() {
      this.draftSaving = true
      try {
        const response = await saveCustomerDraft({ ...this.form, draftId: this.draftId })
        this.draftId = response.data.draftId
        this.lastDraftSavedAt = response.data.savedAt
        localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({ form: this.form, draftId: this.draftId, savedAt: this.lastDraftSavedAt }))
        this.$message.success('客户草稿已保存')
      } finally {
        this.draftSaving = false
      }
    },
    handleSubmit() {
      this.$refs.customerForm.validate(async valid => {
        if (!valid) {
          this.$message.error('请先补齐红色标记的必填资料')
          this.scrollToSection('customer')
          return
        }
        if (!this.duplicateChecked) await this.runDuplicateCheck(false)
        if (this.duplicateRecords.length && !this.allowDuplicate) {
          this.duplicateDialogVisible = true
          return
        }
        await this.submitCustomer()
      })
    },
    async submitCustomer() {
      this.submitting = true
      try {
        const response = await createCustomer({ ...this.form, draftId: this.draftId, duplicateConfirmed: this.allowDuplicate })
        this.submitResult = response.data
        localStorage.removeItem(DRAFT_STORAGE_KEY)
        this.lastDraftSavedAt = ''
        this.successVisible = true
      } finally {
        this.submitting = false
      }
    },
    createAnother() {
      this.successVisible = false
      this.resetFormState()
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    handleReset() {
      this.$confirm('将清空当前页面已填写的全部客户资料，是否继续？', '清空确认', { type: 'warning' }).then(() => {
        this.resetFormState()
        localStorage.removeItem(DRAFT_STORAGE_KEY)
      }).catch(() => {})
    },
    resetFormState() {
      this.form = createEmptyCustomer(this.formatDateTime(new Date()))
      this.draftId = ''
      this.lastDraftSavedAt = ''
      this.duplicateChecked = false
      this.duplicateRecords = []
      this.allowDuplicate = false
      this.estimatedAmount = 0
      this.$nextTick(() => this.$refs.customerForm.clearValidate())
    },
    scrollToSection(key) {
      const target = document.getElementById(`${key}-section`)
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
}
</script>

<style lang="scss" scoped>
.customer-entry-page { min-height:calc(100vh - 84px); padding:24px; background:#f4f6f9; color:#253247; }
.page-heading { display:flex; align-items:center; justify-content:space-between; gap:20px; margin-bottom:18px; }
.page-heading h1 { margin:5px 0 7px; font-size:25px; color:#1f2d3d; }
.page-heading p { margin:0; max-width:850px; color:#8a96a8; font-size:13px; line-height:1.6; }
.eyebrow { color:#8c6a36; font-size:12px; font-weight:700; letter-spacing:1px; }
.heading-actions { display:flex; gap:8px; flex-shrink:0; }
.source-alert { margin-bottom:16px; border:1px solid #dbeafe; background:#f7fbff; }
.entry-layout { display:grid; grid-template-columns:minmax(0,1fr) 260px; gap:16px; align-items:start; }
.form-card,.side-card { border:0; border-radius:10px; margin-bottom:16px; box-shadow:0 2px 12px rgba(27,45,75,.055); }
.form-card { scroll-margin-top:80px; }
.section-heading,.section-heading>div { display:flex; align-items:center; }
.section-heading { justify-content:space-between; }
.section-heading>div { gap:12px; }
.section-heading h2 { margin:0 0 4px; color:#263445; font-size:16px; }
.section-heading p { margin:0; color:#9aa5b4; font-size:12px; font-weight:400; }
.section-heading>span { color:#9aa5b4; font-size:12px; }
.section-index { width:38px; height:38px; display:grid; place-items:center; border-radius:10px; color:#fff; background:linear-gradient(135deg,#d9bf8b,#8c6a36); font-size:12px; font-weight:700; box-shadow:0 8px 16px -12px rgba(111,84,43,.8); }
.section-index.intention { background:linear-gradient(135deg,#c9aa70,#80602f); }
.section-index.detail { background:linear-gradient(135deg,#b99a62,#6f542b); }
.customer-form ::v-deep .el-form-item { margin-bottom:21px; }
.customer-form ::v-deep .el-form-item__label { color:#5d6979; font-size:13px; }
.customer-form ::v-deep .el-input__inner,.customer-form ::v-deep .el-textarea__inner { border-color:#dfe5ec; }
.customer-form ::v-deep .el-input__inner:focus,.customer-form ::v-deep .el-textarea__inner:focus { border-color:#b8945a; box-shadow:0 0 0 2px rgba(184,148,90,.1); }
.full-control { width:100%; }
.country-select { width:128px; }
.customer-form ::v-deep .country-select .el-input__inner { padding-left:12px; padding-right:26px; }
.selector-input ::v-deep .el-input__inner { cursor:pointer; background:#fbfcfe; }
.tag-selector { display:flex; flex-wrap:wrap; align-items:center; gap:8px; min-height:40px; }
.tag-selector button { padding:7px 12px; border:1px solid #dfe5ec; border-radius:16px; color:#687588; background:#fff; cursor:pointer; transition:.2s; }
.tag-selector button:hover { border-color:#c9aa70; color:#8c6a36; background:#fbf8f1; }
.tag-selector button.active { border-color:#ffb0c9; color:#ef5484; background:#fff0f5; }
.tag-selector button i { margin-right:4px; }
.tag-selector small { margin-left:4px; color:#a0a9b7; }
.amount-hint { display:flex; align-items:center; gap:9px; padding:10px 14px; border-radius:7px; color:#68758a; background:#f5f8ff; font-size:12px; }
.amount-hint>i { color:#5d8df5; font-size:16px; }.amount-hint .el-button { margin-left:auto; }
.form-footer { position:sticky; z-index:5; bottom:0; display:flex; align-items:center; justify-content:flex-end; gap:9px; padding:14px 18px; border-radius:10px 10px 0 0; background:rgba(255,255,255,.96); box-shadow:0 -4px 20px rgba(37,50,71,.08); backdrop-filter:blur(8px); }
.form-footer>div { display:flex; align-items:center; gap:7px; margin-right:auto; color:#8c97a7; font-size:12px; }.form-footer>div i { color:#45b8ac; }
aside { position:sticky; top:76px; }
.progress-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:17px; }
.progress-head>div { display:flex; flex-direction:column; }.progress-head small { color:#8f9aaa; }.progress-head b { margin-top:5px; font-size:30px; color:#263445; }
.progress-row { display:flex; align-items:center; justify-content:space-between; padding:11px 0; border-top:1px solid #f0f2f5; cursor:pointer; font-size:13px; }
.progress-row span { color:#647185; }.progress-row span i { width:24px; color:#8794a7; }.progress-row b { color:#405066; }
.side-title { display:flex; align-items:center; justify-content:space-between; font-weight:700; }
.check-row { display:flex; align-items:center; gap:8px; padding:7px 0; color:#9aa4b2; font-size:13px; }.check-row i { color:#f3ad3d; }.check-row.ready { color:#526074; }.check-row.ready i { color:#40b497; }
.check-button { width:100%; margin-top:12px; }
.duplicate-state { margin-top:10px; padding:8px; border-radius:6px; color:#29977f; background:#effaf7; font-size:12px; text-align:center; }.duplicate-state.danger { color:#dc6a3b; background:#fff5ee; }
.trace-card dl { display:grid; grid-template-columns:75px 1fr; gap:12px 6px; margin:0; font-size:12px; }.trace-card dt { color:#9aa5b4; }.trace-card dd { margin:0; color:#526074; text-align:right; word-break:break-word; }
.selector-toolbar { margin-bottom:15px; }.selector-toolbar .el-input { width:320px; }
.source-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; }
.source-grid button { display:flex; flex-direction:column; align-items:flex-start; min-height:88px; padding:14px; border:1px solid #e7dfd2; border-radius:8px; background:#fffdf9; cursor:pointer; text-align:left; transition:.2s; }.source-grid button:hover { border-color:#c9aa70; box-shadow:0 7px 18px rgba(111,84,43,.12); transform:translateY(-1px); }.source-grid i { color:#b8945a; font-size:17px; }.source-grid b { margin:8px 0 4px; color:#344157; }.source-grid small { color:#98a3b2; }
.selector-tip { margin-top:10px; color:#9ca6b4; font-size:12px; }
.duplicate-table { margin-top:15px; }
.success-content { padding:6px 0 14px; text-align:center; }.success-content>span { display:grid; place-items:center; width:64px; height:64px; margin:0 auto 15px; border-radius:50%; color:#fff; background:linear-gradient(135deg,#5bd2b6,#31ad90); font-size:30px; }.success-content h2 { margin:0 0 13px; color:#2f3d51; }.success-content p { margin:7px 0; color:#7e8998; }.success-content p b { color:#8c6a36; }
@media (max-width:1200px) { .entry-layout { grid-template-columns:1fr; } aside { position:static; display:grid; grid-template-columns:repeat(3,1fr); gap:16px; } .side-card { margin-bottom:0; } }
@media (max-width:768px) { .customer-entry-page { padding:14px; } .page-heading { align-items:flex-start; flex-direction:column; } .heading-actions { width:100%; }.heading-actions .el-button { flex:1; } aside { grid-template-columns:1fr; }.form-footer>div { display:none; }.source-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
</style>
