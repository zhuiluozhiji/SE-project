export const activityStatusMap = {
  draft: '草稿',
  open: '可加入',
  full: '已满',
  closed: '已结束',
  offline: '已下架'
}

export const eventColorTypeMap = {
  course: '课程',
  activity: '已加入活动',
  recommended: '推荐活动',
  conflict: '冲突',
  expired: '已结束'
}

export const defaultRecommendedActivities = [
  {
    id: 101,
    title: '人工智能前沿讲座',
    description: '围绕大模型、智能体和可信 AI 的前沿进展进行分享。',
    speaker: '张三教授',
    organizer: '计算机科学与技术学院',
    college: '计算机科学与技术学院',
    category: '讲座',
    campus: '紫金港',
    location: '紫金港校区西区报告厅',
    start_time: '2026-06-06T14:00:00',
    end_time: '2026-06-06T16:00:00',
    hot_score: 87,
    recommend_score: 92,
    status: 'open',
    tags: ['人工智能', '计算机'],
    matched_tags: ['人工智能'],
    reason: '默认推荐活动'
  }
]
