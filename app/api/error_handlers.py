from fastapi import HTTPException

from app.core.exceptions import (
    CannotCloseDealWithZeroAmountException,
    ConflictException,
    ContactHasActiveDealsException,
    ContactNotFoundException,
    DealNotFoundException,
    InvalidDealStageTransitionException,
    NotFoundException,
    PermissionDeniedException,
    TaskDueDateInPastException,
    UserNotMemberOfOrganizationException,
    ValidationException,
)


def map_domain_exception_to_http(domain_exception: Exception) -> HTTPException:
    """Преобразует доменное исключение в HTTP исключение"""

    if isinstance(
            domain_exception, (NotFoundException, ContactNotFoundException, DealNotFoundException)
    ):
        return HTTPException(status_code=404, detail=str(domain_exception))

    elif isinstance(domain_exception, (PermissionDeniedException, UserNotMemberOfOrganizationException)):
        return HTTPException(status_code=403, detail=str(domain_exception))

    elif isinstance(
            domain_exception,
            (
                    ValidationException,
                    InvalidDealStageTransitionException,
                    CannotCloseDealWithZeroAmountException,
                    TaskDueDateInPastException,
            ),
    ):
        return HTTPException(status_code=400, detail=str(domain_exception))

    elif isinstance(domain_exception, (ConflictException, ContactHasActiveDealsException)):
        return HTTPException(status_code=409, detail=str(domain_exception))

    else:
        return HTTPException(status_code=500, detail="Internal server error")
