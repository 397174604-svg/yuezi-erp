import axios from 'axios'
import { MessageBox, Message } from 'element-ui'
import store from '@/store'
import { getToken } from '@/utils/auth'

let lastErrorMessage = ''
let lastErrorAt = 0
let reloginDialogOpen = false

function handleSessionExpired() {
  const onLoginPage = window.location.hash.indexOf('#/login') === 0

  // Requests that were already in flight may finish after the router has
  // reached the login page.  Clear the stale token silently in that case so
  // the login form is never covered by a second, misleading logout dialog.
  if (onLoginPage) {
    if (store.getters.token) store.dispatch('user/resetToken')
    return
  }

  if (reloginDialogOpen) return
  reloginDialogOpen = true
  MessageBox.alert('当前登录状态已失效，请重新登录后继续操作。', '登录状态已失效', {
    confirmButtonText: '重新登录',
    type: 'warning',
    closeOnClickModal: false,
    closeOnPressEscape: false,
    callback: () => {
      store.dispatch('user/resetToken').finally(() => {
        reloginDialogOpen = false
        window.location.href = `${window.location.origin}${window.location.pathname}#/login`
      })
    }
  })
}

function notifyError(message) {
  const now = Date.now()
  // A page can issue several dependent requests at once.  Show the actual
  // problem once instead of stacking identical 400/403/404 notifications.
  if (message === lastErrorMessage && now - lastErrorAt < 1500) return
  lastErrorMessage = message
  lastErrorAt = now
  Message({ message, type: 'error', duration: 5 * 1000 })
}

function businessErrorMessage(error) {
  const response = error && error.response
  const payload = response && response.data
  const serverMessage = payload && typeof payload.message === 'string' && payload.message.trim()
    ? payload.message.trim()
    : ''
  const status = response && response.status
  // Compatibility keys retained for release diagnostics:
  // 400: '请求参数不符合要求'
  // 403: '当前账号没有此操作权限或无权访问该门店'
  // 404: '业务接口不存在或尚未接入，请勿将此结果视为成功'
  const statusMessages = {
    400: '提交信息不符合业务规则，请检查必填项、金额、日期或当前状态。',
    401: '登录状态已失效，请重新登录后继续操作。',
    403: '当前账号没有执行此业务操作的权限或无权访问该门店，请联系管理员授权。',
    404: '业务记录不存在，或当前门店无权访问；请刷新数据后重试。',
    409: '当前业务状态不允许此操作，请刷新数据后重试。',
    422: '提交信息校验失败，请检查填写内容。'
  }
  if (serverMessage || statusMessages[status]) return serverMessage || statusMessages[status]
  if (!response) return '网络连接异常，请检查网络或稍后重试。'
  return '业务服务暂时不可用，请稍后重试或联系系统管理员。'
}

// 顶栏门店是业务写入的默认归属。历史工作台中有些弹窗没有再次渲染门店
// 字段，导致用户已切换黄河路店却仍被后端判定为“未选择门店”。显式填写
// 的业务门店优先；只有缺失时才继承顶栏，且“全部门店”始终不能写入。
function inheritCurrentStore(config) {
  const method = String(config.method || 'get').toLowerCase()
  const url = String(config.url || '')
  const currentStoreId = String(store.getters.currentStoreId || 'all')
  if (!['post', 'put', 'patch'].includes(method) || !url.startsWith('/vue-element-admin/erp/') || currentStoreId === 'all') return
  if (!config.data || Object.prototype.toString.call(config.data) !== '[object Object]') return
  if (config.data.selectedStoreId === undefined || config.data.selectedStoreId === null || config.data.selectedStoreId === '') config.data.selectedStoreId = currentStoreId
  if (config.data.storeId === undefined || config.data.storeId === null || config.data.storeId === '') config.data.storeId = currentStoreId
}

// create an axios instance
const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API, // url = base url + request url
  // withCredentials: true, // send cookies when cross-domain requests
  timeout: 5000 // request timeout
})

// request interceptor
service.interceptors.request.use(
  config => {
    // do something before request is sent

    if (store.getters.token) {
      // let each request carry token
      // ['X-Token'] is a custom headers key
      // please modify it according to the actual situation
      config.headers['X-Token'] = getToken()
    }
    inheritCurrentStore(config)
    return config
  },
  error => {
    // do something with request error
    console.log(error) // for debug
    return Promise.reject(error)
  }
)

// response interceptor
service.interceptors.response.use(
  /**
   * If you want to get http information such as headers or status
   * Please return  response => response
  */

  /**
   * Determine the request status by custom code
   * Here is just an example
   * You can also judge the status by HTTP Status Code
   */
  response => {
    const res = response.data

    // if the custom code is not 20000, it is judged as an error.
    if (res.code !== 20000) {
      // 50008: Illegal token; 50012: Other clients logged in; 50014: Token expired;
      if (res.code === 50008 || res.code === 50012 || res.code === 50014) {
        handleSessionExpired()
      } else {
        notifyError(res.message || '业务处理失败，请稍后重试。')
      }
      return Promise.reject(new Error(res.message || 'Error'))
    } else {
      return res
    }
  },
  error => {
    if (error && error.response && error.response.status === 401) {
      handleSessionExpired()
      return Promise.reject(error)
    }
    const message = businessErrorMessage(error)
    error.message = message
    // Background widgets (notifications and dashboard summaries) are allowed
    // to degrade to an empty/partial state.  Their callers opt in explicitly
    // so one unavailable source never stacks red messages over the page.
    if (!(error && error.config && error.config.silentError)) notifyError(message)
    return Promise.reject(error)
  }
)

export default service
