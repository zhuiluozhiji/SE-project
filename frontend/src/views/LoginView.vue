<template>
  <section class="login-page fade-in">
    <div class="login-hero">
      <p class="login-kicker">ZJU Campus</p>
      <h2>校园学术活动<br />智能推荐平台</h2>
      <p class="login-hero-desc">
        连接活动发现、日程管理与学术成长轨迹。登录后即可同步课表、获取个性化推荐与冲突检测。
      </p>
    </div>

    <div class="login-form-wrap">
      <div class="login-card">
        <h3 class="login-title">{{ isRegister ? '创建账号' : '欢迎回来' }}</h3>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          @submit.prevent="handleSubmit"
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>
          <el-form-item prop="confirmPassword" v-if="isRegister">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="确认密码"
              size="large"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-form-item prop="college" v-if="isRegister">
            <el-input
              v-model.trim="form.college"
              placeholder="学院，如：计算机科学与技术学院"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="major" v-if="isRegister">
            <el-input
              v-model.trim="form.major"
              placeholder="专业，如：计算机科学与技术"
              size="large"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="login-btn"
              @click="handleSubmit"
            >
              {{ isRegister ? '注册' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <p class="login-toggle">
          {{ isRegister ? '已有账号？' : '没有账号？' }}
          <el-button link type="primary" @click="isRegister = !isRegister; resetForm()">
            {{ isRegister ? '去登录' : '去注册' }}
          </el-button>
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()

const isRegister = ref(false)
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  college: '',
  major: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 64, message: '用户名长度需为3-64位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ],
  college: [{ max: 128, message: '学院名称不能超过128个字符', trigger: 'blur' }],
  major: [{ max: 128, message: '专业名称不能超过128个字符', trigger: 'blur' }]
}

const resetForm = () => {
  form.username = ''
  form.password = ''
  form.confirmPassword = ''
  form.college = ''
  form.major = ''
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      if (isRegister.value) {
        await auth.register({
          username: form.username,
          password: form.password,
          college: form.college || undefined,
          major: form.major || undefined
        })
        ElMessage.success('注册成功，已自动登录')
      } else {
        await auth.login({ username: form.username, password: form.password })
        ElMessage.success('登录成功')
      }
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
  grid-template-columns: 1fr 1fr;
  min-height: calc(100vh - 72px - 64px - 2px);
  align-items: center;
  gap: 48px;
  max-width: 960px;
  margin: 0 auto;
}

.login-hero {
  padding-right: 32px;
}

.login-kicker {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 14px;
}

.login-hero h2 {
  margin: 0 0 16px;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.25;
  font-family: var(--font-display);
  letter-spacing: 0.03em;
}

.login-hero-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.7;
}

.login-form-wrap {
  display: flex;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 380px;
  padding: 36px 32px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.login-title {
  margin: 0 0 24px;
  font-size: 22px;
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 0.03em;
}

.login-btn {
  width: 100%;
}

.login-toggle {
  margin: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: var(--text-tertiary);
}

@media (max-width: 960px) {
  .login-page {
    grid-template-columns: 1fr;
    gap: 24px;
    min-height: auto;
  }
  .login-hero {
    padding-right: 0;
    text-align: center;
  }
  .login-hero h2 {
    font-size: 24px;
  }
}
</style>
