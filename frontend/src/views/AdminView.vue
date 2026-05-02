<template>
  <section class="admin-page fade-in">
    <div class="page-panel admin-header">
      <div>
        <h2 class="page-title">后台管理</h2>
        <p class="muted">活动维护、标签修正与爬虫记录统一管理。</p>
      </div>
      <el-space>
        <el-button type="primary">新增活动</el-button>
        <el-button>触发爬虫</el-button>
        <el-button>查看日志</el-button>
      </el-space>
    </div>

    <div class="stats-grid">
      <div class="card stat-card" v-for="item in stats" :key="item.label">
        <p class="muted">{{ item.label }}</p>
        <h3>{{ item.value }}</h3>
        <span class="chip" :class="item.level">{{ item.tag }}</span>
      </div>
    </div>

    <div class="card admin-table">
      <div class="table-header">
        <h3 class="section-title">活动管理列表</h3>
        <el-input placeholder="搜索活动标题" class="table-search" />
      </div>
      <el-table :data="rows" style="width: 100%" stripe>
        <el-table-column prop="title" label="活动标题" />
        <el-table-column prop="campus" label="校区" width="120" />
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="操作" width="160">
          <template #default>
            <el-button size="small" type="primary" plain>编辑</el-button>
            <el-button size="small" type="danger" plain>下架</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script setup>
const stats = [
  { label: '今日新增', value: '6 场', tag: '爬虫 4 | 手动 2', level: '' },
  { label: '待审核', value: '12 场', tag: '需人工确认', level: 'warning' },
  { label: '已下架', value: '3 场', tag: '状态同步完成', level: '' }
]

const rows = [
  {
    title: 'AI 赋能城市治理：从算法到公共服务',
    campus: '紫金港',
    time: '2026-05-01 15:00',
    status: 'open'
  },
  {
    title: '量子信息前沿报告：纠缠与计算的新突破',
    campus: '玉泉',
    time: '2026-05-02 10:30',
    status: 'open'
  },
  {
    title: '社会科学数据分析工作坊',
    campus: '西溪',
    time: '2026-05-03 13:30',
    status: 'offline'
  }
]
</script>

<style scoped>
.admin-page {
  display: grid;
  gap: 20px;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.admin-table {
  display: grid;
  gap: 12px;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-search {
  width: 240px;
}
</style>
