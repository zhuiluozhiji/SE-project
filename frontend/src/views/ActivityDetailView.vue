<template>
  <section class="page-panel">
    <h2 class="page-title">活动详情</h2>
    <p class="muted">当前活动 ID：{{ $route.params.id }}</p>
    <el-space>
      <el-button type="primary">一键加入日程</el-button>
      <el-button>检测冲突</el-button>
    </el-space>
  </section>
</template>
