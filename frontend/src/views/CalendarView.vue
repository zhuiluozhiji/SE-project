<template>
  <section class="calendar-page fade-in">
    <div class="page-panel calendar-header">
      <div>
        <h2 class="page-title">个人日历</h2>
        <p class="muted">课程与活动统一呈现，冲突与状态清晰标识。</p>
      </div>
      <div class="header-actions">
        <el-button>刷新日程</el-button>
        <el-button type="primary">导出 ICS</el-button>
      </div>
    </div>

    <div class="legend">
      <StatusTag label="课程" status="open" />
      <StatusTag label="活动" status="open" />
      <StatusTag label="推荐" status="full" />
      <StatusTag label="冲突" status="conflict" />
      <StatusTag label="结束" status="closed" />
    </div>

    <div class="calendar-grid">
      <div class="card week-view">
        <div class="week-header">
          <span>周一</span><span>周二</span><span>周三</span><span>周四</span><span>周五</span><span>周六</span><span>周日</span>
        </div>
        <div class="week-body">
          <div class="day" v-for="day in 7" :key="day">
            <div class="day-slot" v-for="slot in 4" :key="slot">
              <span class="event" v-if="eventMap[day] && eventMap[day][slot]">
                {{ eventMap[day][slot] }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card side-panel">
        <h3 class="section-title">即将开始</h3>
        <div class="schedule-list">
          <div class="schedule-item" v-for="item in schedules" :key="item.title">
            <div>
              <strong>{{ item.title }}</strong>
              <p class="muted">{{ item.time }} · {{ item.location }}</p>
            </div>
            <span class="chip" :class="item.level">{{ item.status }}</span>
          </div>
        </div>
        <div class="divider"></div>
        <div class="conflict-panel">
          <h4>冲突提醒</h4>
          <p class="muted">本周 2 个活动与课程重叠，请及时处理。</p>
          <el-button type="danger" plain>查看冲突详情</el-button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import StatusTag from '../components/StatusTag.vue'

const schedules = [
  {
    title: '科研写作工作坊',
    time: '今天 19:00',
    location: '紫金港 A102',
    status: '冲突',
    level: 'danger'
  },
  {
    title: '量子信息前沿报告',
    time: '明天 10:30',
    location: '玉泉报告厅',
    status: '活动',
    level: ''
  },
  {
    title: '统计建模课程',
    time: '周四 09:00',
    location: '线上',
    status: '课程',
    level: ''
  }
]

const eventMap = {
  1: { 2: '统计建模' },
  2: { 1: '跨学科研讨' },
  3: { 3: 'AI 写作分享' },
  4: { 2: '数据分析课' },
  5: { 1: '青年论坛' },
  6: { 2: '阅读小组' }
}
</script>

<style scoped>
.calendar-page {
  display: grid;
  gap: 16px;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.legend {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.calendar-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 16px;
}

.week-view {
  padding: 16px;
}

.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-weight: 600;
  color: #5c4f3d;
  margin-bottom: 10px;
}

.week-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.day {
  display: grid;
  gap: 6px;
}

.day-slot {
  height: 58px;
  border-radius: 12px;
  background: #f8efe2;
  border: 1px dashed #e2d3c0;
  display: grid;
  place-items: center;
  font-size: 12px;
  color: #5b5142;
}

.event {
  background: #0f766e;
  color: #ffffff;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
}

.side-panel {
  display: grid;
  gap: 12px;
}

.schedule-list {
  display: grid;
  gap: 12px;
}

.schedule-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.conflict-panel {
  background: #fff4f1;
  border: 1px solid #f0d1c8;
  border-radius: 12px;
  padding: 12px;
}

@media (max-width: 960px) {
  .calendar-grid {
    grid-template-columns: 1fr;
  }
}
</style>
