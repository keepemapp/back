from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork


def send_welcome_email(
    cmd, user_uow: AbstractUnitOfWork
):
    """Sends welcome email"""
    raise NotImplementedError