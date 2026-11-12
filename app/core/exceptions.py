"""Custom exceptions shared across the Calorify modules.

Services raise these instead of returning ``None`` sentinels, so routes
can react to specific failures while unexpected errors keep propagating.
"""


class CalorifyError(Exception):
    """Base class for all application-specific errors."""


class EmailAlreadyRegisteredError(CalorifyError):
    """Raised when registering with an email that already has an account."""


class InvalidMealTypeError(CalorifyError):
    """Raised when a meal type is not breakfast, lunch, dinner or snack."""


class NutritionProviderError(CalorifyError):
    """Base class for failures inside a nutrition provider."""


class ProviderNotConfiguredError(NutritionProviderError):
    """Raised when a provider's required API key is missing."""
