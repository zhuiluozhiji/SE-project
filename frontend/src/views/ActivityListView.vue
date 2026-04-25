<template>
  <section class="page-panel">
    <h2 class="page-title">活动列表</h2>
    <el-form class="filter-row" inline>
      <el-form-item label="关键词">
        <el-input placeholder="人工智能 / 讲座 / 学院" />
      </el-form-item>
      <el-form-item label="校区">
        <el-select placeholder="全部校区" clearable>
          <el-option label="紫金港" value="zjg" />
          <el-option label="玉泉" value="yq" />
          <el-option label="西溪" value="xx" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary">查询</el-button>
      </el-form-item>
    </el-form>
    <EmptyState title="活动列表骨架已就绪" description="活动卡片、分页、筛选排序将在这里接入。" />
  </section>
</template>

<script setup>
import EmptyState from '../components/EmptyState.vue'
</script>

<style scoped>
.filter-row {
  margin-bottom: 16px;
}
</style>
