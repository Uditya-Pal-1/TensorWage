import React from "react";
import { Bar } from "react-chartjs-2";
import { Chart, BarElement, CategoryScale, LinearScale } from "chart.js";

Chart.register(BarElement, CategoryScale, LinearScale);

export default function SalaryChart({ data }) {
  const chartData = {
    labels: ["Actual Avg Salary", "Predicted Salary"],
    datasets: [
      {
        label: "Salary (₹)",
        data: [data.actual, data.predicted],
        backgroundColor: ["#34d399", "#60a5fa"]
      }
    ]
  };

  const options = {
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  return (
    <div className="mt-6">
      <h3 className="text-lg font-bold text-center mb-2">Actual vs Predicted Salary</h3>
      <Bar data={chartData} options={options} />
    </div>
  );
}
