import React, { useState, useEffect } from "react";
import axios from "axios";
import SalaryResult from "./SalaryResult";
import SalaryChart from "./SalaryChart";

const API_BASE_URL = "https://employee-salary-prediction-1-ws7v.onrender.com"; // Your Flask backend URL

export default function SalaryForm() {
  const [formData, setFormData] = useState({
    experience: "",
    education: "",
    jobTitle: "",
    gender: "",
    age: "",
  });
  const [jobTitles, setJobTitles] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  

  useEffect(() => {
    // Fetch job titles from backend
    axios.get(`${API_BASE_URL}/job-titles`)
      .then((res) => setJobTitles(res.data.job_titles))
      .catch((err) => console.error(err));
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setPrediction(null);
    setChartData(null);

    try {
      // Predict salary
      const res = await axios.post(`${API_BASE_URL}/predict`, {
        "Years of Experience": formData.experience,
        "Education Level": formData.education,
        "Job Title": formData.jobTitle,
        "Gender": formData.gender,
        "Age": formData.age
      });
      const predictedSalary = res.data.predicted_salary;

      setPrediction(predictedSalary);

      // Fetch actual average salary for chart
      const avgRes = await axios.post(`${API_BASE_URL}/average-salary`, {
        "Job Title": formData.jobTitle
      });
      setChartData({
        actual: avgRes.data.average_salary,
        predicted: predictedSalary
      });
    } catch (error) {
      alert(error.response?.data?.error || "An error occurred");
    }
    setLoading(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 max-w-lg w-full">
      <h2 className="text-2xl font-bold mb-4 text-blue-700">Enter Your Details</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block font-medium">Years of Experience</label>
          <input
            type="number"
            name="experience"
            min="0"
            max="25"
            value={formData.experience}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded px-3 py-2"
            required
          />
        </div>

        <div>
          <label className="block font-medium">Education Level</label>
          <select
            name="education"
            value={formData.education}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded px-3 py-2"
            required
          >
            <option value="">Select</option>
            <option value="Bachelor's">Bachelor's</option>
            <option value="Masters">Masters</option>
            <option value="PhD">PhD</option>
          </select>
        </div>

        <div>
          <label className="block font-medium">Job Title</label>
          <input
            type="text"
            name="jobTitle"
            value={formData.jobTitle}
            onChange={handleChange}
            list="jobTitles"
            className="w-full border border-gray-300 rounded px-3 py-2"
            placeholder="Start typing job title..."
            required
          />
          <datalist id="jobTitles">
            {jobTitles?.map((title) => (
  <option key={title}>{title}</option>
))}
          </datalist>
        </div>

        <div>
          <label className="block font-medium">Gender</label>
          <select
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded px-3 py-2"
            required
          >
            <option value="">Select</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </div>

        <div>
          <label className="block font-medium">Age</label>
          <input
            type="number"
            name="age"
            min="23"
            max="53"
            value={formData.age}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded px-3 py-2"
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors"
        >
          {loading ? "Predicting..." : "Predict Salary"}
        </button>
      </form>

      {prediction && <SalaryResult salary={prediction} />}
      {chartData && <SalaryChart data={chartData} />}
    </div>
  );
}
