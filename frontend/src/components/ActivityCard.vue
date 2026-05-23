<template>
  <article class="card activity-card" @click="$router.push(`/activities/${activity.id}`)">
    <div class="card-top">
      <StatusTag :label="statusLabel" :status="activity.status || 'open'" />
      <span class="muted">{{ formatTime(activity.start_time || activity.time) }}</span>
    </div>
    <h3>{{ activity.title }}</h3>
    <p class="muted">{{ truncate(activity.description || activity.summary, 80) }}</p>
    <div class="tag-row" v-if="tags.length">
      <span class="chip" v-for="tag in tags" :key="tag">{{ tag }}</span>
    </div>
    <div class="card-meta">
      <span>{{ activity.campus || '' }} {{ activity.location || '' }}</span>
      <el-button size="small" type="primary" plain @click.stop="$router.push(`/activities/${activity.id}`)">
        查看详情
      </el-button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import StatusTag from './StatusTag.vue'

const props = defineProps({
  activity: {
    type: Object,
    required: true
  }
})

const statusMap = {
  open: '可加入',
  full: '已满',
  closed: '已结束',
  offline: '已下架',
  draft: '草稿'
}

const statusLabel = computed(() => {
  return statusMap[props.activity.status] || props.activity.status || '未知'
})

const tags = computed(() => {
  if (Array.isArray(props.activity.tags)) return props.activity.tags
  if (typeof props.activity.tags === 'string') return props.activity.tags.split(',')
  return []
})

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const truncate = (text, max) => {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}
</script>

<style scoped>
.activity-card {
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}

.activity-card:hover {
  box-shadow: 0 16px 36px rgba(44, 34, 16, 0.14);
  transform: translateY(-2px);
}

.activity-card h3 {
  margin: 8px 0 6px;
  font-size: 18px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  color: #7a6a55;
  font-size: 12px;
}
</style>
