<template>
  <el-tag :type="tagType" effect="light">{{ label }}</el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  status: {
    type: String,
    default: 'open'
  }
})

const tagType = computed(() => {
  const map = {
    open: 'success',
    full: 'warning',
    closed: 'info',
    offline: 'danger',
    conflict: 'danger'
  }
  return map[props.status] || 'primary'
})
</script>
