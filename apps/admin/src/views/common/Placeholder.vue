<template>
  <el-result icon="info" :title="title" sub-title="该模块将在 C1 阶段填充（宽表 + 表单 + 批量操作；对应后端接口已就绪）">
    <template #extra>
      <el-tag type="warning" effect="plain">建设中 · C1</el-tag>
    </template>
  </el-result>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const title = computed(() => (useRoute().meta?.title as string) || '建设中')
</script>
