<template>
  <section class="profile-page fade-in">
    <div v-if="loading" v-loading="loading" class="loading-block" />

    <template v-else-if="user">
      <div class="profile-hero page-panel">
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

      <div class="card appearance-card">
        <div class="appearance-head">
          <div>
            <h3 class="section-title">外观设置</h3>
            <p class="muted">支持统一调整网页背景、卡片颜色、透明度、文字颜色和本地图片纹理，个人日历会跟随当前外观一起变化，修改会实时预览，保存后刷新仍保留。</p>
          </div>
          <div class="appearance-actions">
            <el-button
              :type="!isDark ? 'primary' : 'default'"
              plain
              @click="applyThemePreset('light')"
            >
              亮色预设
            </el-button>
            <el-button
              :type="isDark ? 'primary' : 'default'"
              plain
              @click="applyThemePreset('dark')"
            >
              深色预设
            </el-button>
            <el-button type="primary" @click="saveAppearanceSettings">保存设置</el-button>
          </div>
        </div>

        <div class="appearance-layout">
          <div class="appearance-form">
            <el-form label-position="top">
              <el-form-item label="背景模式">
                <el-radio-group v-model="currentBackgroundSettings.mode" size="small">
                  <el-radio-button label="default">默认</el-radio-button>
                  <el-radio-button label="solid">纯色</el-radio-button>
                  <el-radio-button label="gradient">渐变</el-radio-button>
                  <el-radio-button label="image">图片</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <el-form-item v-if="currentBackgroundSettings.mode === 'solid'" label="背景颜色">
                <div class="appearance-color-row">
                  <el-color-picker v-model="currentBackgroundSettings.color" />
                  <code class="appearance-color-code">{{ currentBackgroundSettings.color }}</code>
                </div>
              </el-form-item>

              <template v-if="currentBackgroundSettings.mode === 'gradient'">
                <el-form-item label="起始颜色">
                  <div class="appearance-color-row">
                    <el-color-picker v-model="currentBackgroundSettings.gradientFrom" />
                    <code class="appearance-color-code">{{ currentBackgroundSettings.gradientFrom }}</code>
                  </div>
                </el-form-item>

                <el-form-item label="结束颜色">
                  <div class="appearance-color-row">
                    <el-color-picker v-model="currentBackgroundSettings.gradientTo" />
                    <code class="appearance-color-code">{{ currentBackgroundSettings.gradientTo }}</code>
                  </div>
                </el-form-item>

                <el-form-item label="渐变角度">
                  <el-slider v-model="currentBackgroundSettings.angle" :min="0" :max="360" :step="5" show-input />
                </el-form-item>
              </template>

              <el-form-item v-if="currentBackgroundSettings.mode === 'image'" label="背景图片">
                <div class="appearance-upload-stack">
                  <el-upload
                    ref="backgroundImageUploadRef"
                    action="#"
                    :auto-upload="false"
                    :show-file-list="false"
                    :limit="1"
                    :accept="APPEARANCE_IMAGE_ACCEPT"
                    :on-change="handleBackgroundImageChange"
                    :on-exceed="handleBackgroundImageExceed"
                  >
                    <el-button plain>上传背景图片</el-button>
                  </el-upload>
                  <div class="appearance-upload-meta">
                    <span class="faint">{{ currentBackgroundSettings.backgroundImageName || '未选择图片' }}</span>
                    <el-button
                      v-if="currentBackgroundSettings.backgroundImage"
                      text
                      @click="clearBackgroundImage"
                    >
                      移除图片
                    </el-button>
                  </div>
                  <p class="faint appearance-hint">支持 PNG / JPG / WEBP；图片会在浏览器本地压缩保存，不上传到服务器。</p>
                </div>
              </el-form-item>

              <el-form-item v-if="currentBackgroundSettings.mode !== 'default'" label="遮罩强度">
                <el-slider v-model="currentBackgroundSettings.overlay" :min="0" :max="40" :step="1" show-input />
                <p class="faint appearance-hint">数值越高，文字越清楚；{{ overlayTip }}</p>
              </el-form-item>

              <div class="appearance-subsection">
                <span class="appearance-subtitle">卡片样式</span>
                <p class="faint appearance-hint">会影响页面内主要内容卡片与面板，包括个人日历，不改动按钮和课程事件块的语义配色。</p>
              </div>

              <el-form-item label="卡片模式">
                <el-radio-group v-model="currentBackgroundSettings.cardMode" size="small">
                  <el-radio-button label="default">默认</el-radio-button>
                  <el-radio-button label="custom">自定义</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <template v-if="currentBackgroundSettings.cardMode === 'custom'">
                <el-form-item label="卡片颜色">
                  <div class="appearance-color-row">
                    <el-color-picker v-model="currentBackgroundSettings.cardColor" />
                    <code class="appearance-color-code">{{ currentBackgroundSettings.cardColor }}</code>
                  </div>
                </el-form-item>

                <el-form-item label="卡片透明度">
                  <el-slider v-model="currentBackgroundSettings.cardOpacity" :min="35" :max="100" :step="1" show-input />
                  <p class="faint appearance-hint">数值越低越通透，建议保持在 68 - 94 之间。</p>
                </el-form-item>

                <el-form-item label="卡片图片">
                  <div class="appearance-upload-stack">
                    <el-upload
                      ref="cardImageUploadRef"
                      action="#"
                      :auto-upload="false"
                      :show-file-list="false"
                      :limit="1"
                      :accept="APPEARANCE_IMAGE_ACCEPT"
                      :on-change="handleCardImageChange"
                      :on-exceed="handleCardImageExceed"
                    >
                      <el-button plain>上传卡片图片</el-button>
                    </el-upload>
                    <div class="appearance-upload-meta">
                      <span class="faint">{{ currentBackgroundSettings.cardImageName || '未选择图片，可只保留纯色卡片' }}</span>
                      <el-button
                        v-if="currentBackgroundSettings.cardImage"
                        text
                        @click="clearCardImage"
                      >
                        移除图片
                      </el-button>
                    </div>
                    <p class="faint appearance-hint">会同步作用到主要内容卡片、侧栏和顶栏，建议搭配较高透明度使用。</p>
                  </div>
                </el-form-item>

                <el-form-item label="主文字颜色">
                  <div class="appearance-color-row">
                    <el-color-picker v-model="currentBackgroundSettings.cardTextColor" />
                    <code class="appearance-color-code">{{ currentBackgroundSettings.cardTextColor }}</code>
                  </div>
                </el-form-item>

                <el-form-item label="辅助文字颜色">
                  <div class="appearance-color-row">
                    <el-color-picker v-model="currentBackgroundSettings.cardMutedColor" />
                    <code class="appearance-color-code">{{ currentBackgroundSettings.cardMutedColor }}</code>
                  </div>
                </el-form-item>
              </template>
            </el-form>
          </div>

          <div class="appearance-preview-panel">
            <span class="faint">实时预览</span>
            <div class="appearance-preview" :style="previewStyle">
              <div class="appearance-preview-card" :style="previewCardStyle">
                <strong>页面外观</strong>
                <p>{{ previewMessage }}</p>
                <span class="appearance-preview-meta">{{ previewCardMessage }}</span>
              </div>
              <div class="appearance-preview-surface">
                <span class="appearance-preview-chip" :style="previewChipStyle">内容卡片</span>
                <span class="appearance-preview-chip subtle" :style="previewSubtleChipStyle">背景层</span>
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
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../store/auth'
import { useBackgroundTheme } from '../composables/useBackgroundTheme'
import { useDarkMode } from '../composables/useDarkMode'

const auth = useAuthStore()
const { isDark, setTheme } = useDarkMode()
const {
  backgroundSettings,
  initBackgroundTheme,
  saveBackgroundSettings,
  applyThemePresetBackgroundSettings
} = useBackgroundTheme()

const APPEARANCE_IMAGE_ACCEPT = 'image/png,image/jpeg,image/webp'
const APPEARANCE_IMAGE_MAX_BYTES = 6 * 1024 * 1024
const APPEARANCE_IMAGE_MAX_DATA_URL_LENGTH = 2_000_000
const BACKGROUND_IMAGE_MAX_DIMENSION = 1800
const CARD_IMAGE_MAX_DIMENSION = 1200
const APPEARANCE_IMAGE_QUALITY = 0.82

const loading = ref(false)
const error = ref('')
const backgroundImageUploadRef = ref(null)
const cardImageUploadRef = ref(null)

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

const currentBackgroundSettings = computed(() => {
  return backgroundSettings.app
})

const overlayTip = computed(() => {
  return '建议保持在 12 - 24 之间'
})

const DEFAULT_CARD_PREVIEW = {
  light: {
    bg: 'rgba(255, 255, 255, 0.94)',
    chipBg: 'rgba(255, 255, 255, 0.9)',
    chipSubtleBg: 'rgba(255, 255, 255, 0.68)',
    text: '#1e1b18',
    muted: '#5c564d',
    border: 'rgba(232, 226, 214, 0.92)'
  },
  dark: {
    bg: 'rgba(33, 37, 41, 0.94)',
    chipBg: 'rgba(41, 46, 51, 0.94)',
    chipSubtleBg: 'rgba(41, 46, 51, 0.74)',
    text: '#e8e6e3',
    muted: '#b0aca5',
    border: 'rgba(78, 86, 95, 0.9)'
  }
}

const clampAlpha = (value) => {
  return Math.min(0.98, Math.max(0, value))
}

const hexToRgb = (value) => {
  const normalized = typeof value === 'string' ? value.trim().replace('#', '') : ''
  const full = normalized.length === 3
    ? normalized.split('').map((char) => char + char).join('')
    : normalized
  if (!/^[0-9a-fA-F]{6}$/.test(full)) {
    return { r: 255, g: 255, b: 255 }
  }
  return {
    r: parseInt(full.slice(0, 2), 16),
    g: parseInt(full.slice(2, 4), 16),
    b: parseInt(full.slice(4, 6), 16)
  }
}

const rgbaFromHex = (value, alpha) => {
  const { r, g, b } = hexToRgb(value)
  return `rgba(${r}, ${g}, ${b}, ${clampAlpha(alpha).toFixed(2)})`
}

const buildImageLayer = (value) => {
  return value ? `url("${value}")` : ''
}

const buildTintedImageBackground = (baseColor, image) => {
  if (!image) return baseColor
  const imageLayer = buildImageLayer(image)
  return `linear-gradient(${baseColor}, ${baseColor}), ${imageLayer}`
}

const buildPreviewLayer = (settings) => {
  if (settings.mode === 'solid') {
    return settings.color
  }
  if (settings.mode === 'gradient') {
    return `linear-gradient(${settings.angle}deg, ${settings.gradientFrom} 0%, ${settings.gradientTo} 100%)`
  }
  if (settings.mode === 'image') {
    return settings.backgroundImage
      ? buildImageLayer(settings.backgroundImage)
      : (isDark.value
        ? 'linear-gradient(135deg, #2a3038 0%, #1e252d 100%)'
        : 'linear-gradient(135deg, #f7f1e6 0%, #e9eff8 100%)')
  }
  if (isDark.value) {
    return 'linear-gradient(135deg, #2a3038 0%, #1e252d 100%)'
  }
  return 'linear-gradient(135deg, #f7f1e6 0%, #e9eff8 100%)'
}

const previewStyle = computed(() => {
  const settings = currentBackgroundSettings.value
  const overlayBase = isDark.value ? '17, 20, 24' : '255, 255, 255'
  const overlayAlpha = settings.mode === 'default'
    ? (isDark.value ? '0.08' : '0.12')
    : (settings.overlay / 100).toFixed(2)

  return {
    background: `linear-gradient(rgba(${overlayBase}, ${overlayAlpha}), rgba(${overlayBase}, ${overlayAlpha})), ${buildPreviewLayer(settings)}`
  }
})

const previewCardPalette = computed(() => {
  const settings = currentBackgroundSettings.value
  const themeKey = isDark.value ? 'dark' : 'light'

  if (settings.cardMode !== 'custom') {
    return DEFAULT_CARD_PREVIEW[themeKey]
  }

  const baseAlpha = settings.cardOpacity / 100
  return {
    bg: rgbaFromHex(settings.cardColor, baseAlpha),
    chipBg: rgbaFromHex(settings.cardColor, baseAlpha + 0.08),
    chipSubtleBg: rgbaFromHex(settings.cardColor, baseAlpha + 0.16),
    text: settings.cardTextColor,
    muted: settings.cardMutedColor,
    border: rgbaFromHex(settings.cardMutedColor, 0.18)
  }
})

const previewCardStyle = computed(() => {
  return {
    background: buildTintedImageBackground(previewCardPalette.value.bg, currentBackgroundSettings.value.cardImage),
    borderColor: previewCardPalette.value.border,
    color: previewCardPalette.value.text,
    '--preview-card-muted': previewCardPalette.value.muted,
    backgroundPosition: 'center',
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat'
  }
})

const previewChipStyle = computed(() => {
  return {
    background: previewCardPalette.value.chipBg,
    borderColor: previewCardPalette.value.border,
    color: previewCardPalette.value.text
  }
})

const previewSubtleChipStyle = computed(() => {
  return {
    background: previewCardPalette.value.chipSubtleBg,
    borderColor: previewCardPalette.value.border,
    color: previewCardPalette.value.muted
  }
})

const previewMessage = computed(() => {
  if (currentBackgroundSettings.value.mode === 'image' && !currentBackgroundSettings.value.backgroundImage) {
    return '当前处于图片背景模式，请先上传一张图片开始预览。'
  }
  if (currentBackgroundSettings.value.mode === 'default') {
    return '当前使用系统默认背景。切换到纯色或渐变后会立即预览。'
  }
  return '当前设置已实时预览，点击“保存设置”后刷新页面仍会保留。'
})

const previewCardMessage = computed(() => {
  if (currentBackgroundSettings.value.cardMode !== 'custom') {
    return '卡片保持当前主题默认样式。'
  }
  if (currentBackgroundSettings.value.cardImage) {
    return `卡片图片已叠加当前色调，透明度 ${currentBackgroundSettings.value.cardOpacity}% · 主副文字颜色已同步更新。`
  }
  return `卡片透明度 ${currentBackgroundSettings.value.cardOpacity}% · 主副文字颜色已同步更新。`
})

const isAllowedAppearanceImage = (file) => {
  return ['image/png', 'image/jpeg', 'image/webp'].includes(file?.type)
}

const readFileAsDataUrl = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(reader.result)
  reader.onerror = () => reject(new Error('读取图片失败，请重试。'))
  reader.readAsDataURL(file)
})

const loadImageElement = (src) => new Promise((resolve, reject) => {
  const image = new Image()
  image.onload = () => resolve(image)
  image.onerror = () => reject(new Error('图片解析失败，请换一张图片试试。'))
  image.src = src
})

const compressAppearanceImage = async (file, maxDimension) => {
  if (!file) {
    throw new Error('未读取到图片文件。')
  }
  if (!isAllowedAppearanceImage(file)) {
    throw new Error('仅支持 PNG / JPG / WEBP 图片。')
  }
  if (file.size > APPEARANCE_IMAGE_MAX_BYTES) {
    throw new Error('图片过大，请选择 6MB 以内的图片。')
  }

  const originalDataUrl = await readFileAsDataUrl(file)
  const image = await loadImageElement(originalDataUrl)
  const width = image.naturalWidth || image.width
  const height = image.naturalHeight || image.height
  const scale = Math.min(1, maxDimension / Math.max(width, height))
  const targetWidth = Math.max(1, Math.round(width * scale))
  const targetHeight = Math.max(1, Math.round(height * scale))
  const canvas = document.createElement('canvas')
  canvas.width = targetWidth
  canvas.height = targetHeight

  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('浏览器暂不支持图片压缩。')
  }

  ctx.drawImage(image, 0, 0, targetWidth, targetHeight)
  const compressedDataUrl = canvas.toDataURL('image/webp', APPEARANCE_IMAGE_QUALITY)
  const finalDataUrl = compressedDataUrl.length < originalDataUrl.length ? compressedDataUrl : originalDataUrl

  if (finalDataUrl.length > APPEARANCE_IMAGE_MAX_DATA_URL_LENGTH) {
    throw new Error('图片压缩后仍然较大，建议换一张更小或更简单的图片。')
  }

  return finalDataUrl
}

const setBackgroundImage = (dataUrl, name = '') => {
  currentBackgroundSettings.value.backgroundImage = dataUrl
  currentBackgroundSettings.value.backgroundImageName = name
}

const setCardImage = (dataUrl, name = '') => {
  currentBackgroundSettings.value.cardImage = dataUrl
  currentBackgroundSettings.value.cardImageName = name
}

const applyAppearanceImage = async ({ file, maxDimension, setter, uploadRef, label }) => {
  const rawFile = file?.raw
  if (!rawFile) return

  try {
    const dataUrl = await compressAppearanceImage(rawFile, maxDimension)
    setter(dataUrl, rawFile.name || '')
    ElMessage.success(`${label}已更新，记得点击“保存设置”。`)
  } catch (uploadError) {
    ElMessage.error(uploadError?.message || `${label}上传失败。`)
  } finally {
    uploadRef.value?.clearFiles()
  }
}

const handleBackgroundImageChange = async (file) => {
  await applyAppearanceImage({
    file,
    maxDimension: BACKGROUND_IMAGE_MAX_DIMENSION,
    setter: setBackgroundImage,
    uploadRef: backgroundImageUploadRef,
    label: '背景图片'
  })
}

const handleCardImageChange = async (file) => {
  await applyAppearanceImage({
    file,
    maxDimension: CARD_IMAGE_MAX_DIMENSION,
    setter: setCardImage,
    uploadRef: cardImageUploadRef,
    label: '卡片图片'
  })
}

const createExceedHandler = (uploadRef, handler) => (files) => {
  const nextFile = files?.[0]
  uploadRef.value?.clearFiles()
  if (nextFile) {
    uploadRef.value?.handleStart(nextFile)
    handler({ raw: nextFile })
  }
}

const handleBackgroundImageExceed = createExceedHandler(backgroundImageUploadRef, handleBackgroundImageChange)
const handleCardImageExceed = createExceedHandler(cardImageUploadRef, handleCardImageChange)

const clearBackgroundImage = () => {
  setBackgroundImage('', '')
}

const clearCardImage = () => {
  setCardImage('', '')
}

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

const saveAppearanceSettings = () => {
  const saved = saveBackgroundSettings()
  if (!saved) {
    ElMessage.error('外观保存失败，可能是图片过大导致浏览器本地存储空间不足。')
    return
  }
  ElMessage.success('外观已保存')
}

const applyThemePreset = (mode) => {
  setTheme(mode)
  const saved = applyThemePresetBackgroundSettings(mode)
  if (!saved) {
    ElMessage.warning('预设已切换，但浏览器本地保存失败，请稍后重试。')
    return
  }
  ElMessage.success(mode === 'dark' ? '已切换为深色预设，外观已恢复默认' : '已切换为亮色预设，外观已恢复默认')
}

onMounted(() => {
  initBackgroundTheme()
  fetchProfile()
})
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
  grid-template-columns: minmax(0, 1fr);
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

.appearance-card {
  display: grid;
  gap: 18px;
}

.appearance-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.appearance-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.appearance-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 18px;
  align-items: start;
}

.appearance-form :deep(.el-form-item__label) {
  color: var(--text-secondary);
}

.appearance-color-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.appearance-color-code {
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--bg-warm);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  font-size: 12px;
}

.appearance-hint {
  margin-top: 8px;
  font-size: 12px;
}

.appearance-upload-stack {
  display: grid;
  gap: 8px;
  width: 100%;
}

.appearance-upload-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.appearance-subsection {
  display: grid;
  gap: 4px;
  margin: 4px 0 2px;
}

.appearance-subtitle {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.appearance-preview-panel {
  display: grid;
  gap: 10px;
}

.appearance-preview {
  min-height: 260px;
  padding: 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 14px;
  background-position: center;
  background-size: cover;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}

.appearance-preview-card {
  --preview-card-muted: var(--text-secondary);
  padding: 16px 18px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-sm);
  display: grid;
  gap: 6px;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.appearance-preview-card strong {
  display: block;
  font-size: 15px;
  color: inherit;
}

.appearance-preview-card p {
  color: var(--preview-card-muted);
  font-size: 13px;
}

.appearance-preview-meta {
  color: var(--preview-card-muted);
  font-size: 12px;
}

.appearance-preview-surface {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.appearance-preview-chip {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(255, 255, 255, 0.65);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.appearance-preview-chip.subtle {
  background: rgba(255, 255, 255, 0.55);
  color: var(--text-secondary);
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

[data-theme="dark"] .appearance-color-code {
  background: #2b2f34;
  border-color: #3b4148;
  color: #d1d5db;
}

[data-theme="dark"] .appearance-preview-card {
  background: rgba(29, 33, 38, 0.82);
  border-color: rgba(96, 106, 118, 0.45);
}

[data-theme="dark"] .appearance-preview-card strong {
  color: inherit;
}

[data-theme="dark"] .appearance-preview-card p {
  color: var(--preview-card-muted, #d1d5db);
}

[data-theme="dark"] .appearance-preview-chip {
  background: rgba(29, 33, 38, 0.78);
  border-color: rgba(96, 106, 118, 0.45);
  color: #f3f4f6;
}

[data-theme="dark"] .appearance-preview-chip.subtle {
  background: rgba(29, 33, 38, 0.56);
  color: #d1d5db;
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
  .appearance-layout {
    grid-template-columns: 1fr;
  }
}
</style>
