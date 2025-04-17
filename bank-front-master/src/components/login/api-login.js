import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_BASE_URL;
const loginApi = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

const signupApi = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const login = async (username, password) => {
    try {
        return await loginApi.post(
            '/api/login/', {
                username: username,
                password: password
            }
        );
    } catch (error) {
        console.error('Error during API call:', error);
        return {
            status: 401
        }
    }
};

export const signup = async (username, password, password2, init_balance) => {
    try {
        return await loginApi.post(
            '/api/signup/', {
                username: username,
                password: password,
                password2: password2,
                balance: init_balance
            }
        );
    } catch (error) {
        console.error('Error during API call:', error);
        return {
            status: 401
        }
    }
}