class DomainException(Exception):
    """Базовое доменное исключение"""

    pass


class NotFoundException(DomainException):
    """Ресурс не найден"""

    pass


class PermissionDeniedException(DomainException):
    """Отказано в доступе"""
    pass


class ValidationException(DomainException):
    """Ошибка валидации"""

    pass


class ConflictException(DomainException):
    """Конфликт данных"""

    pass


class ContactNotFoundException(NotFoundException):
    """Контакт не найден"""

    pass


class DealNotFoundException(NotFoundException):
    """Сделка не найдена"""

    pass


class TaskNotFoundException(NotFoundException):
    """Задача не найдена"""

    pass


class OrganizationNotFoundException(NotFoundException):
    """Организация не найдена"""

    pass


class ContactHasActiveDealsException(ConflictException):
    """Нельзя удалить контакт с активными сделками"""

    pass


class InvalidDealStageTransitionException(ValidationException):
    """Недопустимый переход стадии сделки"""

    pass


class CannotCloseDealWithZeroAmountException(ValidationException):
    """Нельзя закрыть сделку с нулевой суммой"""

    pass


class TaskDueDateInPastException(ValidationException):
    """Дата выполнения задачи не может быть в прошлом"""

    pass


class UserNotMemberOfOrganizationException(PermissionDeniedException):
    """Пользователь не является членом организации"""
    
    pass
