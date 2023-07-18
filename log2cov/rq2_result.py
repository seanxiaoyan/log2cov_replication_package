import evaluation

def main():
    ''' salt unit '''
    type_of_test = 'unit'
    project_name = 'salt'
    coverage_db_name = 'salt_unit_after'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)

    
    ''' nova unit '''
    type_of_test = 'unit'
    project_name = 'nova'
    coverage_db_name = 'nova_unit_after'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)


    ''' homeassistant unit '''
    type_of_test = 'unit'
    project_name = 'homeassistant'
    coverage_db_name = 'homeassistant_unit_after'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)


if __name__ == "__main__":
    print("RQ2 - Resolve Dependency Result")
    print("Accuracy after resolve dependency\n")
    main()