<template>
  <section class="home-page fade-in">
    <div class="hero">
      <div class="hero-body">
        <span class="hero-kicker">Campus Academic Events</span>
        <h2 class="hero-title">发现属于你的学术活动</h2>
        <p class="hero-desc">
          基于兴趣标签与学术轨迹，从全校讲座、研讨会与沙龙中为你筛选最相关的活动。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="$router.push('/activities')">立即探索</el-button>
          <el-button size="large" @click="$router.push('/courses/import')">导入课表</el-button>
        </div>
      </div>
      <div class="hero-stats">
        <div class="hero-stat" v-for="s in heroStats" :key="s.label">
          <strong>{{ s.value }}</strong>
          <span>{{ s.label }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-head">
        <h3 class="section-title">为你推荐</h3>
        <el-button text type="primary" @click="$router.push('/activities?sort=recommend')">查看全部</el-button>
      </div>

      <div v-if="loading" class="card-grid rec-grid">
        <div class="card skeleton" v-for="n in 3" :key="n">
          <div class="sk-line w-50"></div>
          <div class="sk-line w-80"></div>
          <div class="sk-line w-30"></div>
        </div>
      </div>

      <div v-else-if="error" class="empty-state">
        <p>推荐数据加载失败</p>
        <small>{{ error }}</small>
        <el-button size="small" @click="fetchRecommendations">重试</el-button>
      </div>

      <div v-else class="card-grid rec-grid">
        <article
          class="card rec-card"
          v-for="item in recommendations"
          :key="item.id || item.title"
          @click="openRecommendation(item)"
        >
          <div class="rec-top">
            <span class="chip rec-label">{{ item.matched_tags?.[0] || item.tag || '推荐' }}</span>
            <span class="faint">{{ fmtDate(item.start_time || item.time) }}</span>
          </div>
          <p class="rec-reason" v-if="item.reason">{{ item.reason }}</p>
          <h4 class="rec-title">{{ item.title }}</h4>
          <p class="muted rec-desc">{{ truncate(item.description || item.desc, 64) }}</p>
          <div class="rec-foot">
            <span class="faint">{{ item.campus || '' }} {{ item.location || '' }}</span>
            <span class="rec-arrow">&rarr;</span>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendedActivities } from '../api/recommendations'
import { getActivities, recordActivityInteraction } from '../api/activities'
import { defaultRecommendedActivities } from '../utils/constants'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const recommendations = ref([])

const heroStats = reactive([
  { label: '可参与活动', value: '--' },
  { label: '推荐匹配', value: '--' },
  { label: '本周新增', value: '--' }
])

const fmtDate = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())}`
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
    const items = res.data?.items || res.data?.activities || res.data || []
    recommendations.value = items.length ? items : defaultRecommendedActivities
    if (res.data?.total !== undefined) {
      heroStats[1].value = res.data.total
    } else {
      heroStats[1].value = recommendations.value.length
    }
  } catch {
    recommendations.value = defaultRecommendedActivities
    heroStats[1].value = defaultRecommendedActivities.length
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await getActivities({ page: 1, page_size: 1 })
    if (res.data?.total !== undefined) {
      heroStats[0].value = res.data.total
      heroStats[2].value = Math.min(res.data.total, 12)
    }
  } catch { /* 非关键 */ }
}

const openRecommendation = async (item) => {
  if (!item?.id) return
  try {
    await recordActivityInteraction(item.id, {
      action_type: 'recommend_click',
      source: 'home_recommendation'
    })
  } catch { /* 行为上报不阻塞跳转 */ }
  router.push(`/activities/${item.id}`)
}

onMounted(() => {
  fetchRecommendations()
  fetchStats()
})
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 32px;
}

/* ── Hero ── */
.hero {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 32px;
  padding: 28px 32px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
}

.hero-body {
  max-width: 560px;
}

.hero-kicker {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 16px;
}

.hero-title {
  margin: 0 0 14px;
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.02em;
  font-family: var(--font-display);
}

.hero-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.65;
  max-width: 440px;
}

.hero-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.hero-stats {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  min-width: 170px;
}

.hero-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 24px;
  background: var(--bg-warm);
  text-align: center;
}

.hero-stat strong {
  font-size: 28px;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--text-primary);
}

.hero-stat span {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* ── 推荐区 ── */
.section {
  display: grid;
  gap: 16px;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.rec-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.rec-card {
  cursor: pointer;
  min-width: 0;
}

.rec-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.rec-label {
  max-width: calc(100% - 52px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rec-reason {
  margin: 0 0 12px;
  min-height: 40px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rec-title {
  margin: 0 0 6px;
  font-size: 17px;
  font-family: var(--font-display);
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--text-primary);
}

.rec-desc {
  margin-bottom: 14px;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rec-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
}

.rec-foot .faint {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rec-arrow {
  font-size: 16px;
  color: var(--text-tertiary);
  transition: color 0.2s, transform 0.2s;
}

.rec-card:hover .rec-arrow {
  color: var(--accent);
  transform: translateX(3px);
}

/* ── 骨架屏 ── */
.skeleton {
  min-height: 140px;
  display: grid;
  gap: 12px;
  align-content: start;
}

.sk-line {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--bg-muted) 25%, var(--border-light) 50%, var(--bg-muted) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.w-50 { width: 50%; }
.w-80 { width: 80%; }
.w-30 { width: 30%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (max-width: 960px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 24px;
  }
  .hero-title {
    font-size: 24px;
  }
  .hero-stats {
    flex-direction: row;
  }
  .hero-stat {
    flex: 1;
  }
}
</style>
