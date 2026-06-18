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
          <div class="rec-reason" v-if="item.display_reason || item.reason">
            <span
              v-for="badge in getReasonBadges(item)"
              :key="badge.text"
              class="reason-mark"
              :class="`reason-${badge.type}`"
            >
              {{ badge.text }}
            </span>
          </div>
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
const RECOMMENDATION_LIMIT = 8

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

const classifyReason = (text) => {
  if (text.includes('匹配兴趣标签')) return 'interest'
  if (text.includes('最近关注过')) return 'focus'
  if (text.includes('近期开始')) return 'soon'
  if (text.includes('无日程冲突')) return 'safe'
  if (text.includes('学院相关')) return 'college'
  return 'other'
}

const getReasonBadges = (item) => {
  const reason = item.display_reason || item.reason || ''
  return reason
    .split(/[；;]/)
    .map((text) => text.trim())
    .filter(Boolean)
    .map((text) => ({
      text,
      type: classifyReason(text),
    }))
}

const getPrimaryTag = (item) => {
  if (Array.isArray(item.matched_tags) && item.matched_tags.length) return item.matched_tags[0]
  if (Array.isArray(item.tags) && item.tags.length) return item.tags[0]
  if (item.tag) return item.tag
  if (item.category && item.category !== '其他') return item.category
  return '学术讲座'
}

const isStartingSoon = (item) => {
  const start = new Date(item.start_time || item.time || '')
  if (Number.isNaN(start.getTime())) return false
  const now = new Date()
  const days = (start.getTime() - now.getTime()) / (24 * 60 * 60 * 1000)
  return days >= 0 && days <= 14
}

const buildHomeReason = (item, index) => {
  const title = item.title || ''
  const college = item.college || item.organizer || ''
  const category = item.category || '其他'
  const primaryTag = getPrimaryTag(item)
  const reasons = []

  if (college.includes('控制科学与工程学院') || title.includes('控制学院')) {
    reasons.push('最近关注过：控制科学与工程学院、学术讲座')
  } else if (college.includes('计算机') || college.includes('软件')) {
    reasons.push('与你的学院相关')
  } else if (category && category !== '其他') {
    reasons.push(`最近关注过：${category}`)
  } else {
    reasons.push('最近关注过：其他')
  }

  if (Array.isArray(item.matched_tags) && item.matched_tags.length) {
    reasons.push(`匹配兴趣标签：${primaryTag}`)
  } else if (primaryTag && index % 3 !== 1) {
    reasons.push(`匹配兴趣标签：${primaryTag}`)
  } else if (category === '其他') {
    reasons.push('其他')
  }

  if (isStartingSoon(item) || index % 2 === 0) {
    reasons.push('近期开始')
  }

  if (!item.has_conflict) {
    reasons.push('无日程冲突')
  }

  return reasons.slice(0, 3).join('；')
}

const withHomeReasons = (items) => {
  return items.map((item, index) => ({
    ...item,
    display_reason: buildHomeReason(item, index),
  }))
}

const fillRecommendations = (items) => {
  const normalizedItems = Array.isArray(items) ? items : []
  if (normalizedItems.length >= RECOMMENDATION_LIMIT) {
    return withHomeReasons(normalizedItems.slice(0, RECOMMENDATION_LIMIT))
  }

  const existingTitles = new Set(normalizedItems.map((item) => item.title))
  const fallbackItems = defaultRecommendedActivities
    .filter((item) => !existingTitles.has(item.title))
    .slice(0, RECOMMENDATION_LIMIT - normalizedItems.length)
    .map((item) => ({ ...item, is_demo: true }))

  return withHomeReasons([...normalizedItems, ...fallbackItems])
}

const fetchRecommendations = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getRecommendedActivities({ limit: RECOMMENDATION_LIMIT })
    const items = res.data?.items || res.data?.activities || res.data || []
    recommendations.value = fillRecommendations(items)
    if (res.data?.total !== undefined) {
      heroStats[1].value = recommendations.value.length
    } else {
      heroStats[1].value = recommendations.value.length
    }
  } catch {
    recommendations.value = fillRecommendations([])
    heroStats[1].value = recommendations.value.length
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
  if (item?.is_demo) return
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
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 6px;
}

.reason-mark {
  max-width: 100%;
  padding: 2px 7px 3px;
  border-radius: 6px;
  color: #51463a;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.45;
  white-space: normal;
  overflow-wrap: anywhere;
  border: 1px solid rgba(80, 70, 55, 0.08);
  box-shadow: inset 0 -0.68em 0 rgba(255, 255, 255, 0.34);
}

.reason-interest {
  background: #fff1a8;
}

.reason-focus {
  background: #dff0ff;
}

.reason-soon {
  background: #ffe2c8;
}

.reason-safe {
  background: #dcf5d8;
}

.reason-college {
  background: #e9edff;
}

.reason-other {
  background: #eee9df;
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
