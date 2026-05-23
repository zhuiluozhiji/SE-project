<template>
  <section class="detail-page fade-in">
    <div v-if="loading" v-loading="loading" class="loading-placeholder" />

    <div v-else-if="error" class="empty-state">
      <p>加载失败</p>
      <small>{{ error }}</small>
      <el-button type="primary" size="small" @click="fetchDetail">重试</el-button>
    </div>

    <template v-else-if="activity">
      <div class="hero detail-hero">
        <div>
          <p class="chip">{{ statusLabel }}</p>
          <h2 class="hero-title">{{ activity.title }}</h2>
          <p class="hero-subtitle">
            主讲人：{{ activity.speaker || '待定' }}｜组织单位：{{ activity.organizer || '待定' }}
          </p>
        </div>
        <div class="action-card">
          <div class="action-top">
            <span class="chip warning">{{ formatTime(activity.start_time) }}</span>
            <span class="muted">{{ activity.campus }} · {{ activity.location }}</span>
          </div>
          <el-button type="primary" size="large" :loading="adding" @click="addToSchedule">
            一键加入日程
          </el-button>
          <el-button size="large" :loading="checking" @click="checkConflict">检测冲突</el-button>
          <p class="muted" v-if="conflictCount > 0">
            已为你预检 {{ conflictCount }} 个潜在冲突。
          </p>
        </div>
      </div>

      <div class="detail-grid">
        <div class="card">
          <h3 class="section-title">关键信息</h3>
          <div class="info-grid">
            <div>
              <span class="muted">时间</span>
              <strong>{{ formatFullTime(activity.start_time) }} - {{ formatFullTime(activity.end_time) }}</strong>
            </div>
            <div>
              <span class="muted">地点</span>
              <strong>{{ activity.campus }} · {{ activity.location }}</strong>
            </div>
            <div>
              <span class="muted">类别</span>
              <strong>{{ activity.category || '未分类' }}</strong>
            </div>
            <div v-if="activity.tags && activity.tags.length">
              <span class="muted">标签</span>
              <div class="tag-row">
                <span class="chip" v-for="tag in activity.tags" :key="tag">{{ tag }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3 class="section-title">活动简介</h3>
          <p class="muted">{{ activity.description || '暂无详细介绍' }}</p>
          <div class="divider" v-if="activity.speaker"></div>
          <div class="speaker" v-if="activity.speaker">
            <div class="avatar">{{ (activity.speaker || '?').slice(0, 2) }}</div>
            <div>
              <strong>{{ activity.speaker }}</strong>
              <p class="muted">{{ activity.organizer || '' }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="card conflict-card" v-if="conflicts.length > 0">
        <div>
          <h3 class="section-title">冲突提示</h3>
          <p class="muted">检测到 {{ conflicts.length }} 个时间冲突，可选择继续加入。</p>
        </div>
        <el-button type="danger" plain @click="conflictVisible = true">查看冲突明细</el-button>
      </div>

      <el-dialog v-model="conflictVisible" class="conflict-dialog" width="520px">
        <template #header>
          <div class="modal-header">
            <h4>冲突明细</h4>
            <span class="muted">{{ conflicts.length }} 项</span>
          </div>
        </template>
        <div class="modal-body">
          <div class="modal-item" v-for="item in conflicts" :key="item.title">
            <strong>{{ item.title }}</strong>
            <p class="muted">{{ item.time || formatTime(item.start_time) }} · {{ item.location }}</p>
          </div>
        </div>
        <template #footer>
          <div class="modal-actions">
            <el-button @click="conflictVisible = false">取消</el-button>
            <el-button type="primary" :loading="adding" @click="addToSchedule">仍要加入</el-button>
          </div>
        </template>
      </el-dialog>
    </template>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getActivityDetail } from '../api/activities'
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

const statusMap = {
  open: '可加入',
  full: '已满',
  closed: '已结束',
  offline: '已下架',
  draft: '草稿'
}
const statusLabel = () => {
  const s = activity.value?.status
  return statusMap[s] || s || '未知'
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const formatFullTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const fetchDetail = async () => {
  loading.value = true
  error.value = ''
  try {
    const id = Number(route.params.id)
    const res = await getActivityDetail(id)
    activity.value = res.data
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const checkConflict = async () => {
  checking.value = true
  try {
    const res = await checkConflictApi({ activity_id: Number(route.params.id) })
    conflicts.value = res.data?.conflicts || res.data || []
    conflictCount.value = conflicts.value.length
    if (conflicts.value.length > 0) {
      conflictVisible.value = true
    } else {
      ElMessage.success('没有检测到时间冲突')
    }
  } catch {
    // 错误已在拦截器中处理
  } finally {
    checking.value = false
  }
}

const addToSchedule = async () => {
  adding.value = true
  try {
    await addActivityToSchedule({ activity_id: Number(route.params.id) })
    ElMessage.success('已加入日程')
    conflictVisible.value = false
  } catch {
    // 错误已在拦截器中处理
  } finally {
    adding.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.detail-page {
  display: grid;
  gap: 20px;
}

.loading-placeholder {
  min-height: 300px;
}

.empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  min-height: 200px;
  gap: 8px;
  color: #6b7280;
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
