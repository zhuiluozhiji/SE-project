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
          <p>第一阶段 MVP 骨架，业务接口与页面可并行填充。</p>
        </div>
        <el-button type="primary" @click="$router.push('/login')">登录</el-button>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const routeTitle = computed(() => route.meta.title || '校园学术活动智能推荐平台')
</script>
