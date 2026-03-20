class TagSystem:
    """
    Class that works like an enum to list all the tags that can be used in the system. It is not an enum because we want to be able to add tags without modifying the code of the class.
    """

    # Tag to identify scenarios that were created for importing a scenario in an external lab
    # Value is the id of the scenario that was imported
    SCENARIO_IMPORTER_TAG_KEY = "gws_import_scenario_id"
