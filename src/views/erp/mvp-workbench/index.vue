<template>
  <div v-loading="loading" class="mvp-page">
    <div class="page-heading">
      <div>
        <h2>客户签约与入住中心</h2>
        <p>统一办理客户建档、合同审核、收款审核、订房与入住，业务状态自动衔接。</p>
      </div>
      <div class="heading-actions">
        <el-button size="small" icon="el-icon-bank-card" @click="$router.push('/mvp/assets')">会员资产</el-button>
        <el-button size="small" icon="el-icon-refresh" :loading="loading" @click="loadAll">刷新数据</el-button>
      </div>
    </div>

    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      :closable="false"
      show-icon
      class="load-error"
    />

    <div class="summary-row">
      <div v-for="item in visibleSummaryCards" :key="item.key" class="summary-card">
        <div class="summary-label">{{ item.label }}</div>
        <div class="summary-value">{{ summaryOverview[item.key] || 0 }}</div>
      </div>
    </div>

    <el-alert
      title="请按“客户建档 → 合同审核 → 收款审核 → 订房入住”的顺序办理"
      type="warning"
      :closable="false"
      show-icon
    />

    <el-steps :active="workflowActive" finish-status="success" simple class="workflow-steps">
      <el-step title="客户建档" />
      <el-step title="合同审核" />
      <el-step title="收款审核" />
      <el-step title="订房入住" />
    </el-steps>

    <el-tabs v-model="activeTab" class="business-tabs">
      <el-tab-pane v-if="hasPermission('CUSTOMER.VIEW')" label="1 客户建档" name="customers">
        <el-form
          v-if="hasPermission('CUSTOMER.CREATE')"
          ref="customerForm"
          :model="customerForm"
          :rules="customerRules"
          label-width="92px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="customerForm.storeId" filterable>
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="客户姓名" prop="name">
                <el-input v-model.trim="customerForm.name" maxlength="50" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="手机号" prop="phone">
                <el-input v-model.trim="customerForm.phone" maxlength="11" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="微信号">
                <el-input v-model.trim="customerForm.wechat" maxlength="80" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="客户阶段" prop="stage">
                <el-select v-model="customerForm.stage">
                  <el-option v-for="stage in customerStages" :key="stage" :label="stage" :value="stage" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="意向等级" prop="intentLevel">
                <el-select v-model="customerForm.intentLevel" placeholder="请选择意向等级">
                  <el-option
                    v-for="item in intentLevels"
                    :key="item.value"
                    :label="`${item.value} · ${item.label}`"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="客户来源" prop="source">
                <el-select
                  v-model="customerForm.source"
                  filterable
                  allow-create
                  default-first-option
                  placeholder="请选择或输入来源"
                >
                  <el-option v-for="source in customerSources" :key="source" :label="source" :value="source" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="业务员" prop="salesStaffId">
                <el-select v-model="customerForm.salesStaffId" clearable filterable>
                  <el-option
                    v-for="staff in customerStaff"
                    :key="staff.id"
                    :label="`${staff.name}（${staff.department || staff.position || '员工'}）`"
                    :value="staff.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="客户类型" prop="customerType">
                <el-select v-model="customerForm.customerType" placeholder="请选择客户类型">
                  <el-option v-for="item in customerTypes" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item v-if="customerForm.customerType === '孕期待产'" key="edc" label="预产期" prop="edc">
                <el-date-picker
                  v-model="customerForm.edc"
                  type="date"
                  value-format="yyyy-MM-dd"
                  :picker-options="futureDateOptions"
                />
              </el-form-item>
              <el-form-item v-else-if="customerForm.customerType === '已分娩'" key="deliveryDate" label="分娩日期" prop="deliveryDate">
                <el-date-picker
                  v-model="customerForm.deliveryDate"
                  type="date"
                  value-format="yyyy-MM-dd"
                  :picker-options="pastDateOptions"
                />
              </el-form-item>
              <el-form-item v-else key="noDate" label="关键日期">
                <el-input disabled placeholder="先选择客户类型" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="备注">
                <el-input v-model.trim="customerForm.remark" maxlength="500" />
              </el-form-item>
            </el-col>
            <el-col :span="6" class="form-actions">
              <el-button
                type="primary"
                icon="el-icon-plus"
                :loading="submitting.customer"
                @click="submitCustomer"
              >保存并签合同</el-button>
            </el-col>
            <el-col :span="24">
              <div class="customer-rule-tip">
                客户阶段用于记录业务进度；意向等级中 A 为近期可签约、B 为明确需求、C 为初步咨询、D 为低意向、E 为无效或沉睡客户。
              </div>
            </el-col>
          </el-row>
        </el-form>

        <el-table :data="filteredCustomers" border stripe empty-text="当前门店暂无客户，请先完成客户建档">
          <el-table-column prop="customer_no" label="客户编号" min-width="150" />
          <el-table-column prop="name" label="客户姓名" min-width="110" />
          <el-table-column prop="phone" label="手机号" min-width="125" />
          <el-table-column prop="store_name" label="门店" min-width="170" />
          <el-table-column prop="salesperson" label="业务员" min-width="110" />
          <el-table-column prop="source" label="客户来源" min-width="120" />
          <el-table-column prop="intent_level" label="意向" min-width="80" />
          <el-table-column prop="customer_type" label="客户类型" min-width="110" />
          <el-table-column label="预产/分娩日期" min-width="125">
            <template slot-scope="{ row }">{{ row.edc || row.delivery_date || '-' }}</template>
          </el-table-column>
          <el-table-column label="客户阶段" min-width="150">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="录入时间" min-width="160" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="hasPermission('SALES.VIEW')" label="2 合同签订" name="contracts">
        <el-form
          v-if="hasPermission('SALES.CREATE')"
          ref="contractForm"
          :model="contractForm"
          :rules="contractRules"
          label-width="100px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="contractForm.storeId">
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择客户" prop="customerId">
                <el-select v-model="contractForm.customerId" filterable>
                  <el-option
                    v-for="customer in contractCustomers"
                    :key="customer.id"
                    :label="`${customer.name}（${customer.customer_no}）`"
                    :value="customer.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="合同类型" prop="contractType">
                <el-select v-model="contractForm.contractType">
                  <el-option v-for="type in options.contractTypes" :key="type" :label="type" :value="type" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="套餐名称">
                <el-select
                  v-model="contractForm.packagePriceRuleId"
                  filterable
                  :disabled="!contractForm.storeId"
                  :placeholder="contractForm.storeId ? '请选择已启用套餐' : '请先选择门店'"
                  @change="applyContractPackage"
                >
                  <el-option
                    v-for="item in contractPackages"
                    :key="item.packagePriceRuleId"
                    :label="`${item.packageName} · ${item.roomType} · ${item.days}天 · ¥${Number(item.referencePrice || 0).toLocaleString('zh-CN')}`"
                    :value="item.packagePriceRuleId"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="参考价格" prop="referenceAmount">
                <el-input-number v-model="contractForm.referenceAmount" :min="0" :precision="2" :controls="false" :disabled="Boolean(contractForm.packagePriceRuleId)" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="活动价（参考）">
                <el-input-number v-model="contractForm.activityAmount" :min="0" :precision="2" :controls="false" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="成交金额" prop="amount">
                <el-input-number v-model="contractForm.amount" :min="0" :precision="2" :controls="false" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="折扣率">
                <el-input :value="discountRateText" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="入住天数" prop="days">
                <el-input-number v-model="contractForm.days" :min="1" :max="365" :disabled="Boolean(contractForm.packagePriceRuleId)" />
                <div v-if="contractForm.packagePriceRuleId" class="inline-presets">已按所选套餐自动带入</div>
                <div v-else class="inline-presets">未选套餐时可按合同约定填写</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="预住日期" prop="stayRange">
                <el-date-picker
                  v-model="contractForm.checkInDate"
                  type="date"
                  placeholder="请选择预计入住日"
                  value-format="yyyy-MM-dd"
                  :picker-options="futureDateOptions"
                  @change="syncContractStayRange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="签单日期" prop="signDate">
                <el-date-picker
                  v-model="contractForm.signDate"
                  type="date"
                  value-format="yyyy-MM-dd"
                  :picker-options="pastDateOptions"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8" class="form-actions">
              <el-button
                type="primary"
                icon="el-icon-plus"
                :loading="submitting.contract"
                @click="submitContract"
              >保存合同</el-button>
            </el-col>
            <el-col v-if="isBackdatedContract" :span="24">
              <el-form-item label="补录原因" prop="backfillReason">
                <el-input
                  v-model.trim="contractForm.backfillReason"
                  maxlength="200"
                  placeholder="例如：业务员次日补录纸质合同；系统会保留本次录入时间"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <div class="formula-tip">
            <span>折扣率=成交金额/参考价格</span>
            <span>未入账金额=已收款未审核的金额</span>
            <span>选择套餐后自动带入入住天数、参考价格与活动价；成交金额由业务员按实际合同填写</span>
          </div>
        </el-form>

        <el-table :data="filteredContracts" border stripe empty-text="当前门店暂无合同，请先选择客户新增合同">
          <el-table-column prop="contract_no" label="合同编号" min-width="175" />
          <el-table-column prop="customer_name" label="客户姓名" min-width="110" />
          <el-table-column prop="contract_type" label="合同类型" min-width="110" />
          <el-table-column prop="package_name" label="套餐名称" min-width="150" />
          <el-table-column prop="days" label="天数" min-width="70" align="right" />
          <el-table-column prop="reference_amount" label="参考价格" min-width="105" align="right" />
          <el-table-column prop="amount" label="成交金额" min-width="105" align="right" />
          <el-table-column label="折扣率" min-width="90" align="right">
            <template slot-scope="{ row }">{{ formatPercent(row.discount_rate) }}</template>
          </el-table-column>
          <el-table-column prop="paid" label="已入账" min-width="95" align="right" />
          <el-table-column prop="unposted_amount" label="未入账" min-width="95" align="right" />
          <el-table-column prop="outstanding_amount" label="欠款" min-width="95" align="right" />
          <el-table-column label="状态" min-width="145">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="sign_date" label="签单日期" min-width="110" />
          <el-table-column label="录入方式" min-width="95">
            <template slot-scope="{ row }">
              <el-tag v-if="row.is_backfill" size="mini" type="warning">历史补录</el-tag>
              <span v-else>正常录入</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="100">
            <template slot-scope="{ row }">
              <el-button
                v-if="['已签合同但未审核', '待审核'].includes(row.status) && hasPermission('SALES.APPROVE')"
                type="text"
                :loading="submitting.contractApproval === row.id"
                @click="approveContract(row)"
              >审核</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="hasPermission('FINANCE.VIEW')" label="3 收款审核" name="receipts">
        <el-form
          v-if="hasPermission('FINANCE.CREATE')"
          ref="receiptForm"
          :model="receiptForm"
          :rules="receiptRules"
          label-width="96px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="receiptForm.storeId">
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择合同" prop="contractId">
                <el-select v-model="receiptForm.contractId" filterable>
                  <el-option
                    v-for="contract in receiptContracts"
                    :key="contract.id"
                    :label="`${contract.customer_name}（${contract.contract_no}）`"
                    :value="contract.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="收款类型" prop="receiptType">
                <el-select v-model="receiptForm.receiptType">
                  <el-option v-for="type in contractReceiptTypes" :key="type.value" :label="type.label" :value="type.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="收款金额" prop="amount">
                <el-input-number
                  v-model="receiptForm.amount"
                  :min="0"
                  :max="receiptAvailableAmount"
                  :precision="2"
                  :controls="false"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="支付方式" prop="paymentMethod">
                <el-select v-model="receiptForm.paymentMethod">
                  <el-option v-for="method in options.paymentMethods" :key="method" :label="method" :value="method" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="收款时间" prop="receivedAt">
                <el-date-picker
                  v-model="receiptForm.receivedAt"
                  type="datetime"
                  value-format="yyyy-MM-dd HH:mm:ss"
                  :picker-options="pastDateOptions"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="备注">
                <el-input v-model.trim="receiptForm.remark" maxlength="500" />
              </el-form-item>
            </el-col>
            <el-col :span="6" class="form-actions">
              <el-button
                type="primary"
                icon="el-icon-plus"
                :loading="submitting.receipt"
                @click="submitReceipt"
              >登记收款</el-button>
            </el-col>
            <el-col v-if="isBackdatedReceipt" :span="24">
              <el-form-item label="补录原因" prop="backfillReason">
                <el-input
                  v-model.trim="receiptForm.backfillReason"
                  maxlength="200"
                  placeholder="填写实际收款凭证日期及延迟录入原因，审核后才计入已收款"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <div v-if="selectedReceiptContract" class="receipt-summary">
            <span>合同金额：{{ formatMoney(selectedReceiptContract.amount) }}</span>
            <span>已审核入账：{{ formatMoney(selectedReceiptContract.paid) }}</span>
            <span>待审核：{{ formatMoney(selectedReceiptContract.unposted_amount) }}</span>
            <span>本次最多可收：{{ formatMoney(receiptAvailableAmount) }}</span>
          </div>
        </el-form>

        <el-table :data="filteredReceipts" border stripe empty-text="当前门店暂无收款记录，请先审核合同">
          <el-table-column prop="receipt_no" label="收款单号" min-width="175" />
          <el-table-column prop="customer_name" label="客户姓名" min-width="110" />
          <el-table-column prop="contract_no" label="合同编号" min-width="175" />
          <el-table-column prop="store_name" label="门店" min-width="150" />
          <el-table-column prop="receipt_type" label="收款类型" min-width="120" />
          <el-table-column prop="amount" label="收款金额" min-width="110" align="right" />
          <el-table-column prop="payment_method" label="支付方式" min-width="95" />
          <el-table-column prop="receiver" label="收款人" min-width="100" />
          <el-table-column prop="received_at" label="收款时间" min-width="160" />
          <el-table-column label="状态" min-width="90">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" min-width="100">
            <template slot-scope="{ row }">
              <el-button
                v-if="row.status === '待审核' && hasPermission('FINANCE.APPROVE')"
                type="text"
                :loading="submitting.receiptApproval === row.id"
                @click="approveReceipt(row)"
              >审核</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane v-if="hasPermission('ROOM.VIEW')" label="4 订房入住" name="bookings">
        <el-form
          v-if="hasPermission('ROOM.CREATE')"
          ref="bookingForm"
          :model="bookingForm"
          :rules="bookingRules"
          label-width="92px"
          class="business-form"
        >
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="门店" prop="storeId">
                <el-select v-model="bookingForm.storeId">
                  <el-option v-for="store in options.stores" :key="store.id" :label="store.name" :value="store.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择合同" prop="contractId">
                <el-select v-model="bookingForm.contractId" filterable placeholder="先选择合同">
                  <el-option
                    v-for="contract in bookingContracts"
                    :key="contract.id"
                    :label="`${contract.customer_name}（${contract.package_name || '未配置套餐'} / ${contract.contract_no}）`"
                    :value="contract.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="选择房间" prop="roomId">
                <el-select v-model="bookingForm.roomId" filterable :disabled="!bookingForm.contractId" placeholder="先选择合同后再选房间">
                  <el-option
                    v-for="room in bookingRooms"
                    :key="room.id"
                    :label="`${room.room_no}（${room.room_type} / ${room.status}）`"
                    :value="room.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="入住日期" prop="stayRange">
                <el-date-picker
                  v-model="bookingForm.stayRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="入住日期"
                  end-placeholder="离店日期"
                  value-format="yyyy-MM-dd"
                  :picker-options="futureDateOptions"
                />
              </el-form-item>
            </el-col>
            <el-col :span="24" class="form-actions">
              <el-button
                type="primary"
                icon="el-icon-plus"
                :loading="submitting.booking"
                @click="submitBooking"
              >办理订房</el-button>
            </el-col>
          </el-row>
          <div class="booking-rule-tip">
            先选已审核且已入账的合同。合同已配置套餐房型时，仅显示匹配的可用房间；未配置套餐的中心店合同可按实际房型办理。
          </div>
        </el-form>

        <el-table :data="filteredBookings" border stripe empty-text="当前门店暂无订房记录，请先完成合同和收款审核">
          <el-table-column prop="booking_no" label="订房单号" min-width="175" />
          <el-table-column prop="customer_name" label="客户姓名" min-width="110" />
          <el-table-column prop="contract_no" label="合同编号" min-width="175" />
          <el-table-column prop="store_name" label="门店" min-width="170" />
          <el-table-column prop="room_no" label="房间号" min-width="90" />
          <el-table-column prop="check_in" label="入住日期" min-width="110" />
          <el-table-column prop="check_out" label="离店日期" min-width="110" />
          <el-table-column label="状态" min-width="90">
            <template slot-scope="{ row }"><el-tag size="mini">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="actual_check_in_at" label="实际入住时间" min-width="160" />
          <el-table-column label="操作" min-width="100">
            <template slot-scope="{ row }">
              <el-button
                v-if="row.status === '已订房' && hasPermission('ROOM.EXECUTE')"
                type="text"
                :loading="submitting.checkIn === row.id"
                @click="checkIn(row)"
              >办理入住</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import {
  getMvpOptions,
  getMvpOverview,
  getMvpList,
  createMvpRecord,
  performMvpAction
} from '@/api/erp-mvp'

function today() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now.getTime() - offset).toISOString().slice(0, 10)
}

function startOfToday() {
  const value = new Date()
  value.setHours(0, 0, 0, 0)
  return value
}

function endOfToday() {
  const value = new Date()
  value.setHours(23, 59, 59, 999)
  return value
}

function daysBetween(start, end) {
  if (!start || !end) return 0
  const startTime = new Date(`${start}T00:00:00`).getTime()
  const endTime = new Date(`${end}T00:00:00`).getTime()
  return Math.round((endTime - startTime) / 86400000)
}

function addDays(value, days) {
  const date = new Date(`${value}T00:00:00`)
  date.setDate(date.getDate() + Number(days || 0))
  const offset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offset).toISOString().slice(0, 10)
}

function nowText() {
  const now = new Date()
  const pad = value => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

export default {
  name: 'MvpWorkbench',
  data() {
    return {
      loading: false,
      loadError: '',
      activeTab: 'customers',
      submitting: {
        customer: false,
        contract: false,
        contractApproval: '',
        receipt: false,
        receiptApproval: '',
        booking: false,
        checkIn: ''
      },
      overview: {},
      options: {
        stores: [],
        staff: [],
        contractTypes: [],
        receiptTypes: [],
        paymentMethods: [],
        packages: [],
        permissions: [],
        roles: [],
        bookingContracts: []
      },
      customers: [],
      contracts: [],
      receipts: [],
      rooms: [],
      bookings: [],
      summaryCards: [
        { key: 'customers', label: '客户数', permission: 'CUSTOMER.VIEW' },
        { key: 'contracts', label: '合同数', permission: 'SALES.VIEW' },
        { key: 'pendingContracts', label: '待审合同', permission: 'SALES.VIEW' },
        { key: 'pendingReceipts', label: '待审收款', permission: 'FINANCE.VIEW' },
        { key: 'bookings', label: '订房/入住', permission: 'ROOM.VIEW' }
      ],
      customerStages: ['新线索', '跟进中', '已到店'],
      intentLevels: [
        { value: 'A', label: '近期可签约' },
        { value: 'B', label: '明确需求/方案比较' },
        { value: 'C', label: '初步咨询/持续培育' },
        { value: 'D', label: '低意向/需求较弱' },
        { value: 'E', label: '无效或沉睡' }
      ],
      customerSources: ['客户介绍', '住附近', '电话来访', '大众点评', '美团咨询', '抖音咨询', '小红书咨询', '自然上门', '网络搜索', '市场渠道', '二胎入住', '内部资源'],
      customerTypes: [
        { value: '孕期待产', label: '孕期待产（月子服务）' },
        { value: '已分娩', label: '已分娩（月子服务）' },
        { value: '非孕产服务', label: '产康/散客/托管等' }
      ],
      contractReceiptTypes: [
        { value: '合同首付', label: '合同首付（第一笔合同款）' },
        { value: '合同补余收款', label: '合同补余收款（后续补款）' },
        { value: '合同收款', label: '合同收款（一次性或通用合同款）' },
        { value: '其他收款', label: '其他收款（必须写明用途）' }
      ],
      futureDateOptions: {
        disabledDate(value) {
          return value.getTime() < startOfToday().getTime()
        }
      },
      pastDateOptions: {
        disabledDate(value) {
          return value.getTime() > endOfToday().getTime()
        }
      },
      customerForm: {
        storeId: '',
        name: '',
        phone: '',
        wechat: '',
        stage: '新线索',
        intentLevel: '',
        source: '',
        salesStaffId: '',
        customerType: '',
        edc: '',
        deliveryDate: '',
        remark: ''
      },
      contractForm: {
        storeId: '',
        customerId: '',
        contractType: '月子合同',
        packageName: '',
        packageId: '',
        packageVersionId: '',
        packagePriceRuleId: '',
        roomTypeId: '',
        roomType: '',
        referenceAmount: 0,
        activityAmount: 0,
        amount: 0,
        days: 28,
        checkInDate: '',
        stayRange: [],
        signDate: today(),
        backfillReason: ''
      },
      receiptForm: {
        storeId: '',
        contractId: '',
        receiptType: '合同首付',
        amount: 0,
        paymentMethod: '转账',
        receivedAt: nowText(),
        backfillReason: '',
        remark: ''
      },
      bookingForm: {
        storeId: '',
        contractId: '',
        roomId: '',
        stayRange: []
      },
      customerRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        name: [{ required: true, message: '请输入客户姓名', trigger: 'blur' }],
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }
        ],
        stage: [{ required: true, message: '请选择客户阶段', trigger: 'change' }],
        intentLevel: [{ required: true, message: '请选择意向等级', trigger: 'change' }],
        source: [{ required: true, message: '请选择或输入客户来源', trigger: 'change' }],
        salesStaffId: [{ required: true, message: '请选择业务员', trigger: 'change' }],
        customerType: [{ required: true, message: '请选择客户类型', trigger: 'change' }],
        edc: [{ required: true, message: '请选择预产期', trigger: 'change' }],
        deliveryDate: [{ required: true, message: '请选择分娩日期', trigger: 'change' }]
      },
      contractRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        customerId: [{ required: true, message: '请选择客户', trigger: 'change' }],
        contractType: [{ required: true, message: '请选择合同类型', trigger: 'change' }],
        referenceAmount: [{ required: true, type: 'number', min: 0.01, message: '请输入参考价格', trigger: 'blur' }],
        amount: [{ required: true, type: 'number', min: 0.01, message: '请输入成交金额', trigger: 'blur' }],
        days: [{ required: true, type: 'number', min: 1, message: '请输入入住天数', trigger: 'blur' }],
        stayRange: [{ required: true, type: 'array', min: 2, message: '请选择预住日期', trigger: 'change' }],
        signDate: [{ required: true, message: '请选择签单日期', trigger: 'change' }],
        backfillReason: [{ required: true, message: '历史补录必须填写原因', trigger: 'blur' }]
      },
      receiptRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        contractId: [{ required: true, message: '请选择合同', trigger: 'change' }],
        receiptType: [{ required: true, message: '请选择收款类型', trigger: 'change' }],
        amount: [{ required: true, type: 'number', min: 0.01, message: '请输入收款金额', trigger: 'blur' }],
        paymentMethod: [{ required: true, message: '请选择支付方式', trigger: 'change' }],
        receivedAt: [{ required: true, message: '请选择实际收款时间', trigger: 'change' }],
        backfillReason: [{ required: true, message: '历史收款补录必须填写原因', trigger: 'blur' }]
      },
      bookingRules: {
        storeId: [{ required: true, message: '请选择门店', trigger: 'change' }],
        contractId: [{ required: true, message: '请选择已审核合同', trigger: 'change' }],
        roomId: [{ required: true, message: '请选择房间', trigger: 'change' }],
        stayRange: [{ required: true, type: 'array', min: 2, message: '请选择入住日期', trigger: 'change' }]
      }
    }
  },
  computed: {
    workflowActive() {
      return Math.max(0, ['customers', 'contracts', 'receipts', 'bookings'].indexOf(this.activeTab))
    },
    visibleSummaryCards() {
      return this.summaryCards.filter(item => this.hasPermission(item.permission))
    },
    summaryOverview() {
      const formKeyByTab = {
        customers: 'customerForm',
        contracts: 'contractForm',
        receipts: 'receiptForm',
        bookings: 'bookingForm'
      }
      const activeForm = this[formKeyByTab[this.activeTab]]
      const storeId = Number((activeForm && activeForm.storeId) || this.$route.query.storeId)
      if (!storeId) return this.overview

      const belongsToStore = item => Number(item.store_id) === storeId
      const customers = this.customers.filter(belongsToStore)
      const contracts = this.contracts.filter(belongsToStore)
      const receipts = this.receipts.filter(belongsToStore)
      const bookings = this.bookings.filter(belongsToStore)
      return {
        customers: customers.length,
        contracts: contracts.length,
        pendingContracts: contracts.filter(item => ['已签合同但未审核', '待审核'].includes(item.status)).length,
        pendingReceipts: receipts.filter(item => item.status === '待审核').length,
        bookings: bookings.length
      }
    },
    customerStaff() {
      return this.options.staff.filter(item => !this.customerForm.storeId || Number(item.store_id) === Number(this.customerForm.storeId))
    },
    filteredCustomers() {
      return this.customers.filter(item => !this.customerForm.storeId || Number(item.store_id) === Number(this.customerForm.storeId))
    },
    filteredContracts() {
      return this.contracts.filter(item => !this.contractForm.storeId || Number(item.store_id) === Number(this.contractForm.storeId))
    },
    filteredReceipts() {
      return this.receipts.filter(item => !this.receiptForm.storeId || Number(item.store_id) === Number(this.receiptForm.storeId))
    },
    filteredBookings() {
      return this.bookings.filter(item => !this.bookingForm.storeId || Number(item.store_id) === Number(this.bookingForm.storeId))
    },
    contractCustomers() {
      return this.customers.filter(item => !this.contractForm.storeId || Number(item.store_id) === Number(this.contractForm.storeId))
    },
    contractPackages() {
      if (!this.contractForm.storeId) return []
      return (this.options.packages || []).filter(item => Number(item.store_id || item.storeId) === Number(this.contractForm.storeId))
    },
    receiptContracts() {
      return this.contracts.filter(item => (
        ['已审核', '审核通过'].includes(item.status) &&
        Number(item.outstanding_amount || 0) - Number(item.unposted_amount || 0) > 0 &&
        (!this.receiptForm.storeId || Number(item.store_id) === Number(this.receiptForm.storeId))
      ))
    },
    bookingContracts() {
      return this.options.bookingContracts.filter(item => !this.bookingForm.storeId || Number(item.store_id) === Number(this.bookingForm.storeId))
    },
    bookingRooms() {
      const contract = this.selectedBookingContract
      const requiredRoomType = contract && String(contract.room_type || '').trim()
      return this.rooms.filter(item => (
        (!this.bookingForm.storeId || Number(item.store_id) === Number(this.bookingForm.storeId)) &&
        (!requiredRoomType || item.room_type === requiredRoomType) &&
        (item.status === '空闲' || Number(item.id) === Number(this.bookingForm.roomId))
      ))
    },
    selectedBookingContract() {
      return this.options.bookingContracts.find(item => Number(item.id) === Number(this.bookingForm.contractId)) || null
    },
    selectedReceiptContract() {
      return this.contracts.find(item => Number(item.id) === Number(this.receiptForm.contractId)) || null
    },
    receiptAvailableAmount() {
      if (!this.selectedReceiptContract) return 0
      return Math.max(
        0,
        Number(this.selectedReceiptContract.outstanding_amount || 0) -
          Number(this.selectedReceiptContract.unposted_amount || 0)
      )
    },
    isBackdatedContract() {
      return Boolean(this.contractForm.signDate && this.contractForm.signDate < today())
    },
    isBackdatedReceipt() {
      return Boolean(this.receiptForm.receivedAt && this.receiptForm.receivedAt.slice(0, 10) < today())
    },
    discountRateText() {
      if (!this.contractForm.referenceAmount) return '0.00%'
      return `${(this.contractForm.amount / this.contractForm.referenceAmount * 100).toFixed(2)}%`
    }
  },
  watch: {
    '$route.query': {
      handler() {
        if (this.customers.length) this.applyRouteContext()
      },
      deep: true
    },
    'customerForm.storeId'() {
      const selected = this.options.staff.find(item => Number(item.id) === Number(this.customerForm.salesStaffId))
      if (selected && Number(selected.store_id) !== Number(this.customerForm.storeId)) this.customerForm.salesStaffId = ''
    },
    'customerForm.customerType'(type) {
      if (type !== '孕期待产') this.customerForm.edc = ''
      if (type !== '已分娩') this.customerForm.deliveryDate = ''
      this.clearFormValidation('customerForm')
    },
    'contractForm.storeId'() {
      const selected = this.customers.find(item => Number(item.id) === Number(this.contractForm.customerId))
      if (selected && Number(selected.store_id) !== Number(this.contractForm.storeId)) this.contractForm.customerId = ''
      const selectedPackage = (this.options.packages || []).find(item => Number(item.packagePriceRuleId) === Number(this.contractForm.packagePriceRuleId))
      if (selectedPackage && Number(selectedPackage.store_id || selectedPackage.storeId) !== Number(this.contractForm.storeId)) this.clearContractPackage()
    },
    'contractForm.signDate'() {
      if (!this.isBackdatedContract) this.contractForm.backfillReason = ''
      this.clearFormValidation('contractForm')
    },
    'receiptForm.storeId'() {
      const selected = this.contracts.find(item => Number(item.id) === Number(this.receiptForm.contractId))
      if (selected && Number(selected.store_id) !== Number(this.receiptForm.storeId)) this.receiptForm.contractId = ''
    },
    'receiptForm.contractId'(contractId) {
      const contract = this.contracts.find(item => Number(item.id) === Number(contractId))
      this.receiptForm.amount = 0
      if (!contract) return
      this.receiptForm.receiptType = Number(contract.paid || 0) > 0 ? '合同补余收款' : '合同首付'
    },
    'receiptForm.receivedAt'() {
      if (!this.isBackdatedReceipt) this.receiptForm.backfillReason = ''
      this.clearFormValidation('receiptForm')
    },
    'bookingForm.storeId'() {
      const selectedContract = this.options.bookingContracts.find(item => Number(item.id) === Number(this.bookingForm.contractId))
      if (selectedContract && Number(selectedContract.store_id) !== Number(this.bookingForm.storeId)) this.bookingForm.contractId = ''
      const selectedRoom = this.rooms.find(item => Number(item.id) === Number(this.bookingForm.roomId))
      if (selectedRoom && Number(selectedRoom.store_id) !== Number(this.bookingForm.storeId)) this.bookingForm.roomId = ''
    },
    'bookingForm.contractId'(contractId) {
      const contract = this.options.bookingContracts.find(item => Number(item.id) === Number(contractId))
      this.bookingForm.roomId = ''
      if (!contract) return
      if (contract.expected_check_in >= today() && contract.expected_check_out > contract.expected_check_in) {
        this.bookingForm.stayRange = [contract.expected_check_in, contract.expected_check_out]
      } else {
        this.bookingForm.stayRange = []
      }
    }
  },
  created() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      this.loading = true
      this.loadError = ''
      try {
        const options = await getMvpOptions()
        this.options = options.data
        const emptyList = () => Promise.resolve({ data: { list: [], total: 0 }})
        const [overview, customers, contracts, receipts, rooms, bookings] = await Promise.all([
          getMvpOverview(),
          this.hasPermission('CUSTOMER.VIEW') ? getMvpList('customers') : emptyList(),
          this.hasPermission('SALES.VIEW') ? getMvpList('contracts') : emptyList(),
          this.hasPermission('FINANCE.VIEW') ? getMvpList('receipts') : emptyList(),
          this.hasPermission('ROOM.VIEW') ? getMvpList('rooms') : emptyList(),
          this.hasPermission('ROOM.VIEW') ? getMvpList('bookings') : emptyList()
        ])
        this.overview = overview.data
        this.customers = customers.data.list
        this.contracts = contracts.data.list
        this.receipts = receipts.data.list
        this.rooms = rooms.data.list
        this.bookings = bookings.data.list
        this.applyDefaultStores()
        this.applyRouteContext()
        this.ensureActiveTab()
      } catch (error) {
        this.loadError = `业务数据加载失败：${error.message || '请联系系统管理员'}`
      } finally {
        this.loading = false
      }
    },
    ensureActiveTab() {
      const tabs = [
        { name: 'customers', permission: 'CUSTOMER.VIEW' },
        { name: 'contracts', permission: 'SALES.VIEW' },
        { name: 'receipts', permission: 'FINANCE.VIEW' },
        { name: 'bookings', permission: 'ROOM.VIEW' }
      ]
      const allowed = tabs.filter(item => this.hasPermission(item.permission))
      if (!allowed.some(item => item.name === this.activeTab) && allowed.length) {
        this.activeTab = allowed[0].name
      }
    },
    hasPermission(permission) {
      return this.options.permissions.includes(permission)
    },
    applyDefaultStores() {
      if (!this.options.stores.length) return
      const requestedStoreId = Number(this.$route.query.storeId)
      const requestedStore = this.options.stores.find(item => Number(item.id) === requestedStoreId)
      const defaultStore = requestedStore ? requestedStore.id : this.options.stores[0].id
      const formKeys = ['customerForm', 'contractForm', 'receiptForm', 'bookingForm']
      formKeys.forEach(key => {
        if (!this[key].storeId) this[key].storeId = defaultStore
      })
    },
    applyRouteContext() {
      const requestedStoreId = Number(this.$route.query.storeId)
      const store = this.options.stores.find(item => Number(item.id) === requestedStoreId)
      if (store) {
        const formKeys = ['customerForm', 'contractForm', 'receiptForm', 'bookingForm']
        formKeys.forEach(key => { this[key].storeId = store.id })
      }
      const customerId = Number(this.$route.query.customerId)
      const customer = this.customers.find(item => Number(item.id) === customerId)
      if (customer) {
        this.customerForm.storeId = customer.store_id
        this.contractForm.storeId = customer.store_id
        this.contractForm.customerId = customer.id
        this.receiptForm.storeId = customer.store_id
        this.bookingForm.storeId = customer.store_id
      }
      const requestedTab = String(this.$route.query.open || '')
      if (['customers', 'contracts', 'receipts', 'bookings'].includes(requestedTab)) {
        this.activeTab = requestedTab
      }
    },
    validate(ref) {
      return new Promise(resolve => this.$refs[ref].validate(valid => resolve(valid)))
    },
    clearFormValidation(ref) {
      this.$nextTick(() => {
        if (this.$refs[ref]) this.$refs[ref].clearValidate()
      })
    },
    async confirmAction(message, title) {
      try {
        await this.$confirm(message, title, { type: 'warning' })
        return true
      } catch (error) {
        return false
      }
    },
    async submitCustomer() {
      if (!await this.validate('customerForm')) return
      if (this.customerForm.customerType === '孕期待产' && this.customerForm.edc < today()) {
        return this.$message.warning('预产期不能早于今天')
      }
      if (this.customerForm.customerType === '已分娩' && this.customerForm.deliveryDate > today()) {
        return this.$message.warning('分娩日期不能晚于今天')
      }
      this.submitting.customer = true
      try {
        const storeId = this.customerForm.storeId
        const response = await createMvpRecord('customers', this.customerForm)
        Object.assign(this.customerForm, {
          storeId,
          name: '',
          phone: '',
          wechat: '',
          stage: '新线索',
          intentLevel: '',
          source: '',
          salesStaffId: '',
          customerType: '',
          edc: '',
          deliveryDate: '',
          remark: ''
        })
        await this.loadAll()
        this.contractForm.storeId = storeId
        this.contractForm.customerId = response.data.id
        this.activeTab = 'contracts'
        this.clearFormValidation('customerForm')
        this.$message.success('客户已保存，已带入合同签订')
      } finally {
        this.submitting.customer = false
      }
    },
    clearContractPackage() {
      Object.assign(this.contractForm, {
        packageName: '',
        packageId: '',
        packageVersionId: '',
        packagePriceRuleId: '',
        roomTypeId: '',
        roomType: '',
        referenceAmount: 0,
        activityAmount: 0,
        amount: 0
      })
    },
    applyContractPackage(packagePriceRuleId) {
      const selected = (this.options.packages || []).find(item => Number(item.packagePriceRuleId) === Number(packagePriceRuleId))
      if (!selected) {
        this.clearContractPackage()
        return
      }
      this.contractForm.packageName = selected.packageName
      this.contractForm.packageId = selected.packageId || selected.id
      this.contractForm.packageVersionId = selected.packageVersionId
      this.contractForm.packagePriceRuleId = selected.packagePriceRuleId
      this.contractForm.roomTypeId = selected.roomTypeId
      this.contractForm.roomType = selected.roomType
      this.contractForm.days = Number(selected.days || 28)
      this.contractForm.referenceAmount = Number(selected.referencePrice || 0)
      this.contractForm.activityAmount = Number(selected.activityPrice || selected.referencePrice || 0)
      this.contractForm.amount = Number(selected.salePrice || selected.referencePrice || 0)
      if (this.contractForm.checkInDate) {
        this.contractForm.stayRange = [
          this.contractForm.checkInDate,
          addDays(this.contractForm.checkInDate, this.contractForm.days)
        ]
      }
    },
    setContractDays(days) {
      this.contractForm.days = days
      if (this.contractForm.checkInDate) {
        this.contractForm.stayRange = [
          this.contractForm.checkInDate,
          addDays(this.contractForm.checkInDate, days)
        ]
      }
    },
    syncContractStayRange(checkInDate) {
      this.contractForm.checkInDate = checkInDate || ''
      this.contractForm.stayRange = checkInDate
        ? [checkInDate, addDays(checkInDate, this.contractForm.days)]
        : []
    },
    async submitContract() {
      if (!await this.validate('contractForm')) return
      if (this.contractForm.amount > this.contractForm.referenceAmount) {
        return this.$message.warning('成交金额不能大于参考价格')
      }
      if (this.contractForm.stayRange[0] < today()) {
        return this.$message.warning('预住日期不能早于今天；历史合同只能补录签单日期，不能在此倒填入住计划')
      }
      const stayDays = daysBetween(this.contractForm.stayRange[0], this.contractForm.stayRange[1])
      if (stayDays !== Number(this.contractForm.days)) {
        return this.$message.warning(`入住天数与预住日期不一致，当前日期范围为 ${stayDays} 天`)
      }
      if (this.contractForm.signDate > today()) {
        return this.$message.warning('签单日期不能晚于今天')
      }
      this.submitting.contract = true
      try {
        const storeId = this.contractForm.storeId
        await createMvpRecord('contracts', {
          ...this.contractForm,
          expectedCheckIn: this.contractForm.stayRange[0],
          expectedCheckOut: this.contractForm.stayRange[1]
        })
        Object.assign(this.contractForm, {
          storeId,
          customerId: '',
          contractType: '月子合同',
          packageName: '',
          packageId: '',
          packageVersionId: '',
          packagePriceRuleId: '',
          roomTypeId: '',
          roomType: '',
          referenceAmount: 0,
          activityAmount: 0,
          amount: 0,
          days: 28,
          checkInDate: '',
          stayRange: [],
          signDate: today(),
          backfillReason: ''
        })
        await this.loadAll()
        this.activeTab = 'contracts'
        this.clearFormValidation('contractForm')
        this.$message.success('合同已保存，请在列表中完成审核')
      } finally {
        this.submitting.contract = false
      }
    },
    async approveContract(row) {
      if (!await this.confirmAction(`确认审核合同 ${row.contract_no}？`, '合同审核')) return
      this.submitting.contractApproval = row.id
      try {
        await performMvpAction('contracts', row.id, 'approve')
        await this.loadAll()
        this.receiptForm.storeId = row.store_id
        this.receiptForm.contractId = row.id
        this.activeTab = 'receipts'
        this.$message.success('合同审核完成，已带入收款登记')
      } finally {
        this.submitting.contractApproval = ''
      }
    },
    async submitReceipt() {
      if (!await this.validate('receiptForm')) return
      if (!this.selectedReceiptContract) return this.$message.warning('请选择有效合同')
      if (Number(this.receiptForm.amount) > this.receiptAvailableAmount) {
        return this.$message.warning('本次收款不能超过合同剩余可收金额')
      }
      if (new Date(this.receiptForm.receivedAt.replace(' ', 'T')).getTime() > Date.now()) {
        return this.$message.warning('实际收款时间不能晚于当前时间')
      }
      if (this.receiptForm.receiptType === '其他收款' && !this.receiptForm.remark) {
        return this.$message.warning('其他收款必须在备注中写明款项用途')
      }
      this.submitting.receipt = true
      try {
        const storeId = this.receiptForm.storeId
        const contractId = this.receiptForm.contractId
        await createMvpRecord('receipts', this.receiptForm)
        Object.assign(this.receiptForm, {
          storeId,
          contractId,
          receiptType: '合同首付',
          amount: 0,
          paymentMethod: '转账',
          receivedAt: nowText(),
          backfillReason: '',
          remark: ''
        })
        await this.loadAll()
        this.receiptForm.amount = 0
        this.activeTab = 'receipts'
        this.clearFormValidation('receiptForm')
        this.$message.success('收款已登记，请在列表中完成审核')
      } finally {
        this.submitting.receipt = false
      }
    },
    async approveReceipt(row) {
      if (!await this.confirmAction(
        `确认审核 ${row.receipt_type} ${this.formatMoney(row.amount)}？审核后将计入合同已收款。`,
        `收款审核 · ${row.receipt_no}`
      )) return
      this.submitting.receiptApproval = row.id
      try {
        await performMvpAction('receipts', row.id, 'approve')
        await this.loadAll()
        const contract = this.contracts.find(item => item.contract_no === row.contract_no)
        const bookingOption = contract && this.options.bookingContracts.find(item => Number(item.id) === Number(contract.id))
        if (bookingOption) {
          this.bookingForm.storeId = bookingOption.store_id
          this.bookingForm.contractId = bookingOption.id
          this.activeTab = 'bookings'
          this.$message.success('收款审核完成，已带入订房办理')
        } else {
          const existingBooking = this.bookings.find(item => item.contract_no === row.contract_no && item.status !== '已取消')
          if (existingBooking) {
            this.bookingForm.storeId = existingBooking.store_id
            this.activeTab = 'bookings'
            this.$message.success('收款审核完成；该合同已有订房记录，已切换到对应门店查看')
          } else {
            this.$message.success('收款审核完成，合同已入账；若未出现订房选项，请检查合同状态和门店')
          }
        }
      } finally {
        this.submitting.receiptApproval = ''
      }
    },
    async submitBooking() {
      if (!await this.validate('bookingForm')) return
      if (this.bookingForm.stayRange[0] < today()) {
        return this.$message.warning('入住日期不能早于今天')
      }
      this.submitting.booking = true
      try {
        const storeId = this.bookingForm.storeId
        await createMvpRecord('bookings', {
          ...this.bookingForm,
          checkIn: this.bookingForm.stayRange[0],
          checkOut: this.bookingForm.stayRange[1]
        })
        Object.assign(this.bookingForm, { storeId, contractId: '', roomId: '', stayRange: [] })
        await this.loadAll()
        this.activeTab = 'bookings'
        this.clearFormValidation('bookingForm')
        this.$message.success('订房办理完成，请在入住当天办理入住')
      } finally {
        this.submitting.booking = false
      }
    },
    async checkIn(row) {
      if (!await this.confirmAction(`确认客户 ${row.customer_name} 入住 ${row.room_no} 房？`, '办理入住')) return
      this.submitting.checkIn = row.id
      try {
        await performMvpAction('bookings', row.id, 'check-in')
        await this.loadAll()
        this.activeTab = 'bookings'
        this.$message.success('入住办理完成，客户和房态已同步更新')
      } finally {
        this.submitting.checkIn = ''
      }
    },
    formatPercent(value) {
      return `${(Number(value || 0) * 100).toFixed(2)}%`
    },
    formatMoney(value) {
      return `¥${Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
  }
}
</script>

<style lang="scss" scoped>
.mvp-page {
  min-height: calc(100vh - 84px);
  padding: 16px;
  background: #f4f1ea;
}

.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 12px;

  h2 {
    margin: 0;
    color: #493719;
    font-size: 22px;
  }

  p {
    margin: 6px 0 0;
    color: #7d6c52;
    font-size: 13px;
  }
}

.heading-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: none;
}

.load-error {
  margin-bottom: 12px;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.summary-card {
  padding: 14px 16px;
  border: 1px solid #ded0b4;
  border-radius: 4px;
  background: #fffdf8;
}

.summary-label {
  color: #7d6c52;
  font-size: 13px;
}

.summary-value {
  margin-top: 6px;
  color: #6e4f20;
  font-size: 28px;
  font-weight: 600;
}

.workflow-steps {
  margin-top: 12px;
  border: 1px solid #ded0b4;
  background: #fffdf8;
}

.business-tabs {
  margin-top: 12px;
  padding: 0 16px 16px;
  border: 1px solid #ded0b4;
  background: #fff;
}

.business-form {
  margin-bottom: 14px;
  padding: 14px 12px 2px;
  background: #faf7f0;

  ::v-deep .el-select,
  ::v-deep .el-date-editor,
  ::v-deep .el-input-number {
    width: 100%;
  }
}

.form-actions {
  padding-bottom: 16px;
  text-align: right;
}

.formula-tip {
  display: flex;
  flex-wrap: wrap;
  gap: 28px;
  padding: 0 0 12px 100px;
  color: #9b6b20;
  font-size: 13px;
}

.inline-presets {
  display: flex;
  gap: 10px;
  height: 22px;

  ::v-deep .el-button {
    padding: 2px 0;
    font-size: 12px;
  }
}

.receipt-summary,
.booking-rule-tip {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  padding: 0 0 12px 96px;
  color: #7a5a29;
  font-size: 12px;
  line-height: 1.7;
}

.booking-rule-tip {
  padding-left: 92px;
}

.customer-rule-tip {
  padding: 0 0 12px 92px;
  color: #8a6731;
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 1100px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-row {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
