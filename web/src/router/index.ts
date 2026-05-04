import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '我的短剧' },
  },
  {
    path: '/project/:id/characters',
    name: 'Characters',
    component: () => import('@/views/CharacterStudio.vue'),
    meta: { title: '角色设计' },
  },
  {
    path: '/project/:id/script',
    name: 'Script',
    component: () => import('@/views/ScriptEditor.vue'),
    meta: { title: '写剧本' },
  },
  {
    path: '/project/:id/storyboard',
    name: 'Storyboard',
    component: () => import('@/views/Storyboard.vue'),
    meta: { title: '分镜板' },
  },
  {
    path: '/project/:id/production',
    name: 'Production',
    component: () => import('@/views/Production.vue'),
    meta: { title: '开始制作' },
  },
  {
    path: '/project/:id/timeline',
    name: 'Timeline',
    component: () => import('@/views/TimelineEditor.vue'),
    meta: { title: '时间轴' },
  },
  {
    path: '/project/:id/adjust/text',
    name: 'TextAdjust',
    component: () => import('@/views/TextAdjust.vue'),
    meta: { title: '改台词' },
  },
  {
    path: '/project/:id/adjust/image',
    name: 'ImageAdjust',
    component: () => import('@/views/ImageAdjust.vue'),
    meta: { title: '修图片' },
  },
  {
    path: '/project/:id/adjust/voice',
    name: 'VoiceAdjust',
    component: () => import('@/views/VoiceAdjust.vue'),
    meta: { title: '调配音' },
  },
  {
    path: '/project/:id/adjust/bgm',
    name: 'BgmAdjust',
    component: () => import('@/views/BgmAdjust.vue'),
    meta: { title: '配音乐' },
  },
  {
    path: '/project/:id/adjust/subtitle',
    name: 'SubtitleAdjust',
    component: () => import('@/views/SubtitleAdjust.vue'),
    meta: { title: '改字幕' },
  },
  {
    path: '/project/:id/adjust/video',
    name: 'VideoAdjust',
    component: () => import('@/views/VideoAdjust.vue'),
    meta: { title: '剪视频' },
  },
  {
    path: '/templates',
    name: 'Templates',
    component: () => import('@/views/TemplateWorkshop.vue'),
    meta: { title: '调模板' },
  },
  {
    path: '/project/:id/settings',
    name: 'Settings',
    component: () => import('@/views/GlobalSettings.vue'),
    meta: { title: '全局设定' },
  },
  {
    path: '/project/:id/export',
    name: 'Export',
    component: () => import('@/views/Export.vue'),
    meta: { title: '导出作品' },
  },
  {
    path: '/project/:id/batch-production',
    name: 'BatchProduction',
    component: () => import('@/views/BatchProduction.vue'),
    meta: { title: '批量生产' },
  },
  {
    path: '/project/:id/storage',
    name: 'StorageMonitor',
    component: () => import('@/views/StorageMonitor.vue'),
    meta: { title: '存储空间' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const title = (to.meta?.title as string) || 'TVAiPlatform'
  document.title = `${title} - TVAiPlatform`
  next()
})

export default router
