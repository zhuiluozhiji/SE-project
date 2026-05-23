<template>
  <el-container class="app-shell">
    <el-aside class="app-sidebar" width="232px">
      <div class="brand">
        <span class="brand-mark">SE</span>
        <div>
          <strong>学术活动平台</strong>
          <small>Campus Events</small>
        </div>
      </div>

      <el-menu router :default-active="$route.path" class="nav-menu">
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页推荐</span>
        </el-menu-item>
        <el-menu-item index="/activities">
          <el-icon><List /></el-icon>
          <span>活动列表</span>
        </el-menu-item>
        <el-menu-item index="/calendar">
          <el-icon><Calendar /></el-icon>
          <span>个人日历</span>
        </el-menu-item>
        <el-menu-item index="/courses/import">
          <el-icon><Upload /></el-icon>
          <span>课表导入</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
        <el-menu-item index="/admin">
          <el-icon><Setting /></el-icon>
          <span>后台管理</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <template v-if="auth.isLoggedIn">
          <div class="sidebar-user" @click="$router.push('/profile')">
            <span class="sidebar-avatar">{{ (auth.user?.username || '?').slice(0, 2).toUpperCase() }}</span>
            <div class="sidebar-user-info">
              <strong>{{ auth.user?.username || '用户' }}</strong>
              <small>{{ auth.user?.college || '' }}</small>
            </div>
          </div>
          <el-button text class="logout-btn" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </template>
        <template v-else>
          <el-button type="primary" class="login-btn-side" @click="$router.push('/login')">登录</el-button>
        </template>
      </div>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <h1>{{ routeTitle }}</h1>
        </div>
        <div class="header-actions">
          <el-input
            class="header-search"
            v-model="searchKeyword"
            placeholder="搜索活动、讲座或主讲人..."
            @keyup.enter="goSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, HomeFilled, List, Calendar, Upload, User, Setting, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from './store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const searchKeyword = ref('')
const routeTitle = computed(() => route.meta.title || '校园学术活动智能推荐平台')

const goSearch = () => {
  const kw = searchKeyword.value.trim()
  if (kw) {
    router.push({ path: '/activities', query: { keyword: kw } })
  }
}

const handleLogout = () => {
  auth.logout()
  router.push('/')
}
</script>

<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.header-search {
  width: 260px;
}

/* ── 侧边栏底部用户区 ── */
.sidebar-footer {
  margin-top: auto;
  padding: 16px 14px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}

.sidebar-user:hover {
  background: var(--bg-muted);
}

.sidebar-avatar {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: var(--text-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-display);
  flex-shrink: 0;
}

.sidebar-user-info {
  min-width: 0;
}

.sidebar-user-info strong {
  display: block;
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-user-info small {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.login-btn-side {
  width: 100%;
}
</style>
