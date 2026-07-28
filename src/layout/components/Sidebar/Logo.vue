<template>
  <div class="sidebar-logo-container" :class="{'collapse':collapse}">
    <transition name="sidebarLogoFade">
      <router-link v-if="collapse" key="collapse" class="sidebar-logo-link" to="/">
        <img v-if="compactLogo" :src="compactLogo" class="sidebar-logo sidebar-logo--compact" alt="奇德芬芳">
        <h1 v-else class="sidebar-title">{{ title }} </h1>
      </router-link>
      <router-link v-else key="expand" class="sidebar-logo-link" to="/">
        <img v-if="logo" :src="logo" class="sidebar-logo sidebar-logo--full" alt="奇德芬芳 Kid Fragrance">
        <h1 v-else class="sidebar-title">{{ title }} </h1>
      </router-link>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'SidebarLogo',
  props: {
    collapse: {
      type: Boolean,
      required: true
    }
  },
  data() {
    return {
      title: '奇德芬芳 ERP',
      logo: require('@/assets/brand/qdf-logo.svg'),
      compactLogo: require('@/assets/brand/qdf-symbol.svg')
    }
  }
}
</script>

<style lang="scss" scoped>
.sidebarLogoFade-enter-active {
  transition: opacity 1.5s;
}

.sidebarLogoFade-enter,
.sidebarLogoFade-leave-to {
  opacity: 0;
}

.sidebar-logo-container {
  position: relative;
  width: 100%;
  height: 50px;
  line-height: 50px;
  background: linear-gradient(135deg, #3B342A, #2A2620);
  text-align: center;
  overflow: hidden;
  border-bottom: 1px solid rgba(231, 212, 172, .2);

  & .sidebar-logo-link {
    height: 100%;
    width: 100%;

    & .sidebar-logo {
      object-fit: contain;
      vertical-align: middle;
    }

    & .sidebar-logo--full {
      width: 168px;
      height: 48px;
    }

    & .sidebar-logo--compact {
      width: 32px;
      height: 42px;
    }

    & .sidebar-title {
      display: inline-block;
      margin: 0;
      color: #f7e7c4;
      font-weight: 600;
      line-height: 50px;
      font-size: 15px;
      letter-spacing: 1px;
      font-family: Avenir, Helvetica Neue, Arial, Helvetica, sans-serif;
      vertical-align: middle;
    }
  }

  &.collapse {
    .sidebar-logo {
      margin-right: 0;
    }
  }
}
</style>
