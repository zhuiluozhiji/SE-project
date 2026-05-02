<template>
  <section class="detail-page fade-in">
    <div class="hero detail-hero">
      <div>
        <p class="chip">{{ activity.badge }}</p>
        <h2 class="hero-title">{{ activity.title }}</h2>
        <p class="hero-subtitle">主讲人：{{ activity.speaker }}｜组织单位：{{ activity.org }}</p>
      </div>
      <div class="action-card">
        <div class="action-top">
          <span class="chip warning">{{ activity.time }}</span>
          <span class="muted">{{ activity.location }}</span>
        </div>
        <el-button type="primary" size="large">一键加入日程</el-button>
        <el-button size="large" @click="openConflict">检测冲突</el-button>
        <p class="muted">已为你预检 2 个潜在冲突。</p>
      </div>
    </div>

    <div class="detail-grid">
      <div class="card">
        <h3 class="section-title">关键信息</h3>
        <div class="info-grid">
          <div>
            <span class="muted">时间</span>
            <strong>{{ activity.fullTime }}</strong>
          </div>
          <div>
            <span class="muted">地点</span>
            <strong>{{ activity.locationDetail }}</strong>
          </div>
          <div>
            <span class="muted">标签</span>
            <div class="tag-row">
              <span class="chip" v-for="tag in activity.tags" :key="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3 class="section-title">活动简介</h3>
        <p class="muted">{{ activity.summary }}</p>
        <div class="divider"></div>
        <div class="speaker">
          <div class="avatar">{{ activity.avatar }}</div>
          <div>
            <strong>{{ activity.speaker }}</strong>
            <p class="muted">研究方向：{{ activity.topic }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card conflict-card">
      <div>
        <h3 class="section-title">冲突提示</h3>
        <p class="muted">{{ activity.conflictSummary }}</p>
      </div>
      <el-button type="danger" plain @click="openConflict">查看冲突明细</el-button>
    </div>

    <el-dialog v-model="conflictVisible" class="conflict-dialog" width="520px">
      <template #header>
        <div class="modal-header">
          <h4>冲突明细</h4>
          <span class="muted">{{ activity.conflicts.length }} 项</span>
        </div>
      </template>
      <div class="modal-body">
        <div class="modal-item" v-for="item in activity.conflicts" :key="item.title">
          <strong>{{ item.title }}</strong>
          <p class="muted">{{ item.time }} · {{ item.location }}</p>
        </div>
      </div>
      <template #footer>
        <div class="modal-actions">
          <el-button @click="conflictVisible = false">取消</el-button>
          <el-button type="primary">仍要加入</el-button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const conflictVisible = ref(false)

const openConflict = () => {
  conflictVisible.value = true
}

const activityMap = {
  1: {
    title: 'AI 赋能城市治理：从算法到公共服务',
    badge: '开放报名',
    speaker: '王昱教授（公共管理学院）',
    org: '公共政策研究中心',
    time: '今天 15:00',
    fullTime: '2026-05-01 15:00 - 17:00',
    location: '紫金港 · 行政楼',
    locationDetail: '紫金港 · 行政楼 A302',
    tags: ['人工智能', '城市治理', '跨学科'],
    summary: '聚焦城市治理智能化转型，讨论数据治理、算法应用与公共服务协同路径。',
    avatar: 'WY',
    topic: '城市数据治理、公共政策分析',
    conflictSummary: '检测到与“科研方法论课程”时间重叠 45 分钟，可选择继续加入。',
    conflicts: [
      { title: '科研方法论课程', time: '14:30 - 16:15', location: '教学楼 2A' },
      { title: '学术写作小组讨论', time: '15:50 - 16:30', location: '线上会议' }
    ]
  },
  2: {
    title: '量子信息前沿报告：纠缠与计算的新突破',
    badge: '推荐',
    speaker: '赵谨教授（信息学院）',
    org: '量子信息实验室',
    time: '明天 10:30',
    fullTime: '2026-05-02 10:30 - 12:00',
    location: '玉泉 · 信息学院报告厅',
    locationDetail: '玉泉 · 信息学院报告厅',
    tags: ['量子计算', '前沿报告'],
    summary: '面向研究生与青年学者的前沿分享，涵盖纠缠实验与量子算法最新成果。',
    avatar: 'ZJ',
    topic: '量子算法、纠缠实验',
    conflictSummary: '检测到与“科研导师组会”时间冲突 30 分钟，可选择继续加入。',
    conflicts: [
      { title: '科研导师组会', time: '10:00 - 11:00', location: '信息学院 B201' }
    ]
  },
  3: {
    title: '社会科学数据分析工作坊',
    badge: '名额紧张',
    speaker: '刘珊副教授（社会学院）',
    org: '数据方法中心',
    time: '本周三 13:30',
    fullTime: '2026-05-03 13:30 - 16:30',
    location: '西溪 · 人文楼 402',
    locationDetail: '西溪 · 人文楼 402',
    tags: ['数据分析', '工作坊'],
    summary: '结合真实调查数据讲解研究设计、清洗与可视化流程。',
    avatar: 'LS',
    topic: '社会科学研究方法、数据可视化',
    conflictSummary: '检测到与“统计建模课程”时间重叠 60 分钟，可选择继续加入。',
    conflicts: [
      { title: '统计建模课程', time: '13:00 - 15:00', location: '线上课堂' },
      { title: '实验室例会', time: '15:00 - 15:30', location: '社会学院会议室' }
    ]
  },
  4: {
    title: '新生科研导航：如何选择研究方向',
    badge: '开放报名',
    speaker: '孙廷博士（学术发展中心）',
    org: '学术发展中心',
    time: '本周四 18:00',
    fullTime: '2026-05-04 18:00 - 19:30',
    location: '紫金港 · 学术交流中心',
    locationDetail: '紫金港 · 学术交流中心',
    tags: ['科研规划', '新生'],
    summary: '面向新生的科研入门交流，帮助建立研究方向与方法论意识。',
    avatar: 'ST',
    topic: '科研规划、学术训练',
    conflictSummary: '检测到与“学院新生班会”时间冲突 20 分钟，可选择继续加入。',
    conflicts: [
      { title: '学院新生班会', time: '18:00 - 18:50', location: '学术交流中心 301' }
    ]
  },
  5: {
    title: '人文社科青年论坛',
    badge: '学院推荐',
    speaker: '周涵副教授（人文学院）',
    org: '人文学院',
    time: '本周五 14:00',
    fullTime: '2026-05-05 14:00 - 16:00',
    location: '西溪 · 文科楼 201',
    locationDetail: '西溪 · 文科楼 201',
    tags: ['人文社科', '论坛'],
    summary: '围绕学术表达与跨学科协作，邀请多学院青年学者对话。',
    avatar: 'ZH',
    topic: '学术表达、跨学科协作',
    conflictSummary: '检测到与“学术写作课”时间重叠 30 分钟，可选择继续加入。',
    conflicts: [
      { title: '学术写作课', time: '13:30 - 15:00', location: '文科楼 101' },
      { title: '导师例会', time: '15:30 - 16:00', location: '人文学院会议室' }
    ]
  },
  6: {
    title: '科研写作与国际投稿策略分享',
    badge: '热门',
    speaker: '陈亦文教授（信息学院）',
    org: '学术发展中心',
    time: '本周六 16:00',
    fullTime: '2026-05-06 16:00 - 18:00',
    location: '玉泉 · 图书馆报告厅',
    locationDetail: '玉泉 · 图书馆报告厅',
    tags: ['学术写作', '科研训练'],
    summary: '从选刊、投稿到审稿回复，提供实操策略与案例拆解。',
    avatar: 'CY',
    topic: '知识管理、AI 写作辅助、人机协作',
    conflictSummary: '检测到与“科研伦理课程”时间重叠 45 分钟，可选择继续加入。',
    conflicts: [
      { title: '科研伦理课程', time: '16:00 - 17:00', location: '图书馆 B201' },
      { title: '学院读书会', time: '17:30 - 18:00', location: '线上会议' }
    ]
  }
}

const activity = computed(() => {
  const id = Number(route.params.id)
  return activityMap[id] || activityMap[1]
})
</script>

<style scoped>
.detail-page {
  display: grid;
  gap: 20px;
}

.detail-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.7fr);
  gap: 20px;
}

.action-card {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid #eadac6;
  padding: 16px;
  display: grid;
  gap: 10px;
  box-shadow: 0 14px 30px rgba(54, 40, 18, 0.1);
}

.action-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.info-grid {
  display: grid;
  gap: 14px;
}

.info-grid strong {
  display: block;
  margin-top: 4px;
}

.speaker {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #0f766e;
  color: #ffffff;
  font-weight: 600;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.conflict-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #fff4f1;
  border-color: #f0d1c8;
}


.conflict-dialog :deep(.el-dialog) {
  border-radius: 16px;
  border: 1px solid #eadac6;
  box-shadow: 0 16px 32px rgba(54, 40, 18, 0.12);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.modal-body {
  display: grid;
  gap: 12px;
}

.modal-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8efe2;
  border: 1px solid #e2d3c0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
}

@media (max-width: 960px) {
  .detail-hero {
    grid-template-columns: 1fr;
  }
}
</style>
