<template>
  <section class="home-page fade-in">
    <div class="hero">
      <div>
        <p class="chip">AI 推荐引擎就绪</p>
        <h2 class="hero-title">今天也有值得参加的学术活动</h2>
        <p class="hero-subtitle">
          从兴趣标签、热门趋势与学院动态中发现最匹配的讲座、研讨会与学术沙龙。
        </p>
        <div class="hero-actions">
          <el-button type="primary">立即探索</el-button>
          <el-button>导入课表</el-button>
        </div>
      </div>
      <div class="hero-card">
        <h3>本周你的日程概览</h3>
        <div class="hero-metrics">
          <div>
            <strong>12</strong>
            <span>学术活动</span>
          </div>
          <div>
            <strong>4</strong>
            <span>课程冲突</span>
          </div>
          <div>
            <strong>6</strong>
            <span>推荐匹配</span>
          </div>
        </div>
        <p class="muted">建议优先参加“可解释推荐”标注的活动。</p>
      </div>
    </div>

    <div class="stats-grid">
      <div class="card stat-card" v-for="item in stats" :key="item.label">
        <p class="muted">{{ item.label }}</p>
        <h3>{{ item.value }}</h3>
        <span class="chip" :class="item.type">{{ item.tag }}</span>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h3 class="section-title">今日推荐</h3>
        <el-button text>查看全部</el-button>
      </div>
      <div class="card-grid recommendation-grid">
        <article class="card" v-for="card in recommendations" :key="card.title">
          <div class="card-top">
            <span class="chip">{{ card.tag }}</span>
            <span class="muted">{{ card.time }}</span>
          </div>
          <h4>{{ card.title }}</h4>
          <p class="muted">{{ card.desc }}</p>
          <div class="card-meta">
            <span>{{ card.location }}</span>
            <el-button size="small" type="primary" plain>查看详情</el-button>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
const stats = [
  { label: '本周新增活动', value: '38 场', tag: '紫金港为主', type: '' },
  { label: '与你兴趣匹配', value: '14 场', tag: 'AI / 数据 / 管理', type: 'warning' },
  { label: '已加入日程', value: '6 场', tag: '同步到日历', type: '' }
]

const recommendations = [
  {
    title: '生成式 AI 与科研写作的新协作方式',
    time: '今天 19:00',
    tag: '高匹配推荐',
    location: '紫金港｜人文学院',
    desc: '与你的“人工智能 + 学术写作”兴趣标签匹配，活动即将开始。'
  },
  {
    title: '跨学科科研方法工作坊：从数据到洞察',
    time: '明天 14:00',
    tag: '热门活动',
    location: '玉泉｜科技馆',
    desc: '近期报名热度上升，适合管理与数据方向的同学。'
  },
  {
    title: '青年学者圆桌：开放科学与学术伦理',
    time: '本周五 15:30',
    tag: '学院推荐',
    location: '西溪｜学术报告厅',
    desc: '来自学院官方推荐名单，强调跨领域交流与实践案例。'
  }
]
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 24px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
  gap: 20px;
}

.hero-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.hero-card {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid #eadac6;
  padding: 18px;
  box-shadow: 0 16px 32px rgba(54, 40, 18, 0.1);
}

.hero-card h3 {
  margin: 0 0 12px;
  font-family: "Noto Serif SC", "Noto Sans SC", serif;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 8px;
}

.hero-metrics strong {
  display: block;
  font-size: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.stat-card h3 {
  margin: 6px 0 8px;
  font-size: 22px;
}

.section {
  display: grid;
  gap: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.recommendation-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  color: #7a6a55;
  font-size: 12px;
}

@media (max-width: 960px) {
  .hero {
    grid-template-columns: 1fr;
  }
}
</style>
