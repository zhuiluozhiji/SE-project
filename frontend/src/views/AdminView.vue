<template>
  <section class="page-panel">
    <h2 class="page-title">后台管理</h2>
    <el-space>
      <el-button type="primary">新增活动</el-button>
      <el-button>触发爬虫</el-button>
      <el-button>查看日志</el-button>
    </el-space>
    <div class="admin-placeholder">
      <EmptyState title="后台骨架已就绪" description="活动修正、下架、爬虫记录和统计看板将在这里展开。" />
    </div>
  </section>
</template>

<script setup>
import EmptyState from '../components/EmptyState.vue'
</script>

<style scoped>
.admin-placeholder {
  margin-top: 16px;
}
</style>
