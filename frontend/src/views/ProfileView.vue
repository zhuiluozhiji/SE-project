<template>
  <section class="profile-page fade-in">
    <div v-if="loading" v-loading="loading" class="loading-placeholder" />

    <template v-else-if="user">
      <div class="card profile-card">
        <div class="profile-header">
          <div class="avatar">{{ (user.username || '?').slice(0, 2).toUpperCase() }}</div>
          <div>
            <h2 class="page-title">{{ user.username || '未设置昵称' }}</h2>
            <p class="muted">{{ user.college || '未设置学院' }} · {{ user.major || '' }}</p>
          </div>
        </div>
        <div class="profile-meta">
          <div>
            <span class="muted">已加入活动</span>
            <strong>{{ stats.joined || '--' }}</strong>
          </div>
          <div>
            <span class="muted">兴趣标签</span>
            <strong>{{ stats.tagCount || '--' }}</strong>
          </div>
          <div>
            <span class="muted">本周冲突</span>
            <strong>{{ stats.conflicts || '--' }}</strong>
          </div>
        </div>
      </div>

      <div class="profile-grid">
        <div class="card">
          <h3 class="section-title">兴趣标签</h3>
          <div class="tag-row" v-if="userTags.length">
            <span class="chip" v-for="tag in userTags" :key="tag">{{ tag }}</span>
          </div>
          <p class="muted" v-else>暂无兴趣标签</p>
          <p class="muted">推荐理由将基于以上标签生成。</p>
        </div>

        <div class="card">
          <h3 class="section-title">学术轨迹</h3>
          <div v-if="timeline.length === 0" class="empty-hint">
            <p class="muted">暂无活动记录</p>
          </div>
          <div class="timeline" v-else>
            <div class="timeline-item" v-for="item in timeline" :key="item.id || item.title">
              <span class="dot"></span>
              <div>
                <strong>{{ item.action || '参加' }}：{{ item.title }}</strong>
                <p class="muted">{{ formatTime(item.created_at || item.time) }} · {{ item.campus || item.location || '' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="error" class="empty-state">
      <p>加载失败</p>
      <small>{{ error }}</small>
      <el-button size="small" type="primary" @click="fetchProfile">重试</el-button>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()

const loading = ref(false)
const error = ref('')

const user = computed(() => auth.user)

const stats = reactive({
  joined: '--',
  tagCount: '--',
  conflicts: '--'
})

const userTags = computed(() => {
  return auth.user?.interests || auth.user?.tags || []
})

const timeline = ref([])

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const fetchProfile = async () => {
  loading.value = true
  error.value = ''
  try {
    await auth.fetchUser()
    if (auth.user?.tags) {
      stats.tagCount = auth.user.tags.length
    }
    if (auth.user?.joined_count !== undefined) {
      stats.joined = auth.user.joined_count
    }
    if (auth.user?.conflict_count !== undefined) {
      stats.conflicts = auth.user.conflict_count
    }
    if (auth.user?.timeline) {
      timeline.value = auth.user.timeline
    }
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(fetchProfile)
</script>

<style scoped>
.profile-page {
  display: grid;
  gap: 16px;
}

.loading-placeholder {
  min-height: 200px;
}

.profile-card {
  display: grid;
  gap: 14px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: #0f766e;
  color: #ffffff;
  font-weight: 700;
}

.profile-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.profile-meta strong {
  display: block;
  font-size: 20px;
  margin-top: 4px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.timeline {
  display: grid;
  gap: 12px;
}

.timeline-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.timeline-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e27a38;
  margin-top: 6px;
}

.empty-hint {
  text-align: center;
  padding: 24px 0;
}

.empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  min-height: 200px;
  gap: 8px;
  color: #6b7280;
}
</style>
