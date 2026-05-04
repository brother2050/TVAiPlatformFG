<template>
  <el-container class="app-container">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="app-aside">
      <div class="logo">
        <span v-if="!isCollapsed">TVAiPlatform</span>
        <span v-else>TV</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        router
        background-color="#1d1e2c"
        text-color="#a3a6b4"
        active-text-color="#409eff"
        class="nav-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <template #title>总览</template>
        </el-menu-item>

        <el-menu-item v-if="projectId" :index="`/project/${projectId}/characters`">
          <el-icon><User /></el-icon>
          <template #title>角色</template>
        </el-menu-item>

        <el-menu-item v-if="projectId" :index="`/project/${projectId}/script`">
          <el-icon><Document /></el-icon>
          <template #title>剧本</template>
        </el-menu-item>

        <el-menu-item v-if="projectId" :index="`/project/${projectId}/storyboard`">
          <el-icon><Picture /></el-icon>
          <template #title>分镜</template>
        </el-menu-item>

        <el-menu-item v-if="projectId" :index="`/project/${projectId}/production`">
          <el-icon><VideoCamera /></el-icon>
          <template #title>制片</template>
        </el-menu-item>

        <el-sub-menu v-if="projectId" index="adjust-menu">
          <template #title>
            <el-icon><Edit /></el-icon>
            <span>精修</span>
          </template>
          <el-menu-item :index="`/project/${projectId}/adjust/text`">改台词</el-menu-item>
          <el-menu-item :index="`/project/${projectId}/adjust/image`">修图片</el-menu-item>
          <el-menu-item :index="`/project/${projectId}/adjust/voice`">调配音</el-menu-item>
          <el-menu-item :index="`/project/${projectId}/adjust/bgm`">配音乐</el-menu-item>
          <el-menu-item :index="`/project/${projectId}/adjust/subtitle`">改字幕</el-menu-item>
          <el-menu-item :index="`/project/${projectId}/adjust/video`">剪视频</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/templates">
          <el-icon><Files /></el-icon>
          <template #title>模板</template>
        </el-menu-item>

        <el-menu-item v-if="projectId" :index="`/project/${projectId}/settings`">
          <el-icon><Setting /></el-icon>
          <template #title>设定</template>
        </el-menu-item>

        <el-menu-item v-if="projectId" :index="`/project/${projectId}/export`">
          <el-icon><Download /></el-icon>
          <template #title>输出</template>
        </el-menu-item>
      </el-menu>

      <div class="collapse-btn" @click="isCollapsed = !isCollapsed">
        <el-icon>
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </div>
    </el-aside>

    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Monitor, User, Document, Picture, VideoCamera, Edit,
  Files, Setting, Download, Fold, Expand,
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapsed = ref(false)

const projectId = computed(() => {
  const id = route.params.id
  return typeof id === 'string' ? id : undefined
})

const activeMenu = computed(() => route.path)
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.app-aside {
  background: #1d1e2c;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-menu {
  flex: 1;
  overflow-y: auto;
  border-right: none;
}

.collapse-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a3a6b4;
  cursor: pointer;
  border-top: 1px solid rgba(255, 255, 255, 0.08);

  &:hover {
    color: #409eff;
  }
}

.app-main {
  background: #f5f7fa;
  overflow-y: auto;
  padding: 20px;
}
</style>
