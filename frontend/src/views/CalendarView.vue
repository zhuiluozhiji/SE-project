<template>
  <section class="calendar-page fade-in">
    <div class="page-panel cal-header">
      <div>
        <h2 class="page-title">个人日历</h2>
        <p class="muted">
          第 {{ weekNumber }} 周（{{ weekParity }}）
        </p>
      </div>
      <div class="cal-toolbar">
        <el-button-group class="toolbar-group parity-toggle-group">
          <el-button
            class="parity-toggle-button"
            :class="{ 'is-selected-parity': showOdd }"
            :type="showOdd ? 'primary' : 'default'"
            @click="showOdd = true"
          >
            单周
          </el-button>
          <el-button
            class="parity-toggle-button"
            :class="{ 'is-selected-parity': !showOdd }"
            :type="!showOdd ? 'primary' : 'default'"
            @click="showOdd = false"
          >
            双周
          </el-button>
        </el-button-group>
        <el-button-group class="toolbar-group">
          <el-button @click="prevWeek">上一周</el-button>
          <el-button class="current-week-button" type="primary" plain>{{ weekRangeText }}</el-button>
          <el-button @click="nextWeek">下一周</el-button>
        </el-button-group>
        <el-button class="screenshot-add-button" type="primary" plain @click="openScreenshotDialog">截图加入</el-button>
        <el-button @click="fetchSchedules">刷新</el-button>
        <el-button class="export-ics-button" @click="exportIcs" :loading="exporting">导出 ICS</el-button>
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
              <el-tooltip
                v-for="event in getTimelineEvents(di)"
                :key="event.id || event.title"
                placement="right-start"
                effect="light"
                :show-after="120"
                :offset="10"
                popper-class="timeline-event-tooltip"
              >
                <template #content>
                  <div class="timeline-tooltip">
                    <strong>{{ event.title }}</strong>
                    <div class="tooltip-meta">{{ formatRange(event.start_time, event.end_time) }}</div>
                    <div v-if="event.teacher" class="tooltip-meta">{{ event.teacher }}</div>
                    <div v-if="event.location" class="tooltip-meta">{{ event.location }}</div>
                    <div v-if="event.remark" class="tooltip-meta">备注：{{ event.remark }}</div>
                    <div v-if="event.conflict" class="tooltip-warning">存在时间冲突</div>
                  </div>
                </template>
                <div
                  class="timeline-event"
                  :class="[
                    event.type || 'course',
                    {
                      'has-conflict': event.conflict,
                      'is-compact': event._isCompact
                    }
                  ]"
                  :style="{
                    top: event._top + 'px',
                    height: event._height + 'px',
                    left: event._left + '%',
                    width: event._width + '%',
                    ...event.colorStyle
                  }"
                  :title="timelineEventSummary(event)"
                  :aria-label="timelineEventSummary(event)"
                  role="button"
                  tabindex="0"
                  @click="openEventDialog(event)"
                  @keydown.enter.prevent="openEventDialog(event)"
                  @keydown.space.prevent="openEventDialog(event)"
                >
                  <div class="ev-title-row">
                    <span class="ev-marker">{{ event.markerLabel }}</span>
                    <span v-if="event.conflict" class="ev-conflict-label">冲突</span>
                    <div class="ev-name">{{ event.title }}</div>
                  </div>
                  <div v-if="event.remark && event._showRemark !== false" class="ev-remark">{{ event.remark }}</div>
                  <div v-if="event._showTime !== false" class="ev-time">{{ event.startTime }}-{{ event.endTime }}</div>
                  <div v-if="event.location && event._showLocation !== false" class="ev-location">{{ event.location }}</div>
                  <span v-if="event.weekType && !event._isCompact" class="week-tag">{{ event.weekType }}</span>
                </div>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>

      <div class="card side-panel">
        <h3 class="section-title">课程/活动一览</h3>
        <div v-if="weekCourses.length === 0" class="empty-hint">
          <p class="muted">本周暂无课程</p>
        </div>
        <div class="side-list" v-else>
          <div class="side-item" v-for="c in weekCourses" :key="c.id || c.title">
            <div class="side-item-left">
              <span class="ev-marker side-marker" :style="c.colorStyle">{{ c.markerLabel }}</span>
              <div>
                <strong>{{ c.title }}</strong>
                <p class="muted">{{ c.teacher }} &middot; {{ c.location }}</p>
              </div>
            </div>
            <div class="side-item-right">
              <span class="faint">{{ c.dayLabel }} {{ c.timeLabel }}</span>
              <span class="chip" v-if="c.weekType">{{ c.weekType }}</span>
              <el-button size="small" text @click="openEventDialog(c)">编辑</el-button>
            </div>
          </div>
        </div>

        <div class="divider"></div>
        <h3 class="section-title">即将开始</h3>
        <div v-if="upcoming.length === 0" class="empty-hint">
          <p class="muted">本周暂无活动安排</p>
        </div>
        <div class="side-list" v-else>
          <div
            class="side-item clickable"
            v-for="item in upcoming"
            :key="item.id || item.title"
            role="button"
            tabindex="0"
            @click="openEventDialog(item)"
            @keydown.enter.prevent="openEventDialog(item)"
            @keydown.space.prevent="openEventDialog(item)"
          >
            <div class="side-item-left">
              <span class="ev-marker side-marker" :style="item.colorStyle">{{ item.markerLabel }}</span>
              <div>
              <strong>{{ item.title }}</strong>
              <p class="muted">{{ formatDate(item.start_time || item.time) }} &middot; {{ item.location || '--' }}</p>
              </div>
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

  <el-dialog v-model="screenshotDialogVisible" title="截图加入日程" width="min(640px, 94vw)" append-to-body align-center>
    <div class="screenshot-dialog-body">
      <el-upload
        ref="screenshotUploadRef"
        drag
        action="#"
        :auto-upload="false"
        multiple
        :limit="MAX_SCREENSHOT_FILES"
        accept=".png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff"
        :on-change="handleScreenshotFileChange"
        :on-remove="handleScreenshotFileRemove"
        :on-exceed="handleScreenshotFileExceed"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <p>拖拽活动截图到这里</p>
        <small class="faint">支持 PNG / JPG / WEBP / BMP / TIFF</small>
      </el-upload>

      <div class="screenshot-capture-actions">
        <el-button
          size="small"
          @click="captureCalendarScreenshot"
          :disabled="screenshotFiles.length >= MAX_SCREENSHOT_FILES"
        >
          快捷截屏
        </el-button>
        <span class="faint">{{ screenshotFiles.length }}/{{ MAX_SCREENSHOT_FILES }} · {{ SCREENSHOT_SHORTCUT_LABEL }}</span>
      </div>

      <el-form :model="screenshotForm" label-width="86px" class="screenshot-form">
        <el-form-item label="活动名称">
          <el-input v-model="screenshotForm.title" placeholder="活动名称" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="screenshotForm.location" placeholder="地点" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="screenshotForm.remark"
            type="textarea"
            maxlength="500"
            show-word-limit
            :autosize="{ minRows: 2, maxRows: 3 }"
          />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="screenshotStartTime"
                type="datetime"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="开始时间"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="screenshotEndTime"
                type="datetime"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="结束时间"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="预计时长">
          <div class="duration-input">
            <el-input-number
              v-model="screenshotEstimatedDurationMinutes"
              :min="1"
              :step="15"
              controls-position="right"
            />
            <span>min</span>
          </div>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="标识">
              <el-input v-model="screenshotForm.marker_label" maxlength="1" />
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="颜色">
              <div class="color-swatch-grid screenshot-swatches">
                <button
                  v-for="option in scheduleColorOptions"
                  :key="option.value"
                  type="button"
                  class="color-swatch"
                  :class="{ active: screenshotForm.color_type === option.value }"
                  :style="swatchStyle(option)"
                  :aria-label="option.name"
                  :title="option.name"
                  @click="screenshotForm.color_type = option.value"
                ></button>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div v-if="screenshotConflicts.length" class="screenshot-conflicts">
        <strong>检测到冲突</strong>
        <div v-for="item in screenshotConflicts" :key="item.id || item.title">
          {{ item.title }} · {{ formatRange(item.start_time, item.end_time) }}
        </div>
      </div>

      <div v-if="screenshotRawText" class="screenshot-preview">
        <strong>识别文本</strong>
        <p>{{ screenshotRawText }}</p>
      </div>
    </div>
    <template #footer>
      <el-button @click="screenshotDialogVisible = false">取消</el-button>
      <el-button :loading="recognizingScreenshot" :disabled="!screenshotFileReady" @click="recognizeScreenshot">
        识别截图
      </el-button>
      <el-button
        type="primary"
        :loading="addingScreenshotEvent"
        :disabled="!canAddScreenshotEvent"
        @click="addScreenshotEvent"
      >
        加入日程
      </el-button>
    </template>
  </el-dialog>

  <el-dialog
    v-model="cropDialogVisible"
    title="框选截图范围"
    width="min(920px, 96vw)"
    append-to-body
    align-center
    @closed="clearCropState"
  >
    <div class="crop-stage">
      <div
        v-if="cropImageUrl"
        ref="cropStageRef"
        class="crop-canvas"
        @pointerdown="startCropSelection"
        @pointermove="moveCropSelection"
        @pointerup="finishCropSelection"
        @pointercancel="finishCropSelection"
      >
        <img
          ref="cropImageRef"
          :src="cropImageUrl"
          draggable="false"
          alt=""
          @load="resetCropSelection"
        />
        <div
          v-if="hasCropSelection"
          class="crop-selection"
          :style="cropSelectionStyle"
        ></div>
      </div>
    </div>
    <template #footer>
      <el-button @click="cropDialogVisible = false">取消</el-button>
      <el-button @click="confirmCapturedScreenshot(false)">截取整张</el-button>
      <el-button
        type="primary"
        :loading="confirmingCrop"
        :disabled="!hasCropSelection"
        @click="confirmCapturedScreenshot(true)"
      >
        确认框选
      </el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="conflictVisible" title="冲突明细" width="480px" append-to-body align-center>
    <div class="dialog-list">
      <div class="dialog-item" v-for="item in conflictEvents" :key="item.id || item.title">
        <strong>{{ item.title }}</strong>
        <p class="faint">{{ formatRange(item.start_time, item.end_time) }} &middot; {{ item.location || '--' }}</p>
      </div>
    </div>
  </el-dialog>

  <el-dialog v-model="eventDialogVisible" class="course-dialog" width="min(520px, 92vw)" append-to-body align-center>
    <template #header>
      <div class="dialog-title">
        <span
          v-if="selectedEvent"
          class="ev-marker dialog-marker"
          :style="selectedEvent.colorStyle"
        >{{ selectedEvent.markerLabel }}</span>
        <strong>{{ selectedEvent?.title || '日程详情' }}</strong>
      </div>
    </template>

    <div v-if="selectedEvent" class="event-detail">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="时间">
          {{ formatDate(selectedEvent.start_time) }} - {{ selectedEvent.endTime }}
        </el-descriptions-item>
        <el-descriptions-item label="地点">
          {{ selectedEvent.location || '地点待定' }}
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          {{ typeLabel(selectedEvent) }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="selectedEvent.rawType === 'course'" class="course-delete-panel">
        <h4>删除范围</h4>
        <el-radio-group v-model="deleteScope" class="delete-scope-group">
          <el-radio-button value="one">仅本次</el-radio-button>
          <el-radio-button value="day">删除当天</el-radio-button>
          <el-radio-button value="all">全部这门课</el-radio-button>
        </el-radio-group>
        <p class="muted">{{ deleteScopeHint }}</p>
      </div>

      <div class="event-edit-panel">
        <h4>标识与备注</h4>
        <el-input
          v-model="selectedMarkerLabel"
          class="marker-input"
          maxlength="1"
          show-word-limit
        />
        <div class="color-swatch-grid">
          <button
            v-for="option in scheduleColorOptions"
            :key="option.value"
            type="button"
            class="color-swatch"
            :class="{ active: selectedColorType === option.value }"
            :style="swatchStyle(option)"
            :aria-label="option.name"
            :title="option.name"
            @click="selectedColorType = option.value"
          ></button>
        </div>
        <el-input
          v-model="selectedRemark"
          class="remark-input"
          type="textarea"
          maxlength="500"
          show-word-limit
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="eventDialogVisible = false">关闭</el-button>
      <el-button
        type="primary"
        plain
        :loading="savingAppearance"
        @click="saveSelectedEventAppearance"
      >
        保存修改
      </el-button>
      <el-button
        v-if="selectedEvent?.rawType === 'activity'"
        type="danger"
        :loading="deletingActivity"
        @click="removeSelectedActivity"
      >
        删除活动
      </el-button>
      <el-button
        v-if="selectedEvent?.rawType === 'course'"
        type="danger"
        :loading="deletingCourse"
        @click="removeSelectedCourse"
      >
        删除课程
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import {
  addCustomEventToSchedule,
  checkCustomEventConflict,
  deleteScheduleEvent,
  getSchedules,
  recognizeScheduleImage,
  updateScheduleEventAppearance
} from '../api/schedules'
import { deleteCourse } from '../api/courses'
import {
  captureScreenImage,
  isAllowedScreenshotFile,
  isScreenshotShortcut,
  MAX_SCREENSHOT_FILES,
  SCREENSHOT_SHORTCUT_LABEL
} from '../utils/screenCapture'

const loading = ref(false)
const error = ref('')
const exporting = ref(false)
const conflictVisible = ref(false)
const eventDialogVisible = ref(false)
const allEvents = ref([])
const weekOffset = ref(0)
const showOdd = ref(true)
const selectedEvent = ref(null)
const deleteScope = ref('one')
const deletingCourse = ref(false)
const deletingActivity = ref(false)
const savingAppearance = ref(false)
const selectedColorType = ref('green')
const selectedMarkerLabel = ref('活')
const selectedRemark = ref('')
const screenshotDialogVisible = ref(false)
const screenshotUploadRef = ref(null)
const screenshotFiles = ref([])
const screenshotFileReady = ref(false)
const cropDialogVisible = ref(false)
const cropImageUrl = ref('')
const cropImageRef = ref(null)
const cropStageRef = ref(null)
const cropSourceFile = ref(null)
const cropSelection = reactive({ x: 0, y: 0, width: 0, height: 0 })
const cropDragStart = reactive({ x: 0, y: 0 })
const cropping = ref(false)
const confirmingCrop = ref(false)
const recognizingScreenshot = ref(false)
const addingScreenshotEvent = ref(false)
const screenshotRawText = ref('')
const screenshotWarnings = ref([])
const screenshotConflicts = ref([])
const DEFAULT_ESTIMATED_DURATION_MINUTES = 120
const MIN_CROP_SIZE = 12

const screenshotForm = reactive({
  title: '',
  location: '',
  start_time: null,
  end_time: null,
  remark: '',
  estimated_duration_minutes: DEFAULT_ESTIMATED_DURATION_MINUTES,
  color_type: 'green',
  marker_label: '活'
})

const scheduleColorOptions = [
  { name: '蓝', value: 'blue', border: '#5f84c3', bg: '#e9f0fb', darkBorder: '#6cb6ff', darkBg: '#24384d' },
  { name: '绿', value: 'green', border: '#62a374', bg: '#e8f4ec', darkBorder: '#89d185', darkBg: '#263b2a' },
  { name: '青', value: 'teal', border: '#4c9d9b', bg: '#e5f4f3', darkBorder: '#62d6c8', darkBg: '#203b3a' },
  { name: '黄', value: 'amber', border: '#d0a340', bg: '#fbf2d9', darkBorder: '#e6db74', darkBg: '#3a3620' },
  { name: '橙', value: 'orange', border: '#d78245', bg: '#faecdf', darkBorder: '#f2a97f', darkBg: '#402d26' },
  { name: '红', value: 'red', border: '#cf625b', bg: '#fae7e5', darkBorder: '#ff7b72', darkBg: '#452b2d' },
  { name: '紫', value: 'purple', border: '#8772bd', bg: '#f0ebfa', darkBorder: '#d2a8ff', darkBg: '#372c44' },
  { name: '粉', value: 'pink', border: '#ca6c9d', bg: '#fae9f1', darkBorder: '#ff9bce', darkBg: '#412b38' },
  { name: '灰', value: 'gray', border: '#7d8793', bg: '#eceff3', darkBorder: '#b1bac4', darkBg: '#2f343a' }
]

const defaultColorByType = {
  course: 'blue',
  activity: 'green',
  exam: 'purple'
}

const defaultMarkerByType = {
  course: '课',
  activity: '活',
  exam: '考'
}

const PX_PER_HOUR = 80
const START_HOUR = 8
const END_HOUR = 21.5
const SEMESTER_WEEK_ONE_MONDAY = new Date(2026, 2, 2)

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
  const sorted = events
    .map((event) => ({ ...event }))
    .sort((a, b) => a._startMin - b._startMin)
  const gap = 2
  const layoutParallelCluster = (cluster) => {
    const tracks = []
    cluster.forEach((event) => {
      let placed = false
      for (let i = 0; i < tracks.length; i++) {
        if (tracks[i] <= event._startMin) {
          tracks[i] = event._endMin
          event._track = i
          placed = true
          break
        }
      }
      if (!placed) {
        event._track = tracks.length
        tracks.push(event._endMin)
      }
    })
    const totalTracks = tracks.length || 1
    cluster.forEach((event) => {
      event._left = (event._track / totalTracks) * 100
      event._width = (100 / totalTracks) - gap
      event._isCompact = totalTracks > 1
      event._isStackedConflict = false
      event._showTime = !event._isCompact && event._height >= 34
      event._showLocation = !event._isCompact && event._height >= 48
      event._showRemark = !event._isCompact && event._height >= 64
    })
  }
  const flushCluster = (cluster) => {
    if (!cluster.length) return
    layoutParallelCluster(cluster)
  }

  let cluster = []
  let clusterEnd = -1
  sorted.forEach((event) => {
    if (!cluster.length) {
      cluster = [event]
      clusterEnd = event._endMin
      return
    }
    if (event._startMin < clusterEnd) {
      cluster.push(event)
      clusterEnd = Math.max(clusterEnd, event._endMin)
      return
    }
    flushCluster(cluster)
    cluster = [event]
    clusterEnd = event._endMin
  })
  flushCluster(cluster)
  return sorted
}

const getTimelineEvents = (dayIndex) => {
  const wd = dayIndex + 1
  const raw = allEvents.value
    .filter((c) => {
      if (c.weekday !== wd) return false
      if (!showOdd.value && c.weekType === '单周') return false
      if (showOdd.value && c.weekType === '双周') return false
      return true
    })
  return layoutEvents(raw)
}

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
  const days = Math.floor((monday - SEMESTER_WEEK_ONE_MONDAY) / (24 * 60 * 60 * 1000))
  return Math.floor(days / 7) + 1
})

const weekParity = computed(() => weekNumber.value % 2 === 1 ? '单周' : '双周')

const syncWeekParityFilter = () => {
  showOdd.value = weekNumber.value % 2 === 1
}

const prevWeek = () => {
  weekOffset.value--
  syncWeekParityFilter()
  fetchSchedules()
}
const nextWeek = () => {
  weekOffset.value++
  syncWeekParityFilter()
  fetchSchedules()
}

const canAddScreenshotEvent = computed(() => {
  return Boolean(
    screenshotForm.title?.trim()
    && screenshotForm.start_time
    && screenshotForm.end_time
    && screenshotForm.marker_label?.trim()
  )
})

const hasCropSelection = computed(() => {
  return cropSelection.width >= MIN_CROP_SIZE && cropSelection.height >= MIN_CROP_SIZE
})

const cropSelectionStyle = computed(() => ({
  left: `${cropSelection.x}px`,
  top: `${cropSelection.y}px`,
  width: `${cropSelection.width}px`,
  height: `${cropSelection.height}px`
}))

const formatDate = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const formatRange = (start, end) => {
  if (!start) return ''
  const startDate = formatDate(start)
  if (!end) return startDate
  const d = new Date(end)
  const pad = (n) => String(n).padStart(2, '0')
  return `${startDate}-${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const timelineEventSummary = (event) => {
  return [
    event.title,
    formatRange(event.start_time, event.end_time),
    event.teacher,
    event.location,
    event.remark ? `备注：${event.remark}` : '',
    event.conflict ? '存在时间冲突' : ''
  ]
    .filter(Boolean)
    .join('\n')
}

const resolveRequestErrorMessage = (err, fallback) => {
  const responseMessage = err?.response?.data?.message
  if (responseMessage) return responseMessage
  const message = err?.message
  if (!message || /^Request failed with status code \d+$/.test(message)) return fallback
  return message
}

const toLocalIso = (value) => {
  if (!value) return null
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) {
    return value.length === 16 ? `${value}:00` : value
  }
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return null
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`
}

const normalizeDurationMinutes = (value) => {
  const minutes = Number(value)
  return Number.isFinite(minutes) && minutes > 0 ? minutes : DEFAULT_ESTIMATED_DURATION_MINUTES
}

const addMinutesToLocalIso = (value, minutes) => {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  date.setMinutes(date.getMinutes() + normalizeDurationMinutes(minutes))
  return toLocalIso(date)
}

const shouldReplaceEstimatedEnd = (start, end) => {
  if (!start) return false
  if (!end) return true
  const startDate = new Date(start)
  const endDate = new Date(end)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return true
  return endDate <= startDate
}

const getPositiveDurationFromRange = (start, end) => {
  if (!start || !end) return null
  const startDate = new Date(start)
  const endDate = new Date(end)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return null
  }
  const minutes = Math.round((endDate - startDate) / 60000)
  return minutes > 0 ? minutes : null
}

const syncScreenshotDurationFromRange = (start = screenshotForm.start_time, end = screenshotForm.end_time) => {
  const minutes = getPositiveDurationFromRange(start, end)
  if (!minutes) return false
  screenshotForm.estimated_duration_minutes = minutes
  return true
}

const fillScreenshotEstimatedEndTime = (force = false) => {
  if (!screenshotForm.start_time) return
  if (!force && !shouldReplaceEstimatedEnd(screenshotForm.start_time, screenshotForm.end_time)) return
  const endTime = addMinutesToLocalIso(
    screenshotForm.start_time,
    screenshotForm.estimated_duration_minutes
  )
  if (endTime) screenshotForm.end_time = endTime
}

const screenshotStartTime = computed({
  get: () => screenshotForm.start_time,
  set: (value) => {
    screenshotForm.start_time = value
    if (syncScreenshotDurationFromRange(value, screenshotForm.end_time)) return
    fillScreenshotEstimatedEndTime(true)
  }
})

const screenshotEndTime = computed({
  get: () => screenshotForm.end_time,
  set: (value) => {
    screenshotForm.end_time = value
    syncScreenshotDurationFromRange(screenshotForm.start_time, value)
  }
})

const screenshotEstimatedDurationMinutes = computed({
  get: () => screenshotForm.estimated_duration_minutes,
  set: (value) => {
    screenshotForm.estimated_duration_minutes = normalizeDurationMinutes(value)
    fillScreenshotEstimatedEndTime(true)
  }
})

const typeLabel = (event) => {
  const map = { course: '课程', activity: '活动', exam: '考试' }
  return map[event.rawType || event.type] || '日程'
}

const openEventDialog = (event) => {
  selectedEvent.value = event
  deleteScope.value = 'one'
  selectedColorType.value = getColorOption(event.color_type, event.rawType).value
  selectedMarkerLabel.value = event.markerLabel || defaultMarkerForType(event.rawType)
  selectedRemark.value = event.remark || ''
  eventDialogVisible.value = true
}

const resetScreenshotState = () => {
  screenshotFiles.value = []
  screenshotFileReady.value = false
  screenshotRawText.value = ''
  screenshotWarnings.value = []
  screenshotConflicts.value = []
  clearCropState()
  Object.assign(screenshotForm, {
    title: '',
    location: '',
    start_time: null,
    end_time: null,
    remark: '',
    estimated_duration_minutes: DEFAULT_ESTIMATED_DURATION_MINUTES,
    color_type: 'green',
    marker_label: '活'
  })
  screenshotUploadRef.value?.clearFiles()
}

const openScreenshotDialog = () => {
  resetScreenshotState()
  screenshotDialogVisible.value = true
}

const resetCropSelection = () => {
  cropSelection.x = 0
  cropSelection.y = 0
  cropSelection.width = 0
  cropSelection.height = 0
  cropping.value = false
}

const clearCropState = () => {
  if (cropImageUrl.value) URL.revokeObjectURL(cropImageUrl.value)
  cropImageUrl.value = ''
  cropSourceFile.value = null
  resetCropSelection()
}

const syncScreenshotFiles = (uploadFiles = []) => {
  const rawFiles = uploadFiles
    .map((item) => item.raw || item)
    .filter(Boolean)

  if (rawFiles.some((file) => !isAllowedScreenshotFile(file))) {
    screenshotFiles.value = []
    screenshotFileReady.value = false
    screenshotUploadRef.value?.clearFiles()
    ElMessage.warning('请上传 PNG、JPG、WEBP、BMP 或 TIFF 格式的图片。')
    return
  }

  screenshotFiles.value = rawFiles.slice(0, MAX_SCREENSHOT_FILES)
  screenshotFileReady.value = screenshotFiles.value.length > 0
}

const handleScreenshotFileChange = (_file, uploadFiles = []) => {
  screenshotRawText.value = ''
  screenshotWarnings.value = []
  screenshotConflicts.value = []
  syncScreenshotFiles(uploadFiles)
}

const handleScreenshotFileRemove = (_file, uploadFiles = []) => {
  screenshotRawText.value = ''
  screenshotWarnings.value = []
  screenshotConflicts.value = []
  syncScreenshotFiles(uploadFiles)
}

const handleScreenshotFileExceed = (files) => {
  const nextFiles = [...screenshotFiles.value, ...(files || [])].slice(0, MAX_SCREENSHOT_FILES)
  screenshotUploadRef.value?.clearFiles()
  nextFiles.forEach((file) => screenshotUploadRef.value?.handleStart(file))
  syncScreenshotFiles(nextFiles)
  ElMessage.warning(`一个活动最多支持 ${MAX_SCREENSHOT_FILES} 张截图。`)
}

const showCropDialogForFile = (file) => {
  clearCropState()
  cropSourceFile.value = file
  cropImageUrl.value = URL.createObjectURL(file)
  cropDialogVisible.value = true
}

const cropPointerPosition = (event) => {
  const stage = cropStageRef.value
  const image = cropImageRef.value
  const rect = stage?.getBoundingClientRect()
  if (!stage || !image || !rect) return { x: 0, y: 0 }
  return {
    x: Math.min(Math.max(event.clientX - rect.left + stage.scrollLeft, 0), image.clientWidth),
    y: Math.min(Math.max(event.clientY - rect.top + stage.scrollTop, 0), image.clientHeight)
  }
}

const startCropSelection = (event) => {
  if (!cropImageRef.value) return
  resetCropSelection()
  const point = cropPointerPosition(event)
  cropDragStart.x = point.x
  cropDragStart.y = point.y
  cropSelection.x = point.x
  cropSelection.y = point.y
  cropSelection.width = 0
  cropSelection.height = 0
  cropping.value = true
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

const moveCropSelection = (event) => {
  if (!cropping.value) return
  const point = cropPointerPosition(event)
  cropSelection.x = Math.min(cropDragStart.x, point.x)
  cropSelection.y = Math.min(cropDragStart.y, point.y)
  cropSelection.width = Math.abs(point.x - cropDragStart.x)
  cropSelection.height = Math.abs(point.y - cropDragStart.y)
}

const finishCropSelection = (event) => {
  if (!cropping.value) return
  moveCropSelection(event)
  cropping.value = false
  event.currentTarget.releasePointerCapture?.(event.pointerId)
}

const imageFromFile = (file) => new Promise((resolve, reject) => {
  const url = URL.createObjectURL(file)
  const image = new Image()
  image.onload = () => {
    URL.revokeObjectURL(url)
    resolve(image)
  }
  image.onerror = () => {
    URL.revokeObjectURL(url)
    reject(new Error('截图预览失败，请重试。'))
  }
  image.src = url
})

const cropImageFile = async (file) => {
  if (!hasCropSelection.value) return file
  const image = await imageFromFile(file)
  const rect = cropImageRef.value?.getBoundingClientRect()
  if (!rect || !image.naturalWidth || !image.naturalHeight) return file

  const scaleX = image.naturalWidth / rect.width
  const scaleY = image.naturalHeight / rect.height
  const sourceX = Math.round(cropSelection.x * scaleX)
  const sourceY = Math.round(cropSelection.y * scaleY)
  const sourceWidth = Math.round(cropSelection.width * scaleX)
  const sourceHeight = Math.round(cropSelection.height * scaleY)
  if (sourceWidth < MIN_CROP_SIZE || sourceHeight < MIN_CROP_SIZE) return file

  const canvas = document.createElement('canvas')
  canvas.width = sourceWidth
  canvas.height = sourceHeight
  const context = canvas.getContext('2d')
  if (!context) throw new Error('截图裁剪失败，请重试。')
  context.drawImage(
    image,
    sourceX,
    sourceY,
    sourceWidth,
    sourceHeight,
    0,
    0,
    sourceWidth,
    sourceHeight
  )
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))
  if (!blob) throw new Error('截图裁剪失败，请重试。')
  return new File([blob], `activity-schedule-crop-${Date.now()}.png`, { type: 'image/png' })
}

const appendScreenshotFile = (file) => {
  screenshotUploadRef.value?.handleStart(file)
  syncScreenshotFiles([...screenshotFiles.value, file])
}

const confirmCapturedScreenshot = async (useSelection = true) => {
  if (!cropSourceFile.value) return
  if (confirmingCrop.value) return
  confirmingCrop.value = true
  try {
    const file = useSelection ? await cropImageFile(cropSourceFile.value) : cropSourceFile.value
    appendScreenshotFile(file)
    cropDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err?.message || '截图裁剪失败，请重试。')
  } finally {
    confirmingCrop.value = false
  }
}

const captureCalendarScreenshot = async () => {
  if (!screenshotDialogVisible.value) openScreenshotDialog()
  if (screenshotFiles.value.length >= MAX_SCREENSHOT_FILES) {
    ElMessage.warning(`一个活动最多支持 ${MAX_SCREENSHOT_FILES} 张截图。`)
    return
  }
  try {
    const file = await captureScreenImage('activity-schedule')
    showCropDialogForFile(file)
  } catch (err) {
    ElMessage.warning(err?.message || '截屏已取消')
  }
}

const handleScreenshotShortcut = (event) => {
  if (!isScreenshotShortcut(event)) return
  event.preventDefault()
  event.stopPropagation()
  captureCalendarScreenshot()
}

const handleCropKeyboard = (event) => {
  if (!cropDialogVisible.value) return
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    if (hasCropSelection.value) {
      confirmCapturedScreenshot(true)
    }
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    cropDialogVisible.value = false
  }
}

const recognizeScreenshot = async () => {
  if (!screenshotFiles.value.length) {
    ElMessage.warning('请先选择活动截图。')
    return
  }

  recognizingScreenshot.value = true
  screenshotRawText.value = ''
  screenshotWarnings.value = []
  screenshotConflicts.value = []
  try {
    const formData = new FormData()
    screenshotFiles.value.forEach((file) => formData.append('files', file))
    const res = await recognizeScheduleImage(formData)
    const data = res.data || {}
    const event = data.event || {}
    const activity = data.activity || {}
    Object.assign(screenshotForm, {
      title: event.title || activity.title || '',
      location: event.location || activity.location || '',
      start_time: event.start_time || activity.start_time || null,
      end_time: event.end_time || activity.end_time || null,
      remark: event.remark || activity.remark || '',
      color_type: event.color_type || 'green',
      marker_label: event.marker_label || '活'
    })
    if (!syncScreenshotDurationFromRange()) {
      fillScreenshotEstimatedEndTime(false)
    }
    screenshotRawText.value = data.raw_text || ''
    screenshotWarnings.value = data.warnings || []
    screenshotConflicts.value = data.conflicts || []
    if (screenshotWarnings.value.length) {
      ElMessage.warning(`已识别，请补充：${screenshotWarnings.value.join('、')}`)
    } else {
      ElMessage.success('已识别活动信息')
    }
  } catch { /* 拦截器已处理 */ } finally {
    recognizingScreenshot.value = false
  }
}

const buildScreenshotPayload = (forceAdd = false) => ({
  title: screenshotForm.title.trim(),
  location: screenshotForm.location?.trim() || null,
  start_time: toLocalIso(screenshotForm.start_time),
  end_time: toLocalIso(screenshotForm.end_time),
  remark: screenshotForm.remark?.trim() || null,
  color_type: screenshotForm.color_type || 'green',
  marker_label: screenshotForm.marker_label?.trim() || '活',
  force_add: forceAdd
})

const addScreenshotEvent = async () => {
  const payload = buildScreenshotPayload(false)
  if (!payload.title || !payload.start_time || !payload.end_time) {
    ElMessage.warning('请先补全活动名称和起止时间。')
    return
  }
  if (new Date(payload.start_time) >= new Date(payload.end_time)) {
    ElMessage.warning('结束时间必须晚于开始时间。')
    return
  }

  addingScreenshotEvent.value = true
  try {
    const checkRes = await checkCustomEventConflict(payload)
    const conflicts = checkRes.data?.conflicts || []
    let forceAdd = false
    if (conflicts.length) {
      screenshotConflicts.value = conflicts
      const detail = conflicts
        .map((item) => `${item.title} · ${formatRange(item.start_time, item.end_time)}`)
        .join('\n')
      try {
        await ElMessageBox.confirm(
          `检测到冲突日程：\n${detail}\n\n仍然加入吗？`,
          '确认加入冲突日程',
          {
            type: 'warning',
            confirmButtonText: '仍然加入',
            cancelButtonText: '取消'
          }
        )
        forceAdd = true
      } catch {
        return
      }
    }

    const addRes = await addCustomEventToSchedule(buildScreenshotPayload(forceAdd))
    const alreadyExists = addRes.data?.already_exists
    ElMessage.success(alreadyExists ? '该日程已存在' : '已加入日程')
    screenshotDialogVisible.value = false
    await fetchSchedules()
  } catch (err) {
    ElMessage.error(err?.message || '加入日程失败，请稍后重试。')
  } finally {
    addingScreenshotEvent.value = false
  }
}

const deleteScopeHint = computed(() => {
  if (deleteScope.value === 'day') return '删除当前星期中这门课的所有时段。'
  if (deleteScope.value === 'all') return '删除课表中同名同教师课程的全部时段。'
  return '只移除当前日期的这一节课，其他周的重复课程会保留。'
})

const deleteScopeConfirmText = computed(() => {
  if (deleteScope.value === 'day') return '删除当天的'
  if (deleteScope.value === 'all') return '删除全部'
  return '删除本次'
})

const removeSelectedCourse = async () => {
  const event = selectedEvent.value
  if (!event?.course_id) {
    ElMessage.error('未找到对应课程记录，请刷新日历后重试。')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定${deleteScopeConfirmText.value}“${event.title}”吗？对应课程日程会同步移除。`,
      '删除课程',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  deletingCourse.value = true
  try {
    const res = await deleteCourse(event.course_id, deleteScope.value, {
      occurrenceStart: deleteScope.value === 'one' ? toLocalIso(event.start_time) : null
    })
    const deletedCourses = res.data?.deleted_courses || 0
    const deletedEvents = res.data?.deleted_events || 0
    const cancelledOccurrences = res.data?.cancelled_occurrences || 0
    if (deleteScope.value === 'one' && cancelledOccurrences > 0) {
      ElMessage.success('已移除本次课程，其他周的重复课程已保留。')
    } else {
      ElMessage.success(`已删除 ${deletedCourses} 条课程记录，移除 ${deletedEvents} 条日程。`)
    }
    eventDialogVisible.value = false
    await fetchSchedules()
  } catch (err) {
    ElMessage.error(err?.message || '删除课程失败，请稍后重试。')
  } finally {
    deletingCourse.value = false
  }
}

const saveSelectedEventAppearance = async () => {
  const event = selectedEvent.value
  if (!event?.id) {
    ElMessage.error('未找到对应日程，请刷新日历后重试。')
    return
  }

  savingAppearance.value = true
  try {
    await updateScheduleEventAppearance(event.id, {
      color_type: selectedColorType.value,
      marker_label: selectedMarkerLabel.value,
      remark: selectedRemark.value
    })
    ElMessage.success('日程已更新')
    eventDialogVisible.value = false
    await fetchSchedules()
  } catch (err) {
    ElMessage.error(err?.message || '更新日程失败，请稍后重试。')
  } finally {
    savingAppearance.value = false
  }
}

const removeSelectedActivity = async () => {
  const event = selectedEvent.value
  if (!event?.id || event.rawType !== 'activity') {
    ElMessage.error('未找到对应活动日程，请刷新日历后重试。')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定从日程中删除“${event.title}”吗？活动本身不会被下架。`,
      '删除活动日程',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  deletingActivity.value = true
  try {
    await deleteScheduleEvent(event.id)
    ElMessage.success('活动日程已删除')
    eventDialogVisible.value = false
    await fetchSchedules()
  } catch (err) {
    ElMessage.error(err?.message || '删除活动日程失败，请稍后重试。')
  } finally {
    deletingActivity.value = false
  }
}

const weekCourses = computed(() => {
  return allEvents.value.filter((c) => {
    if (c.rawType !== 'course') return false
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
  return allEvents.value.filter((e) => e.conflict)
})

const exams = computed(() => {
  return allEvents.value
    .filter((c) => c.rawType === 'exam')
    .map((c) => ({ title: c.title, examDate: formatDate(c.start_time), location: c.location }))
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
    if (res.code !== 0) throw new Error(res.message || '日程加载失败')
    allEvents.value = normalizeScheduleItems(res.data?.items || [])
  } catch (err) {
    allEvents.value = []
    error.value = resolveRequestErrorMessage(
      err,
      '日程加载失败，请确认后端服务正在运行后重试。'
    )
  } finally {
    loading.value = false
  }
}

const normalizeScheduleItems = (items) => {
  return items.map((item) => {
    const start = new Date(item.start_time)
    const end = new Date(item.end_time)
    const startMin = start.getHours() * 60 + start.getMinutes()
    const endMin = end.getHours() * 60 + end.getMinutes()
    const normalizedType = item.type || 'course'
    const colorOption = getColorOption(item.color_type, normalizedType)
    return {
      ...item,
      rawType: item.type,
      type: normalizedType,
      conflict: Boolean(item.is_conflict),
      markerLabel: item.marker_label || defaultMarkerForType(item.type),
      remark: item.remark || '',
      colorStyle: colorStyle(colorOption),
      weekday: start.getDay() || 7,
      startTime: timeText(start),
      endTime: timeText(end),
      startPeriod: sectionFromTime(timeText(start), 'start'),
      endPeriod: sectionFromTime(timeText(end), 'end'),
      teacher: item.teacher || '',
      weekType: parseWeekType(item.weeks),
      _startMin: startMin,
      _endMin: endMin,
      _top: Math.max(0, (startMin - START_HOUR * 60) / 60 * PX_PER_HOUR),
      _height: Math.max(10, (endMin - startMin) / 60 * PX_PER_HOUR)
    }
  })
}

const getColorOption = (value, eventType) => {
  const color = value || defaultColorByType[eventType] || 'gray'
  return scheduleColorOptions.find((option) => option.value === color)
    || scheduleColorOptions.find((option) => option.value === 'gray')
}

const colorStyle = (option) => ({
  '--event-bg': option.bg,
  '--event-border': option.border,
  '--event-bg-dark': option.darkBg || option.bg,
  '--event-border-dark': option.darkBorder || option.border
})

const swatchStyle = (option) => ({
  '--swatch-bg': option.bg,
  '--swatch-border': option.border
})

const defaultMarkerForType = (eventType) => {
  return defaultMarkerByType[eventType] || '日'
}

const parseWeekType = (weeks) => {
  if (!weeks) return ''
  if (String(weeks).includes('单周')) return '单周'
  if (String(weeks).includes('双周')) return '双周'
  return ''
}

const timeText = (date) => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const sectionFromTime = (value, boundary) => {
  const sectionTimes = [
    ['08:00', '08:45'],
    ['08:50', '09:35'],
    ['10:00', '10:45'],
    ['10:50', '11:35'],
    ['11:40', '12:25'],
    ['13:25', '14:10'],
    ['14:15', '15:00'],
    ['15:05', '15:50'],
    ['16:15', '17:00'],
    ['17:05', '17:50'],
    ['18:50', '19:35'],
    ['19:40', '20:25'],
    ['20:30', '21:15']
  ]
  const index = sectionTimes.findIndex((item) => item[boundary === 'start' ? 0 : 1] === value)
  return index >= 0 ? index + 1 : ''
}

const exportIcs = async () => {
  exporting.value = true
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const token = localStorage.getItem('token')
    const response = await fetch(`${baseUrl}/schedules/export-ics/file`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error('导出失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'schedule.ics'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('ICS 导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  syncWeekParityFilter()
  fetchSchedules()
  window.addEventListener('keydown', handleScreenshotShortcut, true)
  window.addEventListener('keydown', handleCropKeyboard, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleScreenshotShortcut, true)
  window.removeEventListener('keydown', handleCropKeyboard, true)
})
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
  align-items: stretch;
}

.toolbar-group {
  display: flex;
}

.cal-toolbar :deep(.el-button) {
  min-width: 92px;
  min-height: 32px;
  justify-content: center;
}

.cal-toolbar :deep(.el-button + .el-button) {
  margin-left: 0;
}

[data-theme="dark"] .parity-toggle-group :deep(.parity-toggle-button) {
  --el-button-bg-color: #252526;
  --el-button-border-color: #3e3e42;
  --el-button-text-color: #d4d4d4;
  --el-button-hover-bg-color: #313135;
  --el-button-hover-border-color: #4f5257;
  --el-button-hover-text-color: #f4f4f4;
  --el-button-active-bg-color: #34343a;
  --el-button-active-border-color: #5a5d63;
  --el-button-active-text-color: #ffffff;
}

[data-theme="dark"] .parity-toggle-group :deep(.parity-toggle-button.is-selected-parity),
[data-theme="dark"] :deep(.export-ics-button.el-button) {
  --el-button-bg-color: var(--el-fill-color-blank);
  --el-button-border-color: var(--el-border-color);
  --el-button-text-color: var(--el-text-color-regular);
  --el-button-hover-text-color: var(--el-color-primary);
  --el-button-hover-bg-color: var(--el-color-primary-light-9);
  --el-button-hover-border-color: var(--el-color-primary-light-7);
  --el-button-active-text-color: var(--el-color-primary);
  --el-button-active-bg-color: var(--el-color-primary-light-9);
  --el-button-active-border-color: var(--el-color-primary);
}

[data-theme="dark"] :deep(.current-week-button.el-button) {
  --el-button-bg-color: #1f5f87;
  --el-button-border-color: #4fa6d6;
  --el-button-text-color: #effbff;
  --el-button-hover-text-color: #f3fbff;
  --el-button-hover-bg-color: #2674a3;
  --el-button-hover-border-color: #68c0f2;
  --el-button-active-text-color: #ffffff;
  --el-button-active-bg-color: #2c84b7;
  --el-button-active-border-color: #7ad3ff;
}

[data-theme="dark"] :deep(.screenshot-add-button.el-button) {
  --el-button-bg-color: #1689da;
  --el-button-border-color: #48b5ff;
  --el-button-text-color: #ffffff;
  --el-button-hover-text-color: #ffffff;
  --el-button-hover-bg-color: #24a0f2;
  --el-button-hover-border-color: #6bc8ff;
  --el-button-active-text-color: #ffffff;
  --el-button-active-bg-color: #117bc6;
  --el-button-active-border-color: #54beff;
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

[data-theme="dark"] .page-panel.cal-header,
[data-theme="dark"] .timetable-card,
[data-theme="dark"] .side-panel {
  background: #252526;
  border-color: #3e3e42;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.3);
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

[data-theme="dark"] .timeline-wrap,
[data-theme="dark"] .timeline-body {
  background: #1e1e1e;
}

[data-theme="dark"] .timeline-header {
  background: #2d2d30;
  border-bottom-color: #3e3e42;
}

.time-ruler {
  width: 56px;
  flex-shrink: 0;
  position: relative;
  border-right: 1px solid var(--border);
  background: var(--bg-warm);
}

[data-theme="dark"] .time-ruler {
  background: #252526;
  border-right-color: #3e3e42;
}

.ruler-tick {
  position: absolute;
  width: 100%;
  text-align: center;
  font-size: 10px;
  color: var(--text-tertiary);
  transform: translateY(-50%);
}

[data-theme="dark"] .ruler-tick,
[data-theme="dark"] .day-head small,
[data-theme="dark"] .legend-item {
  color: #8b949e;
}

.day-col {
  flex: 1;
  position: relative;
}

[data-theme="dark"] .day-col {
  background: #1e1e1e;
  box-shadow: inset 1px 0 0 #252526;
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

[data-theme="dark"] .day-head strong {
  color: #d4d4d4;
}

[data-theme="dark"] .bg-line {
  border-top-color: #2a2d2e;
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
  background: var(--event-bg);
  border-left: 3px solid var(--event-border);
  cursor: pointer;
}

.timeline-event:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.timeline-event.has-conflict {
  background: #fdeaea;
  border-left-color: var(--danger);
  box-shadow: inset 0 0 0 1px var(--danger);
}

.timeline-event.has-conflict .ev-marker {
  background: var(--danger);
}

.timeline-event.has-conflict .ev-remark {
  color: var(--danger);
}

.timeline-event.has-conflict .ev-remark::before {
  background: var(--danger);
}

[data-theme="dark"] .timeline-event {
  background: var(--event-bg-dark, var(--event-bg));
  border-left-color: var(--event-border-dark, var(--event-border));
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05), 0 6px 14px rgba(0, 0, 0, 0.28);
}

[data-theme="dark"] .timeline-event .ev-marker {
  background: var(--event-border-dark, var(--event-border));
}

[data-theme="dark"] .timeline-event .ev-name {
  color: #f4f6fb;
}

[data-theme="dark"] .timeline-event .ev-time,
[data-theme="dark"] .timeline-event .ev-location {
  color: rgba(244, 246, 251, 0.78);
}

[data-theme="dark"] .timeline-event .ev-remark {
  color: var(--event-border-dark, var(--event-border));
}

[data-theme="dark"] .timeline-event .ev-remark::before {
  background: var(--event-border-dark, var(--event-border));
}

[data-theme="dark"] .timeline-event.has-conflict {
  background: #4a262c;
  border-left-color: #ff7b72;
  box-shadow: inset 0 0 0 1px rgba(255, 123, 114, 0.72), 0 6px 14px rgba(0, 0, 0, 0.32);
}

[data-theme="dark"] .timeline-event.has-conflict .ev-marker {
  background: #ff7b72;
}

[data-theme="dark"] .timeline-event.has-conflict .ev-name,
[data-theme="dark"] .timeline-event.has-conflict .ev-time,
[data-theme="dark"] .timeline-event.has-conflict .ev-location {
  color: #fff0ee;
}

[data-theme="dark"] .timeline-event.has-conflict .ev-conflict-label,
[data-theme="dark"] .timeline-event.has-conflict .ev-remark {
  color: #ffb2ab;
}

[data-theme="dark"] .timeline-event.has-conflict .ev-remark::before {
  background: #ffb2ab;
}

.timeline-event.is-compact {
  padding: 4px 4px 3px;
  border-left-width: 2px;
}

.ev-title-row {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  min-width: 0;
  flex: 0 0 auto;
  padding-right: 24px;
}

.ev-marker {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 16px;
  background: var(--event-border);
  color: #fff;
  font-size: 10px;
  line-height: 1;
  font-weight: 700;
}

.ev-conflict-label {
  color: var(--danger);
  font-size: 10px;
  line-height: 1.1;
  font-weight: 700;
  flex: 0 0 auto;
  padding-top: 2px;
}

.timeline-event.is-compact .ev-title-row {
  display: block;
  min-height: 100%;
  padding-right: 0;
}

.timeline-event.is-compact .ev-marker {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 14px;
  height: 14px;
  font-size: 9px;
  flex: 0 0 14px;
  z-index: 1;
}

.timeline-event.is-compact .ev-conflict-label {
  position: absolute;
  top: 6px;
  left: 22px;
  font-size: 8px;
  padding-top: 0;
  z-index: 1;
}

.ev-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 12px;
  min-width: 0;
  overflow: hidden;
  line-height: 1.25;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.timeline-event.is-compact .ev-name {
  display: block;
  height: calc(100% - 18px);
  padding-top: 18px;
  font-size: 11px;
  line-height: 1.12;
  white-space: normal;
  overflow: hidden;
  text-overflow: clip;
  display: block;
  word-break: break-all;
  overflow-wrap: anywhere;
}

.ev-remark,
.ev-time {
  color: var(--text-tertiary);
  font-size: 9px;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 0 0 auto;
}

.ev-remark {
  color: var(--event-border);
  font-size: 11px;
  font-weight: 600;
  padding-left: 8px;
  position: relative;
}

.timeline-event.is-compact .ev-remark,
.timeline-event.is-compact .ev-time,
.timeline-event.is-compact .ev-location {
  font-size: 8px;
  display: none;
}

.ev-remark::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--event-border);
  transform: translateY(-50%);
}

.ev-location {
  color: var(--text-tertiary);
  font-size: 9px;
  line-height: 1.25;
  min-height: 0;
  overflow: hidden;
  white-space: normal;
  overflow-wrap: anywhere;
  flex: 1 1 auto;
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

.timeline-tooltip {
  display: grid;
  gap: 4px;
  max-width: 248px;
  font-size: 12px;
  line-height: 1.45;
}

.timeline-tooltip strong {
  color: var(--text-primary);
  font-size: 13px;
}

.tooltip-meta {
  color: var(--text-secondary);
  word-break: break-word;
}

.tooltip-warning {
  color: var(--danger);
  font-weight: 600;
}

:deep(.timeline-event-tooltip) {
  max-width: 280px;
}

/* ── Side panel ── */
.side-panel {
  display: grid;
  gap: 14px;
  position: sticky;
  top: 88px;
  min-width: 0;
}

.side-list {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.side-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-warm);
  border: 1px solid var(--border-light);
}

[data-theme="dark"] .side-item,
[data-theme="dark"] .dialog-item,
[data-theme="dark"] .screenshot-preview,
[data-theme="dark"] .crop-canvas {
  background: #2d2d30;
  border-color: #3e3e42;
}

[data-theme="dark"] .side-item:hover,
[data-theme="dark"] .side-item.clickable:focus-visible {
  background: #34343a;
}

[data-theme="dark"] .side-item-left strong,
[data-theme="dark"] .section-title {
  color: #d4d4d4;
}

.side-item.clickable {
  cursor: pointer;
}

.side-item.clickable:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.side-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1 1 auto;
  min-width: 0;
}

.side-item-left > div {
  min-width: 0;
}

.side-item-left strong {
  font-size: 13px;
  display: block;
  white-space: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.side-item-left p {
  margin: 2px 0 0;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.side-marker {
  width: 20px;
  height: 20px;
  flex-basis: 20px;
  font-size: 11px;
}

.side-item-right {
  text-align: right;
  font-size: 11px;
  flex: 0 1 84px;
  min-width: 64px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.side-item-right .faint,
.side-item-right :deep(.el-button) {
  max-width: 100%;
}

.side-item-right .faint {
  overflow-wrap: anywhere;
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

.screenshot-dialog-body {
  display: grid;
  gap: 14px;
}

.upload-icon {
  font-size: 36px;
  color: var(--accent);
}

.screenshot-capture-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.screenshot-form :deep(.el-date-editor.el-input) {
  width: 100%;
}

.duration-input {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.duration-input span {
  color: var(--text-secondary);
  font-size: 13px;
}

.screenshot-swatches {
  padding-top: 2px;
}

.screenshot-conflicts,
.screenshot-preview {
  padding: 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  background: var(--bg-warm);
  font-size: 13px;
}

.screenshot-conflicts {
  display: grid;
  gap: 6px;
  color: var(--danger);
  background: var(--danger-light);
  border-color: #edc8c6;
}

.screenshot-preview {
  max-height: 160px;
  overflow: auto;
}

.screenshot-preview p {
  margin: 8px 0 0;
  white-space: pre-wrap;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.crop-stage {
  display: grid;
  gap: 10px;
}

.crop-canvas {
  position: relative;
  width: 100%;
  max-height: 68vh;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-warm);
  cursor: crosshair;
  user-select: none;
  touch-action: none;
}

.crop-canvas img {
  display: block;
  width: 100%;
  height: auto;
  pointer-events: none;
}

.crop-selection {
  position: absolute;
  border: 2px solid var(--accent);
  background: rgba(96, 141, 193, 0.18);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.28);
  pointer-events: none;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.dialog-title strong {
  min-width: 0;
  overflow-wrap: anywhere;
}

.dialog-marker {
  width: 22px;
  height: 22px;
  flex-basis: 22px;
  font-size: 12px;
}

.event-detail {
  display: grid;
  gap: 16px;
}

.course-delete-panel {
  display: grid;
  gap: 10px;
}

.event-edit-panel {
  display: grid;
  gap: 10px;
}

.course-delete-panel h4,
.event-edit-panel h4 {
  margin: 0;
}

.delete-scope-group,
.color-swatch-grid {
  display: flex;
  flex-wrap: wrap;
}

.marker-input {
  max-width: 120px;
}

.remark-input {
  max-width: 100%;
}

.color-swatch-grid {
  gap: 8px;
}

.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--swatch-border);
  background: var(--swatch-bg);
  cursor: pointer;
  padding: 0;
  box-shadow: inset 0 0 0 3px var(--bg-surface);
}

.color-swatch.active {
  outline: 2px solid var(--swatch-border);
  outline-offset: 2px;
}

[data-theme="dark"] .course-dot   { background: #7a9ed3; }
[data-theme="dark"] .activity-dot { background: #8bc4a0; }
[data-theme="dark"] .exam-dot     { background: #a08ec8; }

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
