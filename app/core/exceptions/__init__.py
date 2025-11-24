from .domain import (
    CannotCloseDealWithZeroAmountException,
    ConflictException,
    ContactHasActiveDealsException,
    ContactNotFoundException,
    DealNotFoundException,
    DomainException,
    InvalidDealStageTransitionException,
    NotFoundException,
    OrganizationNotFoundException,
    PermissionDeniedException,
    TaskDueDateInPastException,
    TaskNotFoundException,
    UserNotMemberOfOrganizationException,
    ValidationException,
)
from .http import (
    CRMException,
    HTTPConflictException,
    HTTPNotFoundException,
    HTTPPermissionDeniedException,
    HTTPValidationException,
)

__all__ = [
    # Доменные исключения
    "DomainException",
    "NotFoundException",
    "PermissionDeniedException",
    "ValidationException",
    "ConflictException",
    "ContactNotFoundException",
    "DealNotFoundException",
    "TaskNotFoundException",
    "OrganizationNotFoundException",
    "ContactHasActiveDealsException",
    "InvalidDealStageTransitionException",
    "CannotCloseDealWithZeroAmountException",
    "TaskDueDateInPastException",
    "UserNotMemberOfOrganizationException",
    # HTTP исключения
    "CRMException",
    "HTTPNotFoundException",
    "HTTPPermissionDeniedException",
    "HTTPValidationException",
    "HTTPConflictException",
]
