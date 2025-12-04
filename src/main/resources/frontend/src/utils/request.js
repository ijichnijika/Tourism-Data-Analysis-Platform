import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
    baseURL: '/api', // Vite proxy will handle this
    timeout: 5000
})

// Request interceptor
service.interceptors.request.use(
    config => {
        return config
    },
    error => {
        console.log(error)
        return Promise.reject(error)
    }
)

// Response interceptor
service.interceptors.response.use(
    response => {
        const res = response.data
        // Assuming backend returns { code: 0, data: ..., msg: ... }
        if (res.code !== 0 && res.code !== 200) { // Adjust based on your backend success code
            ElMessage({
                message: res.msg || 'Error',
                type: 'error',
                duration: 5 * 1000
            })
            return Promise.reject(new Error(res.msg || 'Error'))
        } else {
            return res.data
        }
    },
    error => {
        console.log('err' + error)
        ElMessage({
            message: error.message,
            type: 'error',
            duration: 5 * 1000
        })
        return Promise.reject(error)
    }
)

export default service
