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
          <span>首页推荐</span>
        </el-menu-item>
        <el-menu-item index="/activities">
          <span>活动列表</span>
        </el-menu-item>
        <el-menu-item index="/calendar">
          <span>个人日历</span>
        </el-menu-item>
        <el-menu-item index="/courses/import">
          <span>课表导入</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <span>个人中心</span>
        </el-menu-item>
        <el-menu-item index="/admin">
          <span>后台管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div>
          <h1>{{ routeTitle }}</h1>
          <p>聚合校园学术活动与个人日程，优先保证主流程清晰可用。</p>
        </div>
        <div class="header-actions">
          <el-input
            class="header-search"
            v-model="searchKeyword"
            placeholder="搜索活动、讲座或主讲人"
            @keyup.enter="goSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <template v-if="auth.isLoggedIn">
            <el-button text @click="$router.push('/profile')">
              {{ auth.user?.username || '用户' }}
            </el-button>
            <el-button type="danger" plain size="small" @click="handleLogout">退出</el-button>
          </template>
          <template v-else>
            <el-button type="primary" @click="$router.push('/login')">登录</el-button>
          </template>
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
import { Search } from '@element-plus/icons-vue'
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
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-search {
  width: 260px;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #fff5e3;
  border: 1px solid #eadac6;
  font-size: 12px;
  color: #6b5b45;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0f766e;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.2);
}
</style>
