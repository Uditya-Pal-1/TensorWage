"""Small standard-library Ridge regression used by TensorWage."""


class SalaryModel:
    def __init__(self, education_levels, job_titles, weights):
        self.education_levels = education_levels
        self.job_titles = job_titles
        self.weights = weights

    def _features(self, education, job_title, experience):
        values = [1.0, float(experience) / 25.0]
        values.extend(1.0 if education == level else 0.0 for level in self.education_levels)
        values.extend(1.0 if job_title == title else 0.0 for title in self.job_titles)
        return values

    def predict_one(self, record):
        values = self._features(
            record["Education Level"], record["Job Title"], record["Years of Experience"]
        )
        return max(0.0, sum(weight * value for weight, value in zip(self.weights, values)) * 1000.0)


def fit_ridge(records, regularization=1.0):
    education_levels = sorted({record["Education Level"] for record in records})
    job_titles = sorted({record["Job Title"] for record in records})
    feature_count = 2 + len(education_levels) + len(job_titles)
    matrix = [[0.0] * feature_count for _ in range(feature_count)]
    target = [0.0] * feature_count

    for record in records:
        values = [1.0, float(record["Years of Experience"]) / 25.0]
        values.extend(1.0 if record["Education Level"] == level else 0.0 for level in education_levels)
        values.extend(1.0 if record["Job Title"] == title else 0.0 for title in job_titles)
        salary_thousands = float(record["Salary"]) / 1000.0
        for row_index, value in enumerate(values):
            target[row_index] += value * salary_thousands
            for column_index, other in enumerate(values):
                matrix[row_index][column_index] += value * other

    # The intercept stays unpenalized; a small ridge penalty stabilizes sparse job titles.
    for index in range(1, feature_count):
        matrix[index][index] += regularization

    weights = _solve(matrix, target)
    return SalaryModel(education_levels, job_titles, weights)


def _solve(matrix, target):
    """Solve a dense linear system with partial pivoting."""
    size = len(target)
    augmented = [row[:] + [target[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Training features are not identifiable; add more data.")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        for index in range(column, size + 1):
            augmented[column][index] /= pivot_value
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                for index in range(column, size + 1):
                    augmented[row][index] -= factor * augmented[column][index]
    return [augmented[index][size] for index in range(size)]
