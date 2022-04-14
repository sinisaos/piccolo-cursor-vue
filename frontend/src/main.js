import 'bootstrap/dist/css/bootstrap.css'
import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'
import App from './App.vue'
import router from './router'
import Axios from 'axios'

Vue.use(BootstrapVue)
Vue.prototype.$http = Axios
Axios.defaults.withCredentials = true
Axios.defaults.baseURL = "http://localhost:8000"

Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
