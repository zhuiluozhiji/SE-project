<template>
  <section class="page-panel">
    <h2 class="page-title">个人日历</h2>
    <el-row :gutter="12" class="legend">
      <el-col :span="4"><StatusTag label="课程" status="open" /></el-col>
      <el-col :span="4"><StatusTag label="活动" status="open" /></el-col>
      <el-col :span="4"><StatusTag label="推荐" status="full" /></el-col>
      <el-col :span="4"><StatusTag label="冲突" status="conflict" /></el-col>
      <el-col :span="4"><StatusTag label="结束" status="closed" /></el-col>
    </el-row>
    <EmptyState title="日历骨架已就绪" description="后续接入课程、活动、冲突标识和 ICS 导出。" />
  </section>
</template>

<script setup>
import EmptyState from '../components/EmptyState.vue'
import StatusTag from '../components/StatusTag.vue'
</script>

<style scoped>
.legend {
  margin-bottom: 16px;
}
</style>
