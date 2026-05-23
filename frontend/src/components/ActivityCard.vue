<template>
  <article class="card activity-card" @click="$router.push(`/activities/${activity.id}`)">
    <div class="card-top">
      <StatusTag :label="statusLabel" :status="activity.status || 'open'" />
      <span class="faint">{{ fmtDate(activity.start_time || activity.time) }}</span>
    </div>
    <h3 class="card-title">{{ activity.title }}</h3>
    <p class="muted card-desc">{{ truncate(activity.description || activity.summary, 72) }}</p>
    <div class="tag-row" v-if="tags.length">
      <span class="chip" v-for="tag in tags.slice(0, 3)" :key="tag">{{ tag }}</span>
    </div>
    <div class="card-foot">
      <span class="faint">{{ activity.campus || '' }} {{ activity.location || '' }}</span>
      <span class="card-arrow">&rarr;</span>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import StatusTag from './StatusTag.vue'

const props = defineProps({
  activity: { type: Object, required: true }
})

const statusMap = {
  open: '可加入',
  full: '已满',
  closed: '已结束',
  offline: '已下架',
  draft: '草稿'
}

const statusLabel = computed(() => statusMap[props.activity.status] || props.activity.status || '未知')

const tags = computed(() => {
  if (Array.isArray(props.activity.tags)) return props.activity.tags
  if (typeof props.activity.tags === 'string') return props.activity.tags.split(',')
  return []
})

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
</script>

<style scoped>
.activity-card {
  cursor: pointer;
}

.card-title {
  margin: 8px 0 6px;
  font-size: 17px;
  font-family: var(--font-display);
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--text-primary);
}

.card-desc {
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  font-size: 12px;
}

.card-arrow {
  font-size: 16px;
  color: var(--text-tertiary);
  transition: color 0.2s, transform 0.2s;
}

.activity-card:hover .card-arrow {
  color: var(--accent);
  transform: translateX(3px);
}
</style>
