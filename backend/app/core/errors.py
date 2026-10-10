class SeedPending(Exception):
    """The player's rating seed is still being fetched"""

class ChartNotFoundForRating(Exception):
    """No Charts were found within the player's search rating."""

class MatchNotFound(Exception):
    def __init__(self, match_id: int):
        super().__init__(f"Match {match_id} not found.")
