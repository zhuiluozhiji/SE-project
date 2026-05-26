export const MAX_SCREENSHOT_FILES = 5
export const SCREENSHOT_SHORTCUT_LABEL = 'Option/Alt + Shift + S'

export const isAllowedScreenshotFile = (file) => {
  const name = file?.name?.toLowerCase() || ''
  return /\.(png|jpe?g|webp|bmp|tiff?)$/.test(name)
}

export const isScreenshotShortcut = (event) => {
  const isSKey = event.code === 'KeyS' || event.key?.toLowerCase() === 's'
  return event.altKey && event.shiftKey && isSKey
}

export const captureScreenImage = async (prefix = 'activity') => {
  if (!navigator.mediaDevices?.getDisplayMedia) {
    throw new Error('当前浏览器不支持快捷截屏，请直接上传图片。')
  }

  const stream = await navigator.mediaDevices.getDisplayMedia({
    video: { cursor: 'always' },
    audio: false
  })

  try {
    const video = document.createElement('video')
    video.srcObject = stream
    video.muted = true
    await video.play()
    await new Promise((resolve) => requestAnimationFrame(resolve))

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720
    const context = canvas.getContext('2d')
    if (!context) throw new Error('截屏生成失败，请重试。')
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))
    if (!blob) throw new Error('截屏生成失败，请重试。')
    return new File([blob], `${prefix}-${Date.now()}.png`, { type: 'image/png' })
  } finally {
    stream.getTracks().forEach((track) => track.stop())
  }
}
