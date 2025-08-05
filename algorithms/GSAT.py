"""
Created on Sun Apr 21 20:22:24 2024

@author: Sergio
"""

import subprocess
import random
import tempfile
import os
import shutil

class GSAT:
    # Initialization method with parameters to define the SAT problem
    def __init__(self, variables, clauses, clauseLength, seed):
        self.variables = variables  # Number of variables in the formula
        self.clauses = clauses       # Number of clauses in the formula
        self.clauseLength = clauseLength  # Number of literals per clause
        self.seed = seed            # Seed for randomness
        self.formula = self.generate_random_model()  # Generate the initial random SAT formula

    # Generates a random SAT model using an external program
    def generate_random_model(self):
        temp_dir = tempfile.mkdtemp()
        file_formula = os.path.join(temp_dir, "random_formula.txt")
        try:
            path_generator_model = "./generator/communityAttachment/random"  # Path to the external model generator
            arguments = ['-n', str(self.variables), '-m', str(self.clauses),
                        '-k', str(self.clauseLength), '-s', str(self.seed)]
            process = subprocess.Popen([path_generator_model] + arguments, stdout=subprocess.PIPE)
            output, _ = process.communicate()
            decoded_output = output.decode("utf-8")
            with open(file_formula, "w") as file:
                file.write(decoded_output)
            formula = [[int(value) for value in line.split()[:-1]] for line in decoded_output.splitlines()[6:]]
            return formula
        finally:
            shutil.rmtree(temp_dir)

    # Evaluate a given variable assignment against the formula
    def evaluate_formula(self, assignment):
        satisfied = {clause+1: False for clause in range(self.clauses)}
        for clause in range(1, self.clauses + 1):
            satisfied[clause] = False
            for literal in self.formula[clause-1]:
                if (literal > 0 and assignment[abs(literal)]) or (literal < 0 and not assignment[abs(literal)]):
                    satisfied[clause] = True
                    break
        return satisfied

    # Get a dictionary linking variables to the clauses they appear in
    def get_variable_clauses(self, assignment):
        variable_clauses = {}
        score_clauses = {}
        for clause_index, clause in enumerate(self.formula, start=1):
            for literal in clause:
                if assignment[abs(literal)]:
                    variable = literal
                else:
                    variable = -literal
                if variable not in variable_clauses:
                    variable_clauses[variable] = []
                variable_clauses[variable].append(clause_index)
                if clause_index not in score_clauses:
                    score_clauses[clause_index] = 0
                if variable > 0:
                    score_clauses[clause_index] += 1
        return variable_clauses, score_clauses

    # Count how many clauses are satisfied in total
    def get_satisfied_total(self, satisfied):
        return sum(value for value in satisfied.values())

    # Main method to solve the SAT problem using a max flips and max tries approach
    def solve(self, max_flips, max_tries):
        clause_variable_info = {}
        for clause_idx, clause in enumerate(self.formula, start=1):
            var_indices = {}
            for i, lit in enumerate(clause):
                var = abs(lit)
                var_indices[var] = i
            clause_variable_info[clause_idx] = var_indices

        for tries in range(max_tries):
            assignment = {var: random.choice([True, False]) for var in range(1, self.variables+1)}

            variable_clauses, score_clauses = self.get_variable_clauses(assignment)
            satisfied_total = sum(1 for score in score_clauses.values() if score != 0)

            if satisfied_total == self.clauses:
                return True, tries+1, 1

            for flips in range(max_flips):

                best_move = None
                best_satisfied = 0
                move_candidates = []

                for literal in variable_clauses.keys():
                    var = abs(literal)
                    current_value = assignment[var]

                    new_scores = {}
                    new_satisfied = satisfied_total

                    affected_clauses = variable_clauses.get(var if current_value else -var, []) + \
                                    variable_clauses.get(-var if current_value else var, [])

                    for clause in affected_clauses:
                        old_score = score_clauses[clause]
                        literal_sign = 1 if (var in self.formula[clause-1]) else -1

                        if (current_value and literal_sign > 0) or (not current_value and literal_sign < 0):
                            new_score = old_score - 1 if old_score != 0 else 0
                        else:
                            new_score = old_score + 1 if old_score != 3 else 3

                        if old_score == 1 and new_score == 0:
                            new_satisfied -= 1
                        elif old_score == 0 and new_score == 1:
                            new_satisfied += 1

                        new_scores[clause] = new_score

                    move_info = {
                        'var': var,
                        'new_scores': new_scores,
                        'new_satisfied': new_satisfied,
                        'old_key': var if current_value else -var,
                        'new_key': -var if current_value else var
                    }
                    move_candidates.append(move_info)

                    if new_satisfied > best_satisfied:
                        best_satisfied = new_satisfied
                        best_move = move_info

                assignment[best_move['var']] = not assignment[best_move['var']]

                if best_move['old_key'] in variable_clauses:
                    if best_move['new_key'] in variable_clauses:
                        variable_clauses[best_move['old_key']], variable_clauses[best_move['new_key']] = \
                            variable_clauses[best_move['new_key']], variable_clauses[best_move['old_key']]
                    else:
                        variable_clauses[best_move['new_key']] = variable_clauses.pop(best_move['old_key'])

                for clause, score in best_move['new_scores'].items():
                    score_clauses[clause] = score
                satisfied_total = best_move['new_satisfied']

                if satisfied_total == self.clauses:
                    return True, tries+1, flips+1

        return False, max_tries, max_flips
