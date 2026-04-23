import numpy as np

class MultiArmedBanditExperience:
    def __init__(self, data, epsilon=0.5, ratings_weight=0.0, experience_weight=0.0):
        self.data = data
        self.epsilon = epsilon
        self.ratings_weight = ratings_weight
        self.experience_weight = experience_weight

        # Normalize Ratings and Experience
        self.data['Normalized Ratings'] = (self.data['Ratings'] - self.data['Ratings'].min()) / (self.data['Ratings'].max() - self.data['Ratings'].min())
        self.data['Normalized Experience'] = (self.data['Experience'] - self.data['Experience'].min()) / (self.data['Experience'].max() - self.data['Experience'].min())

        # Compute composite scores
        self.data['Composite Score'] = self.data['Normalized Ratings'] * self.ratings_weight + self.data['Normalized Experience'] * self.experience_weight

        # Initialize dictionaries to keep track of composite scores and counts for each doctor
        self.scores = self.data.groupby(['Doctor Speciality', 'Doctor Name'])['Composite Score'].mean().to_dict()
        self.counts = self.data.groupby(['Doctor Speciality', 'Doctor Name'])['Composite Score'].count().to_dict()

    def recommend_doctor(self, specialists):
        recommendations = {}
        for specialist in specialists:
            doctors = self.data[self.data['Doctor Speciality'] == specialist]
            if doctors.empty:
                recommendations[specialist] = "No doctors available for this specialty."
                continue

            # Sort doctors by composite score in descending order
            sorted_doctors = doctors.sort_values(by='Composite Score', ascending=False).head(5)
            top_doctors = []
            recommended_names = set()  # Set to store recommended doctor names

            for _ in range(5):  # Select top 5 doctors based on stochastic policy
                if np.random.rand() < self.epsilon:  # Explore
                    # Randomly choose a doctor
                    recommendation = doctors.sample()
                else:  # Exploit
                    max_score = -np.inf
                    for index, row in doctors.iterrows():
                        key = (specialist, row['Doctor Name'])
                        if self.scores[key] > max_score and row['Doctor Name'] not in recommended_names:
                            max_score = self.scores[key]
                            recommendation = row.to_frame().T
                            recommended_names.add(row['Doctor Name'])  # Add doctor name to set of recommended names

                doctor_name = recommendation['Doctor Name'].iloc[0]
                doctor_rating = recommendation['Ratings'].iloc[0]
                doctor_experience = recommendation['Experience'].iloc[0]
                top_doctors.append((doctor_name, doctor_rating, doctor_experience))

            recommendations[specialist] = top_doctors

        return recommendations

