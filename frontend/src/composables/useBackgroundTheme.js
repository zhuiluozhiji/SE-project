import { reactive, watch } from 'vue'

const BACKGROUND_SETTINGS_KEY = 'se-background-settings'
const SCOPE_KEYS = ['app', 'calendar']
const MODE_KEYS = ['default', 'solid', 'gradient']
const CARD_MODE_KEYS = ['default', 'custom']

const DEFAULT_BACKGROUND_SETTINGS = {
  app: {
    mode: 'default',
    color: '#f4efe7',
    gradientFrom: '#f7f1e6',
    gradientTo: '#e8eff8',
    angle: 135,
    overlay: 18,
    cardMode: 'default',
    cardColor: '#fffaf2',
    cardOpacity: 92,
    cardTextColor: '#1e1b18',
    cardMutedColor: '#5c564d'
  },
  calendar: {
    mode: 'default',
    color: '#edf4f8',
    gradientFrom: '#f1f7fa',
    gradientTo: '#e6edf8',
    angle: 145,
    overlay: 12,
    cardMode: 'default',
    cardColor: '#f6fbff',
    cardOpacity: 88,
    cardTextColor: '#1a2430',
    cardMutedColor: '#536273'
  }
}

const THEME_PRESET_SETTINGS = {
  light: {
    app: { ...DEFAULT_BACKGROUND_SETTINGS.app },
    calendar: { ...DEFAULT_BACKGROUND_SETTINGS.calendar }
  },
  dark: {
    app: {
      mode: 'default',
      color: '#21262d',
      gradientFrom: '#2a3038',
      gradientTo: '#1e252d',
      angle: 135,
      overlay: 18,
      cardMode: 'default',
      cardColor: '#262b31',
      cardOpacity: 94,
      cardTextColor: '#e8e6e3',
      cardMutedColor: '#b0aca5'
    },
    calendar: {
      mode: 'default',
      color: '#20252c',
      gradientFrom: '#272d35',
      gradientTo: '#1c222c',
      angle: 145,
      overlay: 12,
      cardMode: 'default',
      cardColor: '#252628',
      cardOpacity: 92,
      cardTextColor: '#f4f6fb',
      cardMutedColor: '#aab6c3'
    }
  }
}

const backgroundSettings = reactive({
  app: { ...DEFAULT_BACKGROUND_SETTINGS.app },
  calendar: { ...DEFAULT_BACKGROUND_SETTINGS.calendar }
})

let initialized = false
let syncAttached = false

const cloneScopeSettings = (scope) => ({ ...scope })

const clampNumber = (value, min, max, fallback) => {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return fallback
  return Math.min(max, Math.max(min, numeric))
}

const clampAlpha = (value) => {
  return Math.min(0.98, Math.max(0, value))
}

const normalizeColor = (value, fallback) => {
  if (typeof value !== 'string') return fallback
  const trimmed = value.trim()
  return /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(trimmed) ? trimmed : fallback
}

const normalizeEnum = (value, allowedValues, fallback) => {
  return allowedValues.includes(value) ? value : fallback
}

const hexToRgbString = (value, fallback) => {
  const normalized = normalizeColor(value, fallback).replace('#', '')
  const full = normalized.length === 3
    ? normalized.split('').map((char) => char + char).join('')
    : normalized

  const r = parseInt(full.slice(0, 2), 16)
  const g = parseInt(full.slice(2, 4), 16)
  const b = parseInt(full.slice(4, 6), 16)
  return `${r}, ${g}, ${b}`
}

const rgbaFromHex = (value, alpha, fallback) => {
  return `rgba(${hexToRgbString(value, fallback)}, ${alpha})`
}

const normalizeScopeSettings = (input, defaults) => {
  const source = input && typeof input === 'object' ? input : {}
  return {
    mode: normalizeEnum(source.mode, MODE_KEYS, defaults.mode),
    color: normalizeColor(source.color, defaults.color),
    gradientFrom: normalizeColor(source.gradientFrom, defaults.gradientFrom),
    gradientTo: normalizeColor(source.gradientTo, defaults.gradientTo),
    angle: clampNumber(source.angle, 0, 360, defaults.angle),
    overlay: clampNumber(source.overlay, 0, 60, defaults.overlay),
    cardMode: normalizeEnum(source.cardMode, CARD_MODE_KEYS, defaults.cardMode),
    cardColor: normalizeColor(source.cardColor, defaults.cardColor),
    cardOpacity: clampNumber(source.cardOpacity, 30, 100, defaults.cardOpacity),
    cardTextColor: normalizeColor(source.cardTextColor, defaults.cardTextColor),
    cardMutedColor: normalizeColor(source.cardMutedColor, defaults.cardMutedColor)
  }
}

const serializeSettings = () => ({
  app: cloneScopeSettings(backgroundSettings.app),
  calendar: cloneScopeSettings(backgroundSettings.calendar)
})

const buildBackgroundLayer = (settings) => {
  if (settings.mode === 'solid') {
    return settings.color
  }
  if (settings.mode === 'gradient') {
    return `linear-gradient(${settings.angle}deg, ${settings.gradientFrom} 0%, ${settings.gradientTo} 100%)`
  }
  return 'none'
}

const applyScopeVariables = (root, prefix, settings) => {
  const enabled = settings.mode === 'default' ? '0' : '1'
  const overlayAlpha = settings.mode === 'default'
    ? '0'
    : (settings.overlay / 100).toFixed(2)
  const cardAlpha = clampAlpha(settings.cardOpacity / 100)
  const cardElevatedAlpha = clampAlpha(cardAlpha + 0.08)
  const cardStrongAlpha = clampAlpha(cardAlpha + 0.16)

  root.style.setProperty(`--${prefix}-bg-layer`, buildBackgroundLayer(settings))
  root.style.setProperty(`--${prefix}-bg-enabled`, enabled)
  root.style.setProperty(`--${prefix}-bg-overlay-alpha`, overlayAlpha)
  root.style.setProperty(`--${prefix}-card-enabled`, settings.cardMode === 'custom' ? '1' : '0')
  root.style.setProperty(`--${prefix}-card-bg-rgb`, hexToRgbString(settings.cardColor, DEFAULT_BACKGROUND_SETTINGS[prefix].cardColor))
  root.style.setProperty(`--${prefix}-card-bg-alpha`, cardAlpha.toFixed(2))
  root.style.setProperty(`--${prefix}-card-bg`, rgbaFromHex(settings.cardColor, cardAlpha.toFixed(2), DEFAULT_BACKGROUND_SETTINGS[prefix].cardColor))
  root.style.setProperty(`--${prefix}-card-bg-elevated`, rgbaFromHex(settings.cardColor, cardElevatedAlpha.toFixed(2), DEFAULT_BACKGROUND_SETTINGS[prefix].cardColor))
  root.style.setProperty(`--${prefix}-card-bg-strong`, rgbaFromHex(settings.cardColor, cardStrongAlpha.toFixed(2), DEFAULT_BACKGROUND_SETTINGS[prefix].cardColor))
  root.style.setProperty(`--${prefix}-card-text`, normalizeColor(settings.cardTextColor, DEFAULT_BACKGROUND_SETTINGS[prefix].cardTextColor))
  root.style.setProperty(`--${prefix}-card-muted`, normalizeColor(settings.cardMutedColor, DEFAULT_BACKGROUND_SETTINGS[prefix].cardMutedColor))
  root.style.setProperty(`--${prefix}-card-faint`, rgbaFromHex(settings.cardMutedColor, 0.78, DEFAULT_BACKGROUND_SETTINGS[prefix].cardMutedColor))
  root.style.setProperty(`--${prefix}-card-border`, rgbaFromHex(settings.cardMutedColor, 0.18, DEFAULT_BACKGROUND_SETTINGS[prefix].cardMutedColor))
  root.dataset[`${prefix}CardMode`] = settings.cardMode
}

export const applyBackgroundSettings = () => {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  applyScopeVariables(root, 'app', backgroundSettings.app)
  applyScopeVariables(root, 'calendar', backgroundSettings.calendar)
}

const loadBackgroundSettings = () => {
  if (typeof localStorage === 'undefined') return
  try {
    const raw = localStorage.getItem(BACKGROUND_SETTINGS_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    Object.assign(
      backgroundSettings.app,
      normalizeScopeSettings(parsed?.app, DEFAULT_BACKGROUND_SETTINGS.app)
    )
    Object.assign(
      backgroundSettings.calendar,
      normalizeScopeSettings(parsed?.calendar, DEFAULT_BACKGROUND_SETTINGS.calendar)
    )
  } catch {
    // Ignore malformed persisted settings and fall back to defaults.
  }
}

export function useBackgroundTheme() {
  const initBackgroundTheme = () => {
    if (!initialized) {
      loadBackgroundSettings()
      initialized = true
    }
    if (!syncAttached) {
      watch(backgroundSettings, applyBackgroundSettings, { deep: true })
      syncAttached = true
    }
    applyBackgroundSettings()
  }

  const saveBackgroundSettings = () => {
    if (typeof localStorage === 'undefined') return
    localStorage.setItem(BACKGROUND_SETTINGS_KEY, JSON.stringify(serializeSettings()))
  }

  const resetBackgroundScope = (scope) => {
    if (!SCOPE_KEYS.includes(scope)) return
    Object.assign(backgroundSettings[scope], cloneScopeSettings(DEFAULT_BACKGROUND_SETTINGS[scope]))
    applyBackgroundSettings()
    saveBackgroundSettings()
  }

  const applyThemePresetBackgroundSettings = (themeMode) => {
    const presetKey = themeMode === 'dark' ? 'dark' : 'light'
    SCOPE_KEYS.forEach((scope) => {
      Object.assign(
        backgroundSettings[scope],
        cloneScopeSettings(THEME_PRESET_SETTINGS[presetKey][scope])
      )
    })
    applyBackgroundSettings()
    saveBackgroundSettings()
  }

  return {
    backgroundSettings,
    defaultBackgroundSettings: DEFAULT_BACKGROUND_SETTINGS,
    initBackgroundTheme,
    saveBackgroundSettings,
    resetBackgroundScope,
    applyThemePresetBackgroundSettings
  }
}
