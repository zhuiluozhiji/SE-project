<template>
  <section class="calendar-page fade-in">
    <div class="page-panel cal-header">
      <div>
        <h2 class="page-title">个人日历</h2>
        <p class="muted">
          第 {{ weekNumber }} 周（{{ weekParity }}）&nbsp;&middot;&nbsp;
          课程与活动统一呈现，冲突清晰标识
        </p>
      </div>
      <div class="cal-toolbar">
        <el-button-group size="small">
          <el-button :type="showOdd ? 'primary' : 'default'" @click="showOdd = true">单周</el-button>
          <el-button :type="!showOdd ? 'primary' : 'default'" @click="showOdd = false">双周</el-button>
        </el-button-group>
        <el-button-group>
          <el-button @click="prevWeek">上一周</el-button>
          <el-button type="primary" plain>{{ weekRangeText }}</el-button>
          <el-button @click="nextWeek">下一周</el-button>
        </el-button-group>
        <el-button @click="fetchSchedules">刷新</el-button>
        <el-button type="primary" @click="exportIcs" :loading="exporting">导出 ICS</el-button>
      </div>
    </div>

    <div class="legend">
      <span class="legend-item"><span class="dot course-dot"></span>课程</span>
      <span class="legend-item"><span class="dot activity-dot"></span>活动</span>
      <span class="legend-item"><span class="dot rec-dot"></span>推荐</span>
      <span class="legend-item"><span class="dot conflict-dot"></span>冲突</span>
      <span class="legend-item"><span class="dot exam-dot"></span>考试</span>
    </div>

    <div v-loading="loading" class="cal-grid">
      <div class="card timetable-card">
        <div class="timeline-wrap">
          <div class="timeline-header">
            <div class="ruler-spacer"></div>
            <div
              v-for="d in weekDays"
              :key="d.label"
              class="day-head"
            >
              <strong>{{ d.label }}</strong>
              <small>{{ d.date }}</small>
            </div>
          </div>
          <div class="timeline-body">
            <div class="time-ruler">
              <div
                v-for="h in hourMarkers"
                :key="h.label"
                class="ruler-tick"
                :style="{ top: h.top + 'px' }"
              >{{ h.label }}</div>
            </div>
            <div v-for="(day, di) in weekDays" :key="di" class="day-col">
              <div class="day-bg">
                <div
                  v-for="h in hourMarkers"
                  :key="h.label"
                  class="bg-line"
                  :style="{ top: h.top + 'px' }"
                ></div>
              </div>
              <div
                v-for="event in getTimelineEvents(di)"
                :key="event.id || event.title"
                class="timeline-event"
                :class="[event.type || 'course', { conflict: event.conflict }]"
                :style="{
                  top: event._top + 'px',
                  height: event._height + 'px',
                  left: event._left + '%',
                  width: event._width + '%'
                }"
              >
                <div class="ev-name">{{ event.title }}</div>
                <div class="ev-time">{{ event.startTime }}-{{ event.endTime }}</div>
                <div class="ev-meta" v-if="event.teacher">{{ event.teacher }}</div>
                <div class="ev-meta">{{ event.location || '' }}</div>
                <span v-if="event.weekType" class="week-tag">{{ event.weekType }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card side-panel">
        <h3 class="section-title">课程一览</h3>
        <div v-if="weekCourses.length === 0" class="empty-hint">
          <p class="muted">本周暂无课程</p>
        </div>
        <div class="side-list" v-else>
          <div class="side-item" v-for="c in weekCourses" :key="c.id || c.title">
            <div class="side-item-left">
              <span class="dot" :class="(c.type || 'course') + '-dot'"></span>
              <div>
                <strong>{{ c.title }}</strong>
                <p class="muted">{{ c.teacher }} &middot; {{ c.location }}</p>
              </div>
            </div>
            <div class="side-item-right">
              <span class="faint">{{ c.dayLabel }} {{ c.timeLabel }}</span>
              <span class="chip" v-if="c.weekType">{{ c.weekType }}</span>
            </div>
          </div>
        </div>

        <div class="divider"></div>
        <h3 class="section-title">即将开始</h3>
        <div v-if="upcoming.length === 0" class="empty-hint">
          <p class="muted">本周暂无活动安排</p>
        </div>
        <div class="side-list" v-else>
          <div class="side-item" v-for="item in upcoming" :key="item.id || item.title">
            <div>
              <strong>{{ item.title }}</strong>
              <p class="muted">{{ formatDate(item.start_time || item.time) }} &middot; {{ item.location || '--' }}</p>
            </div>
            <span class="chip" :class="item.type">{{ typeLabel(item) }}</span>
          </div>
        </div>

        <div class="divider"></div>
        <div class="conflict-box" v-if="conflictEvents.length > 0">
          <strong>冲突提醒</strong>
          <p class="muted">本周 {{ conflictEvents.length }} 个活动与课程时间重叠</p>
          <el-button type="danger" plain size="small" @click="conflictVisible = true">查看详情</el-button>
        </div>
        <div class="conflict-box safe" v-else>
          <strong>冲突提醒</strong>
          <p class="muted">本周暂无冲突，日程安排良好</p>
        </div>

        <div class="divider"></div>
        <h3 class="section-title">近期考试</h3>
        <div v-if="exams.length === 0" class="empty-hint">
          <p class="muted">暂无临近考试</p>
        </div>
        <div class="side-list" v-else>
          <div class="exam-item" v-for="e in exams" :key="e.title">
            <strong>{{ e.title }}</strong>
            <p class="muted">{{ e.examDate }} &middot; {{ e.location }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="empty-state">
      <p>加载失败</p>
      <small>{{ error }}</small>
      <el-button size="small" @click="fetchSchedules">重试</el-button>
    </div>
  </section>

  <el-dialog v-model="conflictVisible" title="冲突明细" width="480px" append-to-body align-center>
    <div class="dialog-list">
      <div class="dialog-item" v-for="item in conflictEvents" :key="item.id || item.title">
        <strong>{{ item.title }}</strong>
        <p class="faint">{{ formatDate(item.start_time || item.time) }} &middot; {{ item.location || '--' }}</p>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSchedules } from '../api/schedules'

const loading = ref(false)
const error = ref('')
const exporting = ref(false)
const conflictVisible = ref(false)
const allEvents = ref([])
const weekOffset = ref(0)
const showOdd = ref(true)

const PX_PER_HOUR = 80
const START_HOUR = 8
const END_HOUR = 21.5

const parseTime = (t) => {
  if (!t) return 0
  const parts = t.split(':')
  return parseInt(parts[0]) * 60 + parseInt(parts[1])
}

const hourMarkers = computed(() => {
  const markers = []
  const totalMinutes = (END_HOUR - START_HOUR) * 60
  const totalPx = totalMinutes / 60 * PX_PER_HOUR
  for (let h = START_HOUR; h <= Math.floor(END_HOUR); h++) {
    const top = (h - START_HOUR) * PX_PER_HOUR
    if (top <= totalPx) markers.push({ label: `${String(h).padStart(2, '0')}:00`, top })
  }
  return markers
})

const timelineHeight = computed(() => (END_HOUR - START_HOUR) * PX_PER_HOUR)

const layoutEvents = (events) => {
  if (!events.length) return events
  const sorted = [...events].sort((a, b) => a._startMin - b._startMin)
  const tracks = []
  sorted.forEach((e) => {
    let placed = false
    for (let i = 0; i < tracks.length; i++) {
      if (tracks[i] <= e._startMin) {
        tracks[i] = e._endMin
        e._track = i
        placed = true
        break
      }
    }
    if (!placed) {
      e._track = tracks.length
      tracks.push(e._endMin)
    }
  })
  const totalTracks = tracks.length || 1
  const gap = 2
  sorted.forEach((e) => {
    e._left = (e._track / totalTracks) * 100
    e._width = (100 / totalTracks) - gap
  })
  return sorted
}

const getTimelineEvents = (dayIndex) => {
  const wd = dayIndex + 1
  const baseMinutes = START_HOUR * 60
  const raw = defaultCourses
    .filter((c) => {
      if (c.weekday !== wd) return false
      if (!showOdd.value && c.weekType === '单周') return false
      if (showOdd.value && c.weekType === '双周') return false
      return true
    })
    .map((c) => {
      const startMin = parseTime(c.startTime) || (c.startPeriod ? (START_HOUR * 60 + (c.startPeriod - 1) * 45) : 0)
      const endMin = parseTime(c.endTime) || (c.endPeriod ? (START_HOUR * 60 + c.endPeriod * 45) : startMin + 45)
      return {
        ...c,
        _startMin: startMin,
        _endMin: endMin,
        _top: Math.max(0, (startMin - baseMinutes) / 60 * PX_PER_HOUR),
        _height: Math.max(10, (endMin - startMin) / 60 * PX_PER_HOUR)
      }
    })
  return layoutEvents(raw)
}

const defaultCourses = [
  { id: 'c1',  title: '机器学习',     teacher: '李明远', location: '紫金港东1A-203',   weekday: 1, startPeriod: 1, endPeriod: 2, type: 'course', weekType: '每周', startTime: '08:00', endTime: '09:35' },
  { id: 'c2',  title: '机器学习',     teacher: '李明远', location: '紫金港东1A-203',   weekday: 4, startPeriod: 3, endPeriod: 4, type: 'course', weekType: '每周', startTime: '10:00', endTime: '11:35' },
  { id: 'c3',  title: '高等数学',     teacher: '张晓峰', location: '紫金港西2-315',    weekday: 2, startPeriod: 1, endPeriod: 3, type: 'course', weekType: '每周', startTime: '08:00', endTime: '10:45' },
  { id: 'c4',  title: '数据库系统',   teacher: '王海燕', location: '玉泉教3-208',     weekday: 1, startPeriod: 6, endPeriod: 7, type: 'course', weekType: '单周', startTime: '13:25', endTime: '15:00' },
  { id: 'c5',  title: '数据库系统',   teacher: '王海燕', location: '玉泉教3-208',     weekday: 5, startPeriod: 1, endPeriod: 2, type: 'course', weekType: '单周', startTime: '08:00', endTime: '09:35' },
  { id: 'c6',  title: '数据结构',     teacher: '陈志强', location: '紫金港东1B-501',   weekday: 2, startPeriod: 6, endPeriod: 8, type: 'course', weekType: '每周', startTime: '13:25', endTime: '15:50' },
  { id: 'c7',  title: '计算机网络',   teacher: '赵丽娜', location: '玉泉曹光彪东-102', weekday: 4, startPeriod: 6, endPeriod: 7, type: 'course', weekType: '每周', startTime: '13:25', endTime: '15:00' },
  { id: 'c8',  title: '英语写作',     teacher: '刘文博', location: '紫金港外语楼-310', weekday: 5, startPeriod: 3, endPeriod: 4, type: 'course', weekType: '每周', startTime: '10:00', endTime: '11:35' },
  { id: 'c9',  title: '操作系统',     teacher: '孙浩然', location: '玉泉教4-106',     weekday: 3, startPeriod: 3, endPeriod: 5, type: 'course', weekType: '双周', startTime: '10:00', endTime: '12:25' },
  { id: 'c10', title: '学术前沿讲座', teacher: '轮值',   location: '紫金港学术报告厅', weekday: 3, startPeriod: 9, endPeriod: 10, type: 'recommended', weekType: '单周', startTime: '16:15', endTime: '17:50' },
  { id: 'e1',  title: '生成式AI与科研写作', teacher: '特邀嘉宾', location: '紫金港学术报告厅', weekday: 5, startPeriod: 6, endPeriod: 9, type: 'activity', weekType: '每周', startTime: '14:00', endTime: '16:00' },
]

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

const weekNumber = computed(() => {
  const monday = getMonday(weekOffset.value)
  const startOfYear = new Date(monday.getFullYear(), 0, 1)
  const days = Math.floor((monday - startOfYear) / (24 * 60 * 60 * 1000))
  return Math.ceil((days + startOfYear.getDay() + 1) / 7)
})

const weekParity = computed(() => weekNumber.value % 2 === 1 ? '单周' : '双周')

const prevWeek = () => { weekOffset.value--; fetchSchedules() }
const nextWeek = () => { weekOffset.value++; fetchSchedules() }

const formatDate = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const typeLabel = (event) => {
  const map = { course: '课程', activity: '活动', recommended: '推荐', conflict: '冲突', exam: '考试' }
  return map[event.color_type || event.type] || '活动'
}

const weekCourses = computed(() => {
  return defaultCourses.filter((c) => {
    if (!showOdd.value && c.weekType === '单周') return false
    if (showOdd.value && c.weekType === '双周') return false
    return true
  }).map((c) => ({
    ...c,
    dayLabel: ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'][c.weekday],
    timeLabel: `${c.startPeriod}-${c.endPeriod}节`
  }))
})

const upcoming = computed(() => {
  return allEvents.value
    .filter((e) => new Date(e.start_time || e.time) >= new Date())
    .sort((a, b) => new Date(a.start_time || a.time) - new Date(b.start_time || b.time))
    .slice(0, 5)
})

const conflictEvents = computed(() => {
  return allEvents.value.filter((e) => (e.color_type || e.type) === 'conflict')
})

const exams = computed(() => {
  const seen = new Set()
  return defaultCourses
    .filter((c) => c.examDate && !seen.has(c.title + c.examDate) && seen.add(c.title + c.examDate))
    .map((c) => ({ title: c.title, examDate: c.examDate, location: c.location }))
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
    const res = await getSchedules({ start_date: fmt(monday), end_date: fmt(sunday) })
    allEvents.value = res.data?.events || res.data?.items || res.data || []
  } catch { /* 后端不可用时静默使用内置数据 */ } finally {
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

onMounted(fetchSchedules)
</script>

<style scoped>
.calendar-page {
  display: grid;
  gap: 16px;
}

.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
}

.cal-toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* ── Legend ── */
.legend {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.course-dot   { background: #6a8cbf; }
.activity-dot { background: #7aaa8a; }
.rec-dot      { background: var(--accent); }
.conflict-dot { background: var(--danger); }
.exam-dot     { background: #8b7ab8; }

/* ── Grid ── */
.cal-grid {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

/* ── Timeline ── */
.timetable-card {
  padding: 0;
  overflow: hidden;
}

.timeline-wrap {
  position: relative;
}

.timeline-header {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--bg-warm);
}

.ruler-spacer {
  width: 56px;
  flex-shrink: 0;
}

.day-head {
  flex: 1;
  padding: 10px 4px;
  text-align: center;
  background: inherit;
}

.day-head strong {
  display: block;
  font-size: 13px;
  color: var(--text-primary);
}

.day-head small {
  font-size: 11px;
  color: var(--text-tertiary);
}

.timeline-body {
  display: flex;
  position: relative;
  height: v-bind(timelineHeight + 'px');
}

.time-ruler {
  width: 56px;
  flex-shrink: 0;
  position: relative;
  border-right: 1px solid var(--border);
  background: var(--bg-warm);
}

.ruler-tick {
  position: absolute;
  width: 100%;
  text-align: center;
  font-size: 10px;
  color: var(--text-tertiary);
  transform: translateY(-50%);
}

.day-col {
  flex: 1;
  position: relative;
}

.day-bg {
  position: absolute;
  inset: 0;
}

.bg-line {
  position: absolute;
  width: 100%;
  border-top: 1px solid var(--border-light);
}

/* ── Event blocks ── */
.timeline-event {
  position: absolute;
  border-radius: 4px;
  padding: 3px 6px;
  font-size: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 16px;
  border-left: 3px solid transparent;
}

.timeline-event.course {
  background: #ecf0f7;
  border-left-color: #6a8cbf;
}

.timeline-event.activity {
  background: #e8f2ec;
  border-left-color: #7aaa8a;
}

.timeline-event.recommended {
  background: var(--accent-light);
  border-left-color: var(--accent);
}

.timeline-event.conflict {
  background: var(--danger-light);
  border-left-color: var(--danger);
}

.timeline-event.exam {
  background: #f0ecf7;
  border-left-color: #8b7ab8;
}

.ev-name {
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.ev-time, .ev-meta {
  color: var(--text-tertiary);
  font-size: 9px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.week-tag {
  position: absolute;
  top: 2px;
  right: 3px;
  font-size: 8px;
  background: rgba(0,0,0,0.06);
  color: var(--text-tertiary);
  padding: 0px 4px;
  border-radius: 2px;
}

/* ── Side panel ── */
.side-panel {
  display: grid;
  gap: 14px;
  position: sticky;
  top: 88px;
}

.side-list {
  display: grid;
  gap: 8px;
}

.side-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-warm);
  border: 1px solid var(--border-light);
}

.side-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.side-item-left strong {
  font-size: 13px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.side-item-left p { margin: 2px 0 0; font-size: 11px; }

.side-item-left .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.side-item-right {
  text-align: right;
  font-size: 11px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.empty-hint { text-align: center; padding: 16px 0; }

.conflict-box {
  padding: 14px;
  border-radius: var(--radius-sm);
  background: var(--danger-light);
  border: 1px solid #edc8c6;
  display: grid;
  gap: 6px;
}

.conflict-box.safe {
  background: var(--success-light);
  border-color: #b8d8c3;
}

.conflict-box p { font-size: 12px; }
.conflict-box strong { font-size: 13px; }

.exam-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: #f8f6fb;
  border: 1px solid #e3ddf0;
}

.exam-item strong { font-size: 13px; color: #5c4a8a; }
.exam-item p { margin: 2px 0 0; font-size: 11px; }

/* ── dialog ── */
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

[data-theme="dark"] .course-dot   { background: #7a9ed3; }
[data-theme="dark"] .activity-dot { background: #8bc4a0; }
[data-theme="dark"] .exam-dot     { background: #a08ec8; }

[data-theme="dark"] .timeline-event.course {
  background: #1e222d;
  border-left-color: #6a8cbf;
}

[data-theme="dark"] .timeline-event.activity {
  background: #1e2822;
  border-left-color: #7aaa8a;
}

[data-theme="dark"] .timeline-event.exam {
  background: #24202d;
  border-left-color: #8b7ab8;
}

[data-theme="dark"] .conflict-box {
  border-color: #5a3a38;
}

[data-theme="dark"] .conflict-box.safe {
  border-color: #3a5a48;
}

[data-theme="dark"] .exam-item {
  background: #24202d;
  border-color: #3d3850;
}

[data-theme="dark"] .exam-item strong { color: #a08ec8; }

@media (max-width: 1200px) {
  .cal-grid {
    grid-template-columns: 1fr;
  }
  .side-panel {
    position: static;
  }
  .timetable-card {
    overflow-x: auto;
  }
  .timeline-wrap {
    min-width: 720px;
  }
}
</style>
