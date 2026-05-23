import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '首页推荐' }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录注册' }
  },
  {
    path: '/activities',
    name: 'activities',
    component: () => import('../views/ActivityListView.vue'),
    meta: { title: '活动列表' }
  },
  {
    path: '/activities/:id',
    name: 'activity-detail',
    component: () => import('../views/ActivityDetailView.vue'),
    meta: { title: '活动详情' }
  },
  {
    path: '/calendar',
    name: 'calendar',
    component: () => import('../views/CalendarView.vue'),
    meta: { title: '个人日历', requiresAuth: true }
  },
  {
    path: '/courses/import',
    name: 'course-import',
    component: () => import('../views/CourseImportView.vue'),
    meta: { title: '课表导入', requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { title: '个人中心', requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/AdminView.vue'),
    meta: { title: '后台管理', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    ElMessage.warning('请先登录')
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
