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
            <div v-if="descriptionParagraphs.length" class="detail-desc">
              <p v-for="(paragraph, index) in descriptionParagraphs" :key="`${index}-${paragraph.slice(0, 12)}`">
                {{ paragraph }}
              </p>
            </div>
            <p v-else class="detail-desc">暂无详细介绍</p>

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
              <div v-if="activity.source_url">
                <dt>来源</dt>
                <dd>
                  <el-link
                    type="primary"
                    :href="activity.source_url"
                    target="_blank"
                    :underline="false"
                  >
                    查看原文 <el-icon style="vertical-align:middle"><Link /></el-icon>
                  </el-link>
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
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
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

const sectionHeadingPattern = /^[一二三四五六七八九十百千万]+、\S+/
const listItemPattern = /^([0-9]+[.．、)]|[（(][0-9一二三四五六七八九十]+[）)]|-\s+|[•●▪◦])\s*/
const listMarkerOnlyPattern = /^([一二三四五六七八九十百千万]+[、.．]|[0-9]+[.．、)]|[（(][一二三四五六七八九十]+[）)])$/
const numericListMarkerOnlyPattern = /^[0-9]+[.．、)]$/
const fieldLinePattern = /^[\u4e00-\u9fa5A-Za-z0-9]{2,12}[：:]\s*(?:\S.*)?$/
const paragraphEndPattern = /[。！？!?；;：:]$/
const continuationStartPattern = /^[，,。！？!?；;：:、）)]/
const categoryLabelOnlyPattern = /^(?:社会实践|志愿者活动|团支部活动|讲座报告|学术科技|创新创业|文体活动)\s*[：:]$/
const attachmentLabelPattern = /(附件\s*[0-9一二三四五六七八九十]*\s*[：:])/g
const attachmentLabelOnlyPattern = /^附件\s*[0-9一二三四五六七八九十]*\s*[：:]$/
const fieldLabelOnlyPattern = /^[\u4e00-\u9fa5A-Za-z0-9]{2,12}[：:]\s*$/
const numberedFieldLabelPattern = /^([0-9]+[.．、)]|[（(][0-9一二三四五六七八九十]+[）)])\s*[\u4e00-\u9fa5A-Za-z0-9]{2,12}[：:]\s*$/
const inlineListMarkerPattern = /([\u4e00-\u9fa5）)])([0-9]+[.．、)])(?=\s*$|\s*[\u4e00-\u9fa5A-Za-z])/g
const inlineCategoryLabelPattern = /((?:社会实践|志愿者活动|团支部活动|讲座报告|学术科技|创新创业|文体活动)\s*[：:])/g
const urlStartPattern = /^https?:\/\//
const detachedMarkerNumberPattern = /^[0-9一二三四五六七八九十百千万]+$/
const detachedMarkerPunctuationPattern = /^[.．、)]$/
const labelWithoutColonPattern = /^[\u4e00-\u9fa5A-Za-z0-9]{2,12}$/
const colonOnlyPattern = /^[：:]$/

const normalizeYearDigits = (text) => text.replace(
  /\b(?:\d\s*){4}(?=\s*(?:年|年度|级|届|[-—~/,，。；;:：）)]|$))/g,
  (year) => year.replace(/\s+/g, '')
)

const normalizeLine = (line) => normalizeYearDigits(
  line.replace(/\u00a0/g, ' ').replace(/[ \t]+/g, ' ').trim()
)

const nextContentLine = (lines, startIndex) => {
  for (let index = startIndex; index < lines.length; index += 1) {
    if (lines[index]) return lines[index]
  }
  return ''
}

const compactDescriptionLines = (text) => {
  const lines = text.split('\n').map((line) => normalizeLine(line))
  const compacted = []

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]
    const next = lines[index + 1] || ''
    const markerWithContent = next.match(/^([.．、)])\s*(\S.*)$/)

    if (line.endsWith('附件') && /^[0-9一二三四五六七八九十]+$/.test(next)) {
      compacted.push(`${line}${next}`)
      index += 1
      continue
    }

    if (
      line
      && detachedMarkerNumberPattern.test(line)
      && markerWithContent
      && !/^\d/.test(markerWithContent[2])
    ) {
      compacted.push(`${line}${next}`)
      index += 1
      continue
    }

    if (
      line
      && detachedMarkerNumberPattern.test(line)
      && detachedMarkerPunctuationPattern.test(next)
    ) {
      const afterMarker = nextContentLine(lines, index + 2)
      if (afterMarker && !/^-?\d+$/.test(afterMarker)) {
        compacted.push(`${line}${next}`)
        index += 1
        continue
      }
    }

    if (line && labelWithoutColonPattern.test(line) && colonOnlyPattern.test(next)) {
      compacted.push(`${line}${next}`)
      index += 1
      continue
    }

    compacted.push(line)
  }

  return compacted
}

const splitStructuredLine = (line) => line
  .replace(inlineListMarkerPattern, '$1\n$2')
  .replace(inlineCategoryLabelPattern, '\n$1')
  .replace(attachmentLabelPattern, '\n$1')
  .split('\n')
  .map((part) => part.trim())
  .filter(Boolean)

const isOpenFieldLabel = (text) => (
  attachmentLabelOnlyPattern.test(text)
  || fieldLabelOnlyPattern.test(text)
  || numberedFieldLabelPattern.test(text)
)

const shouldBreakBeforeField = (line) => (
  attachmentLabelOnlyPattern.test(line) || categoryLabelOnlyPattern.test(line)
)

const needsSpaceBetween = (prev, next) => {
  if (!prev || !next) return false
  if (listMarkerOnlyPattern.test(prev)) return numericListMarkerOnlyPattern.test(prev)
  const prevChar = prev.at(-1) || ''
  const nextChar = next[0] || ''
  if (/\d/.test(prevChar) && /\d/.test(nextChar)) return false
  return /[A-Za-z0-9]/.test(prevChar) && /[A-Za-z0-9]/.test(nextChar)
}

const shouldStartParagraph = (current, line) => {
  if (!current || !line) return false
  if (listMarkerOnlyPattern.test(current)) return false
  if (isOpenFieldLabel(current)) return false
  if (urlStartPattern.test(line)) return false
  if (continuationStartPattern.test(line)) return false
  return paragraphEndPattern.test(current)
}

const formatDescription = (text) => {
  if (!text) return []

  const normalized = text.replace(/\r\n?/g, '\n').trim()
  if (!normalized) return []

  const paragraphs = []
  let current = ''

  const flush = () => {
    if (!current) return
    paragraphs.push(current)
    current = ''
  }

  for (const rawLine of compactDescriptionLines(normalized)) {
    const lines = splitStructuredLine(normalizeLine(rawLine))

    if (!lines.length) {
      if (current && (listMarkerOnlyPattern.test(current) || isOpenFieldLabel(current))) {
        continue
      }
      flush()
      continue
    }

    for (const line of lines) {
      if (sectionHeadingPattern.test(line)) {
        flush()
        paragraphs.push(line)
        continue
      }

      if (urlStartPattern.test(line)) {
        if (!current) {
          current = line
          continue
        }

        current += `${needsSpaceBetween(current, line) ? ' ' : ''}${line}`
        continue
      }

      if (fieldLinePattern.test(line)) {
        if (current && (listMarkerOnlyPattern.test(current) || !shouldBreakBeforeField(line))) {
          current += `${needsSpaceBetween(current, line) ? ' ' : ''}${line}`
          continue
        }

        flush()
        if (isOpenFieldLabel(line)) {
          current = line
          continue
        }
        paragraphs.push(line)
        continue
      }

      if (listItemPattern.test(line) && current) {
        flush()
      }

      if (shouldStartParagraph(current, line)) {
        flush()
      }

      if (!current) {
        current = line
        continue
      }

      current += `${needsSpaceBetween(current, line) ? ' ' : ''}${line}`
    }
  }

  flush()
  return paragraphs
}

const descriptionParagraphs = computed(() => formatDescription(activity.value?.description))

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

watch(
  () => route.params.id,
  () => {
    fetchDetail()
  },
  { immediate: true }
)
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
  white-space: normal;
  word-break: break-word;
}

.detail-desc p {
  margin: 0;
}

.detail-desc p + p {
  margin-top: 0.8em;
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
