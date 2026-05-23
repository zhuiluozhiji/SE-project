<template>
  <section class="login-page fade-in">
    <div class="login-hero">
      <h2>校园学术活动智能推荐平台</h2>
      <p>以兴趣为线索，连接活动发现、日程管理与学术成长轨迹。</p>
      <div class="hero-stats">
        <div>
          <strong>1,280</strong>
          <span>已汇聚活动</span>
        </div>
        <div>
          <strong>92%</strong>
          <span>推荐匹配率</span>
        </div>
      </div>
    </div>
    <div class="card login-card">
      <h2 class="page-title">{{ isRegister ? '注册账号' : '登录' }}</h2>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" v-if="isRegister">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleSubmit">
            {{ isRegister ? '注册' : '登录' }}
          </el-button>
          <el-button size="large" @click="isRegister = !isRegister; resetForm()">
            {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
          </el-button>
        </el-form-item>
      </el-form>
      <p class="muted">登录后可同步课表、生成日程冲突提示与个性化推荐。</p>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()

const isRegister = ref(false)
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const resetForm = () => {
  form.username = ''
  form.password = ''
  form.confirmPassword = ''
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      if (isRegister.value) {
        ElMessage.info('注册功能将在后续版本开放，请使用测试账号登录')
        loading.value = false
        return
      }
      await auth.login({ username: form.username, password: form.password })
      ElMessage.success('登录成功')
      router.push('/')
    } catch {
      // 错误已在 http 拦截器中处理
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 0.9fr);
  gap: 20px;
}

.login-hero {
  padding: 24px;
  border-radius: 20px;
  background: linear-gradient(135deg, #f6efe4 0%, #f2dfc5 60%, #f0d2b1 100%);
  border: 1px solid #eadac6;
  box-shadow: 0 14px 30px rgba(54, 40, 18, 0.1);
}

.login-hero h2 {
  margin: 0 0 8px;
  font-family: "Noto Serif SC", "Noto Sans SC", serif;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.hero-stats strong {
  display: block;
  font-size: 22px;
}

.login-card {
  align-self: center;
}

@media (max-width: 960px) {
  .login-page {
    grid-template-columns: 1fr;
  }
}
</style>
