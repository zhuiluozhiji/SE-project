<template>
  <section class="detail-page fade-in">
    <div v-if="loading" v-loading="loading" class="loading-block" />

    <div v-else-if="error" class="empty-state">
      <p>加载失败</p>
      <small>{{ error }}</small>
      <el-button type="primary" size="small" @click="fetchDetail">重试</el-button>
    </div>

    <template v-else-if="activity">
      <div class="detail-hero">
        <div class="detail-hero-body">
          <span class="chip">{{ statusLabel() }}</span>
          <h2 class="detail-title">{{ activity.title }}</h2>
          <p class="detail-sub">
            {{ activity.speaker || '主讲人待定' }} &nbsp;&middot;&nbsp; {{ activity.organizer || '组织单位待定' }}
          </p>
        </div>
        <div class="detail-action">
          <div class="action-info">
            <div class="action-time">
              <span class="action-date">{{ fmtShort(activity.start_time) }}</span>
              <span class="faint">{{ fmtTime(activity.start_time) }} - {{ fmtTime(activity.end_time) }}</span>
            </div>
            <span class="faint">{{ activity.campus }} &middot; {{ activity.location }}</span>
          </div>
          <el-button class="action-btn" type="primary" size="large" :loading="adding" @click="addToSchedule()">
            加入日程
          </el-button>
          <p class="faint" v-if="checking">正在检测冲突...</p>
          <p class="faint" v-else-if="conflictCount > 0">已预检到 {{ conflictCount }} 个时间冲突</p>
        </div>
      </div>

      <div class="detail-body">
        <div class="detail-main">
          <div class="card info-card">
            <h3 class="section-title">活动详情</h3>
            <p class="detail-desc">{{ activity.description || '暂无详细介绍' }}</p>

            <div class="divider" v-if="activity.speaker"></div>

            <div class="speaker-row" v-if="activity.speaker">
              <div class="speaker-avatar">{{ (activity.speaker || '?').slice(0, 2) }}</div>
              <div>
                <strong>{{ activity.speaker }}</strong>
                <span class="faint">{{ activity.organizer || '' }}</span>
              </div>
            </div>
          </div>

          <div class="card conflict-banner" v-if="conflicts.length > 0">
            <div>
              <strong>时间冲突提醒</strong>
              <p class="faint">检测到 {{ conflicts.length }} 个时间冲突，但仍可继续加入。</p>
            </div>
            <el-button type="danger" plain @click="conflictVisible = true">查看明细</el-button>
          </div>
        </div>

        <div class="detail-side">
          <div class="card meta-card">
            <h3 class="section-title">关键信息</h3>
            <dl class="meta-list">
              <div>
                <dt>时间</dt>
                <dd>{{ fmtFull(activity.start_time) }}<br />{{ fmtFull(activity.end_time) }}</dd>
              </div>
              <div>
                <dt>地点</dt>
                <dd>{{ activity.campus }} &middot; {{ activity.location }}</dd>
              </div>
              <div>
                <dt>类别</dt>
                <dd>{{ activity.category || '未分类' }}</dd>
              </div>
              <div v-if="activity.tags && activity.tags.length">
                <dt>标签</dt>
                <dd>
                  <span class="chip chip-sm" v-for="tag in activity.tags" :key="tag">{{ tag }}</span>
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </template>
  </section>

  <el-dialog v-model="conflictVisible" width="480px" append-to-body align-center>
    <template #header>
      <div class="dialog-head">
        <strong>冲突明细</strong>
        <span class="faint">{{ conflicts.length }} 项</span>
      </div>
    </template>
    <div class="dialog-list">
      <div class="dialog-item" v-for="item in conflicts" :key="item.title">
        <strong>{{ item.title }}</strong>
        <p class="faint">{{ fmtRange(item.start_time, item.end_time) }} &middot; {{ item.location || '--' }}</p>
      </div>
    </div>
    <template #footer>
      <el-button @click="conflictVisible = false">取消</el-button>
      <el-button type="primary" :loading="adding" @click="addToSchedule(true)">仍要加入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getActivityDetail, recordActivityInteraction } from '../api/activities'
import { checkConflict as checkConflictApi, addActivityToSchedule } from '../api/schedules'

const route = useRoute()

const loading = ref(false)
const error = ref('')
const activity = ref(null)
const conflicts = ref([])
const conflictCount = ref(0)
const conflictVisible = ref(false)
const checking = ref(false)
const adding = ref(false)

const statusMap = { open: '可加入', full: '已满', closed: '已结束', offline: '已下架', draft: '草稿' }
const statusLabel = () => statusMap[activity.value?.status] || activity.value?.status || '未知'

const pad = (n) => String(n).padStart(2, '0')

const fmtShort = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getMonth() + 1}-${pad(d.getDate())}`
}

const fmtTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const fmtFull = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const fmtRange = (start, end) => {
  if (!start) return ''
  return end
    ? `${fmtShort(start)} ${fmtTime(start)}-${fmtTime(end)}`
    : fmtFull(start)
}

const fetchDetail = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getActivityDetail(Number(route.params.id))
    activity.value = res.data
    recordInteraction('view')
    await checkConflict()
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const recordInteraction = async (actionType) => {
  try {
    await recordActivityInteraction(Number(route.params.id), {
      action_type: actionType,
      source: 'activity_detail'
    })
  } catch { /* 行为上报不阻塞详情和日程主流程 */ }
}

const checkConflict = async () => {
  checking.value = true
  try {
    const res = await checkConflictApi({ activity_id: Number(route.params.id) })
    conflicts.value = res.data?.conflicts || res.data || []
    conflictCount.value = conflicts.value.length
  } catch { /* 静默失败，冲突检测非阻塞 */ } finally {
    checking.value = false
  }
}

const addToSchedule = async (forceAdd = false) => {
  const confirmed = forceAdd === true
  if (conflicts.value.length > 0 && !confirmed) {
    conflictVisible.value = true
    return
  }
  adding.value = true
  try {
    await addActivityToSchedule({
      activity_id: Number(route.params.id),
      force_add: confirmed
    })
    await recordInteraction('add_schedule')
    ElMessage.success('已加入日程')
    conflictVisible.value = false
  } catch { /* 拦截器已处理 */ } finally {
    adding.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.detail-page {
  display: grid;
  gap: 24px;
}

.loading-block { min-height: 300px; }

/* ── Hero ── */
.detail-hero {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 28px;
  padding: 24px 28px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.detail-title {
  margin: 10px 0 8px;
  font-size: 26px;
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 0.03em;
  line-height: 1.3;
}

.detail-sub {
  margin: 0;
  color: var(--text-secondary);
  font-size: 15px;
}

.detail-action {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 190px;
  padding: 16px;
  background: var(--bg-warm);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
}

.action-time {
  display: flex;
  flex-direction: column;
}

.action-date {
  font-size: 20px;
  font-family: var(--font-display);
  font-weight: 700;
}

.action-info {
  display: grid;
  gap: 6px;
}

.action-btn {
  display: flex;
  width: 100%;
  justify-content: center;
}

/* ── Body ── */
.detail-body {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 16px;
  align-items: start;
}

.detail-main {
  display: grid;
  gap: 16px;
}

.info-card {
  display: grid;
  gap: 12px;
}

.detail-desc {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.75;
}

.speaker-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.speaker-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--text-primary);
  color: var(--bg-surface);
  font-weight: 600;
  font-size: 14px;
}

.speaker-row strong {
  display: block;
  font-size: 14px;
}

.conflict-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--danger-light);
  border-color: var(--danger-light);
}

.conflict-banner p { margin: 4px 0 0; font-size: 12px; }

/* ── Side ── */
.meta-card {
  position: sticky;
  top: 88px;
}

.meta-list {
  display: grid;
  gap: 16px;
  margin: 0;
}

.meta-list dt {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.meta-list dd {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
}

.chip-sm {
  font-size: 11px;
  padding: 2px 8px;
  margin: 2px 4px 2px 0;
}

/* ── Dialog ── */
.dialog-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-list {
  display: grid;
  gap: 10px;
}

.dialog-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-warm);
  border: 1px solid var(--border-light);
}

.dialog-item p { margin: 4px 0 0; font-size: 12px; }

@media (max-width: 960px) {
  .detail-hero {
    grid-template-columns: 1fr;
  }
  .detail-body {
    grid-template-columns: 1fr;
  }
  .meta-card {
    position: static;
  }
}
</style>
