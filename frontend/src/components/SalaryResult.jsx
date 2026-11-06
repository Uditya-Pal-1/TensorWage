import React from "react";

export default function SalaryResult({ salary }) {
  const usdSalary = (salary * 100).toFixed(2); // Assuming 1 USD = 100 INR

  return (
    <div className="mt-6 bg-green-100 p-4 rounded text-center">
      <h3 className="text-lg font-bold">Predicted Salary</h3>
      <p className="text-2xl text-green-700 font-semibold"> $ {salary.toLocaleString()} / year</p>
      <p className="text-lg text-gray-700">≈ ₹ {usdSalary} / year</p>
    </div>
  );
}
