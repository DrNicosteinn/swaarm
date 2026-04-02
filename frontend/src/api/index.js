import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export default {
  createSimulation(data) {
    return api.post("/simulation/create", data);
  },
  runSimulation(id) {
    return api.post(`/simulation/run/${id}`);
  },
  getStatus(id) {
    return api.get(`/simulation/status/${id}`);
  },
  getActions(id, offset = 0, limit = 50) {
    return api.get(`/simulation/actions/${id}`, {
      params: { offset, limit },
    });
  },
  stopSimulation(id) {
    return api.post(`/simulation/stop/${id}`);
  },
  generateReport(id) {
    return api.post(`/report/generate/${id}`);
  },
  getReport(id) {
    return api.get(`/report/get/${id}`);
  },
  chatWithReport(id, message, history = []) {
    return api.post(`/report/chat/${id}`, { message, history });
  },
};
