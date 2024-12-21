import random
import os

def load_students_from_csv(file_path):
    students = []
    with open(file_path, 'r') as file:
        next(file)  # Skip the header line
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 6:  # Ensure the line has the correct number of parts
                tutorial_group, student_id, school, name, gender, cgpa = parts
                student = (
                    tutorial_group,
                    student_id,
                    school,
                    name,
                    gender,
                    float(cgpa)  # Convert CGPA to float
                )
                students.append(student)
    return students

def create_initial_population(students, group_size=5, target_groups=10):
    random.shuffle(students)  # Shuffle the students before grouping
    initial_population = []

    for i in range(0, len(students), group_size):
        group_chunk = students[i:i + group_size]
        if len(group_chunk) == group_size:  
            initial_population.append(group_chunk)

        if len(initial_population) >= target_groups:  # Limit to target groups
            return initial_population
    
    return initial_population[:target_groups]  # Ensure only target groups are returned

def calculate_variance(values):
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)  
    return variance

def individual_fitness_scores(group):
    # Calculate CGPA variance and normalize
    cgpa_values = [student[5] for student in group]
    cgpa_variance = calculate_variance(cgpa_values)
    normalized_cgpa_variance = min(cgpa_variance / 0.177656, 1)  

    # Calculate gender variance and normalize
    gender_values = [1 if student[4] == 'Female' else 0 for student in group]
    gender_variance = calculate_variance(gender_values)
    max_gender_variance = 0.24  # Set based on your realistic limits
    normalized_gender_variance = (gender_variance) / max_gender_variance

    # Calculate school diversity and normalize
    schools = [student[2] for student in group]
    unique_schools = len(set(schools))
    normalized_school_diversity = unique_schools / 5

    return normalized_cgpa_variance, normalized_gender_variance, normalized_school_diversity

def fitness_func(group):
    # Get individual normalized scores
    normalized_cgpa_variance, normalized_gender_variance, normalized_school_diversity = individual_fitness_scores(group)
    
    # Calculate overall fitness score as the average of the normalized values
    fitness_score = ((normalized_cgpa_variance + normalized_gender_variance + normalized_school_diversity) / 3) * 100
    return fitness_score

def select_parents(population):
    fitness_scores = [(group, fitness_func(group)) for group in population]
    # Sort by fitness score
    fitness_scores.sort(key=lambda x: x[1])
    
    # Select most fit (last) and least fit (first)
    least_fit = fitness_scores[0][0]
    most_fit = fitness_scores[-1][0]

    return most_fit, least_fit

def crossover(parent1, parent2):
    # Get individual fitness scores for CGPA and gender for each parent group
    cgpa_variance_parent1, gender_variance_parent1, _ = individual_fitness_scores(parent1)
    
    # Determine the sorting strategy based on which variance is smaller
    if gender_variance_parent1 < cgpa_variance_parent1:
        # Sort one parent by ascending CGPA, the other by descending CGPA
        parent1_sorted = sorted(parent1, key=lambda x: x[5])  # ascending by CGPA
        parent2_sorted = sorted(parent2, key=lambda x: x[5], reverse=True)  # descending by CGPA
    else:
        # Sort one parent by ascending gender, the other by descending gender
        parent1_sorted = sorted(parent1, key=lambda x: x[4])  # ascending by gender
        parent2_sorted = sorted(parent2, key=lambda x: x[4], reverse=True)  # descending by gender

    # Perform crossover: swap students at even indices
    child1 = parent1_sorted[:]
    child2 = parent2_sorted[:]
    for i in range(0, len(parent1), 2):  # Swap students at even indices
        child1[i], child2[i] = child2[i], child1[i]
    
    return child1, child2

def run_genetic_algorithm_for_group(students, target_groups=10, generations=1000):
    population = create_initial_population(students, group_size=5, target_groups=target_groups)
    
    highest_avg_fitness = 0  # Variable to keep track of the highest average fitness score
    best_generation_index = 0  # Index of the generation with the highest average fitness score
    best_population = None  # Variable to store the best population
    best_generation_info = {}  # To store best generation info for this tutorial group

    for generation in range(generations):
        new_population = []
        
        while len(new_population) < target_groups:
            parent1, parent2 = select_parents(population)
            child1, child2 = crossover(parent1, parent2)
            new_population.append(child1)
            new_population.append(child2)

            # Remove parents from the population
            population.remove(parent1)
            population.remove(parent2)
        
        # Calculate average fitness score for the generation
        avg_fitness_score = sum(fitness_func(group) for group in new_population) / len(new_population)
        
        # Check if this generation has the highest average fitness
        if avg_fitness_score > highest_avg_fitness:
            highest_avg_fitness = avg_fitness_score
            best_generation_index = generation + 1  # Store generation index (1-based)
            best_population = new_population.copy()  # Store a copy of the best population
            best_generation_info = {
                "generation": best_generation_index,
                "average_fitness": highest_avg_fitness,
                "fitness_scores": [fitness_func(group) for group in new_population]
            }

        population = new_population  # Set the new population for the next generation
    
    return best_generation_info, best_population

def save_groups_to_csv(groups, file_path='final_groups.csv'):
    file_exists = os.path.isfile(file_path)  # Check if the file already exists
    with open(file_path, 'a') as file:  # Open the file in append mode
        if not file_exists:
            # Write the header only if the file does not exist
            file.write('Group Number,Tutorial Group,Student ID,School,Name,Gender,CGPA\n')

        for group_number, group in enumerate(groups, start=1):
            for student in group:
                # Convert to list, add group number, and convert back to tuple for saving
                student_list = list(student)  
                student_list.insert(0, group_number)  # Add group number at the start
                student_row = ','.join(map(str, student_list)) + '\n'
                file.write(student_row)  # Write the row to the file

def main():
    # Load students from the CSV file
    students = load_students_from_csv('Data_sets/records.csv')
    
    # Group students by their tutorial groups
    tutorial_groups = {}
    for student in students:
        tutorial_group = student[0]
        if tutorial_group not in tutorial_groups:
            tutorial_groups[tutorial_group] = []
        tutorial_groups[tutorial_group].append(student)

    all_best_population = []  # List to hold best populations for all groups

    # Run the genetic algorithm for each tutorial group
    for group_name, group_students in tutorial_groups.items():
        best_generation_info, best_population = run_genetic_algorithm_for_group(group_students)
        
        # Append the best population for the current tutorial group
        all_best_population.extend(best_population)  # Flatten the population

        print(f'Tutorial Group: {group_name}')
        print(f'Best Generation: {best_generation_info["generation"]}')
        print(f'Average Fitness: {best_generation_info["average_fitness"]:.2f}')
        print(f'Fitness Scores: {best_generation_info["fitness_scores"]}')
        print()  # Print an extra newline for better spacing

    # Save all best groups to CSV
    save_groups_to_csv(all_best_population)  # Use the collected best populations

if __name__ == '__main__':
    main()
