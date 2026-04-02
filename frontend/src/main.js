import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import InputView from "./views/InputView.vue";
import SimulationView from "./views/SimulationView.vue";
import ReportView from "./views/ReportView.vue";

const routes = [
  { path: "/", component: InputView },
  { path: "/simulation/:id", component: SimulationView, props: true },
  { path: "/report/:id", component: ReportView, props: true },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

createApp(App).use(router).mount("#app");
