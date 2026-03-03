class PatternRegistry:

    _patterns = {}

    @classmethod
    def register(cls, pattern):
        cls._patterns[pattern.name] = pattern

    @classmethod
    def get_all(cls):
        return cls._patterns.values()
