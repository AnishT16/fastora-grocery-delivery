from rest_framework import status
from rest_framework.exceptions import APIException


class FastoraException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A business rule violation occurred.'
    default_code = 'business_error'


class InsufficientStockError(FastoraException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Insufficient stock available for the requested product.'
    default_code = 'insufficient_stock'


class ProductNotFoundError(FastoraException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested product or inventory record does not exist.'
    default_code = 'product_not_found'


class InvalidQuantityError(FastoraException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Requested quantity must be a positive integer greater than zero.'
    default_code = 'invalid_quantity'


class SlotNotAvailableError(FastoraException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'The selected delivery slot is either full, closed, or past its cutoff time.'
    default_code = 'slot_not_available'


class ZoneNotServiceableError(FastoraException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The specified delivery address is outside all active delivery zones.'
    default_code = 'zone_not_serviceable'


class BatchCapacityExceededError(FastoraException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Cannot add order: delivery batch has reached maximum order capacity.'
    default_code = 'batch_capacity_exceeded'


class InvalidBatchOperationError(FastoraException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid batch transition or state.'
    default_code = 'invalid_batch_operation'


class DeliveryPartnerNotFoundError(FastoraException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The specified delivery partner does not exist or does not hold the delivery_partner role.'
    default_code = 'delivery_partner_not_found'


class EmptyCartError(FastoraException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Cannot checkout with an empty cart.'
    default_code = 'empty_cart'


class AddressNotFoundError(FastoraException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The specified delivery address was not found.'
    default_code = 'address_not_found'


class CODNotAllowedError(FastoraException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Cash on Delivery (COD) is currently disabled in your delivery area.'
    default_code = 'cod_not_allowed'


class PaymentVerificationError(FastoraException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Payment verification failed.'
    default_code = 'payment_verification_error'


class OrderNotFoundError(FastoraException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The specified order does not exist.'
    default_code = 'order_not_found'


class InvalidOrderOperationError(FastoraException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'The requested operation cannot be performed on this order.'
    default_code = 'invalid_order_operation'



