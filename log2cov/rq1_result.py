import evaluation

def main():
    print("\nsalt unit")
    evaluation.validate_resolved_may('salt_unit_initial', 'salt', 'unit')
    print("\nsalt integration")
    evaluation.validate_resolved_may('salt_integration', 'salt', 'integration')
    print("\nnova unit")
    evaluation.validate_resolved_may('nova_unit_initial', 'nova', 'unit')
    print("\nnova functional")
    evaluation.validate_resolved_may('nova_functional', 'nova', 'functional')
    print("\nhomeassistant unit")
    evaluation.validate_resolved_may('homeassistant_unit_initial', 'homeassistant', 'unit')

if __name__ == "__main__":
    print("RQ1 - Resolve Uncertainty Result")
    main()