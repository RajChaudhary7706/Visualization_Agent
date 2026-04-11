import axios from "axios";

const API = axios.create({
    baseURL: "http://localhost:8000",
})

export const analyzeProject = (data) => {
    return API.post("/analyze", data);
}