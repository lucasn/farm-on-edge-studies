from random import randint

n_objects = 50
n_persons = 10

infinity = 10000
epsilon = 0.5
benefit_range = (20, 30)


def main():
    # initialize benefits with random values
    benefits = []
    for i in range(n_persons):
        person_i_benefits = []
        for j in range(n_objects):
            benefit = randint(benefit_range[0], benefit_range[1])
            person_i_benefits.append(benefit)
        benefits.append(person_i_benefits)

    # initialize all prices and profits with zero
    prices = []
    profits = []
    for i in range(n_objects):
        prices.append(0)
        profits.append(0)

    # initialize the assignments lists
    assign_person = []
    assign_object = []
    for i in range(n_persons):
        # -1 means that the object/person isn't assigned
        assign_person.append(-1) 
    for i in range(n_objects):
        assign_object.append(-1)

    person = find_unassigned_person(assign_person)

    while person is not None:
        # find best and second best objects
        best_object = find_best_object(person, benefits, prices)
        second_best_object = find_best_object(person, benefits, prices, best_object)

        # calculate price increment
        best_object_value = benefits[person][best_object] - prices[best_object]
        second_best_object_value = benefits[person][second_best_object] - prices[second_best_object]
        increment = best_object_value - second_best_object_value + epsilon

        # the increment always should be positive
        assert increment > 0

        # update the price
        prices[best_object] += increment
        profits[best_object] = benefits[person][best_object] - prices[best_object]

        # condition to be a feasible assignment
        assert benefits[person][best_object] == (prices[best_object] + profits[best_object])

        # assign the best_object to the person and unassign the owner of the object if exists
        assign_person[person] = best_object
        best_object_owner = assign_object[best_object]
        assign_object[best_object] = person
        if best_object_owner != -1:
            assign_person[best_object_owner] = -1

        person = find_unassigned_person(assign_person)

    for line in benefits:
        for benefit in line:
            print(benefit, end=' ')
        print()
    print()

    for price in prices:
        print(price, end=' ')
    print()
    print()

    for p, o in enumerate(assign_person):
        print(f'{p} -> {o}')


def find_best_object(person, benefits, prices, first_best=None):
    best_object = None
    best_value = -infinity

    for actual_object in range(n_objects):
        if first_best is None or first_best != actual_object:
            actual_value = benefits[person][actual_object] - prices[actual_object]
            if actual_value > best_value:
                best_object = actual_object
                best_value = actual_value
    
    return best_object


def find_unassigned_person(persons):
    for person, obj in enumerate(persons):
        if obj == -1:
            return person
    return None

if __name__ == '__main__':
    main()