<template>
  <section class="calendar-page fade-in">
    <div class="page-panel calendar-header">
      <div>
        <h2 class="page-title">个人日历</h2>
        <p class="muted">课程与活动统一呈现，冲突与状态清晰标识。</p>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button @click="prevWeek">上一周</el-button>
          <el-button type="primary" plain>{{ weekRangeText }}</el-button>
          <el-button @click="nextWeek">下一周</el-button>
        </el-button-group>
        <el-button @click="fetchSchedules">刷新日程</el-button>
        <el-button type="primary" @click="exportIcs" :loading="exporting">导出 ICS</el-button>
      </div>
    </div>

    <div class="legend">
      <span class="legend-item"><span class="dot course"></span>课程</span>
      <span class="legend-item"><span class="dot activity"></span>活动</span>
      <span class="legend-item"><span class="dot recommended"></span>推荐</span>
      <span class="legend-item"><span class="dot conflict"></span>冲突</span>
      <span class="legend-item"><span class="dot expired"></span>已结束</span>
    </div>

    <div v-loading="loading" class="calendar-grid">
      <div class="card week-view">
        <div class="week-header">
          <span v-for="d in weekDays" :key="d.label" :class="{ today: d.isToday }">
            {{ d.label }}
            <small>{{ d.date }}</small>
          </span>
        </div>
        <div class="week-body">
          <div class="day" v-for="(day, di) in weekDays" :key="di">
            <div
              class="day-slot"
              v-for="slot in 5"
              :key="slot"
              :class="{ 'has-event': getEventForDay(di, slot) }"
            >
              <template v-if="getEventForDay(di, slot)">
                <span class="event" :class="getEventType(getEventForDay(di, slot))">
                  {{ getEventForDay(di, slot).title }}
                </span>
                <small class="event-time">{{ formatEventTime(getEventForDay(di, slot)) }}</small>
              </template>
            </div>
            <p class="day-empty" v-if="!getEventsForDay(di).length">无安排</p>
          </div>
        </div>
      </div>

      <div class="card side-panel">
        <h3 class="section-title">即将开始</h3>
        <div v-if="upcoming.length === 0" class="empty-hint">
          <p class="muted">本周暂无活动安排</p>
        </div>
        <div class="schedule-list" v-else>
          <div class="schedule-item" v-for="item in upcoming" :key="item.id || item.title">
            <div>
              <strong>{{ item.title }}</strong>
              <p class="muted">{{ formatEventTime(item) }} · {{ item.location || '--' }}</p>
            </div>
            <span class="chip" :class="getEventType(item)">{{ typeLabel(item) }}</span>
          </div>
        </div>
        <div class="divider"></div>
        <div class="conflict-panel" v-if="conflictEvents.length > 0">
          <h4>冲突提醒</h4>
          <p class="muted">本周 {{ conflictEvents.length }} 个活动与课程时间重叠，请及时处理。</p>
          <el-button type="danger" plain size="small" @click="showConflictDetail">查看冲突详情</el-button>
        </div>
        <div class="conflict-panel" v-else>
          <h4>冲突提醒</h4>
          <p class="muted">本周暂无冲突，日程安排良好。</p>
        </div>
      </div>
    </div>

    <el-dialog v-model="conflictVisible" title="冲突明细" width="500px">
      <div class="conflict-list">
        <div class="conflict-item" v-for="item in conflictEvents" :key="item.id || item.title">
          <strong>{{ item.title }}</strong>
          <p class="muted">{{ formatEventTime(item) }} · {{ item.location || '--' }}</p>
        </div>
      </div>
    </el-dialog>

    <div v-if="error" class="empty-state">
      <p>加载失败</p>
      <small>{{ error }}</small>
      <el-button size="small" @click="fetchSchedules">重试</el-button>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSchedules } from '../api/schedules'

const loading = ref(false)
const error = ref('')
const exporting = ref(false)
const conflictVisible = ref(false)
const allEvents = ref([])

const weekOffset = ref(0)

const getMonday = (offset = 0) => {
  const d = new Date()
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  const monday = new Date(d.setDate(diff))
  monday.setDate(monday.getDate() + offset * 7)
  monday.setHours(0, 0, 0, 0)
  return monday
}

const weekDays = computed(() => {
  const monday = getMonday(weekOffset.value)
  const today = new Date()
  const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    return {
      label: labels[i],
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      isToday: d.toDateString() === today.toDateString(),
      fullDate: d
    }
  })
})

const weekRangeText = computed(() => {
  const monday = getMonday(weekOffset.value)
  const sunday = new Date(monday)
  sunday.setDate(sunday.getDate() + 6)
  const fmt = (d) => `${d.getMonth() + 1}/${d.getDate()}`
  return `${fmt(monday)} - ${fmt(sunday)}`
})

const prevWeek = () => { weekOffset.value--; fetchSchedules() }
const nextWeek = () => { weekOffset.value++; fetchSchedules() }

const formatEventTime = (event) => {
  const t = event.start_time || event.time
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const getEventsForDay = (dayIndex) => {
  const target = weekDays.value[dayIndex]
  if (!target) return []
  return allEvents.value.filter((event) => {
    const eventDate = new Date(event.start_time || event.time)
    return eventDate.toDateString() === target.fullDate.toDateString()
  })
}

const getEventForDay = (dayIndex, slot) => {
  const events = getEventsForDay(dayIndex)
  return events[slot - 1] || null
}

const getEventType = (event) => {
  if (!event) return ''
  const map = {
    course: 'course',
    activity: 'activity',
    recommended: 'recommended',
    conflict: 'conflict',
    expired: 'expired'
  }
  return map[event.color_type || event.type] || 'activity'
}

const typeLabel = (event) => {
  const map = {
    course: '课程',
    activity: '活动',
    recommended: '推荐',
    conflict: '冲突',
    expired: '已结束'
  }
  return map[event.color_type || event.type] || '活动'
}

const upcoming = computed(() => {
  return allEvents.value
    .filter((e) => new Date(e.start_time || e.time) >= new Date())
    .sort((a, b) => new Date(a.start_time || a.time) - new Date(b.start_time || b.time))
    .slice(0, 5)
})

const conflictEvents = computed(() => {
  return allEvents.value.filter((e) => (e.color_type || e.type) === 'conflict')
})

const fetchSchedules = async () => {
  loading.value = true
  error.value = ''
  try {
    const pad = (n) => String(n).padStart(2, '0')
    const monday = getMonday(weekOffset.value)
    const sunday = new Date(monday)
    sunday.setDate(sunday.getDate() + 6)
    const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

    const res = await getSchedules({
      start_date: fmt(monday),
      end_date: fmt(sunday)
    })
    allEvents.value = res.data?.events || res.data?.items || res.data || []
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const exportIcs = async () => {
  exporting.value = true
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const token = localStorage.getItem('token')
    const monday = getMonday(weekOffset.value)
    const sunday = new Date(monday)
    sunday.setDate(sunday.getDate() + 6)
    const pad = (n) => String(n).padStart(2, '0')
    const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

    const response = await fetch(`${baseUrl}/schedules/export-ics?start_date=${fmt(monday)}&end_date=${fmt(sunday)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error('导出失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `schedule_${fmt(monday)}_${fmt(sunday)}.ics`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('ICS 导出失败')
  } finally {
    exporting.value = false
  }
}

const showConflictDetail = () => {
  conflictVisible.value = true
}

onMounted(fetchSchedules)
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
  flex-wrap: wrap;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #5c4f3d;
}

.legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.course { background: #3b82f6; }
.dot.activity { background: #0f766e; }
.dot.recommended { background: #e27a38; }
.dot.conflict { background: #ef4444; }
.dot.expired { background: #9ca3af; }

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

.week-header span {
  padding: 6px 0;
}

.week-header .today {
  background: #0f766e;
  color: #fff;
  border-radius: 10px;
}

.week-header small {
  display: block;
  font-weight: 400;
  font-size: 11px;
  opacity: 0.8;
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
  min-height: 58px;
  border-radius: 12px;
  background: #f8efe2;
  border: 1px dashed #e2d3c0;
  display: grid;
  place-items: center;
  font-size: 12px;
  color: #5b5142;
  padding: 4px;
}

.day-slot.has-event {
  border-style: solid;
  border-color: #d4c9b3;
  background: #fff;
}

.event {
  color: #ffffff;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  text-align: center;
  word-break: break-all;
}

.event.course { background: #3b82f6; }
.event.activity { background: #0f766e; }
.event.recommended { background: #e27a38; }
.event.conflict { background: #ef4444; }
.event.expired { background: #9ca3af; }

.event-time {
  font-size: 10px;
  color: #9ca3af;
}

.day-empty {
  text-align: center;
  font-size: 12px;
  color: #c5bdaa;
  margin: 4px 0;
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

.empty-hint {
  text-align: center;
  padding: 12px 0;
}

.conflict-panel {
  background: #fff4f1;
  border: 1px solid #f0d1c8;
  border-radius: 12px;
  padding: 12px;
}

.conflict-list {
  display: grid;
  gap: 10px;
}

.conflict-item {
  padding: 8px 10px;
  border-radius: 10px;
  background: #f8efe2;
  border: 1px solid #e2d3c0;
}

.empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  min-height: 160px;
  gap: 8px;
  color: #6b7280;
}

@media (max-width: 960px) {
  .calendar-grid {
    grid-template-columns: 1fr;
  }
}
</style>
