import { ref } from 'vue'

const THEME_KEY = 'se-theme'

const isDark = ref(false)

export function useDarkMode() {
  const apply = (dark) => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', dark)
  }

  const init = () => {
    const stored = localStorage.getItem(THEME_KEY)
    const dark = stored !== null ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
    isDark.value = dark
    apply(dark)
  }

  const toggle = () => {
    isDark.value = !isDark.value
    localStorage.setItem(THEME_KEY, isDark.value ? 'dark' : 'light')
    apply(isDark.value)
  }

  return { isDark, init, toggle }
}
