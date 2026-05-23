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
          <el-button type="primary" @click="$router.push('/activities')">立即探索</el-button>
          <el-button @click="$router.push('/courses/import')">导入课表</el-button>
        </div>
      </div>
      <div class="hero-card">
        <h3>本周你的日程概览</h3>
        <div class="hero-metrics">
          <div>
            <strong>{{ stats.totalActivities || '--' }}</strong>
            <span>学术活动</span>
          </div>
          <div>
            <strong>{{ stats.conflicts || '--' }}</strong>
            <span>课程冲突</span>
          </div>
          <div>
            <strong>{{ stats.matched || '--' }}</strong>
            <span>推荐匹配</span>
          </div>
        </div>
        <p class="muted">建议优先参加"可解释推荐"标注的活动。</p>
      </div>
    </div>

    <div class="stats-grid">
      <div class="card stat-card" v-for="item in statCards" :key="item.label">
        <p class="muted">{{ item.label }}</p>
        <h3>{{ item.value }}</h3>
        <span class="chip" :class="item.type">{{ item.tag }}</span>
      </div>
    </div>

    <div class="section">
      <div class="section-header">
        <h3 class="section-title">今日推荐</h3>
        <el-button text @click="$router.push('/activities?sort=recommend')">查看全部</el-button>
      </div>

      <div v-if="loading" class="card-grid recommendation-grid">
        <div class="card skeleton" v-for="n in 3" :key="n">
          <div class="skeleton-line w-60"></div>
          <div class="skeleton-line w-80"></div>
          <div class="skeleton-line w-40"></div>
        </div>
      </div>

      <div v-else-if="error" class="empty-state">
        <p>加载失败</p>
        <small>{{ error }}</small>
        <el-button size="small" @click="fetchRecommendations">重试</el-button>
      </div>

      <div v-else class="card-grid recommendation-grid">
        <article class="card" v-for="card in recommendations" :key="card.id || card.title">
          <div class="card-top">
            <span class="chip">{{ card.reason || card.tag || '推荐' }}</span>
            <span class="muted">{{ formatTime(card.start_time || card.time) }}</span>
          </div>
          <h4>{{ card.title }}</h4>
          <p class="muted">{{ truncate(card.description || card.desc, 60) }}</p>
          <div class="card-meta">
            <span>{{ card.campus || '' }} {{ card.location || '' }}</span>
            <el-button size="small" type="primary" plain @click="$router.push(`/activities/${card.id}`)">
              查看详情
            </el-button>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getRecommendedActivities } from '../api/recommendations'
import { getActivities } from '../api/activities'

const loading = ref(false)
const error = ref('')
const recommendations = ref([])

const stats = reactive({
  totalActivities: '--',
  conflicts: '--',
  matched: '--'
})

const statCards = ref([
  { label: '本周新增活动', value: '-- 场', tag: '紫金港为主', type: '' },
  { label: '与你兴趣匹配', value: '-- 场', tag: 'AI / 数据 / 管理', type: 'warning' },
  { label: '已加入日程', value: '-- 场', tag: '同步到日历', type: '' }
])

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const truncate = (text, max) => {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}

const fetchRecommendations = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getRecommendedActivities({ limit: 6 })
    recommendations.value = res.data?.items || res.data?.activities || res.data || []
    if (res.data?.total) {
      stats.matched = res.data.total
    }
  } catch {
    error.value = '推荐数据加载失败'
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getActivities({ page: 1, page_size: 1 })
    if (res.data?.total !== undefined) {
      stats.totalActivities = res.data.total
      statCards.value[0].value = `${res.data.total} 场`
    }
  } catch {
    // 统计非关键，静默失败
  }
}

onMounted(() => {
  fetchRecommendations()
  fetchStats()
})
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

.empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  min-height: 180px;
  gap: 8px;
  color: #6b7280;
}

.skeleton {
  min-height: 140px;
  display: grid;
  gap: 12px;
  align-content: start;
}

.skeleton-line {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, #ece6db 25%, #f0ebe3 50%, #ece6db 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.w-60 { width: 60%; }
.w-80 { width: 80%; }
.w-40 { width: 40%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (max-width: 960px) {
  .hero {
    grid-template-columns: 1fr;
  }
}
</style>
