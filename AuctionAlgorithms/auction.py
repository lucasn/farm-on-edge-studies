from random import randint

n = 4
epsilon = 0.5
benefit_range = (20, 30)

def check_for_happiness(benefits, prices, assignments):
    for person, obj in enumerate(assignments):
        actual_value = benefits[person][obj] - prices[obj]

        best_value = actual_value
        best_object = obj
        for actual_obj in range(n):
            value = benefits[person][actual_obj] - prices[actual_obj]
            if value > best_value:
                best_value = value
                best_object = actual_obj
        
        if actual_value < (best_value - epsilon):
            #print(f'Best Value: {best_value}')
            return person, best_object
    
    return None, None


def find_second_best_object(person, benefits, prices, best_object):
    second_best_object = None
    second_best_value = -100000
    for actual_object in range(n):
        if actual_object != best_object:
            actual_value = benefits[person][actual_object] - prices[actual_object]
            if actual_value > second_best_value:
                second_best_value = actual_value
                second_best_object = actual_object

    return second_best_object



def log_matrix(matrix):
    for line in matrix:
        for value in line:
            log.write(str(value) + ' ')
        log.write('\n')

def log_array(array):
    for value in array:
        log.write(str(value) + ' ')
    log.write('\n')


log = open('./log.txt', 'w')

# initialize benefits with random values
benefits = []
for i in range(n):
    person_i_benefits = []
    for j in range(n):
        benefit = randint(benefit_range[0], benefit_range[1])
        person_i_benefits.append(benefit)
    benefits.append(person_i_benefits)

log.write('Benefits\n')
log_matrix(benefits)


# initialize all prices with zero
prices = []
for i in range(n):
    prices.append(0)

log.write('\nPrices\n')
log_array(prices)

# assign each person to an object arbitrarily
assignments = []
for i in range(n):
    assignments.append(i)

log.write('\nAssignments\n')
log_array(assignments)

# for i in assignments:
#     print(i, end=' ')
# print()


# check for a person that is not happy
person, desired_obj = check_for_happiness(benefits, prices, assignments)


while person is not None:
    
    # find owner of the object that the unhappy person wants
    desired_obj_owner = None
    for p, obj in enumerate(assignments):
        if obj == desired_obj:
            desired_obj_owner = p

    log.write(f'\nPerson {person} wants object {desired_obj} of the owner {desired_obj_owner}\n')

    # change objects
    aux = assignments[person]
    assignments[person] = assignments[desired_obj_owner]
    assignments[desired_obj_owner] = aux

    # find second best object
    second_best_object = find_second_best_object(person, benefits, prices, desired_obj)

    log.write(f'The second best object is {second_best_object}\n')

    # update value of the chosen object
    increment = (benefits[person][desired_obj] - prices[desired_obj]) \
              - (benefits[person][second_best_object] - prices[second_best_object]) \
              + epsilon
    prices[desired_obj] += increment

    log.write(f'The new price is {prices[desired_obj]}\n')

    # check again for a person that is not happy
    person, desired_obj = check_for_happiness(benefits, prices, assignments)

print('Prices')
for price in prices:
    print(price, end=' ')
print()
print()

for person, obj in enumerate(assignments):
    print(f'Person {person} -> Object {obj}')

log.write('\nPrices\n')
log_array(prices)

log.write('\nAssignments\n')
log_array(assignments)

log.close()