import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import WorkspaceView from '../views/WorkspaceView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/workspace/:id', component: WorkspaceView, props: true },
  ],
})
