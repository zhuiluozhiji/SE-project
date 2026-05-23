<template>
  <section class="profile-page fade-in">
    <div v-if="loading" v-loading="loading" class="loading-block" />

    <template v-else-if="user">
      <div class="profile-hero">
        <div class="profile-avatar">{{ (user.username || '?').slice(0, 2).toUpperCase() }}</div>
        <div class="profile-hero-body">
          <h2 class="profile-name">{{ user.username || '未设置昵称' }}</h2>
          <p class="muted">{{ user.college || '未设置学院' }}<template v-if="user.major"> &middot; {{ user.major }}</template></p>
        </div>
        <div class="profile-numbers">
          <div class="profile-num">
            <strong>{{ stats.joined }}</strong>
            <span>已加入</span>
          </div>
          <div class="profile-num">
            <strong>{{ stats.tagCount }}</strong>
            <span>兴趣标签</span>
          </div>
          <div class="profile-num">
            <strong>{{ stats.conflicts }}</strong>
            <span>本周冲突</span>
          </div>
        </div>
      </div>

      <div class="profile-grid">
        <div class="card">
          <h3 class="section-title">兴趣标签</h3>
          <div class="tag-cluster" v-if="userTags.length">
            <span class="chip" v-for="tag in userTags" :key="tag">{{ tag }}</span>
          </div>
          <p class="muted" v-else>暂无兴趣标签</p>
          <p class="faint tag-hint">推荐理由将基于以上标签生成</p>
        </div>

        <div class="card">
          <h3 class="section-title">学术轨迹</h3>
          <div v-if="timeline.length === 0" class="empty-hint">
            <p class="muted">暂无活动记录，去探索活动吧</p>
          </div>
          <div class="timeline-list" v-else>
            <div class="tl-item" v-for="item in timeline" :key="item.id || item.title">
              <span class="tl-dot"></span>
              <div class="tl-body">
                <strong>{{ item.action || '参加' }}：{{ item.title }}</strong>
                <span class="faint">{{ fmtDate(item.created_at || item.time) }} &middot; {{ item.campus || item.location || '' }}</span>
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

const fmtDate = (t) => {
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
    if (auth.user?.tags) stats.tagCount = auth.user.tags.length
    if (auth.user?.joined_count !== undefined) stats.joined = auth.user.joined_count
    if (auth.user?.conflict_count !== undefined) stats.conflicts = auth.user.conflict_count
    if (auth.user?.timeline) timeline.value = auth.user.timeline
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
  gap: 20px;
}

.loading-block { min-height: 200px; }

/* ── Hero ── */
.profile-hero {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.profile-avatar {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: var(--text-primary);
  color: var(--bg-surface);
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-display);
  flex-shrink: 0;
}

.profile-hero-body {
  flex: 1;
  min-width: 0;
}

.profile-name {
  margin: 0 0 4px;
  font-size: 22px;
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 0.03em;
}

.profile-numbers {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
}

.profile-num {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 20px;
  background: var(--bg-warm);
  min-width: 80px;
}

.profile-num + .profile-num {
  border-left: 1px solid var(--border);
}

.profile-num strong {
  font-size: 22px;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-primary);
}

.profile-num span {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* ── Grid ── */
.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  align-items: start;
}

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.tag-hint {
  font-size: 12px;
}

/* ── Timeline ── */
.timeline-list {
  display: grid;
  gap: 0;
}

.tl-item {
  display: flex;
  gap: 14px;
  padding: 12px 0;
  position: relative;
}

.tl-item + .tl-item {
  border-top: 1px solid var(--border-light);
}

.tl-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
  margin-top: 5px;
}

.tl-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tl-body strong { font-size: 14px; }
.tl-body span { font-size: 12px; }

.empty-hint {
  text-align: center;
  padding: 28px 0;
}

@media (max-width: 960px) {
  .profile-hero {
    flex-wrap: wrap;
  }
  .profile-numbers {
    width: 100%;
  }
  .profile-num {
    flex: 1;
  }
}
</style>
