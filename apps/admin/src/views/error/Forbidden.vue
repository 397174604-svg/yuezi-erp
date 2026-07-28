<template>
  <el-result icon="warning" title="403" sub-title="你的角色无权访问该模块">
    <template #extra>
      <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
    </template>
  </el-result>
</template>

<script setup lang="ts"></script>
