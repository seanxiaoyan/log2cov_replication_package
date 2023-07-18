import evaluation

def main():

    ''' salt unit '''
    type_of_test = 'unit'
    project_name = 'salt'
    coverage_db_name = 'salt_unit_initial'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    evaluation.get_coverage_stats(coverage_db_name)
    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)

    ''' salt integration '''
    type_of_test = 'integration'
    project_name = 'salt'
    coverage_db_name = 'salt_integration'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    evaluation.get_coverage_stats(coverage_db_name)
    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)

    ''' nova unit '''
    type_of_test = 'unit'
    project_name = 'nova'
    coverage_db_name = 'nova_unit_initial'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    evaluation.get_coverage_stats(coverage_db_name)
    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)

    ''' nova functional '''
    type_of_test = 'functional'
    project_name = 'nova'
    coverage_db_name = 'nova_functional'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    evaluation.get_coverage_stats(coverage_db_name)
    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)

    ''' homeassistant unit '''
    type_of_test = 'unit'
    project_name = 'homeassistant'
    coverage_db_name = 'homeassistant_unit_initial'

    print("project name: ", project_name)
    print("type of test: ", type_of_test)

    evaluation.get_coverage_stats(coverage_db_name)
    # print accuracy statistics
    for label in ['Must', 'No', 'May']:
        evaluation.validate_coverage(label, project_name, coverage_db_name, type_of_test)


if __name__ == '__main__':
    print("Exploratory Evaluation Result\n")
    main()