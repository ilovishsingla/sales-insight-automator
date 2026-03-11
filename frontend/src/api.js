import axios from "axios";

const getBackendUrl = () => {
  // Prefer explicit BACKEND_URL, fall back to Vite-specific var, then localhost.
  return (
    import.meta.env.VITE_BACKEND_URL ||
    import.meta.env.BACKEND_URL ||
    "http://localhost:8000"
  );
};

export async function analyzeSales(file, email) {
  const backendUrl = getBackendUrl();
  const formData = new FormData();
  formData.append("file", file);
  formData.append("email", email);

  const response = await axios.post(`${backendUrl}/analyze`, formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });

  return response.data;
}

