<template>
  <div class="login-page">
    <div class="brand-panel">
      <div class="brand-mark"><img src="@/assets/brand/qdf-symbol.svg" alt="奇德芬芳"></div>
      <div class="brand-copy"><span>QIDE FENFANG</span><h1>月子会所<br>ERP 管理云平台</h1><p>让客户、销售、客房、护理、膳食与财务协作更顺畅。</p></div>
      <div class="feature-list"><div><i class="el-icon-data-analysis" /><span>经营数据实时汇总</span></div><div><i class="el-icon-house" /><span>入住服务全程协同</span></div><div><i class="el-icon-lock" /><span>权限与审批安全可控</span></div></div>
      <div class="decor decor-one" /><div class="decor decor-two" />
    </div>
    <div class="login-panel">
      <el-form ref="loginForm" :model="loginForm" :rules="loginRules" class="login-form" autocomplete="on">
        <div class="login-title"><span>WELCOME BACK</span><h2>系统登录</h2><p>登录奇德芬芳月子会所 ERP 工作台</p></div>
        <el-form-item prop="username"><label>账号</label><el-input ref="username" v-model="loginForm.username" prefix-icon="el-icon-user" placeholder="请输入账号" name="username" autocomplete="username" /></el-form-item>
        <el-form-item prop="password"><div class="password-label"><label>密码</label><span>忘记密码？</span></div><el-input ref="password" v-model="loginForm.password" :type="passwordType" prefix-icon="el-icon-lock" placeholder="请输入密码" name="password" autocomplete="current-password" @keyup.enter.native="handleLogin"><i slot="suffix" :class="passwordType === 'password' ? 'el-icon-view' : 'el-icon-hide'" class="password-eye" @click="showPwd" /></el-input></el-form-item>
        <div class="login-options"><el-checkbox v-model="remember">记住账号</el-checkbox><span><i class="el-icon-connection" /> 安全连接</span></div>
        <el-button :loading="loading" class="login-button" type="primary" @click.native.prevent="handleLogin">登 录</el-button>
        <div class="support"><i class="el-icon-headset" /> 登录遇到问题，请联系系统管理员</div>
      </el-form>
      <div class="version">V1.0 · 基于原 ERP 业务框架复刻</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      loginForm: { username: 'admin', password: '' },
      loginRules: {
        username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
        password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少 6 位', trigger: 'blur' }]
      },
      passwordType: 'password',
      remember: true,
      loading: false,
      redirect: undefined,
      otherQuery: {}
    }
  },
  watch: {
    $route: {
      handler(route) {
        const query = route.query
        if (query) {
          this.redirect = query.redirect
          this.otherQuery = Object.keys(query).reduce((acc, cur) => { if (cur !== 'redirect') acc[cur] = query[cur]; return acc }, {})
        }
      },
      immediate: true
    }
  },
  mounted() { if (!this.loginForm.username) this.$refs.username.focus(); else this.$refs.password.focus() },
  methods: {
    showPwd() { this.passwordType = this.passwordType === 'password' ? 'text' : 'password'; this.$nextTick(() => this.$refs.password.focus()) },
    handleLogin() {
      this.$refs.loginForm.validate(valid => {
        if (!valid) return
        this.loading = true
        this.$store.dispatch('user/login', this.loginForm).then(() => {
          this.$router.push({ path: this.redirect || '/', query: this.otherQuery })
        }).finally(() => { this.loading = false })
      })
    }
  }
}
</script>

<style lang="scss">
.login-page .el-input__inner{height:48px;border-radius:8px;border-color:#e1d7c6;background:#fffdf9;padding-left:42px}.login-page .el-input__prefix{left:13px;line-height:48px;color:#a89e8d}.login-page .el-input__suffix{line-height:48px}.login-page .el-form-item{margin-bottom:25px}.login-page .el-form-item__error{padding-top:5px}.login-page .el-checkbox__input.is-checked .el-checkbox__inner,.login-page .el-checkbox__input.is-indeterminate .el-checkbox__inner{background:#B8945A;border-color:#B8945A}.login-page .el-checkbox__input.is-checked+.el-checkbox__label{color:#8C6A36}
</style>
<style lang="scss" scoped>
.login-page{min-height:100vh;display:grid;grid-template-columns:minmax(460px,46%) 1fr;background:#FBF7F0}.brand-panel{position:relative;overflow:hidden;padding:58px 10%;display:flex;flex-direction:column;color:#fff;background:linear-gradient(145deg,#3B342A 0%,#2A2620 58%,#211E19 100%)}.brand-mark{display:grid;place-items:center;width:64px;height:72px;border:1px solid rgba(231,212,172,.38);border-radius:18px;background:rgba(231,212,172,.07);box-shadow:0 10px 28px rgba(0,0,0,.18),inset 0 0 22px rgba(231,212,172,.04)}.brand-mark img{width:37px;height:58px;object-fit:contain}.brand-copy{margin:auto 0}.brand-copy>span{font-size:12px;letter-spacing:4px;color:#E7D4AC}.brand-copy h1{font-size:46px;line-height:1.25;margin:18px 0 20px}.brand-copy p{max-width:430px;font-size:15px;line-height:2;color:#d8cdbd}.feature-list{display:flex;gap:23px;flex-wrap:wrap}.feature-list div{display:flex;align-items:center;gap:7px;font-size:12px;color:#e1d7c6}.feature-list i{color:#E7D4AC}.decor{position:absolute;border-radius:50%;border:1px solid rgba(231,212,172,.13)}.decor-one{width:430px;height:430px;right:-190px;top:-100px}.decor-two{width:280px;height:280px;left:-140px;bottom:-100px}.login-panel{position:relative;display:grid;place-items:center;padding:60px;background:linear-gradient(160deg,#fff 0%,#FBF7F0 100%)}.login-form{width:410px;max-width:100%}.login-title{margin-bottom:36px}.login-title span{color:#8C6A36;font-size:11px;font-weight:700;letter-spacing:2px}.login-title h2{font-size:31px;margin:8px 0 10px;color:#2B2620}.login-title p{margin:0;color:#A89E8D;font-size:14px}.login-form label{display:block;margin-bottom:9px;color:#6E665A;font-size:13px}.password-label{display:flex;justify-content:space-between}.password-label span{font-size:12px;color:#8C6A36;cursor:pointer}.password-eye{cursor:pointer;color:#A89E8D}.login-options{display:flex;align-items:center;justify-content:space-between;margin:-4px 0 24px;color:#A89E8D;font-size:12px}.login-button{width:100%;height:48px;border:0;border-radius:8px;background:linear-gradient(135deg,#E9D4A4,#B8945A 52%,#8C6A36);box-shadow:0 10px 24px rgba(140,106,54,.22);font-size:15px}.support{text-align:center;margin-top:28px;color:#A89E8D;font-size:12px}.version{position:absolute;bottom:28px;color:#b9ae9d;font-size:11px}@media(max-width:900px){.login-page{grid-template-columns:1fr}.brand-panel{display:none}.login-panel{padding:32px 20px}.version{bottom:16px}}
</style>
