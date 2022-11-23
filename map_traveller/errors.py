class TravellerFindingExitError(Exception):
    def __init__(self):
        self.message = "Traveller is already searching for an exit"
