<template>
  <section class="detail-page fade-in">
    <div class="hero detail-hero" v-loading="loading">
      <div>
        <p class="chip">{{ activity.status === 'open' ? '开放报名' : '已下架' }}</p>
        <h2 class="hero-title">{{ activity.title }}</h2>
        <p class="hero-subtitle">主讲人：{{ activity.speaker || '待定' }}｜组织单位：{{ activity.organizer || '待定' }}</p>
      </div>
      <div class="action-card">
        <div class="action-top">
          <span class="chip warning">{{ shortTime }}</span>
          <span class="muted">{{ activity.location || '地点待定' }}</span>
        </div>
        <el-button
          type="primary"
          size="large"
          :loading="adding"
          :disabled="!canJoin"
          @click="joinSchedule(false)"
        >
          {{ joined ? '已加入日程' : '一键加入日程' }}
        </el-button>
        <el-button size="large" :loading="checking" @click="openConflict">检测冲突</el-button>
        <p class="muted">{{ conflictSummary }}</p>
      </div>
    </div>

    <div class="detail-grid">
      <div class="card">
        <h3 class="section-title">关键信息</h3>
        <div class="info-grid">
          <div>
            <span class="muted">时间</span>
            <strong>{{ fullTime }}</strong>
          </div>
          <div>
            <span class="muted">地点</span>
            <strong>{{ activity.location || '地点待定' }}</strong>
          </div>
          <div>
            <span class="muted">标签</span>
            <div class="tag-row">
              <span class="chip" v-for="tag in activity.tags || []" :key="tag">{{ tag }}</span>
              <span v-if="!activity.tags?.length" class="muted">暂无标签</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3 class="section-title">活动简介</h3>
        <p class="muted">{{ activity.description || '暂无活动详情。' }}</p>
        <div class="divider"></div>
        <div class="speaker">
          <div class="avatar">{{ avatarText }}</div>
          <div>
            <strong>{{ activity.speaker || '待定' }}</strong>
            <p class="muted">类别：{{ activity.category || '未分类' }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card conflict-card">
      <div>
        <h3 class="section-title">冲突提示</h3>
        <p class="muted">{{ conflictSummary }}</p>
      </div>
      <el-button type="danger" plain :loading="checking" @click="openConflict">查看冲突明细</el-button>
    </div>

    <el-dialog v-model="conflictVisible" class="conflict-dialog" width="520px">
      <template #header>
        <div class="modal-header">
          <h4>冲突明细</h4>
          <span class="muted">{{ conflicts.length }} 项</span>
        </div>
      </template>
      <div class="modal-body">
        <div v-if="!conflicts.length" class="modal-item">
          <strong>未检测到冲突</strong>
          <p class="muted">该活动可以加入日程。</p>
        </div>
        <div v-else class="conflict-warning">
          <strong>检测到时间重叠</strong>
          <p>继续加入后，日历会把该活动标记为冲突，方便后续处理。</p>
        </div>
        <div class="modal-item" v-for="item in conflicts" :key="item.id">
          <strong>{{ item.title }}</strong>
          <p class="muted">{{ formatRange(item.start_time, item.end_time) }} · {{ item.location || '地点待定' }}</p>
        </div>
      </div>
      <template #footer>
        <div class="modal-actions">
          <el-button @click="conflictVisible = false">取消</el-button>
          <el-button type="primary" :loading="adding" @click="joinSchedule(conflicts.length > 0)">
            {{ conflicts.length ? '仍要加入' : '加入日程' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getActivityDetail } from '../api/activities'
import { addActivityToSchedule, checkConflict } from '../api/schedules'

const route = useRoute()
const activity = ref({})
const conflicts = ref([])
const conflictVisible = ref(false)
const loading = ref(false)
const checking = ref(false)
const adding = ref(false)
const checked = ref(false)
const joined = ref(false)

const loadActivity = async () => {
  loading.value = true
  try {
    const res = await getActivityDetail(route.params.id)
    if (res.code === 0) {
      activity.value = res.data
    } else {
      ElMessage.error(res.message || '活动加载失败')
    }
  } finally {
    loading.value = false
  }
}

const openConflict = async () => {
  checking.value = true
  try {
    const res = await checkConflict({ activity_id: Number(route.params.id) })
    if (res.code === 0) {
      conflicts.value = res.data.conflicts || []
      checked.value = true
      conflictVisible.value = true
    } else {
      ElMessage.error(res.message || '冲突检测失败')
    }
  } finally {
    checking.value = false
  }
}

const joinSchedule = async (forceAdd) => {
  adding.value = true
  try {
    const res = await addActivityToSchedule({
      activity_id: Number(route.params.id),
      force_add: forceAdd
    })
    if (res.code === 0) {
      conflicts.value = res.data.conflicts || []
      checked.value = true
      conflictVisible.value = false
      joined.value = true
      if (res.data.already_exists) {
        ElMessage.info('这个活动已经在你的日程中。')
      } else {
        ElMessage.success(res.data.has_conflict ? '已加入日程，并标记为冲突' : '已加入日程')
      }
    } else if (res.code === 3003) {
      await openConflict()
      ElMessage.warning(res.message)
    } else {
      ElMessage.error(res.message || '加入日程失败')
    }
  } finally {
    adding.value = false
  }
}

const shortTime = computed(() => {
  if (!activity.value.start_time) return '时间待定'
  const date = new Date(activity.value.start_time)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
})

const fullTime = computed(() => {
  if (!activity.value.start_time || !activity.value.end_time) return '时间待定'
  return formatRange(activity.value.start_time, activity.value.end_time)
})

const avatarText = computed(() => {
  return (activity.value.speaker || activity.value.title || '活动').slice(0, 2)
})

const conflictSummary = computed(() => {
  if (!canJoin.value) return '该活动缺少时间信息或已不可加入。'
  if (joined.value) return '该活动已经在你的日程中。'
  if (!checked.value) return '点击检测冲突后，可查看该活动与课程或已有日程的重叠情况。'
  if (!conflicts.value.length) return '未检测到时间冲突。'
  return `检测到 ${conflicts.value.length} 个时间冲突，可确认后继续加入。`
})

const canJoin = computed(() => {
  return activity.value.status === 'open' && activity.value.start_time && activity.value.end_time
})

const formatRange = (start, end) => {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const date = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}-${String(startDate.getDate()).padStart(2, '0')}`
  const startTime = startDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  const endTime = endDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return `${date} ${startTime} - ${endTime}`
}

onMounted(loadActivity)
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
  gap: 12px;
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

.conflict-warning {
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff4f1;
  border: 1px solid #f0d1c8;
}

.conflict-warning p {
  margin: 4px 0 0;
  color: #8a3a2b;
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

  .conflict-card {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
